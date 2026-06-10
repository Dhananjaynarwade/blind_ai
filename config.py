import os

class Config:
    # Flask config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    
    # Database config
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email config
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') != 'False'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'dhananjaynarwade1998@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'Pass@123'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    
    # Testing mode (set to False to send real emails)
    TESTING = False
