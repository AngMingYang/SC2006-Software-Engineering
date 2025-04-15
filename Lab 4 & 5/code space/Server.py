from User_Database_Interface import User_Database_Interface
from flask import Flask, render_template, request, redirect, url_for, session, g, send_from_directory , Response, jsonify
from pyngrok import ngrok
from threading import Thread
import subprocess
from Users import User, Commuter, LTA_Manager, Admin, UserFactory
import secrets  # for generating a secure random secret key
from functools import wraps
from email_manager_control import email_manager_control
from authentication_control import authentication
from Train_Database_Interface import TrainDatabaseInterface  # for route predictions
from congestion_calculate_control import calculate_congestion
from datetime import datetime
from Api_Mall_Interface import ApiMallInterface
from API_Update_Controller import API_Update_Controller
import threading

import matplotlib
matplotlib.use('Agg')  # Set Agg backend for non-GUI operations
import matplotlib.pyplot as plt

from io import BytesIO
import base64
import re  # For regular expression-based sorting

import time
import queue

import os
'''
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
'''
#delete_token() #need to go to google api to authorise the emails to send like 
#https://console.cloud.google.com/auth/clients/61883689561-s08hhjrerf88f4ldosofc1pcjqmcbf65.apps.googleusercontent.com?authuser=4&invt=AbuX1g&project=sc2006-emil


# Set ngrok authtoken
#spare token incase rate limited
#2vZeF2VVp4StpbpitrVimrPedEh_5YXnAaDhQQMuUXFF3NuNj
#2twafWajM5MQ3LZuaOFyAF6IBQz_2EyXeo5SAZDj1jxwmrLYB

ngrok.set_auth_token("2vZeF2VVp4StpbpitrVimrPedEh_5YXnAaDhQQMuUXFF3NuNj")
#ngrok.set_auth_token(" ")   #uncomment to use local host

# Decorator to require login for a view function
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            # If not logged in, redirect to the login page
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def sort_station(station_name):
    # Extract the numeric part from the station name using regex
    match = re.match(r"([A-Za-z]+)(\d+)", station_name)
    if match:
        # Convert the numeric part to an integer for correct sorting
        return int(match.group(2))
    else:
        # Return a large number if no numeric part is found (e.g., for non-standard station names)
        return float('inf')

def sort_line(line):
    # Extract alphabetic and numeric parts of the line
    match = re.match(r"([A-Za-z]+)(\d+)", line)
    if match:
    # Return a tuple with alphabetic and numeric parts for correct sorting
        return (match.group(1), int(match.group(2)))
    else:
        return (line, 0)  # If no number is found, return 0 for sorting
    

def sort_station2(stations):
    def sort_key(station_name):
        if isinstance(station_name, str):  # Check if station_name is a string
            match = re.match(r"([A-Za-z]+)(\d+)", station_name)
            if match:
                # Return a tuple of (alphabetic part, numeric part) for sorting
                return (match.group(1), int(match.group(2)))
        return (station_name, 0)  # Fallback if the match fails

    # Sort using the custom key function
    return sorted(stations, key=sort_key)



                    





class Web_Server_Backend:

    def congestion_refresh(self):
        # Fetch data and process as per original route handler
        user = UserFactory.create_user(session["username"])

        # Security check: Only allow commuters
        if user.get_type() != "Commuter":
            return redirect(url_for("login_error"))

        # Default values for the dropdowns
        line = request.form.get("line", "EWL")  # Default is EWL
        time_interval = request.form.get("time_interval", "30")  # Default is 30 minutes

        # Fetch real-time congestion data (mode 24)
        api_data = ApiMallInterface.get_api_url(24, line)

        if not api_data:
            api_data = "Error fetching real-time congestion data."

        # Predicted data (mode 25)
        predicted_data = []
        filtered_predicted = []
        selected_station = request.form.get("pred_station", "")
        selected_time = request.form.get("pred_time", "")

        if request.method == "POST" and "predict_button" in request.form:
            # Update and fetch predicted data
            API_Update_Controller.update_db(25, line)
            predicted_data = TrainDatabaseInterface.get_data(3)

            # Station list from real-time API
            unique_stations = sorted({entry["Station"] for entry in api_data if "Station" in entry})

            # Sort stations using the second function
            unique_stations = sort_station2(unique_stations)

            # Generate time intervals: "00:00", "00:30", ..., "23:30"
            unique_times = [f"{str(h).zfill(2)}:{'00' if m == 0 else '30'}" for h in range(24) for m in (0, 30)]

            # Extract the time portion from the timestamp string
            def extract_time(ts):
                return ts[11:16] if len(ts) >= 16 else ""

            # Filter predictions by selected station and time
            seen = set()
            filtered_predicted = []
            for entry in predicted_data:
                station = entry[1]
                time_str = extract_time(entry[2])
                key = (station, time_str)

                if (selected_station == "" or station == selected_station) and \
                (selected_time == "" or time_str == selected_time):

                    if key not in seen:
                        seen.add(key)
                        filtered_predicted.append(entry)

        else:
            unique_stations = sorted({entry["Station"] for entry in api_data if "Station" in entry})
            unique_stations = sort_station2(unique_stations)  # Sort stations using the second function
            unique_times = [f"{str(h).zfill(2)}:{'00' if m == 0 else '30'}" for h in range(24) for m in (0, 30)]

        # Process the data for plotting
        if api_data != "Error fetching real-time congestion data.":
            crowd_levels = {'l': 1, 'm': 2, 'h': 3, 'NA': 0}

            sorted_api_data = sorted(api_data, key=lambda x: sort_station(x['Station']))

            stations = [entry['Station'] for entry in sorted_api_data]
            levels = [crowd_levels.get(entry['CrowdLevel'], 0) for entry in sorted_api_data]

            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 6))  # Widen the plot
            ax.bar(stations, levels, color=['green' if x == 1 else 'yellow' if x == 2 else 'red' for x in levels])

            # Set max value for y-axis
            ax.set_ylim(0, 3)

            # Label the y-axis with the crowd levels
            ax.set_ylabel('Crowd Level')
            ax.set_xlabel('Stations')
            ax.set_title(f"Real-Time Crowd Level for {line}")

            # Set fixed ticks for x-axis to avoid the warning
            ax.set_xticks(range(len(stations)))  # This sets the tick positions
            ax.set_xticklabels(stations, rotation=45, ha="right", fontsize=10)  # Now setting tick labels

            # Save the plot to a BytesIO object and encode it for display
            img = BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plot_url = base64.b64encode(img.getvalue()).decode()
            plt.close(fig)  # Close the figure after saving to prevent memory leaks
        else:
            plot_url = None
            sorted_api_data = []

        # Prepare data for the table (only station and crowd density)
        table_data = [(entry['Station'], entry['CrowdLevel']) for entry in sorted_api_data]

        # Sort train lines
        train_lines = ["EWL", "NSL", "CCL", "NEL"]

        sorted_lines = sorted(train_lines, key=sort_line)
        filtered_predicted = sorted(filtered_predicted, key=lambda x: sort_station(x[1]))

        return {
            "username": user.username,
            "line": line,
            "time_interval": time_interval,
            "api_data": api_data,
            "predicted_data": predicted_data,
            "plot_url": plot_url,
            "table_data": table_data,
            "unique_stations": unique_stations,
            "unique_times": unique_times,
            "selected_station": selected_station,
            "selected_time": selected_time,
            "filtered_predicted": filtered_predicted,
            "sorted_lines": sorted_lines
        }
    
    
    
    
    def broadcast_refresh(self):
        print(f"[SSE] Broadcasting to {len(self.clients)} clients")
        for q in self.clients:
            q.put("refresh")
 






    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = secrets.token_hex(16)  # Generate a secret key for sessions
        self.refresh_event = threading.Event()
        self.refresh_flag = False  # Track if data has been refreshed
        self.clients = []



        # Add the database connection close handler
        @self.app.teardown_appcontext
        def close_db(error):
            """Close the database connection after each request."""
            # Pass the db connection explicitly here.
            db = getattr(g, 'db', None)  # You can keep g for this specific purpose
            if db:
                User_Database_Interface.close_db(db)

        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('static', filename)

        # Login route  #Done
        @self.app.route("/", methods=["GET", "POST"])
        def login():
            session.pop("generated_otp", None)
            if request.method == "POST":
                username = request.form["username"]
                password = request.form["password"]

                print(username, password)

                
                if authentication.verify_password(username, password):   
                    user = UserFactory.create_user(username)  # Create user object
                    session["username"] = username
                    return redirect(url_for(user.get_homepage()))  # Factory pattern dynamically chooses appropriate function based on user type
                return redirect(url_for("login_error"))
            

            return render_template("main menu/login.html")


        # Login error route  #Done
        @self.app.route("/login/error",  methods=["GET", "POST"])
        def login_error():
            return render_template("main menu/login_error.html")

        # Logout route  #Done
        @self.app.route("/logout", methods=["GET"])
        def logout():
            session.pop("username", None)
            return redirect(url_for("login"))

        @self.app.route("/account/create", methods=["GET", "POST"])
        def create_account():
            if request.method == "POST":
                username = request.form["username"]
                email = request.form["email"]
                password = request.form["password"]
                first_name = request.form["first_name"]
                last_name = request.form["last_name"]
                user_type = request.form["user_type"]
                threshold_raw = request.form.get("threshold", "101")  # Default to "101" if not provided

                try:
                    threshold = int(threshold_raw)
                except ValueError:
                    threshold = 101  # Default if not a valid number

                # Check if the username already exists
                if User_Database_Interface.user_exists(username):
                    return redirect(url_for("account_exists"))

                # Try adding the user with validated threshold
                if User_Database_Interface.add_user(username, password, email, first_name, last_name, threshold, user_type):
                    return redirect(url_for("account_created"))
                
            return render_template("main menu/create_account.html")
        #return redirect(url_for("create_account"))

    #return render_template("main menu/create_account.html")

        @self.app.route("/account/create/success", methods=["GET"])
        def account_created():
            return render_template("main menu/account_created.html")

        # Route for account already exists error
        @self.app.route("/account/create/exists", methods=["GET"])
        def account_exists():
            return render_template("main menu/account_exists.html")


        @self.app.route("/reset", methods=["GET", "POST"])
        def reset_password():
            if request.method == "POST":
                username = request.form["username"]
                # Ensure that the username exists in the database before proceeding
                if not User_Database_Interface.user_exists(username):
                    return render_template("main menu/reset_password1.html", error="Username does not exist.")
                
                # Store the username in the session as reset_username
                session["reset_username"] = username

                # Redirect to the next route without the username in the URL
                return redirect(url_for("reset_password_sent"))

            return render_template("main menu/reset_password1.html")

        @self.app.route("/reset/password", methods=["GET", "POST"])
        def reset_password_sent():
            username = session.get("reset_username")
            
            if not username:
                return redirect(url_for("reset_password"))
            
            # Check session data for debugging
            print(f"Session Data before OTP generation: {session}")
            
            # If the OTP is not already stored in the session, generate and store it
            if "generated_otp" not in session:
                OTP = email_manager_control.generate_otp()  # Generate OTP
                
                session["generated_otp"] = OTP  # Store OTP in session
                
                # For debugging purposes
                print(f"Generated OTP: {OTP}")  # REMOVE THIS IN THE FUTURE =======================================================
                
                # Send the OTP to the user via email
                email_manager_control.send_otp(username, OTP)
                
            else:
                print(f"OTP already in session: {session['generated_otp']}")  # Debugging line
                
            if request.method == "POST":
                result_OTP = request.form["OTP"]
                new_password = request.form["new_password"]

                # Retrieve the OTP stored in the session
                stored_otp = session.get("generated_otp")

                # For debugging
                print(f"Stored OTP: {stored_otp}")
                print(f"Entered OTP: {result_OTP}")
                
                # Validate the entered OTP (check if it's an integer)
                try:
                    entered_otp = int(result_OTP)
                except ValueError:
                    # If the OTP is not a valid integer, display an error message
                    return render_template("main menu/reset_password2.html", error="Invalid OTP. Please enter a numeric value.", username=username)

                # Check if the entered OTP matches the stored one
                if entered_otp == int(stored_otp):  
                    User_Database_Interface.update_password(username, new_password)
                    
                    # Clear the reset_username and generated_otp from session after password reset
                    session.pop("reset_username", None)
                    session.pop("generated_otp", None)  # Remove the OTP from session after successful reset
                    
                    return redirect(url_for("password_reset_success"))
                else:
                    # If the OTP is incorrect, pop the OTP from the session anyway to prevent reuse
                    session.pop("generated_otp", None)  # Remove the OTP from session on failed attempt
                    
                    return redirect(url_for("OTP_error"))

            return render_template("main menu/reset_password2.html", username=username)

        


        @self.app.route("/reset/password/success", methods=["GET"])
        def password_reset_success():
            return render_template("main menu/reset_password_success.html")

        @self.app.route("/reset/password/OTP_error", methods=["GET"])
        def OTP_error():
            return render_template("main menu/OTP_error.html")






        # Commuter Home Route
        @self.app.route("/commuter/home", methods=["GET"])
        @login_required
        def commuter_home():

            user = UserFactory.create_user(session["username"])
            if user.get_type() == "Commuter":  # Security check to make sure that only commuters can access this page
                return render_template("commuter/commuter_home.html", username=user.username)
            else:
                return redirect(url_for("login_error"))  # Redirect to error page if user is not Commuter
            
        
        

        @self.app.route("/commuter/settings", methods=["GET", "POST"])
        @login_required
        def commuter_settings():
            user = UserFactory.create_user(session["username"])
            if user.get_type() == "Commuter":  # Security check to ensure only commuters can access
                if request.method == "POST":
                    new_email = request.form.get('email')
                    new_first_name = request.form.get('first_name')
                    new_last_name = request.form.get('last_name')
                    new_threshold = request.form.get('threshold')
                    
                    # Update user info in the database
                    success = User_Database_Interface.update_user_details(
                        user.username, new_email, new_first_name, new_last_name, new_threshold
                    )
                    
                    if success:
                        return redirect(url_for('commuter_settings_success'))
                    else:
                        return redirect(url_for('commuter_settings'))
                
                return render_template("commuter/commuter_settings.html", user=user)
            else:
                return redirect(url_for("login_error"))  # Redirect to error page if user is not Commuter
            
        @self.app.route("/commuter/settings/success", methods=["GET", "POST"])
        @login_required
        def commuter_settings_success():
            user = UserFactory.create_user(session["username"])
            if user.get_type() == "Commuter":  # Security check to ensure only commuters can access
                return render_template("commuter/commuter_settings_success.html", user=user)
            else:
                return redirect(url_for("login_error"))  # Redirect to error page if user is not Commuter


        
        
        @self.app.route("/commuter/history", methods=["GET"])
        @login_required
        def commuter_history():
            user = UserFactory.create_user(session["username"])

            if user.get_type() == "Commuter":  # Security check to make sure that only commuters can access this page
                # Fetch user data sorted by history (most recent first)
                user_data = User_Database_Interface.get_user_data_by_history(user.username)

                # If user data exists, pass it to the template
                if user_data:
                    return render_template("commuter/commuter_history.html", 
                                        username=user.username, 
                                        user_data=user_data)
                else:
                    # If no data is found, display a message on the same page or redirect
                    return render_template("commuter/commuter_history.html", 
                                        username=user.username, 
                                        user_data=None, 
                                        message="No history found.")
            else:
                return redirect(url_for("login_error"))  # Redirect to error page if user is not Commuter


        
        



        @self.app.route("/commuter/route_predictions_input", methods=["GET", "POST"])
        @login_required
        def route_predictions_input():
            user = UserFactory.create_user(session["username"])
            if user.get_type() == "Commuter":
                stations = sort_station2(TrainDatabaseInterface.stations)  # Get a list of all stations from 
                return render_template("commuter/route_predictions_input.html", username=user.username, stations=stations)
            else:
                return redirect(url_for("login_error"))



        @self.app.route("/commuter/route_predictions", methods=["GET", "POST"])
        @login_required
        def route_predictions():
            user = UserFactory.create_user(session["username"])
            
            if user.get_type() == "Commuter":
                if request.method == "POST":
                    # Capture form data
                    start_location = request.form.get("start_location")
                    end_location = request.form.get("end_location")

                    #print(start_location,end_location)
                    
                    calc = calculate_congestion.find_shortest_path(start_location,end_location)
                    shortest_path = calc[0]
                    path_time = calc[1]


                    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Get the current date and time
                    User_Database_Interface.add_user_data(user.username, start_location, end_location, date)

                    # For now, we'll just pass these values back to the template
                    return render_template("commuter/route_predictions.html", 
                                        username=user.username, 
                                        shortest_path=shortest_path,
                                        path_time=path_time)
                else:
                    # If not POST, just render the page with no data
                    return redirect(url_for("route_predictions_input"))
            else:
                return redirect(url_for("login_error"))

        
        



        @self.app.route("/commuter/real_time_congestion", methods=["GET", "POST"])
        @login_required
        def real_time_congestion():
            user = UserFactory.create_user(session["username"])

            # Security check: Only allow commuters
            if user.get_type() != "Commuter":
                return redirect(url_for("login_error"))

            # Fetch the latest congestion data (will automatically be updated when SSE sends refresh signal)
            refresh_data = self.congestion_refresh()  # Call the congestion refresh method to get the data

            #self.refresh_flag = False
            
            return render_template("commuter/real_time_congestion.html", **refresh_data)
        
        





        @self.app.route("/commuter/historical_data", methods=["GET", "POST"])
        @login_required
        def historical_data():
            user = UserFactory.create_user(session["username"])
            if user.get_type() != "Commuter":
                return redirect(url_for("login_error"))

            day_type = "WEEKDAY"  # Default value
            
            # If the form is submitted, get the selected day_type (Weekday or Weekend/Holiday)
            if request.method == "POST":
                day_type = request.form.get("day_type")
                day_type = str(day_type.upper())
            
            calculate_congestion.process_data()
            plot_url = calculate_congestion.render_single_graph(day_type)  # Get base64-encoded image URL
            
            return render_template("commuter/historical_data.html", user=user.username, day_type=day_type, plot_url=plot_url)

            










        







        

        





        #LTA Home Route
        @self.app.route('/lta/home', methods=["GET", "POST"])
        @login_required
        def lta_home():
            user = UserFactory.create_user(session["username"])
            if user.get_type() != "LTA_Manager":  # Security check to make sure that only commuters can access this page
                return redirect(url_for("main menu/login_error")) 
                
            else:

                return render_template("lta/lta_home.html", username=user.username)  # Redirect to error page if user is not Commuter




        @self.app.route('/lta/monthly_report', methods=["GET", "POST"])
        @login_required
        def monthly_report():
            user = UserFactory.create_user(session["username"])
            if user.get_type() != "LTA_Manager":
                return redirect(url_for("main menu/login_error"))

            # Default dropdown values
            line = "ALL"
            day_type = "WEEKDAY"
            time_per_hour = None  # Default to no specific time filter

            if request.method == "POST":
                line = request.form.get("line", "ALL")
                day_type = request.form.get("day_type", "WEEKDAY")
                time_per_hour = request.form.get("time_per_hour", None)  # Get the selected time_per_hour

            day_type = str(day_type)
            calculate_congestion.process_data()

            # Render graphs based on selected line and day type
            plot_image = calculate_congestion.render_congestion_predictions_graph(day_type=day_type, line=line)  # Pass line to the function
            plot_image2 = calculate_congestion.render_discrepancy_graph(line, time_per_hour)  # Returns the image in bytes

            month_proportions, total_tap_in = calculate_congestion.get_proportions()
            top_5_busy = calculate_congestion.busiest_stations_top5()

            return render_template(
                'lta/monthly_report.html',
                day_type=day_type,
                plot_url=plot_image,
                plot_url2=plot_image2,  # Pass the second graph
                line=line,
                time_per_hour=time_per_hour,  # Pass time_per_hour to template
                month_proportions=month_proportions,
                total_tap_in=total_tap_in,
                top_5_busy=top_5_busy
            )


    


            
        @self.app.route('/lta/congestion_planning', methods=["GET", "POST"])
        @login_required
        def congestion_planning():
            user = UserFactory.create_user(session["username"])
            if user.get_type() == "LTA_Manager":
                day_type = request.form.get('day_type', 'WEEKDAY')  # Default to 'WEEKDAY' if not selected
                line = request.form.get('line', 'ALL')  # Default to 'ALL' if no line selected
                
                # Generate the graphs based on the selected day_type and line
                congestion_plot_url = calculate_congestion.render_congestion_predictions_graph(day_type, line)
                frequency_plot_url = calculate_congestion.render_train_frequency_graph(day_type, line)

                #print(congestion_plot_url)
                #print(frequency_plot_url)

                # Render the template with the graphs and selected day_type and line
                return render_template('lta/congestion_planning.html', 
                                    plot_url=congestion_plot_url,  # Pass plot_url instead of congestion_plot_url
                                    plot_url2=frequency_plot_url,  # Pass plot_url2 instead of frequency_plot_url
                                    day_type=day_type,
                                    line=line)
            else:
                return redirect(url_for("main menu/login_error"))



            


        @self.app.route('/lta/email', methods=["GET", "POST"])
        @login_required
        def email_functions():
            # Debug: Check the current user
            print(f"User: {session['username']}")
            user = UserFactory.create_user(session["username"])

            # Debug: Check user type
            print(f"User type: {user.get_type()}")

            if user.get_type() != "LTA_Manager":
                print("User is not an LTA Manager. Redirecting to login error page.")
                return redirect(url_for("login_error"))

            # Default values for the dropdowns
            line = request.form.get("line", "EWL")
            time_interval = request.form.get("time_interval", "30")  # Default is 30 minutes

            # Fetch real-time congestion data (mode 24)
            api_data = ApiMallInterface.get_api_url(24, line)

            if not api_data:
                api_data = "Error fetching real-time congestion data."

            # Process the data for plotting
            plot_base64 = None
            if api_data != "Error fetching real-time congestion data.":
                crowd_levels = {'l': 1, 'm': 2, 'h': 3, 'NA': 0}

                # Sort the data by station
                sorted_api_data = sorted(api_data, key=lambda x: sort_station(x['Station']))

                # Prepare the stations and levels
                stations = [entry['Station'] for entry in sorted_api_data]
                levels = [crowd_levels.get(entry['CrowdLevel'], 0) for entry in sorted_api_data]

                # Create the plot
                fig, ax = plt.subplots(figsize=(12, 6))  # Widen the plot
                ax.bar(stations, levels, color=['green' if x == 1 else 'yellow' if x == 2 else 'red' for x in levels])

                # Set max value for y-axis
                ax.set_ylim(0, 3)

                # Label the y-axis with the crowd levels
                ax.set_ylabel('Crowd Level')
                ax.set_xlabel('Stations')
                ax.set_title(f"Real-Time Crowd Level for {line}")

                # Set fixed ticks for x-axis to avoid the warning
                ax.set_xticks(range(len(stations)))  # This sets the tick positions
                ax.set_xticklabels(stations, rotation=45, ha="right", fontsize=10)  # Now setting tick labels

                # Save the plot to a BytesIO object and encode it for display
                img = BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                plot_base64 = base64.b64encode(img.getvalue()).decode()
                plt.close(fig)  # Close the figure after saving to prevent memory leaks

                print(plot_base64)

            # Handle form submissions (POST request)
            if request.method == "POST":
                if "send_threshold_email" in request.form:
                    print("Sending threshold email...")
                    email_manager_control.congestion_threshold_email_send()

                elif "send_realtime_email" in request.form:
                    line_code = request.form.get('line_code', 'CCL')
                    mode = request.form.get('mode', 'h')
                    print(f"Sending real-time congestion email for line {line_code} and mode {mode}...")
                    email_manager_control.congestion_realtime_email_send(line_code=line_code, mode=mode)

            return render_template("lta/email_functions.html", plot_base64=plot_base64, line=line)




        





        # Admin home route
        @self.app.route("/admin/home",  methods=["GET", "POST"])
        @login_required
        def admin_home():
            user = UserFactory.create_user(session["username"])
            if user.get_type() == "Admin":  # This is needed to make sure that even if you are logged in, you cannot just access the admin_home()
                return render_template("admin/admin_home.html", username=user.username)
            else:
                return redirect(url_for("login_error"))
            



        


        @self.app.route("/admin/reset_user_password", methods=["GET", "POST"])
        @login_required
        def admin_reset_user_password():
            user = UserFactory.create_user(session["username"])
            
            # Ensure the current user is actually an admin
            if user.get_type() != "Admin":
                return redirect(url_for("login_error"))
            
            error = None
            success = None

            if request.method == "POST":
                target_username = request.form.get("target_username")
                new_password = request.form.get("new_password")
                
                # Validate if the user exists using the user_exists method
                if not User_Database_Interface.user_exists(target_username):
                    error = f"User '{target_username}' does not exist."
                else:
                    # Update password
                    User_Database_Interface.update_password(target_username, new_password)
                    success = f"Password for user '{target_username}' has been reset successfully."

            return render_template("admin/reset_user_password.html", error=error, success=success)
        

        @self.app.route("/admin/trigger_refresh", methods=["POST"])
        @login_required
        def trigger_refresh():
            user = UserFactory.create_user(session["username"])
            if user.get_type() != "Admin":
                return redirect(url_for("login_error"))
            
           #self.refresh_flag = True   #this line is what causes the refresh to happen
            
            self.broadcast_refresh()


            #print("refresh flag: " + str(self.refresh_flag))

            return redirect(url_for("admin_home"))
        
        @self.app.route("/admin/update_and_trigger_refresh", methods=["POST"])
        @login_required
        def update_and_trigger_refresh():
            user = UserFactory.create_user(session["username"])
            if user.get_type() != "Admin":
                return redirect(url_for("login_error"))

            # Update all APIs
            API_Update_Controller.update_all()

            # Trigger dashboard refresh
            #self.refresh_flag = True
            self.broadcast_refresh()

            #print("refresh flag: " + str(self.refresh_flag))


            return redirect(url_for("admin_home"))

        
        #API_Update_Controller.update_all()




        


        @self.app.route("/sse/congestion")
        def sse_congestion():
            def event_stream():
                messages = queue.Queue()
                self.clients.append(messages)
                try:
                    while True:
                        msg = messages.get()
                        yield f"data: {msg}\n\n"
                except GeneratorExit:
                    self.clients.remove(messages)

            return Response(event_stream(), mimetype="text/event-stream")






        
        
       

    def run(self):
        self.app.run(debug=True, use_reloader=False, threaded=True)

# Set up ngrok to create a public URL
try:
    public_url = ngrok.connect(5000)
    print(f" * ngrok tunnel available at: {public_url}")
except Exception as e:  # Catch all errors
    print("ngrok failed, falling back to localhost.")  #note, NO EMOJIS, IT SPOILS UML.PY
    print("Error details:")
    #traceback.print_exc()  # Optional: prints full error trace
    public_url = "http://127.0.0.1:5000"  # Fallback

# Create and run web server in a non-blocking way
web_server = Web_Server_Backend()

# Run the Flask app in a separate thread so it does not block ngrok's process
def run_app():
    web_server.run()  # Flask blocks the rest of the code, so we need to use threads

if __name__ == "__main__":
    # Start Flask app in a new thread
    thread = Thread(target=run_app)
    thread.start()
    print("Starting web server...")


