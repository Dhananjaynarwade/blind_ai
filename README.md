<<<<<<< HEAD
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
=======
# blind_ai
AI-Powered DevOps Automation Project (Future Scope Included)  

## Project Execution Steps

### Step 1: Clone the Repository

Clone the repository from GitHub to your local machine.

```bash
git clone <repository-url>
```

### Step 2: Navigate to the Project Directory

Move into the main project folder.

```bash
cd Configuration-Management-Automation-with-Ansible
```

### Step 3: Open the Actual Application Folder

In this project, the Flask application files are stored inside a separate folder. Navigate to the folder containing `app.py`.

Example:

```bash
cd project-folder
```

Verify that the folder contains:

```text
app.py
templates/
static/
requirements.txt
```

### Step 4: Create and Activate Virtual Environment (Optional)

Create a virtual environment:

```bash
python -m venv venv
```

Activate the environment.

Windows:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
source venv/bin/activate
```

### Step 5: Install Dependencies

Install the required packages.

```bash
pip install -r requirements.txt
```

If a requirements file is not available:

```bash
pip install flask
```

### Step 6: Run the Application

The application was executed using the following command:

```bash
flask --app app.py run
```

After successful execution, Flask displays output similar to:

```text
* Running on http://127.0.0.1:5000
```

Open the displayed URL in a web browser to access the application.

### Step 7: Access the Application

Visit:

```text
http://127.0.0.1:5000
```

to interact with the project.

## Screenshots and Demonstration

The following screenshots illustrate the execution of the project:

### Screenshot 1: Project Folder Structure

Insert an image showing the project files and directories.

Example:

![Project Structure](screenshots/project-structure.png)

### Screenshot 2: Command Prompt Execution

Insert a screenshot of the terminal after running:

```bash
flask --app app.py run
```

Example:

![Terminal Output](screenshots/flask-run.png)

### Screenshot 3: Application Home Page

Insert a screenshot of the application's landing page.

Example:

![Home Page](screenshots/homepage.png)

### Screenshot 4: Feature Demonstration

Include screenshots highlighting important features and functionalities of the application.

## Notes

* The Flask application files are maintained in a separate folder within the project.
* The application was tested locally using the Flask development server.
* Screenshots included in this document represent the actual execution of the project.


>>>>>>> f5d2526d2327828de24ff260e575b3feb067529d
