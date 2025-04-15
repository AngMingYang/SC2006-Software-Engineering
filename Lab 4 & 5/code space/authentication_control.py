import bcrypt
from User_Database_Interface import User_Database_Interface

class authentication:

    @staticmethod
    def verify_password(username, entered_password):
        """Verify the password by fetching the user's details and comparing hashed password."""
        
        # Fetch user details using the User_Database_Interface
        user_details = User_Database_Interface.get_user_details(username)
        
        if user_details:
            # Extract the stored password from the user details
            stored_password = user_details[1]  # Index 1 corresponds to the Password field
            
            # Check if the entered password matches the stored password
            if bcrypt.checkpw(entered_password.encode(), stored_password):
                print(f"Password for {username} is correct.")
                return True
            else:
                print(f"Password for {username} is incorrect.")
                return False
        else:
            print(f"User {username} not found.")
            return False
