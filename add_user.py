from app import app, User, db

def add_user(username, email, password, verified=False):
    print(f"Attempting to add user: {username}, {email}")
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

# Example usage:
if __name__ == "__main__":
    # Change these values to add your own user
    username = "newuser"
    email = "newuser@example.com"
    password = "password123"
    verified = True  # Set to True to bypass email verification
    
    print("Starting add_user.py script")
    result = add_user(username, email, password, verified)
    print(f"Add user result: {result}")
    
    # Let's try to query the database to see all users
    with app.app_context():
        users = User.query.all()
        print(f"Number of users in database: {len(users)}")
        for user in users:
            print(f"User in DB: {user.id}, {user.username}, {user.email}, Verified: {user.is_verified}") 