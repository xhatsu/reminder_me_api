import os
import pytest
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from routes import *
from unittest.mock import patch, MagicMock
# Import the db object from extensions.py
from extensions import db
# Import your models
from models import User, Reminder

# --- App & Database Configuration ---
app = Flask(__name__)
load_dotenv()
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:isekai1012005@localhost:5432/local_reminder_test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
# Initialize the database with the app
db.init_app(app)

# Mocking the database functions for testing purposes
def search_user_by_email(email):
    # This function will be mocked in tests
    pass
def add_user(username, email, hashed_password):
    # This function will be mocked in tests
    pass
def get_user_by_email(user_email):
    # This function calls the one we intend to mock
    return search_user_by_email(user_email)
# Register Blueprints
app.register_blueprint(api_bp)
# --- Test Function ---

# We'll use pytest for testing.
# A fixture to create a test client for the Flask app.

@pytest.fixture
def client():
    """
    Configures the Flask app for testing and yields a test client.
    Ensures the app is in testing mode.
    """
    app.config['TESTING'] = True # Enable testing mode
    with app.test_client() as client: # Create a test client
        yield client # Yield the client for tests to use

def test_add_user(client):
    request_data = {
        "username": "username2",
        "email": "verylmao@gmail.com",
        "password_hash": "veryHashedPassword",
    }

    response = client.post('/register', json=request_data)
    assert response.status_code == 201

def test_add_reminder_success(client):
    """
    Tests the successful addition of a reminder with all fields.
    """
    print("\n--- Running test_add_reminder_success ---")
    # Sample data for a successful request
    reminder_data = {
        "title": "Buy groceries",
        "due_date": "2025-07-28T19:53:03",
        "user_id": "1",
        "message": "Milk, eggs, bread",
        "recipient_ids": ["2"]
    }
    # Send a POST request to the add_reminder endpoint
    response = client.post('/reminders/add', json=reminder_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json}")

    # Assertions to verify the response
    assert response.status_code == 201 # Expect 201 Created
    assert response.json["message"] == "Reminder created successfully"
    assert response.json["reminder"]["title"] == "Buy groceries"
    assert response.json["reminder"]["created_by"] == 1

def test_add_reminder_missing_title(client):
    """
    Tests the case where the 'title' field is missing.
    """
    print("\n--- Running test_add_reminder_missing_title ---")
    # Data missing the 'title' field
    reminder_data = {
        "due_date": "2025-08-01",
        "user_id": "user123"
    }
    response = client.post('/reminders/add', json=reminder_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json}")

    assert response.status_code == 400 # Expect 400 Bad Request
    assert response.json["message"] == "Missing required field: title"

def test_add_reminder_not_json(client):
    """
    Tests the case where the request is not JSON.
    """
    print("\n--- Running test_add_reminder_not_json ---")
    # Send a request with plain text data instead of JSON
    response = client.post('/reminders/add', data="This is not JSON")
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json}")

    assert response.status_code == 400 # Expect 400 Bad Request
    assert response.json["message"] == "Request must be JSON"

def test_remove_reminder_success(client):
    """
    Tests the successful deletion of a reminder with all fields.
    """
    print("\n--- Running test_add_reminder_success ---")
    # Sample data for a successful request
    request_data = {
        "id": "1",
        "user_id": "1",
    }
    # Send a POST request to the add_reminder endpoint
    response = client.post('/reminders/remove', json=request_data)
    print(f"Response Status Code: {response.status_code}")
    print(f"Response JSON: {response.json}")

    # Assertions to verify the response
    assert response.status_code == 200 # Expect 200



# ----------- Google API Test ---------------

@patch('google.oauth2.id_token.verify_oauth2_token') # Patching where id_token is used
@patch('routes.get_user_by_email')
def test_google_signin_existing_user(mock_search_user, mock_id_token, client):
    """
    Test successful sign-in for an existing user.
    """
    # --- Arrange ---
    # Mock the Google token verification to return a valid user profile
    mock_id_token.verify_oauth2_token.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "1234567890",
        "aud": GOOGLE_CLIENT_ID,
        "email": "test.user@example.com",
        "name": "Test User",
    }

    # Mock the database function to return an existing user
    existing_user = User(
            username="Test User",
            email="test.user@example.com",
            password_hash="password_hash",
            created_at=datetime.utcnow()
        )
    mock_search_user.return_value = existing_user

    # --- Act ---
    response = client.post('/google/signin', json={"id_token": "fake_token_string"})
    print(response.json)
    # --- Assert ---
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["email"] == "test.user@example.com"
    assert json_data["username"] == "Test User"
    # mock_search_user.assert_called_once_with("test.user@example.com")


@patch('google.oauth2.id_token.verify_oauth2_token')
@patch('routes.get_user_by_email')
@patch('routes.register_user')
def test_google_signin_new_user(mock_add_user, mock_search_user, mock_id_token, client):
    """
    Test successful sign-in and registration for a new user.
    """
    # --- Arrange ---
    mock_id_token.verify_oauth2_token.return_value = {
        "sub": "0987654321",
        "aud": GOOGLE_CLIENT_ID,
        "email": "new.user@example.com",
        "name": "New User",
    }

    # Mock the database to show the user does not exist
    mock_search_user.return_value = None

    # Mock the user creation to return a new user object
    new_user_obj = User(
            username="Test User",
            email="new.user@example.com",
            password_hash="password_hash",
            created_at=datetime.utcnow()
        )
    mock_add_user.return_value = new_user_obj

    # --- Act ---
    response = client.post('/google/signin', json={"id_token": "another_fake_token"})
    print(response.json)
    # --- Assert ---
    assert response.status_code == 200
    json_data = response.get_json()


def test_google_signin_no_token(client):
    """
    Test failure when no ID token is provided in the request.
    """
    # --- Act ---
    response = client.post('/google/signin', json={})

    # --- Assert ---
    assert response.status_code == 400
    assert response.get_json()["error"] == "No ID token provided"


@patch('google.oauth2.id_token')
def test_google_signin_invalid_token(mock_id_token, client):
    """
    Test failure when the token is invalid or expired.
    """
    # --- Arrange ---
    # Mock the verification to raise a ValueError, simulating an invalid token
    mock_id_token.verify_oauth2_token.side_effect = ValueError("Invalid token")

    # --- Act ---
    response = client.post('/google/signin', json={"id_token": "invalid_token"})

    # --- Assert ---
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


@patch('google.oauth2.id_token')
def test_google_signin_wrong_audience(mock_id_token, client):
    """
    Test failure when the token's audience (aud) doesn't match the client ID.
    """
    # --- Arrange ---
    mock_id_token.verify_oauth2_token.return_value = {
        "sub": "111222333",
        "aud": "someone_elses_client_id", # Mismatched audience
        "email": "user@example.com",
        "name": "Audience User",
    }

    # --- Act ---
    response = client.post('/google/signin', json={"id_token": "wrong_aud_token"})

    # --- Assert ---
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token"


@patch('google.oauth2.id_token')
@patch('api_test.search_user_by_email')
@patch('api_test.add_user')
def test_google_signin_user_creation_error(mock_add_user, mock_search_user, mock_id_token, client):
    """
    Test failure during the user registration process.
    """
    # --- Arrange ---
    mock_id_token.verify_oauth2_token.return_value = {
        "sub": "44556677",
        "aud": GOOGLE_CLIENT_ID,
        "email": "fail.user@example.com",
        "name": "Fail User",
    }
    mock_search_user.return_value = None
    # Simulate a failure in the database layer during user creation
    mock_add_user.side_effect = UserCreationError("Failed to write to DB")

    # --- Act ---
    response = client.post('/google/signin', json={"id_token": "a_valid_token_for_new_user"})

    # --- Assert ---
    assert response.status_code == 400
    assert "Failed to write to DB" in response.get_json()["error"]


@patch('google.oauth2.id_token')
@patch('api_test.search_user_by_email')
def test_google_signin_generic_server_error(mock_search_user, mock_id_token, client):
    """
    Test a generic 500 error if something unexpected happens.
    """
    # --- Arrange ---
    mock_id_token.verify_oauth2_token.return_value = {
        "sub": "999888777",
        "aud": GOOGLE_CLIENT_ID,
        "email": "error.user@example.com",
        "name": "Error User",
    }
    # Simulate a generic, unexpected exception from the database function
    mock_search_user.side_effect = Exception("Database connection lost")

    # --- Act ---
    response = client.post('/google/signin', json={"id_token": "some_token"})

    # --- Assert ---
    assert response.status_code == 500
    assert response.get_json()["error"] == "An internal server error occurred"
