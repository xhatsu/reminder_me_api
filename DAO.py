# DAO.py

from datetime import datetime

from extensions import db
from models import User, Reminder

def search_user_by_email(email):
    result = User.query.filter_by(email=email).first()
    return result

def search_user_by_id(user_id):
    result = User.query.filter_by(id=user_id).first()
    return result

def add_user(username, email, password_hash):

    temp_user = User.query.filter(
        (User.username == username) | (User.email == email)
    ).first()
    if temp_user:
        raise Exception('User already exists')
    try:
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            created_at=datetime.utcnow()
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"User: {new_user} added successfully")

    except Exception as e:
        db.session.rollback()  # Roll back the session in case of an error
        raise Exception(f"An error occurred while adding new user: {e}")
    return new_user

def verify_user(username, password_hash):
    """
    Verifies a user's password.

    Args:
        username (str): The username to check.
        password_hash (str): The password to verify.

    Returns:
        User: The User object if credentials are correct, otherwise None.
    """
    user = User.query.filter_by(username=username).first()
    if user.password_hash == password_hash:
        return user
    else:
        raise Exception('Password does not match')

def add_reminder_for_user_with_id(title, message, due_date, creator_id, recipient_ids):
    """
    Adds a new reminder to the database and associates it with recipients.

    Args:
        title (str): The title of the reminder.
        message (str): The main content of the reminder.
        due_date (datetime): The date and time the reminder is due.
        creator_id (int): The ID of the user who created the reminder.
        recipient_ids (list[int]): A list of user IDs for who should receive the reminder.

    Returns:
        Reminder: The newly created Reminder object, or None if an error occurred.
    """
    try:
        # First, ensure the creator exists
        creator = User.query.get(creator_id)
        if not creator:
            raise Exception(f"Error: Creator with ID {creator_id} not found.")

        # Create the new reminder instance
        try:
            new_reminder = Reminder(
                title=title,
                message=message,
                due_date=due_date,
                created_by=creator.id,# Associate the creator object directly
                creator = creator,
            )
        except Exception as e:
            raise e

        # Find and associate all recipient users
        if recipient_ids:
            recipients = User.query.filter(User.id.in_(recipient_ids)).all()
            if not recipients:
                raise Exception("Warning: None of the recipient IDs were found.")
            new_reminder.recipients.extend(recipients)

        # Add to the session and commit to the database
        if new_reminder:
            db.session.add(new_reminder)
            db.session.commit()
            print(f"Successfully added reminder '{title}'.")
            return new_reminder
        else:
            raise Exception("Fail to create reminder.")


    except Exception as e:
        db.session.rollback()  # Roll back the session in case of an error
        raise e


def get_reminders_for_user(user_id):
    """
    Finds all reminders associated with a specific user.
    This includes reminders they created and reminders they are set to receive.

    Args:
        user_id (int): The ID of the user.

    Returns:
        dict: A dictionary containing 'created' and 'received' reminders,
              or None if the user is not found.
    """
    user = User.query.get(user_id)
    if not user:
        raise Exception(f"Error: User with ID {user_id} not found.")

    # Reminders the user is set to receive
    received_reminders = user.reminders_to_receive.all()

    # Reminders the user created
    created_reminders = user.created_reminders

    return {
        "created": created_reminders,
        "received": received_reminders
    }


def delete_reminder(reminder_id, user_id):
    """
    Deletes a reminder from the database.
    Only the user who created the reminder is permitted to delete it.

    Args:
        reminder_id (int): The ID of the reminder to delete.
        user_id (int): The ID of the user attempting to delete the reminder.

    Returns:
        bool: True if the reminder was deleted successfully, False otherwise.
    """
    try:
        # Find the reminder by its primary key
        reminder_to_delete = Reminder.query.get(reminder_id)

        if not reminder_to_delete:
            raise Exception(f"Error: Reminder with ID {reminder_id} not found.")

        # Security check: Ensure the user attempting the deletion is the creator
        if reminder_to_delete.created_by != user_id:
            raise Exception(f"Error: User {user_id} is not authorized to delete reminder {reminder_id}.")

        # Delete the reminder and commit
        db.session.delete(reminder_to_delete)
        db.session.commit()

        print(f"Successfully deleted reminder ID {reminder_id}.")
        return True

    except Exception as e:
        db.session.rollback()
        raise e

def add_recipient_to_reminder(reminder_id, user_to_add_id):
    """
    Adds a user as a recipient to an existing reminder.

    Args:
        reminder_id (int): The ID of the reminder to modify.
        user_to_add_id (int): The ID of the user to add as a recipient.

    Returns:
        bool: True if the recipient was added successfully, False otherwise.
    """
    try:
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            raise Exception(f"Error: Reminder with ID {reminder_id} not found.")

        user_to_add = User.query.get(user_to_add_id)
        if not user_to_add:
            raise Exception(f"Error: User with ID {user_to_add_id} not found.")

        print(reminder.recipients)

        # Check if the user is already a recipient
        if user_to_add in reminder.recipients:
            print(f"Info: User {user_to_add.username} is already a recipient.")
            return True # Or False, depending on desired behavior for this case

        # Add the new recipient and commit
        reminder.recipients.append(user_to_add)
        print("debug")
        db.session.commit()
        print(f"Successfully added {user_to_add.username} to reminder '{reminder.title}'.")
        return True

    except Exception as e:
        db.session.rollback()
        raise Exception(f"An error occurred while adding a recipient: {e}")

def remove_recipient_from_reminder(reminder_id, user_to_remove_id):
    """
    Removes a user as a recipient from an existing reminder.

    Args:
        reminder_id (int): The ID of the reminder to modify.
        user_to_remove_id (int): The ID of the user to remove as a recipient.

    Returns:
        bool: True if the recipient was successfully removed or was not a recipient, False otherwise.
    """
    try:
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            raise Exception(f"Error: Reminder with ID {reminder_id} not found.")

        user_to_remove = User.query.get(user_to_remove_id)
        if not user_to_remove:
            raise Exception(f"Error: User with ID {user_to_remove_id} not found.")

        # Check if the user is currently a recipient
        if user_to_remove not in reminder.recipients:
            raise Exception(f"Info: User {user_to_remove.username} is not a recipient of reminder '{reminder.title}'.")

        # Remove the recipient and commit
        reminder.recipients.remove(user_to_remove)
        db.session.commit()
        print(f"Successfully removed {user_to_remove.username} from reminder '{reminder.title}'.")
        return True

    except Exception as e:
        db.session.rollback()
        raise Exception(f"An error occurred while removing a recipient: {e}")
def get_reminders(reminder_id):
    try:
        reminder = Reminder.query.get(reminder_id)
        if not reminder:
            print(f"Error: Reminder with ID {reminder_id} not found.")
            raise Exception("Error: Reminder with ID {reminder_id} not found.")
        else:
            return reminder
    except Exception as e:
        raise Exception(f"An error occurred while getting reminders: {e}")