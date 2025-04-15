from flask import Flask
from email_interface import email_interface
from random import randint
from User_Database_Interface import User_Database_Interface
from datetime import datetime
from congestion_calculate_control import calculate_congestion
from Api_Mall_Interface import ApiMallInterface

app = Flask(__name__)

class email_manager_control:

    @staticmethod
    def generate_otp():
        return randint(100000, 999999)

    @staticmethod
    def send_otp(username, OTP):
        # Log the state of the database before any operation
        try:
            db = User_Database_Interface.get_db()
            
            header = "Password Reset OTP"
            message = f"Here is your OTP for resetting your password: OTP: {OTP}"
            
            # Try sending email and verify the process
            email_sent = email_interface.send_email(username, header, message)
            if email_sent:
                print(f"OTP sent successfully to {username}.")
            else:
                print(f"Failed to send OTP to {username}.")
        except Exception as e:
            print(f"Error sending email: {e}")
        
        # Check the database connection after sending the email
        try:
            db = User_Database_Interface.get_db()

            #if db:
            #    print("Database connection after email sending: Open", db)
            #    print("State of data after OTP generation:")
                #print(User_Database_Interface.get_data(1))  # Check if the data is still available after email sending
            #else:
            #    print("Database connection was lost after sending email.")

        except Exception as e:
            print(f"Error checking database connection: {e}")
        
        return email_sent
    


    @staticmethod
    def congestion_threshold_email():
        

        # Step 1: Get today's day and type
        today = datetime.today()
        day_name = today.strftime("%A")  # E.g. 'Monday'
        day_type = "WEEKENDS/HOLIDAY" if day_name in ["Saturday", "Sunday"] else "WEEKDAY"
        current_hour = today.strftime("%H")  # 24-hour format

        #current_hour = '18'  # For testing purposes note this has to be a string not an int.
        #print(today)
        #print(day_name)
        #print(day_type)
        #print(current_hour)
        #print('\n')

        # Step 2: Get congestion predictions
        predictions = calculate_congestion.congestion_predictions(day_type=day_type)

        #print(predictions) #there is valid data

        # Step 3: Get the current hour's percentage load
        train_capacities = {
            'EW': 1920,
            'NS': 1920,
            'NE': 1920,
            'CC': 931,
            'DT': 931,
            'TE': 1280
        }

        percentage_by_code = []

        for row in predictions:
            #print(row)
            year_month, DAY_TYPE, time_per_hour, pt_code, load = row
            #print(load)
            hour = time_per_hour[:2]

            #print(hour)
            ##print('\n')
            if hour == current_hour:  #note both are string, hour and current_hour are strings

                #if pt_code not in train_capacities:
                #    print(f"Unexpected pt_code not in train_capacities: {pt_code}")
                
                #print(hour)
                #print(current_hour)
                #print('\n========')


                capacity = train_capacities.get(pt_code, 1920)
                #print((2 * capacity * (60 / 2.5)) * 100)
                percentage = load / (2 * capacity * (60 / 2.5)) * 100
                percentage_by_code.append([year_month, DAY_TYPE, time_per_hour, pt_code,percentage])
                

        # Step 4: Check users against thresholds
        user_data = User_Database_Interface.get_data(1)
        alert_emails = {}

        for user in user_data:
            #print(f"User row: {user}")  # Debug print

            username = user[0]
            password = user[1]
            email = user[2]
            first_name = user[3]
            last_name = user[4]
            threshold = user[5]
            user_type = user[6]

            try:
                threshold = int(threshold)
            except ValueError:
                print(f"Invalid threshold for user {username}: {threshold}")
                continue  # Skip users with bad threshold

            if threshold < 100:
                triggered = []
                for row in percentage_by_code:
                    year_month, DAY_TYPE, time_per_hour, pt_code, percentage = row
                    row2 = [username,threshold, year_month, DAY_TYPE, time_per_hour, pt_code, percentage]
                    if threshold < percentage:
                        triggered.append(row2)
                
                if triggered:
                    alert_emails[email] = triggered


        return alert_emails

    
    @staticmethod
    def congestion_threshold_email_send():
        # Get alert emails and triggered data from the previous method
        alerts = email_manager_control.congestion_threshold_email()

        print(alerts)

        # Get the current hour for message header
        current_hour = datetime.now().strftime("%H")

        for email, triggered_list in alerts.items():
            if not triggered_list:
                continue

            # Extract the username from the first row (same for all rows under that email)
            username = triggered_list[0][0]

            header = f"Predicted Congestion Notification for {username} based on past Month Data for current hour."
            
            message_lines = [f"Current Hour: {current_hour}:00\n"]

            for entry in triggered_list:
                _, threshold, year_month, day_type, time_per_hour, pt_code, percentage = entry
                message_lines.append(
                    f"MRT_Line: {pt_code}, Your_Congestion_Threshold: {threshold}, Mrt_Threshold: {percentage:.2f}% \n"
                )

            message = "\n".join(message_lines)

            # Send the email
            email_interface.send_email_by_email(email, header, message)

    
    @staticmethod
    def congestion_realtime_email_send(line_code = "EWL", mode='h'):
        """
        Sends real-time congestion alert emails to users based on live MRT data.
        
        Modes:
        - 'l': alerts for crowd levels 'l', 'm', 'h'
        - 'm': alerts for 'm' or 'h'
        - 'h': alerts for 'h' only
        Any other mode defaults to 'h'
        """
        # Normalize mode
        mode = mode.lower()
        if mode not in ['l', 'm', 'h']:
            mode = 'h'

        # Define crowd levels to match for each mode
        mode_to_levels = {
            'l': ['l', 'm', 'h'],
            'm': ['m', 'h'],
            'h': ['h']
        }

        match_levels = mode_to_levels[mode]

        # Step 1: Fetch real-time congestion data from the API
        try:
            realtime_data = ApiMallInterface.get_api_url("24", line_code)
            print(ApiMallInterface) #debug
        except Exception as e:
            print(f"Error fetching data from API: {e}")
            return

        # Step 2: Filter congested stations based on mode
        congested_stations = [
            entry for entry in realtime_data
            if entry.get("CrowdLevel", "").lower() in match_levels
        ]

        if not congested_stations:
            print("No congestion alerts to send at this time.")
            return

        # Step 3: Get user data
        user_data = User_Database_Interface.get_data(1)

        # Step 4: Send emails to users
        for user in user_data:
            username, _, email, first_name, last_name, _, _ = user

            header = f"Real-Time Congestion Alert for {line_code} Line (Data based on past 10 minutes to live)"
            message_lines = [f"Dear {first_name},\n\nThe following stations on the {line_code} line are currently experiencing congestion levels of: {match_levels[0].upper()}.\n"]

            for station in congested_stations:
                station_code = station["Station"]
                crowd_level = station["CrowdLevel"]
                start_time = station["StartTime"]
                end_time = station["EndTime"]

                message_lines.append(
                    f"Station: {station_code}, Crowd Level: {crowd_level.upper()}, From: {start_time}, To: {end_time}"
                )

            message = "\n".join(message_lines)
            email_interface.send_email_by_email(email, header, message)





# Test Email
'''
with app.app_context():
    to_email = "bancrusher10@gmail.com"
    subject = "Test Email"
    message = "This is a test email sent using the Flask app context."

    result = email_interface.send_email(to_email, subject, message)
    
    if result:
        print("Test email sent successfully.")
    else:
        print("Failed to send test email.")
'''
'''
with app.app_context():
    print(email_manager_control.congestion_threshold_email())
'''

'''
with app.app_context():
    email_manager_control.congestion_threshold_email_send()
'''
'''
with app.app_context():
    email_manager_control.congestion_realtime_email_send(line_code="CCL", mode='h')
'''
