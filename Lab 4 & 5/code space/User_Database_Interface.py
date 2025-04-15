import sqlite3
import bcrypt
from flask import Flask

app = Flask(__name__)

class User_Database_Interface:
    db_path = "User_Database.db"

    @staticmethod
    def get_db():
        """Get a new database connection without using 'g'."""
        db = sqlite3.connect(User_Database_Interface.db_path, check_same_thread=False)
        db.row_factory = sqlite3.Row  # This makes it return dict-like rows.
        return db

    @staticmethod
    def close_db(db):
        """Close the database connection explicitly."""
        if db is not None:
            db.close()

    @staticmethod
    def initialise_database():
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS User (
                    Username TEXT PRIMARY KEY,
                    Password TEXT,
                    Email TEXT,
                    First_Name TEXT,
                    Last_Name TEXT,
                    Threshold INTEGER DEFAULT 101,
                    User_Type TEXT DEFAULT 'Commuter'
                )
            ''')
            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS USER_DATA (
                    Entry_No INTEGER PRIMARY KEY AUTOINCREMENT,
                    Username TEXT,
                    Start_location TEXT,
                    End_location TEXT,
                    Date TEXT
                )
            ''')

            cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS USER_NOTIFICATIONS (
                    Entry_No INTEGER,
                    Username TEXT,
                    Message TEXT,
                    Date TEXT,
                    PRIMARY KEY (Entry_No, Username)
                )
            ''')

            db.commit()
            print("Database initialised successfully.")
        except sqlite3.Error as e:
            print(f"Error initialising database: {e}")
        finally:
            User_Database_Interface.close_db(db)

    @staticmethod
    def hash_password(password):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode(), salt)
        return hashed

    @staticmethod
    def add_user(username, password, email, first_name, last_name, threshold=101, user_type="Commuter"):
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            cursor.execute('''SELECT 1 FROM User WHERE Username = ?''', (username,))
            if cursor.fetchone():
                print(f"Error: Username {username} already exists.")
                return False

            
            #cursor.execute('''SELECT 1 FROM User WHERE Email = ?''', (email,))
            #if cursor.fetchone():
            #    print(f"Error: Email {email} already exists.")
            #    return False
            

            hashed_password = User_Database_Interface.hash_password(password)

            cursor.execute(''' 
                INSERT INTO User (Username, Password, Email, First_Name, Last_Name, Threshold, User_Type)
                VALUES (?,?,?,?,?,?,?) 
            ''', (username, hashed_password, email, first_name, last_name, threshold, user_type))

            db.commit()
            print(f"User {username} added successfully as {user_type}.")
            return True

        except sqlite3.Error as e:
            print(f"Error adding user: {e}")
            return False
        finally:
            User_Database_Interface.close_db(db)
    
    @staticmethod
    def delete_table():
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            cursor.execute('''DROP TABLE IF EXISTS User''')
            db.commit()
            print("User table deleted successfully.")
        except sqlite3.Error as e:
            print(f"Error deleting table: {e}")
        finally:
            User_Database_Interface.close_db(db)

    @staticmethod
    def get_user_details(username):
        try:
            db = User_Database_Interface.get_db()

            # Debug: Check if the database connection is open
            if db:
                print("Database connection established.")
            else:
                print("Failed to establish database connection.")

            cursor = db.cursor()

            # Debug: Check if the cursor is created successfully
            if cursor:
                print("Cursor created successfully.")
            else:
                print("Failed to create cursor.")

            print(f"Looking for user: {username}")

            cursor.execute('''SELECT * FROM User WHERE Username = ?''', (username,))
            result = cursor.fetchone()

            # Debug: Check if result is fetched
            if result:
                print(f"Query result: {result}")
                return result
            else:
                print(f"User {username} not found.")
                return None

        except sqlite3.Error as e:
            print(f"Error fetching user details: {e}")
            return None

        finally:
            print("Closing the database and cursor.")
            User_Database_Interface.close_db(db)
            

    @staticmethod
    def user_exists(username=None):
        """Check if a user already exists in the database based on username."""
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            # Check if username is provided, and query accordingly
            if username:
                cursor.execute('''SELECT 1 FROM User WHERE Username = ?''', (username,))
            else:
                return False  # If no username provided, return False

            # If the query finds a matching user, return True
            return cursor.fetchone() is not None

        except sqlite3.Error as e:
            print(f"Error checking user existence: {e}")
            return False
        finally:
            User_Database_Interface.close_db(db)

    
    @staticmethod
    def get_email_from_username(username):
        """Get the email address of a user based on their username."""
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            cursor.execute('''SELECT Email FROM User WHERE Username = ?''', (username,))
            result = cursor.fetchone()

            if result:
                return result['Email']  # Return the email
            else:
                print(f"User {username} not found.")
                return None
        except sqlite3.Error as e:
            print(f"Error fetching email: {e}")
            return None
        finally:
            User_Database_Interface.close_db(db)

    @staticmethod
    def update_password(username, new_password):
        """Update the password for the user in the database."""
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            # Hash the new password
            hashed_password = User_Database_Interface.hash_password(new_password)

            cursor.execute('''UPDATE User SET Password = ? WHERE Username = ?''', (hashed_password, username))
            db.commit()

            if cursor.rowcount > 0:
                print(f"Password for user {username} updated successfully.")
                return True
            else:
                print(f"User {username} not found.")
                return False
        except sqlite3.Error as e:
            print(f"Error updating password: {e}")
            return False
        finally:
            User_Database_Interface.close_db(db)

    @staticmethod
    def update_user_details(username, email, first_name, last_name, threshold):
        """Update user details in the database."""
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            cursor.execute('''UPDATE User SET Email = ?, First_Name = ?, Last_Name = ?, Threshold = ? WHERE Username = ?''',
                        (email, first_name, last_name, threshold, username))
            db.commit()

            if cursor.rowcount > 0:
                print(f"User {username} updated successfully.")
                return True
            else:
                print(f"User {username} not found.")
                return False
        except sqlite3.Error as e:
            print(f"Error updating user details: {e}")
            return False
        finally:
            User_Database_Interface.close_db(db)

    @staticmethod
    def add_user_data(username, start_location, end_location, date):
        """Add a new entry to the USER_DATA table."""
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            # Insert the user data into the table
            cursor.execute('''
                INSERT INTO USER_DATA (Username, Start_location, End_location, Date)
                VALUES (?, ?, ?, ?)
            ''', (username, start_location, end_location, date))

            db.commit()
            print(f"User data for {username} added successfully.")
            return True

        except sqlite3.Error as e:
            print(f"Error adding user data: {e}")
            return False
        finally:
            User_Database_Interface.close_db(db)


    @staticmethod
    def get_user_data_by_history(username):
        """Retrieve user data sorted by history (date of travel)."""
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            # Query the USER_DATA table to get all the data for the specified user
            cursor.execute('''SELECT * FROM USER_DATA WHERE Username = ? ORDER BY Date DESC''', (username,))
            results = cursor.fetchall()

            if results:
                return results
            else:
                print(f"No data found for user {username}.")
                return None

        except sqlite3.Error as e:
            print(f"Error fetching user data by history: {e}")
            return None
        finally:
            User_Database_Interface.close_db(db)

    
    @staticmethod
    def insert_multiple_data(data, mode=1):
        """
        Insert multiple rows into the specified user-related table.
        
        mode:
            1 - User
            2 - USER_DATA
            3 - USER_NOTIFICATIONS
        data:
            A list of tuples/lists where each inner item matches the schema of the target table.
        """
        User_Database_Interface.initialise_database()

        tables = {
            1: 'User',
            2: 'USER_DATA',
            3: 'USER_NOTIFICATIONS'
        }

        table_name = tables.get(mode)
        if not table_name:
            raise ValueError("Invalid mode. Mode should be 1, 2, or 3.")

        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            # Fetch column names dynamically
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]  # col[1] is the column name

            placeholders = ', '.join(['?'] * len(columns))
            column_names = ', '.join(columns)

            query = f'''INSERT OR IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})'''
            cursor.executemany(query, data)

            db.commit()
            print(f"Inserted {cursor.rowcount} rows into {table_name} successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error inserting multiple data into {table_name}: {e}")
            return False
        finally:
            User_Database_Interface.close_db(db)

    @staticmethod
    def get_data(mode=1):
        """
        Retrieve all rows from the specified user-related table.

        mode:
            1 - User
            2 - USER_DATA
            3 - USER_NOTIFICATIONS

        Returns:
            A list of lists representing each row in the table.
        """
        User_Database_Interface.initialise_database()

        tables = {
            1: 'User',
            2: 'USER_DATA',
            3: 'USER_NOTIFICATIONS'
        }

        table_name = tables.get(mode)
        if not table_name:
            raise ValueError("Invalid mode. Mode should be 1, 2, or 3.")

        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            # Fetch column names dynamically
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]  # col[1] is the column name

            query = f"SELECT {', '.join(columns)} FROM {table_name}"
            cursor.execute(query)
            data = cursor.fetchall()

            return [list(row) for row in data]
        except sqlite3.Error as e:
            print(f"Error fetching data from {table_name}: {e}")
            return []
        finally:
            User_Database_Interface.close_db(db)



'''
# Example Usage inside application context

with app.app_context():
    User_Database_Interface.delete_table()  # This will now work in the application context
    User_Database_Interface.initialise_database()

    # Adding users
    
    User_Database_Interface.add_user("User1", "password123", "bancrusher10@gmail.com", "John", "Doe", 101, "Commuter")
    User_Database_Interface.add_user("User2", "password123", "bancrusher10@gmail.com", "Alice", "Smith", 80, "Commuter")
    User_Database_Interface.add_user("User3", "password123", "bancrusher10@gmail.com", "Bob", "Johnson", 60, "Commuter")

    User_Database_Interface.add_user("LTA1", "password123", "bancrusher10@gmail.com", "Sarah", "Lee", 101, "LTA_Manager")
    User_Database_Interface.add_user("LTA2", "password123", "bancrusher10@gmail.com", "Michael", "Tan", 40, "LTA_Manager")

    User_Database_Interface.add_user("MY", "password123", "bancrusher10@gmail.com", "Ming Yang", "Ang", 101, "Admin")
    User_Database_Interface.add_user("Admin1", "password123", "bancrusher10@gmail.com", "David", "Chong", 101, "Admin")
    
    User_Database_Interface.add_user("fakeuser", "password123", "bancrusher10@gmail.com", "fake", "fake", 101, "wrong_user_type")

    # Print all users and verify passwords
    print("check exists:", User_Database_Interface.user_exists("MY"))

'''


'''
    @staticmethod
    def verify_password(username, entered_password):
        try:
            db = User_Database_Interface.get_db()
            cursor = db.cursor()

            cursor.execute('''  '''SELECT Password FROM User WHERE Username = ? '''  ''', (username,))
            result = cursor.fetchone()

            if result:
                stored_password = result[0]
                return bcrypt.checkpw(entered_password.encode(), stored_password)
            else:
                print(f"User {username} not found.")
                return False
        except sqlite3.Error as e:
            print(f"Error verifying password: {e}")
            return False
    '''
'''
with app.app_context():
    User_Database_Interface.insert_multiple_data([
        (1, "MY", "Train delay from City Hall to Jurong East", "2025-04-10")
    ], 3)
    print(User_Database_Interface.get_data(3))
'''