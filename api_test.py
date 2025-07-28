import os
import pytest
from dotenv import load_dotenv
from flask import Flask, jsonify
from routes import *

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

# Initialize the database with the app
db.init_app(app)

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


# To run these tests:
# 1. Save the code as a Python file (e.g., test_reminders.py).
# 2. Make sure you have Flask and pytest installed:
#    pip install Flask pytest
# 3. Run pytest from your terminal in the same directory:
#    pytest
