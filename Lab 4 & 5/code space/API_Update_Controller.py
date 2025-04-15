from Api_Mall_Interface import ApiMallInterface
from Train_Database_Interface import TrainDatabaseInterface
from flask import Flask

app = Flask(__name__)
'''
class API_Update_Controller:
    
    @staticmethod
    def update_db_7():
        api_data = ApiMallInterface.get_api_url(7)
        print(api_data)
        
        # Check if the API data is empty
        if api_data == []:  # error
            print("Error: updating API data")
            return -1

        # Initialize the database (app context required)
        with app.app_context():
            TrainDatabaseInterface.initialise_database()

            print("Inserting data into database")

            # Loop through the data and insert into the database
            TrainDatabaseInterface.insert_multiple_data(api_data)

            print("Data inserted successfully.")

    @staticmethod
    def update_db_8():  # Fix indentation here
        api_data = ApiMallInterface.get_api_url("8")
        print(api_data)
        
        # Check if the API data is empty
        if api_data == []:  # error
            print("Error: updating API data")
            return -1

        # Initialize the database (app context required)
        with app.app_context():
            TrainDatabaseInterface.initialise_database()

            print("Inserting data into database")

            # Loop through the data and insert into the database
            TrainDatabaseInterface.insert_multiple_data(api_data,2)

            print("Data inserted successfully.")

'''

class API_Update_Controller:
    
    @staticmethod
    def update_db(mode,line = "EWL"):
        """
        Update the database with data from the API based on the given mode (7 or 8).
        
        Parameters:
        mode (int): Mode determines the API endpoint (7 or 8).
        """
        if mode == 7:
            api_data = ApiMallInterface.get_api_url(7)
            print(f"Fetching data from API 7: {api_data}")
            
            if api_data == []:  # error
                print("Error: updating API data")
                return -1

            # Initialize the database (app context required)
            with app.app_context():
                TrainDatabaseInterface.initialise_database()

                print("Inserting data into database")

                # Insert data into the database
                TrainDatabaseInterface.insert_multiple_data(api_data)

                print("Data inserted successfully.")
        
        elif mode == 8:
            api_data = ApiMallInterface.get_api_url(8,line)
            print(f"Fetching data from API 8: {api_data}")
            
            if api_data == []:  # error
                print("Error: updating API data")
                return -1

            # Initialize the database (app context required)
            with app.app_context():
                TrainDatabaseInterface.initialise_database()

                print("Inserting data into database")

                # Insert data into the database for mode 2
                TrainDatabaseInterface.insert_multiple_data(api_data, 2)

                print("Data inserted successfully.")

        elif mode == 24:
            api_data = ApiMallInterface.get_api_url(24, line)
            print(f"Fetching data from API 24: {api_data}")
            
            if api_data == []:  # error
                print("Error: updating API data")
                return -1

            # Return the collected data without inserting into the database
            with app.app_context():
                print("Returning data for mode 24")
                return api_data

        elif mode == 25:
            api_data = ApiMallInterface.get_api_url(25)
            print(f"Fetching data from API 25: {api_data}")
            
            if api_data == []:  # error
                print("Error: updating API data")
                return -1

            # Flatten the nested data for mode 25
            flattened_data = []
            for entry in api_data:
                date = entry['Date']
                for station in entry['Stations']:
                    station_code = station['Station']
                    for interval in station['Interval']:
                        start_time = interval['Start']
                        crowd_level = interval['CrowdLevel']
                        flattened_data.append((date, station_code, start_time, crowd_level))

            with app.app_context():
                TrainDatabaseInterface.initialise_database()

                print("Inserting flattened data into database")

                # Insert flattened data into the database for mode 3
                TrainDatabaseInterface.insert_multiple_data(flattened_data, 3)

                print("Data inserted successfully.")
        
        else:
            print("Error: Invalid mode. Please use mode 7 or 8.")
            return -1
        

    @staticmethod
    def update_all():
        """
        Update the database for all relevant API modes and MRT lines.
        """
        line_codes = [
            "EWL", "NSL", "NEL", "CCL", "DTL", "TEL", "JEL", "BPL"
        ]

        modes_with_line = [8, 24]
        modes_without_line = [7, 25]

        # Run modes that don't require line input
        for mode in modes_without_line:
            print(f"\n--- Updating database with mode {mode} ---")
            API_Update_Controller.update_db(mode)

        # Run modes that require line input
        for line in line_codes:
            for mode in modes_with_line:
                print(f"\n--- Updating database with mode {mode} for line {line} ---")
                API_Update_Controller.update_db(mode, line)


# Example usage

#API_Update_Controller.update_db(8)

#API_Update_Controller.update_all()
