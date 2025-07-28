from flask import Blueprint, jsonify, request
from DAO import *
from models import *

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def index():
    """
    Deny request
    """
    return jsonify({"message": "Request Denied"}), 404

@api_bp.route('/users/<string:user_email>', methods=['GET'])
def get_user_by_email(user_email):
    """
    GET /users/<user_id>: Returns a single user by their ID.
    """
    user = search_user_by_email(user_email)
    print(user)
    if user:
        return jsonify(user.to_dict()), 200
    return jsonify({"message": "User not found"}), 404
@api_bp.route('/reminder/<int:user_id>', methods=['GET'])
def get_reminder_by_user_id(user_id):

    reminders = get_reminders_for_user(user_id)

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

@api_bp.route('/register', methods=['POST'])
def register_user():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400
    data = request.get_json()
    required_fields = ['username', 'email', 'password_hash']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    username = data['username']
    email = data['email']
    hashed_password = data['password_hash']
    try:
        new_user = add_user(username, email, hashed_password)
    except Exception as e:
        return jsonify({"message": "An error occurred", "error": str(e)}), 500
    if not new_user:
        return jsonify({"message": "User creation failed"}), 500
    return jsonify({"message": f"User {new_user.username} registered successfully"}), 201