from app import app, User, db
import sys

def delete_user(user_id):
    """Delete a user from the database by ID"""
    with app.app_context():
        # Find the user
        user = User.query.get(user_id)
        if not user:
            print(f"Error: User with ID {user_id} not found.")
            return False
            
        # Print user details before deletion
        print(f"Found user to delete:")
        print(f"ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Email: {user.email}")
        print(f"Verified: {user.is_verified}")
        
        # Confirm deletion
        confirm = input(f"\nAre you sure you want to delete this user? (y/n): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled.")
            return False
            
        # Delete the user
        db.session.delete(user)
        db.session.commit()
        print(f"\nUser with ID {user_id} deleted successfully!")
        return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python delete_user.py <user_id>")
        print("Example: python delete_user.py 3")
        
        # Show available users
        with app.app_context():
            users = User.query.all()
            if users:
                print("\nAvailable users:")
                for user in users:
                    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")
    else:
        try:
            user_id = int(sys.argv[1])
            delete_user(user_id)
        except ValueError:
            print("Error: User ID must be a number.") 