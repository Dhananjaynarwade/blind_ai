import os
import sys
import json

def setup_email_config():
    print("====== Flask Auth Email Setup ======")
    print("This script will help you configure email sending for your Flask Auth app.")
    print("\nYou'll need a Gmail account with an 'App Password' configured.")
    print("1. Go to your Google Account Security settings: https://myaccount.google.com/security")
    print("2. Make sure 2-Step Verification is enabled")
    print("3. Create an App Password under 'App passwords'")
    
    email = input("\nEnter your Gmail address: ")
    password = input("Enter your Gmail App Password: ")
    
    # Create a config file
    config = {
        "MAIL_USERNAME": email,
        "MAIL_PASSWORD": password,
        "TESTING": False
    }
    
    # Save to config file
    with open('email_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("\nEmail configuration saved to email_config.json")
    print("Now updating config.py to use these settings...")
    
    # Update config.py to use the email_config.json file
    with open('config.py', 'r') as f:
        lines = f.readlines()
    
    with open('config.py', 'w') as f:
        for line in lines:
            if "MAIL_USERNAME = " in line:
                f.write("    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or '{}'\n".format(email))
            elif "MAIL_PASSWORD = " in line:
                f.write("    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '{}'\n".format(password))
            elif "TESTING = " in line:
                f.write("    TESTING = False\n")
            else:
                f.write(line)
    
    print("\nConfiguration complete! You can now run your Flask app:")
    print("python app.py")
    
    # Ask if they want to run the app now
    run_now = input("\nDo you want to run the application now? (y/n): ")
    if run_now.lower() == 'y':
        # Run the app
        print("Starting Flask application...")
        os.system("python app.py")

if __name__ == "__main__":
    setup_email_config() 