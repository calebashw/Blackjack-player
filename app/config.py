import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')  # Load from .env for security
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')  # Database connection
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Allow cookies to be sent in cross-origin requests
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
