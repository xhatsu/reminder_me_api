# models.py

from datetime import datetime
# Import the db object from your extensions file
from extensions import db

# The junction table for the many-to-many relationship
reminder_recipients = db.Table('reminder_recipients',
                               db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                               db.Column('reminder_id', db.Integer, db.ForeignKey('reminder.id'), primary_key=True)
                               )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to reminders created BY this user
    created_reminders = db.relationship('Reminder', back_populates='creator', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at,
        }

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)

    # Foreign key to track the user who created the reminder
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship back to the User who created it
    creator = db.relationship('User', back_populates='created_reminders')

    # The many-to-many relationship for all users who will receive this reminder
    recipients = db.relationship('User', secondary=reminder_recipients,
                                 backref=db.backref('reminders_to_receive', lazy='dynamic'))

    def __repr__(self):
        return f'<Reminder {self.title}>'
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'due_date': self.due_date,
            'created_by': self.created_by,
        }