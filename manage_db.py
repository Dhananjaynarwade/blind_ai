from app import app, User, db
import sys

def list_users():
    """List all users in the database"""
    with app.app_context():
        users = User.query.all()
        print("\nAll users in database:")
        print("======================")
        if not users:
            print("No users found in database.")
            return
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Verified: {user.is_verified}")
            print("----------------------")

def add_user(username, email, password, verified=False):
    """Add a new user to the database"""
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            print(f"Error: User with username '{username}' or email '{email}' already exists.")
            return False
            
        # Create new user
        new_user = User(username=username, email=email, is_verified=verified)
        new_user.set_password(password)
        
        # Add to database
        db.session.add(new_user)
        db.session.commit()
        
        print(f"User '{username}' with email '{email}' added successfully!")
        return True

def update_user(user_id, username=None, email=None, password=None, verified=None):
    """Update an existing user"""
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"Error: User with ID {user_id} not found.")
            return False
        
        if username:
            # Check if username is already taken by another user
            existing = User.query.filter_by(username=username).first()
            if existing and existing.id != user.id:
                print(f"Error: Username '{username}' is already taken.")
                return False
            user.username = username
        
        if email:
            # Check if email is already taken by another user
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                print(f"Error: Email '{email}' is already taken.")
                return False
            user.email = email
            
        if password:
            user.set_password(password)
            
        if verified is not None:
            user.is_verified = verified
            
        db.session.commit()
        print(f"User with ID {user_id} updated successfully!")
        return True

def delete_user(user_id):
    """Delete a user from the database"""
    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"Error: User with ID {user_id} not found.")
            return False
            
        db.session.delete(user)
        db.session.commit()
        print(f"User with ID {user_id} (username: {user.username}) deleted successfully!")
        return True

def find_user(username=None, email=None):
    """Find a user by username or email"""
    with app.app_context():
        query = User.query
        if username:
            query = query.filter(User.username.like(f"%{username}%"))
        if email:
            query = query.filter(User.email.like(f"%{email}%"))
            
        users = query.all()
        
        print(f"\nSearch results ({len(users)} users found):")
        print("======================")
        if not users:
            print("No matching users found.")
            return
            
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Verified: {user.is_verified}")
            print("----------------------")

def show_help():
    """Display help information"""
    print("\nDatabase Management Script")
    print("=========================")
    print("Available commands:")
    print("  list                             - List all users")
    print("  add <username> <email> <password> [verified]  - Add a new user")
    print("  update <id> [--username USERNAME] [--email EMAIL] [--password PASSWORD] [--verified VERIFIED]  - Update user")
    print("  delete <id>                      - Delete a user")
    print("  find [--username USERNAME] [--email EMAIL]  - Find users by username or email")
    print("  help                             - Show this help message")
    print("  exit                             - Exit the program")

def main():
    """Main CLI interface"""
    if len(sys.argv) == 1:
        # Interactive mode
        print("Database Management CLI - Type 'help' for available commands")
        while True:
            try:
                command = input("\nEnter command: ").strip().split()
                if not command:
                    continue
                    
                if command[0] == "list":
                    list_users()
                elif command[0] == "add":
                    if len(command) < 4:
                        print("Error: Not enough arguments. Usage: add <username> <email> <password> [verified]")
                        continue
                    verified = command[4] == "True" if len(command) > 4 else False
                    add_user(command[1], command[2], command[3], verified)
                elif command[0] == "update":
                    if len(command) < 2:
                        print("Error: Not enough arguments. Usage: update <id> [--username USERNAME] [--email EMAIL] [--password PASSWORD] [--verified VERIFIED]")
                        continue
                    try:
                        user_id = int(command[1])
                    except ValueError:
                        print("Error: User ID must be a number")
                        continue
                        
                    username = email = password = None
                    verified = None
                    
                    i = 2
                    while i < len(command):
                        if command[i] == "--username" and i+1 < len(command):
                            username = command[i+1]
                            i += 2
                        elif command[i] == "--email" and i+1 < len(command):
                            email = command[i+1]
                            i += 2
                        elif command[i] == "--password" and i+1 < len(command):
                            password = command[i+1]
                            i += 2
                        elif command[i] == "--verified" and i+1 < len(command):
                            verified = command[i+1] == "True"
                            i += 2
                        else:
                            print(f"Error: Unknown option '{command[i]}'")
                            i += 1
                            
                    update_user(user_id, username, email, password, verified)
                elif command[0] == "delete":
                    if len(command) < 2:
                        print("Error: Not enough arguments. Usage: delete <id>")
                        continue
                    try:
                        user_id = int(command[1])
                    except ValueError:
                        print("Error: User ID must be a number")
                        continue
                    delete_user(user_id)
                elif command[0] == "find":
                    username = email = None
                    
                    i = 1
                    while i < len(command):
                        if command[i] == "--username" and i+1 < len(command):
                            username = command[i+1]
                            i += 2
                        elif command[i] == "--email" and i+1 < len(command):
                            email = command[i+1]
                            i += 2
                        else:
                            print(f"Error: Unknown option '{command[i]}'")
                            i += 1
                            
                    find_user(username, email)
                elif command[0] == "help":
                    show_help()
                elif command[0] == "exit":
                    print("Exiting...")
                    break
                else:
                    print(f"Unknown command: {command[0]}. Type 'help' for available commands.")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {str(e)}")
    else:
        # Command line mode
        command = sys.argv[1]
        
        if command == "list":
            list_users()
        elif command == "add":
            if len(sys.argv) < 5:
                print("Error: Not enough arguments. Usage: python manage_db.py add <username> <email> <password> [verified]")
                return
            verified = sys.argv[5] == "True" if len(sys.argv) > 5 else False
            add_user(sys.argv[2], sys.argv[3], sys.argv[4], verified)
        elif command == "help":
            show_help()
        else:
            print(f"Unknown command: {command}. Type 'help' for available commands.")

if __name__ == "__main__":
    main() 