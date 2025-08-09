import os
import datetime
from datetime import timedelta, timezone
from functools import wraps
from flask import Blueprint, jsonify, request
from flask.cli import load_dotenv
from DAO import *
from models import *
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt

load_dotenv()
api_bp = Blueprint('api', __name__)
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
SECRET_KEY = os.getenv('SECRET_KEY')
print(SECRET_KEY)
class UserCreationError(Exception):
    pass

# -------- Support functions ---------
def jwt_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"msg": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ")[1]
        print(token)
        try:
            print(SECRET_KEY)
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user_id = payload.get("sub")
            request.user_email = payload.get("email")
        except jwt.ExpiredSignatureError:
            return jsonify({"msg": "Token expired"}), 401
        except jwt.InvalidTokenError as InvalidTokenError:
            return jsonify({"msg": "Invalid token", "error": str(InvalidTokenError) }), 401

        return func(*args, **kwargs)

    return wrapper

def get_user_by_email(user_email):
    try:
        user = search_user_by_email(user_email)
    except Exception as e:
        print(e)
        return None
    # print(user)
    return user

def register_user(username, email):
    hashed_password = "hashedPassword"
    try:
        new_user = add_user(username, email, hashed_password)
        if not new_user:
            raise UserCreationError("Database returned no user object after creation.")
        return new_user
    except Exception as e:
        raise UserCreationError(f"An error occurred while registering user: {e}")

# ------- API Routes

@api_bp.route('/')
def index():
    """
    Deny request
    """
    return jsonify({"message": "Request Denied"}), 404

@api_bp.route('/reminders/get', methods=['GET'])
@jwt_required
def get_reminder_by_user_id():
    user_id = getattr(request, "user_id", None)
    try:
        reminders = get_reminders_for_user(user_id)
    except Exception as e:
        return jsonify({"message": str(e)}), 404
    if reminders:
        reminder_data_created = [reminder.to_dict() for reminder in reminders["created"]]
        reminder_data_received = [reminder.to_dict() for reminder in reminders["received"]]
        data = {
            "created": reminder_data_created,
            "received": reminder_data_received,
        }
        return jsonify(data), 200
    return jsonify({"message": "Reminder not found"}), 404

@api_bp.route('/reminders/add', methods=['POST'])
@jwt_required
def add_reminder():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()

    # --- 1. Basic Validation ---
    # Check for required fields
    required_fields = ['title', 'due_date', 'user_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400

    title = data['title']
    user_id = data['user_id']
    message = data.get('message')  # Optional field
    recipient_ids = data.get('recipient_ids') # Optional field for shared reminders

    # --- 2. Validate Data Types and Formats ---
    try:
        # Assuming due_date comes in ISO format (e.g., "YYYY-MM-DDTHH:MM:SS")
        # You might need to adjust the format based on your client
        due_date = datetime.fromisoformat(data['due_date'])
    except ValueError:
        return jsonify({"message": "Invalid due_date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)."}), 400

    # Optional: Validate if user_id and recipient_id exist in your User table

    user = search_user_by_id(user_id)
    if not user:
        return jsonify({"message": f"User {user_id} not found"}), 404
    # --- 3. Create and Save the Reminder ---
    try:
        new_reminder = add_reminder_for_user_with_id(title, message, due_date, user_id, recipient_ids)
        data = {
            "message": "Reminder created successfully",
            "reminder": new_reminder.to_dict() # Return the created reminder's data
        }
        return jsonify(data), 201 # 201 Created status code

    except Exception as e:
        db.session.rollback() # Rollback in case of an error during commit
        return jsonify({"message": "An error occurred while creating the reminder", "error": str(e)}), 500

@api_bp.route('/reminders/remove', methods=['POST'])
@jwt_required
def remove_reminder():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400
    data = request.get_json()
    required_fields = ['id', 'user_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    # Check for user and reminder
    try:
        user = search_user_by_id(data['user_id'])
        if not user:
            return jsonify({"message": f"User {data['user_id']} not found"}), 404
        reminder = get_reminders(data['id'])
        if not reminder:
            return jsonify({"message": "Reminder not found"}), 404
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500
    # Remove reminder
    try:
        delete_reminder(reminder.id, user.id)
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500
    return jsonify({"message": "Reminder removed successfully"}), 200

@api_bp.route('/google/signin', methods=['POST'])
def google_signin():
    # The ID token is sent in the request body
    token = request.json.get("id_token")
    if not token:
        return jsonify({"error": "No ID token provided"}), 400
    try:
        # Validate the token
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        # Check if the token was issued for your client ID
        # if idinfo["aud"] != GOOGLE_CLIENT_ID:
        #     raise ValueError("Invalid aud claim.")

        # The ID token contains the user's profile information
        userid = idinfo["sub"]
        email = idinfo["email"]
        name = idinfo["name"]
    except ValueError as e:
        # The token is invalid, expired, or has a different aud claim
        return jsonify({"error": str(e)}), 401
        # At this point, the user is authenticated.
        # You can now create or retrieve their account in your database.
    try:
        user = get_user_by_email(email)
        if user is None:
            user = register_user(name, email)
        if user:
            payload = {
                'sub': str(user.id),
                'email': user.email,
                'exp': datetime.now(timezone.utc) + timedelta(hours=24),
                }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            print(token)
            return jsonify(
                {
                    "token": token,
                }
            ), 200
    except UserCreationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
