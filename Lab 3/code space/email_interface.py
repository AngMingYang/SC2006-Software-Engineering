import base64

from flask import Flask
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import randint
import os
from User_Database_Interface import User_Database_Interface


# Set the SCOPES for Gmail API
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

app = Flask(__name__)

# Store the current working directory at the start
current_directory = os.path.dirname(os.path.abspath(__file__))  

print(f"Current working directory of email_interface.py is: {current_directory}")

def delete_token():
    try:
        # Check if 'token.json' exists
        if os.path.exists('token.json'):
            os.remove('token.json')  # Delete the token file
            print("Token file 'token.json' has been deleted successfully.")
        else:
            print("Token file 'token.json' not found.")
    except Exception as e:
        print(f"Error deleting token file: {e}")

delete_token()

# Gmail API Authentication and Setup
class GmailAPI:
    @staticmethod
    def authenticate():
        # Use the stored current directory for file paths
        script_dir = current_directory  

        creds = None
        # Check if 'token.json' exists and is valid
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If credentials are invalid or missing, initiate the OAuth process
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    print(f"Refreshing credentials with refresh token: {creds.refresh_token}")
                    creds.refresh(Request())
                    # Save the refreshed credentials
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    print(f"Failed to refresh token: {e}")
                    creds = None
            else:
                # If no valid credentials or no refresh token, request a new token
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        os.path.join(script_dir, 'gmail/credentials.json'), SCOPES)
                    creds = flow.run_local_server(port=8080, access_type='offline')
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    print(f"Failed to obtain new credentials: {e}")
                    return None

        # Build and return the Gmail service
        if creds and creds.valid:
            service = build('gmail', 'v1', credentials=creds)
            return service
        else:
            print("Failed to authenticate. No valid credentials available.")
            return None

    @staticmethod
    def send_email(to_email_address, subject, message_body):
        service = GmailAPI.authenticate()

        if not service:
            print("Failed to authenticate with Gmail API.")
            return False

        message = MIMEMultipart()
        message['to'] = to_email_address
        message['subject'] = subject
        msg = MIMEText(message_body)
        message.attach(msg)

        raw_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

        try:
            send_message = service.users().messages().send(userId="me", body=raw_message).execute()
            print(f"Message Id: {send_message['id']}")
            return True
        except HttpError as error:
            print(f"An error occurred: {error}")
            return False

# Example of sending OTP
class email_interface:
    @staticmethod
    def generate_otp():
        return randint(100000, 999999)  # OTP will be a 6-digit number

    @staticmethod
    def send_email(username, header, message):
        print(f"Generating email for user: {username} with header: {header} and message: {message}")
        
        # Retrieve the user's data from the database
        user_data = User_Database_Interface.get_data(1)
        
        # Find the user's data based on the username (assuming each entry is a list or tuple)
        email = None
        for user in user_data:
            if user[0] == username:  # Assuming the username is in the first index (index 0)
                email = user[2]  # Assuming the email is in the 3rd index (index 2)
                print(f"Found user email: {email}")
                break

        if email:
            print(f"Sending OTP email to: {email}")
            # Generate OTP
            otp = email_interface.generate_otp()
            message = message.replace("OTP", str(otp))  # Insert OTP into the message

            try:
                result = GmailAPI.send_email(email, header, message)  # Pass header as the subject and message as the body
                if result:
                    print(f"Email sent successfully to {email}.")
                else:
                    print(f"Failed to send OTP to {email}.")
                    
                return result
            except Exception as e:
                print(f"Error sending email: {e}")
                return False
        else:
            print(f"Email for user {username} not found.")
            return False
        

    @staticmethod
    def send_email_by_email(email, header, message):
        print(f"Generating email for address: {email} with header: {header} and message: {message}")

        if email:
            print(f"Sending email to: {email}")
            # Generate OTP if needed
            otp = email_interface.generate_otp()
            message = message.replace("OTP", str(otp))  # Insert OTP into the message

            try:
                result = GmailAPI.send_email(email, header, message)  # Send email using Gmail API
                if result:
                    print(f"Email sent successfully to {email}.")
                else:
                    print(f"Failed to send email to {email}.")
                return result
            except Exception as e:
                print(f"Error sending email to {email}: {e}")
                return False
        else:
            print("No email provided.")
            return False
        
    


'''
# Example of how the OTP is generated and sent
if __name__ == "__main__":
    username = "example_user"  # Replace with the actual username
    OTP = email_manager_control.generate_otp()  # Generate OTP
    result = email_manager_control.send_otp(username, OTP)  # Send OTP email

    if result:
        print("OTP sent successfully.")
    else:
        print("Failed to send OTP. User email not found.")
'''

'''
with app.app_context():
    # Get the directory where the current script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Now, you can use relative paths from the script's directory
    credentials_path = os.path.join(script_dir, 'gmail/credentials.json')

    if os.path.exists(credentials_path):
        print("File exists")
    else:
        print("File does not exist")

    # Generate OTP and send it
    OTP = email_interface.generate_otp()
    email_interface.send_otp("MY", OTP)

'''
'''
with app.app_context():
    result = GmailAPI.send_email("bancrusher10@gmail.com", "Test Subject", "Test message")
    if result:
        print("Test email sent successfully.")
    else:
        print("Failed to send test email.")
'''


