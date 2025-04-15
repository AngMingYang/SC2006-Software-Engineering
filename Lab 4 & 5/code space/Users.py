from User_Database_Interface import User_Database_Interface

class User:

    homepage = "logout"
    def __init__(self, username, email, first_name, last_name, threshold=101):
        self.username = username
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.threshold = threshold

    def get_homepage(self):
        """Abstract method to be overridden."""
        raise NotImplementedError("Subclasses should implement this method.")

    def get_type(self):
        """Return the type of the user."""
        raise NotImplementedError("Subclasses should implement this method.")

class Commuter(User):
    homepage = "commuter_home"

    def get_homepage(self):
        return self.homepage

    def get_type(self):
        return "Commuter"

class LTA_Manager(User):
    homepage = "lta_home"

    def get_homepage(self):
        return self.homepage

    def get_type(self):
        return "LTA_Manager"

class Admin(User):
    homepage = "admin_home"

    def get_homepage(self):
        return self.homepage

    def get_type(self):
        return "Admin"

class UserFactory:
    @staticmethod
    def create_user(username):
        user_info = User_Database_Interface.get_user_details(username)
        if not user_info:
            return None  # User not found

        # Unpack user details (7 items)
        username, password, email, first_name, last_name, threshold, user_type= user_info

        # Mapping user types to their respective classes
        user_classes = {
            "Commuter": Commuter,
            "LTA_Manager": LTA_Manager,
            "Admin": Admin
        }

        # Default to Commuter if user type is not recognized
        user_class = user_classes.get(user_type, Commuter)

        # Create and return an instance of the appropriate user class
        return user_class(username, email, first_name, last_name, threshold)
