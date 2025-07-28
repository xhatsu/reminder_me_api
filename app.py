# app.py
import os
from dotenv import load_dotenv
from flask import Flask
from routes import *

# Import the db object from extensions.py
from extensions import db

# --- App & Database Configuration ---
load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:isekai1012005@localhost:5432/local_reminder_test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Initialize the database with the app
db.init_app(app)

# Register Blueprints
app.register_blueprint(api_bp)

if __name__ == '__main__':

    with app.app_context():
        db.create_all()
    app.run(debug=False)