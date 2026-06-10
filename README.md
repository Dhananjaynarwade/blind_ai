# Blind Vision - Assistive Technology Platform

A Flask-based web application providing assistive technology for the visually impaired, with secure user authentication and email verification.

## Features
- User registration with email verification
- Email verification with OTP (One-Time Password)
- Secure login system
- Password visibility toggle
- Dashboard with assistive technology features:
  - Object Detection
  - Text Recognition
  - Color Detection
  - Navigation Assistance

## Requirements
- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Flask-Mail
- PyOTP
- Werkzeug

## Installation
1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Email Configuration

By default, the application will run in "testing mode", where emails are printed to the console instead of being sent.

### Setup Email for Production Use

#### Step 1: Run the setup script
```
python setup_email.py
```
Follow the prompts to enter your Gmail address and app password.

#### Step 2: Manual Configuration
If you prefer to configure manually, edit the `config.py` file:
```python
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-16-character-app-password'
TESTING = False  # Change this to False to send real emails
```

### Gmail Setup Instructions
1. Go to your [Google Account Security Settings](https://myaccount.google.com/security)
2. Make sure 2-Step Verification is enabled
3. Under "Signing in to Google", select "App passwords"
4. Select "Mail" as the app and "Other" as the device (name it "Blind Vision")
5. Click "Generate" and Google will display a 16-character app password
6. Copy this password for use in the application

## Running the Application
1. Run the Flask application:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## How to Use
1. Register a new account with your email
2. Verify your email using the OTP code
3. Login with your verified credentials
4. Access the dashboard with assistive technology features

## Project Structure
```
project/
├── app.py              # Main application file
├── config.py           # Configuration settings
├── setup_email.py      # Email setup assistant
├── requirements.txt    # Required packages
├── instance/           # Database file location
│   └── users.db        # SQLite database file
└── templates/          # HTML templates
    ├── base.html       # Base template with layout and styling
    ├── index.html      # Home page
    ├── login.html      # Login page
    ├── register.html   # Registration page
    ├── verify_email.html # Email verification page
    └── dashboard.html  # Dashboard with features
``` 