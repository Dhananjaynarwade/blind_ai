from app import app, User, db

# Write to both console and file
with open('users_list.txt', 'w') as f:
    with app.app_context():
        users = User.query.all()
        header = "\nAll users in database:"
        separator = "======================"
        print(header)
        f.write(header + "\n")
        print(separator)
        f.write(separator + "\n")
        
        if not users:
            msg = "No users found in database."
            print(msg)
            f.write(msg + "\n")
        
        for user in users:
            id_str = f"ID: {user.id}"
            username_str = f"Username: {user.username}"
            email_str = f"Email: {user.email}"
            verified_str = f"Verified: {user.is_verified}"
            separator_line = "----------------------"
            
            print(id_str)
            f.write(id_str + "\n")
            print(username_str)
            f.write(username_str + "\n")
            print(email_str)
            f.write(email_str + "\n")
            print(verified_str)
            f.write(verified_str + "\n")
            print(separator_line)
            f.write(separator_line + "\n")
            
print("User list has been saved to users_list.txt") 