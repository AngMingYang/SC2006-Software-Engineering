import networkx as nx
import matplotlib.pyplot as plt

from Train_Database_Interface import TrainDatabaseInterface
from flask import Flask,send_file
from Api_Mall_Interface import ApiMallInterface
from datetime import datetime, timedelta
from API_Update_Controller import API_Update_Controller
import pandas as pd
import io
from collections import defaultdict
import os
import re
import base64
from io import BytesIO
import calendar

def get_days_in_month(date_str):
    # Extract the year and month from the date string
    year, month = map(int, date_str.split('-'))

    # Get the number of days in the month
    _, num_days = calendar.monthrange(year, month)
    return num_days


app = Flask(__name__)

class calculate_congestion:
    average_station_travel_time = 2.5
    average_station_commuted = 7
    train_capacities = {
        'EW': 1920,  # East-West Line
        'NS': 1920,  # North-South Line
        'NE': 1920,  # North-East Line
        'CC': 931,   # Circle Line
        'DT': 931,   # Downtown Line
        'TE': 1280   # Thomson-East Coast Line
    } #https://en.wikipedia.org/wiki/List_of_Singapore_MRT_and_LRT_rolling_stock



    @staticmethod
    def calculate():
        data = TrainDatabaseInterface.get_data(2)
        #print(data)
        

        # Use set comprehension to get unique ORIGIN_PT_CODE (index 4)
        unique_origin_codes = list({row[4] for row in data})
        pure_data = calculate_congestion.remove_slashes(unique_origin_codes)
        pure_data.sort()

    
        
        connections = calculate_congestion.generate_connections(pure_data)
        
        # After generating connections, check for any missing connections
        connections = calculate_congestion.add_missing_connections(connections, pure_data)
        
        # Manually add missing connections
        manual_connections = [
            ('SW', 'NE16'), 
            ('SW1', 'NE16'), 
            ('SE5', 'NE16'),
            ('S1', 'NE16'),
            ('PW7', 'NE17'),
            ('PW1', 'NE17'),
            ('PE1', 'NE17'),
            ('PE7', 'NE17'),
            ('CG1', 'EW4'),
            ('CG1', 'DT35'),
            ('CE1', 'CC4'),  # New connection
            ('CE1', 'DT16'), # New connection
            ('CE2', 'TE20'), # New connection
            ('CE2', 'NS27'), # New connection
            ('BP1', 'NS4'),  # New connection
            ('BP6', 'DT1'),  # New connection
            ('BP6', 'BP13'), # New connection
            ('NS1', 'EW14'), # New connection
            ('NS24', 'NE6'), # New connection
            ('NE3', 'EW16'), # New connection
            ('NS9', 'TS1'),  # New connection
            ('NS16', 'TE7'), # New connection
            ('NS17', 'CC15'), # New connection
            ('CE1', 'DT16'), # New connection
            ('CG1', 'DT35'), # New connection
            ('EW8', 'CC9'),  # New connection
            ('NE1', 'CC29'), # New connection
            ('CG1', 'DT35')  # New connection
        ]
        connections = calculate_congestion.add_manual_connections(connections, manual_connections)
        
        connections.sort()

        #print(connections)
        
        # Visualize the connections
        #calculate_congestion.visualize_graph(connections)

        return connections
    
    @staticmethod
    def remove_slashes(station_list):
        processed_stations = []
        for station in station_list:
            # Split the station if it contains a slash
            stations = station.split('/')
            processed_stations.extend(stations)
        return processed_stations
    
    @staticmethod
    def generate_connections(stations_before):
        connections = []
        station_map = {}
        
        for station in stations_before:
            # Split the station name based on slashes
            split_stations = station.split('/')
            if len(split_stations) > 1:
                # Handle cases where we have a slash and two stations
                station_map[split_stations[0]] = split_stations[1]
                connections.append((split_stations[0], split_stations[1]))
            else:
                # Handle cases for normal stations
                prefix = station[:2]  # Assuming prefixes are 2 characters
                suffix = station[2:]
                
                # Check if suffix is numeric before trying to convert it
                if suffix.isdigit():
                    index = int(suffix)
                    # Connect with +1 and -1 stations if they exist
                    if f'{prefix}{index-1}' in stations_before:
                        connections.append((station, f'{prefix}{index-1}'))
                    if f'{prefix}{index+1}' in stations_before:
                        connections.append((station, f'{prefix}{index+1}'))
                else:
                    # If suffix is not numeric, skip the index-based connection logic
                    print(f"Skipping station with non-numeric suffix: {station}")

        # For stations with slashes, ensure they're connected
        for key, value in station_map.items():
            connections.append((key, value))

        return connections

    @staticmethod
    def add_missing_connections(connections, stations):
        # Find all possible stations with numeric suffixes
        all_stations = {station[:2]: [] for station in stations if station[2:].isdigit()}
        
        # Group stations by their prefix
        for station in stations:
            if station[2:].isdigit():
                prefix = station[:2]
                suffix = int(station[2:])
                all_stations[prefix].append(suffix)
        
        # Check for missing stations and create connections
        for prefix, suffixes in all_stations.items():
            # Sort suffixes in increasing order
            suffixes.sort()

            # Iterate through sorted suffixes and connect any missing stations
            for i in range(len(suffixes) - 1):
                current_station = f'{prefix}{suffixes[i]}'
                next_station = f'{prefix}{suffixes[i+1]}'
                # If there's a gap, add a connection
                if suffixes[i+1] - suffixes[i] > 1:
                    for missing_station in range(suffixes[i]+1, suffixes[i+1]):
                        missing_station_name = f'{prefix}{missing_station}'
                        #print(f"Adding connection for missing station: {missing_station_name}")
                        connections.append((current_station, missing_station_name))
                
                # Connect the current station to the next one
                if (current_station, next_station) not in connections and (next_station, current_station) not in connections:
                    connections.append((current_station, next_station))
        
        return connections
    
    @staticmethod
    def add_manual_connections(existing_connections, manual_connections):
        # Add manual connections if they don't already exist
        for conn in manual_connections:
            if conn not in existing_connections and (conn[1], conn[0]) not in existing_connections:
                #print(f"Adding manual connection: {conn}")
                existing_connections.append(conn)
        
        return existing_connections

    @staticmethod
    def visualize_graph(connections):
        # Create a graph using NetworkX
        G = nx.Graph()

        # Add nodes and edges to the graph
        G.add_edges_from(connections)

        # Use spring layout to position the nodes so they don't overlap
        pos = nx.spring_layout(G, seed=42, k=0.20, iterations=5000)  # Adjust 'k' and 'iterations' for better spread

        # Draw the graph using Matplotlib
        plt.figure(figsize=(12, 12))  # Set the figure size
        nx.draw(G, pos, with_labels=True, font_size=8, node_size=500, node_color='skyblue', font_weight='bold')

        # Set title and show the plot
        plt.title("Train Station Connections Map")
        plt.show()


    @staticmethod
    def find_shortest_path(start, end):
        # Create a graph from the connections
        start = str(start)
        end = str(end)
        G = nx.Graph()
        connections = calculate_congestion.calculate()

        #print(connections)
        #print(start, end)

        G.add_edges_from(connections)
        
        # Dijkstra's algorithm to find the shortest path
        try:
            shortest_path = nx.dijkstra_path(G, start, end)
            print(f"Shortest path from {start} to {end}: {shortest_path}")
            return_value = [shortest_path, len(shortest_path) * calculate_congestion.average_station_travel_time]

            #calculate_congestion.visualize_graph(connections)  #bugfixing
            return return_value
        
        except nx.NetworkXNoPath:
            print(f"No path exists between {start} and {end}")
            return None
        

    @staticmethod
    def get_real_time_congestion(line = "EWL"):
        real_time_congestion = ApiMallInterface.get_api_url("24",line)
        return real_time_congestion
    
    @staticmethod
    def get_predicted_congestion(Hour=0, line="EWL"):
        # Get API data
        real_time_congestion = ApiMallInterface.get_api_url("25", line)

        # Store results
        relevant_data = []

        for day_data in real_time_congestion:
            for station in day_data.get("Stations", []):
                station_name = station.get("Station")
                for interval in station.get("Interval", []):
                    # Parse the ISO 8601 time string into a datetime object
                    dt = datetime.fromisoformat(interval["Start"])
                    
                    # Match the hour
                    if dt.hour == Hour:
                        relevant_data.append({
                            "Station": station_name,
                            "Time": interval["Start"],
                            "CrowdLevel": interval["CrowdLevel"]
                        })

        return relevant_data
    
    '''
    @staticmethod
    def Process_data(): 
        try:
            # Assuming you are fetching and updating the database here
            API_Update_Controller.update_db(8, line)
        except Exception as e:
            print(f"API unavailable, checking Database: {e}")
            # Handle any other unexpected errors
        
        
        # Get data from your database
        Train_Movement_data_columns = TrainDatabaseInterface.get_columns("TRAIN_MOVEMENT")
        Train_Movement_data = TrainDatabaseInterface.get_data(2)
        
        # Ensure we have valid data
        if not Train_Movement_data:
            return {"error": "No data available"}
        
        # Initialize an empty list for processed data
        processed = []
        
        # Iterate through the fetched data
        for row in Train_Movement_data:
            # Access values by the correct index positions based on your table definition
            year_month = row[0]  # Index for 'YEAR_MONTH'
            day_type = row[1]     # Index for 'DAY_TYPE'
            TIME_PER_HOUR = row[2]  # Index for 'TIME_PER_HOUR'
            
            # Check if the unique combination exists in the processed list
            existing_group = next((group for group in processed if group[0][0] == year_month and group[0][1] == day_type and group[0][2] == TIME_PER_HOUR), None)
            
            if existing_group:
                # If the group exists, just append the row to that group
                existing_group.append(row)
            else:
                # If the group doesn't exist, create a new group and add the row to the processed list
                processed.append([row])
        
        processed = processed[1:]  # Reverse the list so that the most recent data is at the beginning

        # Step 2: Calculate the total load per hour
        total_load_data = []

        for group in processed:
            # Filter and sort valid rows by TIME_PER_HOUR
            valid_rows = [row for row in group if row[2].isdigit()]
            valid_rows.sort(key=lambda x: x[2])  # string sort is fine

            current_in = 0
            current_out = 0
            
            # Calculate total load for each time_per_hour
            for row in valid_rows:
                try:
                    # Extract necessary fields
                    in_count = int(row[5])
                    out_count = int(row[6])
                except (ValueError, IndexError) as e:
                    print(f"Skipping row due to error: {e}")
                    continue

                current_in += in_count
                current_out += out_count

            total_load = current_in - current_out

            # Append total load for each hour
            total_load_data.append([
                row[0],  # YEAR_MONTH
                row[1],  # DAY_TYPE
                row[2],  # TIME_PER_HOUR
                total_load
            ])

        # Insert the total load data into the database
        TrainDatabaseInterface.insert_multiple_data(total_load_data, 4)

        return total_load_data
        #want total load per hour for all stations.

    '''

    @staticmethod
    def process_data():  #sums total number of people in mrt system for that hour taking account previous hours too.
        try:
            # Assuming data is being fetched from the database
            today = datetime.today()
            last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
            second_last_month = (today.replace(day=1) - timedelta(days=32)).strftime('%Y-%m')
            candidate_months = [last_month, second_last_month]

            for month in candidate_months:
                all_data = TrainDatabaseInterface.get_data(2)  # Assuming this fetches all data
                all_data = all_data[1:]  # Skip header

                filtered_data = [row for row in all_data if row[0] == month]
                if filtered_data:
                    Train_Movement_data = filtered_data  #  Use only the relevant month's data
                    break


            

            # If no data was found after trying both months, update the database and retry
            if not filtered_data:
                API_Update_Controller.update_db(8, "line")  # Replace "line" with the appropriate line identifier
                # Retry once more after the database is updated
                Train_Movement_data = TrainDatabaseInterface.get_data(2)  # Fetch the data again after update
                Train_Movement_data = Train_Movement_data[1:]  # Skip header
                filtered_data = [row for row in Train_Movement_data if row[0] == last_month]
                if not filtered_data:
                    filtered_data = [row for row in Train_Movement_data if row[0] == second_last_month]
                if not filtered_data:
                    print(" No data found even after updating the database.")
                    return []  # If still no data, return an empty list


            # Step 1: Combine values with the same YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR
            combined_data = defaultdict(lambda: {'tap_in': 0, 'tap_out': 0})
            
            # Combine the data first by summing tap_in and tap_out for each combination
            for row in Train_Movement_data:
                year_month, day_type, time_per_hour, pt_type, pt_code, tap_in, tap_out = row
                tap_in, tap_out = int(tap_in), int(tap_out)

                # Define the key for the grouping
                key = (year_month, day_type, time_per_hour)

                # Combine the values for the same key
                combined_data[key]['tap_in'] += tap_in
                combined_data[key]['tap_out'] += tap_out

            # Step 2: Accumulate load values, initialize tap_in and tap_out to 0 for each key
            result_list = []

            # Sort the keys by time_per_hour as integers, but treat hour 0 as 24
            sorted_keys = sorted(combined_data.keys(), key=lambda x: 24 if int(x[2]) == 0 else int(x[2]))

            # Accumulate the load for each sorted (year_month, day_type, time_per_hour) combination
            cumulative_in = 0
            cumulative_out = 0

            prev_tap_out = 0  # Used to delay tap_out by one cycle


            for key in sorted_keys:
                year_month, day_type, time_per_hour = key
                values = combined_data[key]

                # Accumulate the load progressively
                cumulative_in += values['tap_in']
                #cumulative_out += values['tap_out']

                cumulative_out += prev_tap_out  # Add previous cycle's tap_out (delayed by 1)
                prev_tap_out = values['tap_out']  # Store current tap_out for use in next cycle

                # Calculate the total load as the difference between cumulative in and out
                total_people_in_system = cumulative_in - cumulative_out     #DELAY cumulative_out BY 1 CYCLE so that can account for people who tap in and tap out on the same hour.

                # Append the result as (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, LOAD)
                result_list.append((year_month, day_type, time_per_hour, total_people_in_system))

            # Step 3: Return the final result list
            #print(len(result_list))

            TrainDatabaseInterface.delete_table("PROCESSED_DATA")
            TrainDatabaseInterface.insert_multiple_data(result_list,4)



            #calculate_congestion.plot_graph(result_list)
            #return result_list

        except Exception as e:
            print(f"API unavailable, checking Database: {e}")
            # Handle any other unexpected errors
            return []
        

    @staticmethod
    def plot_graph(result_list):
        # Separate the data by day_type
        weekday_data = [item for item in result_list if item[1] == 'WEEKDAY']
        weekend_data = [item for item in result_list if item[1] == 'WEEKENDS/HOLIDAY']
        weekend_weekday_data = [item for item in result_list if item[1] == 'WEEKENDS/HOLIDAY' or item[1] == 'WEEKDAY']

        # Plot Weekday Graph
        calculate_congestion.plot_single_graph(weekday_data, "Weekday")

        # Plot Weekend Graph
        calculate_congestion.plot_single_graph(weekend_data, "Weekend/Holiday")

        # Plot Weekday + Weekend Graph
        calculate_congestion.plot_single_graph(weekend_weekday_data, "Weekday + Weekend/Holiday")

    @staticmethod
    def plot_single_graph(data, day_type):
        # Prepare the data for plotting
        #x = [f'{item[0]} {item[1]} {item[2]}' for item in data]  # Format the x-axis with YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR
        x = [f'{item[0]} {item[1]} {item[2]}' for item in data]  # Format the x-axis with YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR
        y = [item[3] for item in data]  # Get the total_people_in_system (y-axis values)

        # Plot the data
        plt.figure(figsize=(10, 5))
        plt.plot(x, y, marker='o', linestyle='-', color='b')
        plt.xlabel('Date and Time (Year-Month, Day Type, Hour)')
        plt.ylabel('Total People in MRT System')
        plt.title(f'Total People in MRT System Over Time - {day_type}')
        plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
        plt.tight_layout()  # Adjust layout to avoid label overlap
        plt.show()



    # "Weekday" , "Weekend/Holiday"
    @staticmethod
    def render_single_graph(day_type):
        # Fetch data from the database
        data = TrainDatabaseInterface.get_data(4)

        # Separate data into Weekday and Weekend/Holiday
        weekday_data = [item for item in data if item[1] == 'WEEKDAY']
        weekend_data = [item for item in data if item[1] == 'WEEKENDS/HOLIDAY']
        weekend_weekday_data = [item for item in data if item[1] == 'WEEKENDS/HOLIDAY' or item[1] == 'WEEKDAY']

        # Filter data based on the selected day type
        if day_type == "WEEKDAY":
            selected_data = weekday_data
        elif day_type == "WEEKENDS/HOLIDAY":
            selected_data = weekend_data
        else:
            selected_data = []  # Return empty if an invalid day type is provided

        # If no data exists for the selected day type, return None
        if not selected_data:
            return None  # No plot to generate

        # Get the date of the first entry to calculate the number of days in the month
        date_example = selected_data[0][0]  # Assuming the first entry has the date in format YYYY-MM
        days_in_month = get_days_in_month(date_example)

        # Prepare the data for plotting
        x = [f'{item[0]} {item[1]} {item[2]}' for item in selected_data]  # Format the x-axis with YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR
        y = [item[3] / days_in_month for item in selected_data]  # Normalize the total_people_in_system by dividing by the number of days in the month

        # Generate the plot
        plt.figure(figsize=(15, 10))
        plt.plot(x, y, marker='o', linestyle='-', color='b')
        plt.xlabel('Date and Time (Year-Month, Day Type, Hour)')
        plt.ylabel('Total People in MRT System (Normalized Per Day)')
        plt.title(f'Total People in MRT System in one day, last month - {day_type}')
        plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
        plt.tight_layout()  # Adjust layout to avoid label overlap

        # Save the plot to a BytesIO object
        img = BytesIO()
        try:
            plt.savefig(img, format='png')
        except Exception as e:
            print(f"Error saving plot: {e}")
            return None  # Return None if an error occurs

        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()  # Ensure the plot is properly closed after saving

        return plot_url
    

    @staticmethod
    def get_proportions():
        data = TrainDatabaseInterface.get_data(2)

        # Assuming data is being fetched from the database
        today = datetime.today()
        last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        second_last_month = (today.replace(day=1) - timedelta(days=32)).strftime('%Y-%m')
        candidate_months = [last_month, second_last_month]

        filtered_data = []
        for month in candidate_months:
            Train_Movement_data = TrainDatabaseInterface.get_data(2)  # Assuming this fetches all data
            Train_Movement_data = Train_Movement_data[1:]  # Skip header

            filtered_data = [row for row in Train_Movement_data if row[0] == month]
            if filtered_data:
                break  # Exit if data is found

        # If no data was found after trying both months, update the database and retry
        if not filtered_data:
            API_Update_Controller.update_db(8, "line")  # Replace "line" with the appropriate line identifier
            # Retry once more after the database is updated
            Train_Movement_data = TrainDatabaseInterface.get_data(2)  # Fetch the data again after update
            Train_Movement_data = Train_Movement_data[1:]  # Skip header
            filtered_data = [row for row in Train_Movement_data if row[0] == last_month]
            if not filtered_data:
                filtered_data = [row for row in Train_Movement_data if row[0] == second_last_month]
            if not filtered_data:
                print(" No data found even after updating the database.")
                return {}, 0  # Return empty dict and zero sum

        # Define the dictionary of line codes
        lines = {
            "BP": 0,  # Bukit Panjang LRT
            "CC": 0,  # Circle Line
            "DT": 0,  # Downtown Line
            "EW": 0,  # East-West Line
            "NE": 0,  # North East Line
            "NS": 0,  # North-South Line
            # "STC": 0,  # Uncomment if needed
            # "PTC": 0,
            "TE": 0,  # Thomson-East Coast Line
        }

        total_tap_ins = 0

        # Process the data and sum Total_Tap_in for each line
        for row in filtered_data:
            year_month, day_type, time_per_hour, pt_type, pt_code, tap_in, tap_out = row
            tap_in = int(tap_in)

            for line in lines:
                if line in pt_code:
                    lines[line] += tap_in
                    total_tap_ins += tap_in
                    break

        return lines, total_tap_ins

        #({'BP': 3018982, 'CC': 12780654, 'DT': 13666383, 'EW': 19241688, 'NE': 7303446, 'NS': 17034465, 'TE': 3920672}, 76966290)  #one month
        
    @staticmethod
    def tap_discrepancy(line_filter="ALL"):
        """
        Returns tap in - tap out discrepancies per hour per station.

        Args:
            line_filter (str): Specify line prefix (e.g., 'TE', 'NS', 'ALL').

        Returns:
            List of tuples: (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, PT_CODE, DISCREPANCY)
        """

        # Valid MRT lines
        valid_lines = {"BP", "CC", "DT", "EW", "NE", "NS", "TE", "ALL"}

        try:
            # Validate line filter
            line_filter = line_filter.upper()
            if line_filter not in valid_lines:
                print(f" Invalid line '{line_filter}'. Choose from: {', '.join(valid_lines - {'ALL'})} or 'ALL'.")
                return []

            # Determine recent candidate months
            today = datetime.today()
            last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
            second_last_month = (today.replace(day=1) - timedelta(days=32)).strftime('%Y-%m')
            candidate_months = [last_month, second_last_month]

            # Try to get data
            filtered_data = []
            for month in candidate_months:
                Train_Movement_data = TrainDatabaseInterface.get_data(2)[1:]  # Skip header
                filtered_data = [row for row in Train_Movement_data if row[0] == month]
                if filtered_data:
                    break

            # Fallback to DB update if no data
            if not filtered_data:
                API_Update_Controller.update_db(8, "line")
                Train_Movement_data = TrainDatabaseInterface.get_data(2)[1:]
                filtered_data = [row for row in Train_Movement_data if row[0] == last_month]
                if not filtered_data:
                    filtered_data = [row for row in Train_Movement_data if row[0] == second_last_month]
                if not filtered_data:
                    print(" No data found even after updating the database.")
                    return []

            # Filter for a specific line if not 'ALL'
            if line_filter != "ALL":
                filtered_data = [row for row in filtered_data if line_filter in row[4]]  # Check if line_filter is anywhere in pt_code

            # Compute discrepancy
            result = []
            for row in filtered_data:
                year_month, day_type, time_per_hour, pt_type, pt_code, tap_in, tap_out = row
                discrepancy = int(tap_in) - int(tap_out)
                result.append((year_month, day_type, time_per_hour, pt_type, pt_code, discrepancy))

            # Sort result
            result.sort(key=lambda x: (x[0], x[1], int(x[2]), x[4]))
            return result

        except Exception as e:
            print(f" Error computing discrepancies: {e}")
            return []
        


    @staticmethod
    def busiest_stations_top5():
        """
        Returns the top 5 busiest MRT stations based on total tap-ins and tap-outs over the past two months.
        """
        try:
            today = datetime.today()
            last_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
            second_last_month = (today.replace(day=1) - timedelta(days=32)).strftime('%Y-%m')
            candidate_months = [last_month, second_last_month]

            # Step 1: Fetch and filter the data
            filtered_data = []
            for month in candidate_months:
                Train_Movement_data = TrainDatabaseInterface.get_data(2)[1:]  # Skip header
                filtered_data = [row for row in Train_Movement_data if row[0] == month]
                if filtered_data:
                    break

            # Step 2: If nothing found, trigger DB update
            if not filtered_data:
                API_Update_Controller.update_db(8, "line")
                Train_Movement_data = TrainDatabaseInterface.get_data(2)[1:]
                filtered_data = [row for row in Train_Movement_data if row[0] == last_month]
                if not filtered_data:
                    filtered_data = [row for row in Train_Movement_data if row[0] == second_last_month]
                if not filtered_data:
                    print(" No data found even after updating the database.")
                    return [], []

            # Step 3: Sum tap-ins and tap-outs per station
            station_tapins = defaultdict(int)
            station_tapouts = defaultdict(int)
            for row in filtered_data:
                _, _, _, _, pt_code, tap_in, tap_out = row
                station_tapins[pt_code] += int(tap_in)
                station_tapouts[pt_code] += int(tap_out)

            # Step 4: Sort and get top 5 for tap-ins and tap-outs
            top5_tapins = sorted(station_tapins.items(), key=lambda x: x[1], reverse=True)[:5]
            top5_tapouts = sorted(station_tapouts.items(), key=lambda x: x[1], reverse=True)[:5]

            return top5_tapins, top5_tapouts

        except Exception as e:
            print(f" Error retrieving top stations: {e}")
            return [], []
        

        
    @staticmethod
    def render_discrepancy_graph(line_filter="EWL", time_per_hour=None):
        """
        Renders a graph showing tap-in - tap-out discrepancies per station for a specific MRT line and hour.

        Args:
            line_filter (str): Line prefix (e.g., 'EWL', 'NS', 'ALL').
            time_per_hour (str, optional): Specific hour (e.g., '06', '15') to filter the data. If None, aggregates all hours.

        Returns:
            str: base64-encoded image URL of the graph.
        """

        discrepancy_data = calculate_congestion.tap_discrepancy(line_filter)
        if not discrepancy_data:
            return None

        # Aggregate discrepancies per station
        station_discrepancies = {}
        for item in discrepancy_data:
            year_month, day_type, hour, pt_type, pt_code, discrepancy = item

            if time_per_hour and hour != time_per_hour:
                continue  # Skip if not matching the desired hour

            # If line_filter is provided, check if either part of the station code matches the line_filter
            if line_filter != "ALL":
                matches = re.findall(r'[A-Z]+[0-9]+', pt_code)
                # Check if any part of the station code matches the line_filter
                matched = any(line_filter in match for match in matches)
                if not matched:
                    continue  # Doesn't belong to the line
                station_key = pt_code  # Use the full station code
            else:
                station_key = pt_code  # Use the full station code

            if station_key not in station_discrepancies:
                station_discrepancies[station_key] = 0
            station_discrepancies[station_key] += discrepancy

        if not station_discrepancies:
            return None

        # Extract station number for sorting
        def extract_station_number(station_code):
            # Extract line and numeric parts
            match = re.match(r'([A-Z]+)(\d+)(?:/([A-Z]+)(\d+))?', station_code)

            if match:
                line = match.group(1)  # The first line (e.g., 'NS' or 'EW')
                line_number = int(match.group(2))  # The numeric part for that line
                if match.group(3):  # If there's a second part (e.g., '/EW13')
                    second_line = match.group(3)
                    second_line_number = int(match.group(4))
                    return (line, line_number, second_line, second_line_number)
                return (line, line_number)
            return (station_code, float('inf'))  # In case of an error

        stations = sorted(station_discrepancies.keys(), key=extract_station_number)
        values = [station_discrepancies[code] for code in stations]

        # Plot
        plt.figure(figsize=(18, 8))
        plt.bar(stations, values, color='orange')
        plt.xlabel('Station Code')
        plt.ylabel('Discrepancy (Tap-In - Tap-Out)')
        if time_per_hour:
            plt.title(f'Tap-In vs Tap-Out Discrepancy per Station for {line_filter} Line at {time_per_hour}:00 in one month')
        else:
            plt.title(f'Tap-In vs Tap-Out Discrepancy per Station for {line_filter} Line (All Hours) in one month')

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Encode to base64
        img = BytesIO()
        try:
            plt.savefig(img, format='png')
        except Exception as e:
            print(f"Error saving plot: {e}")
            return None
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()

        return plot_url
    

    @staticmethod
    def congestion_predictions(day_type="WEEKDAY"):
        data = TrainDatabaseInterface.get_data(4)  # Retrieve the congestion data
        proportions, total_tap_in = calculate_congestion.get_proportions()  # Retrieve the proportions and total tap-in

        # Separate data into Weekday and Weekend/Holiday
        weekday_data = [item for item in data if item[1] == 'WEEKDAY']
        weekend_data = [item for item in data if item[1] == 'WEEKENDS/HOLIDAY']

        # Filter data based on the selected day type
        if day_type == "WEEKDAY":
            selected_data = weekday_data
        elif day_type == "WEEKENDS/HOLIDAY":
            selected_data = weekend_data
        else:
            selected_data = []  # Return empty if an invalid day type is provided

        # If no data exists for the selected day type, return None
        if not selected_data:
            return None  # No plot to generate

        # Get the number of days in the current month
        date_example = selected_data[0][0]  # Assuming the first entry has the date in format YYYY-MM
        days_in_month = get_days_in_month(date_example)
        #print(days_in_month)

        # Now compute predicted load for each line
        predicted_loads = []
        for entry in selected_data:
            date, day_type, hour, mrt_load = entry  # Extract values for each entry
            mrt_load /= days_in_month  # Normalize to per-day load
            for line, tap_in_for_line in proportions.items():
                # Calculate predicted load for each line using the formula
                predicted_load = mrt_load * (tap_in_for_line / total_tap_in)
                predicted_loads.append([date, day_type, hour, line, round(predicted_load, 1)])

        return predicted_loads
    
    @staticmethod
    def render_congestion_predictions_graph(day_type="WEEKDAY", line="EWL"):
        # Define a mapping of full line names to their abbreviations
        line_mapping = {
            "EWL": "EW",  # EWL maps to EW
            "NSL": "NS",  # NSL maps to NS
            "CCL": "CC",  # CCL maps to CC
            "NEL": "NE",  # NEL maps to NE
            "DTL": "DT",  # DTL maps to DT
        }

        # If the selected line is not 'ALL', map the line to its abbreviation
        if line != "ALL":
            line = line_mapping.get(line, line)  # Default to the same line if not in mapping

        # Use the congestion_predictions function to get the predicted loads
        predicted_loads = calculate_congestion.congestion_predictions(day_type)

        # If there is no data to plot, return None
        if not predicted_loads:
            return None

        # Create the plot
        plt.figure(figsize=(15, 10))

        # If the selected line is 'ALL', plot for all lines
        if line == "ALL":
            # Loop through each line and plot data
            lines_to_plot = set(item[3] for item in predicted_loads)  # Get all unique lines (route_ids)
            for line in lines_to_plot:
                # Filter data for the specific line
                filtered_data = [item for item in predicted_loads if item[3] == line]
                x = [item[2] for item in filtered_data]  # X-axis: TIME_PER_HOUR (Hour)
                y = [item[4] for item in filtered_data]  # Y-axis: Predicted load
                # Plot the predicted load for each line
                plt.plot(x, y, marker='o', linestyle='-', label=f'Predicted Load - {line}')

                # Retrieve the train capacity for the line (default to 1920 if not found)
                capacity = calculate_congestion.train_capacities.get(line, 1920)

                # Calculate frequency lines for the specific train capacity (2.5 min and 6 min frequencies)
                freq_2_5 = (60 / 2.5) * capacity * 2  # 2.5 minute frequency (both directions)
                freq_6 = (60 / 6) * capacity * 2  # 6 minute frequency (both directions)

                # Plot the 2.5-minute and 6-minute frequency lines for this specific line
                plt.axhline(y=freq_2_5, color='r', linestyle='--', label=f'{line} 2.5 min Frequency')
                plt.axhline(y=freq_6, color='g', linestyle='--', label=f'{line} 6 min Frequency')

                # Label the points with their y values
                for i, value in enumerate(y):
                    plt.text(x[i], y[i], str(value), fontsize=9, ha='right', va='bottom')

        else:
            # If a specific line is selected, filter the data for that line
            filtered_data = [item for item in predicted_loads if item[3] == line]
            if not filtered_data:
                print(f"No data available for line {line}.")
                return None
            x = [item[2] for item in filtered_data]  # X-axis: TIME_PER_HOUR (Hour)
            y = [item[4] for item in filtered_data]  # Y-axis: Predicted load
            # Plot the predicted load for the selected line
            plt.plot(x, y, marker='o', linestyle='-', label=f'Predicted Load - {line}')

            # Retrieve the train capacity for the line (default to 1920 if not found)
            capacity = calculate_congestion.train_capacities.get(line, 1920)

            # Calculate frequency lines (2.5 min and 6 min frequencies) for the selected line
            freq_2_5 = (60 / 2.5) * capacity * 2  # 2.5 minute frequency (both directions)
            freq_6 = (60 / 6) * capacity * 2  # 6 minute frequency (both directions)

            # Plot the 2.5-minute and 6-minute frequency lines for the selected line
            plt.axhline(y=freq_2_5, color='r', linestyle='--', label=f'{line} 2.5 min Frequency')
            plt.axhline(y=freq_6, color='g', linestyle='--', label=f'{line} 6 min Frequency')

            # Label the points with their y values
            for i, value in enumerate(y):
                plt.text(x[i], y[i], str(value), fontsize=9, ha='right', va='bottom')

        # Labeling the plot
        plt.xlabel('Time per Hour (Hour of the Day)')
        plt.ylabel('Predicted Load (Total People in MRT System)')
        plt.title(f'Predicted Load for MRT Line {line} - {day_type}' if line != "ALL" else f'Predicted Load for MRT System - {day_type}')
        plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
        plt.tight_layout()  # Adjust layout to avoid label overlap
        plt.legend()

        # Save the plot to a BytesIO object
        img = BytesIO()
        try:
            plt.savefig(img, format='png')
        except Exception as e:
            print(f"Error saving plot: {e}")
            return None  # Return None if an error occurs

        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()  # Convert image to base64
        plt.close()  # Ensure the plot is properly closed after saving

        return plot_url


    



    
    @staticmethod
    def train_frequency_predictions(day_type="WEEKDAY"):
        # Dictionary for train capacities by route

        '''
        train_capacities = {
            'EW': 1920,  # East-West Line
            'NS': 1920,  # North-South Line
            'NE': 1920,  # North-East Line
            'CC': 931,   # Circle Line
            'DT': 931,   # Downtown Line
            'TE': 1280   # Thomson-East Coast Line
        }
        '''

        # Get congestion predictions based on the day type
        congestion_predictions = calculate_congestion.congestion_predictions(day_type)

        # List to store the result with all the relevant information
        frequency_results = []

        # Loop through the congestion predictions to calculate frequencies
        for date, day_type, hour, route_id, load in congestion_predictions:
            # Extract the line identifier (e.g., 'TE', 'NS', 'EW', etc.)
            line_id = route_id[:2]  # Get the first two characters of the route_id (e.g., 'TE', 'NS', 'EW')

            # Get the train capacity for the given route
            train_capacity = calculate_congestion.train_capacities.get(line_id, 1920)  # Default to 1920 if not found

            # Calculate number of trains needed per hour (both directions)
            no_trains = load / (train_capacity * 2)
            no_trains = max(no_trains, 1)  # Ensure at least 1 train per hour

            # Frequency in minutes between trains
            frequency = 60 / no_trains

            # Store the result with date, day_type, hour, route_id, and frequency
            frequency_results.append([date, day_type, hour, route_id, round(frequency, 3)])

        return frequency_results


    @staticmethod
    def render_train_frequency_graph(day_type="WEEKDAY", line="ALL"):
        # Define a mapping of full line names to their abbreviations
        line_mapping = {
            "EWL": "EW",  # EWL maps to EW
            "NSL": "NS",  # NSL maps to NS
            "CCL": "CC",  # CCL maps to CC
            "NEL": "NE",  # NEL maps to NE
            "DTL": "DT",  # DTL maps to DT
        }

        # If the selected line is not 'ALL', map the line to its abbreviation
        if line != "ALL":
            line = line_mapping.get(line, line)  # Default to the same line if not in mapping

        # Get the frequency results from the train_frequency_predictions method
        frequency_results = calculate_congestion.train_frequency_predictions(day_type)

        # If no line is selected, or 'ALL' is selected, return results for all lines
        if line != "ALL":
            frequency_results = [entry for entry in frequency_results if entry[3] == line]  # Assuming index 3 is route_id

        # Check if data is available for the selected line
        if not frequency_results:
            return None  # No data available, return None

        # Prepare the data for plotting (e.g., x-axis = TIME_PER_HOUR, y-axis = Frequency)
        if line == "ALL":
            # Plot for all lines, by filtering based on route_id
            lines_to_plot = set(entry[3] for entry in frequency_results)  # Get all unique lines (route_ids)
            plt.figure(figsize=(15, 10))
            
            for line in lines_to_plot:
                # Filter the results for this line
                filtered_data = [entry for entry in frequency_results if entry[3] == line]
                x = [entry[2] for entry in filtered_data]  # x-axis = TIME_PER_HOUR (Hour)
                y = [entry[4] for entry in filtered_data]  # y-axis = Frequency (minutes between trains)
                
                # Plot the data for the specific line
                plt.plot(x, y, marker='o', linestyle='-', label=f'Frequency - {line}')
                
                # Label the points with their y values
                for i, value in enumerate(y):
                    plt.text(x[i], y[i], str(value), fontsize=9, ha='right', va='bottom')

            # Labeling the plot
            plt.xlabel('Time per Hour (Hour of the Day)')
            plt.ylabel('Frequency of Trains (minutes between trains)')
            plt.title(f'Train Frequency Predictions for MRT System - {day_type}')
            plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
            plt.tight_layout()  # Adjust layout to avoid label overlap
            plt.legend()  # Add legend to differentiate lines

        else:
            # Plot for the specific line
            x = [entry[2] for entry in frequency_results]  # x-axis = TIME_PER_HOUR (Hour)
            y = [entry[4] for entry in frequency_results]  # y-axis = Frequency (minutes between trains)
            
            plt.figure(figsize=(15, 10))
            plt.plot(x, y, marker='o', linestyle='-', color='b')
            
            # Label the points with their y values
            for i, value in enumerate(y):
                plt.text(x[i], y[i], str(value), fontsize=9, ha='right', va='bottom')

            plt.xlabel('Time per Hour (Hour of the Day)')
            plt.ylabel('Frequency of Trains (minutes between trains)')
            plt.title(f'Train Frequency Predictions for {line} - {day_type}')
            plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
            plt.tight_layout()  # Adjust layout to avoid label overlap

        # Save the plot to a BytesIO object
        img = BytesIO()
        try:
            plt.savefig(img, format='png')
        except Exception as e:
            print(f"Error saving plot: {e}")
            return None  # Return None if an error occurs

        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()  # Convert image to base64
        plt.close()  # Ensure the plot is properly closed after saving

        return plot_url
    


    @staticmethod
    def train_frequency_predictions_extra(day_type="WEEKDAY", percent=10):
        # Dictionary for train capacities by route
        '''
        train_capacities = {
            'EW': 1920,  # East-West Line
            'NS': 1920,  # North-South Line
            'NE': 1920,  # North-East Line
            'CC': 931,   # Circle Line
            'DT': 931,   # Downtown Line
            'TE': 1280   # Thomson-East Coast Line
        }
        '''

        # Get congestion predictions based on the day type
        congestion_predictions = calculate_congestion.congestion_predictions(day_type)

        # List to store the result with all the relevant information
        frequency_results = []

        # Loop through the congestion predictions to calculate frequencies
        for date, day_type, hour, route_id, load in congestion_predictions:
            # Increase load by the specified percent
            load = load * (1 + percent / 100)

            # Extract the line identifier (e.g., 'TE', 'NS', 'EW', etc.)
            line_id = route_id[:2]  # Get the first two characters of the route_id (e.g., 'TE', 'NS', 'EW')

            # Get the train capacity for the given route
            train_capacity = calculate_congestion.train_capacities.get(line_id, 1920)  # Default to 1920 if not found

            # Calculate number of trains needed per hour (both directions)
            no_trains = load / (train_capacity * 2)
            no_trains = max(no_trains, 1)  # Ensure at least 1 train per hour

            # Frequency in minutes between trains
            frequency = 60 / no_trains

            # Store the result with date, day_type, hour, route_id, and frequency
            frequency_results.append([date, day_type, hour, route_id, round(frequency, 3)])

        return frequency_results


    @staticmethod
    def render_train_frequency_graph_extra(day_type="WEEKDAY", line="ALL", percent="10"):
        # Define a mapping of full line names to their abbreviations
        line_mapping = {
            "EWL": "EW",  # EWL maps to EW
            "NSL": "NS",  # NSL maps to NS
            "CCL": "CC",  # CCL maps to CC
            "NEL": "NE",  # NEL maps to NE
            "DTL": "DT",  # DTL maps to DT
        }

        # If the selected line is not 'ALL', map the line to its abbreviation
        if line != "ALL":
            line = line_mapping.get(line, line)  # Default to the same line if not in mapping

        # Convert the percent string to a float
        percent = float(percent)

        # Get the frequency results from the train_frequency_predictions_extra method
        frequency_results = calculate_congestion.train_frequency_predictions_extra(day_type, percent)

        # If no line is selected, or 'ALL' is selected, return results for all lines
        if line != "ALL":
            frequency_results = [entry for entry in frequency_results if entry[3] == line]  # Assuming index 3 is route_id

        # Check if data is available for the selected line
        if not frequency_results:
            return None  # No data available, return None

        # Prepare the data for plotting (e.g., x-axis = TIME_PER_HOUR, y-axis = Frequency)
        if line == "ALL":
            # Plot for all lines, by filtering based on route_id
            lines_to_plot = set(entry[3] for entry in frequency_results)  # Get all unique lines (route_ids)
            plt.figure(figsize=(15, 10))
            
            for line in lines_to_plot:
                # Filter the results for this line
                filtered_data = [entry for entry in frequency_results if entry[3] == line]
                x = [entry[2] for entry in filtered_data]  # x-axis = TIME_PER_HOUR (Hour)
                y = [entry[4] for entry in filtered_data]  # y-axis = Frequency (minutes between trains)
                
                # Plot the data for the specific line
                plt.plot(x, y, marker='o', linestyle='-', label=f'Frequency - {line}')
                
                # Label the points with their y values
                for i, value in enumerate(y):
                    plt.text(x[i], y[i], str(value), fontsize=9, ha='right', va='bottom')

            # Labeling the plot
            plt.xlabel('Time per Hour (Hour of the Day)')
            plt.ylabel('Frequency of Trains (minutes between trains)')
            plt.title(f'Train Frequency Predictions for MRT System - {day_type}')
            plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
            plt.tight_layout()  # Adjust layout to avoid label overlap
            plt.legend()  # Add legend to differentiate lines

        else:
            # Plot for the specific line
            x = [entry[2] for entry in frequency_results]  # x-axis = TIME_PER_HOUR (Hour)
            y = [entry[4] for entry in frequency_results]  # y-axis = Frequency (minutes between trains)
            
            plt.figure(figsize=(15, 10))
            plt.plot(x, y, marker='o', linestyle='-', color='b')
            
            # Label the points with their y values
            for i, value in enumerate(y):
                plt.text(x[i], y[i], str(value), fontsize=9, ha='right', va='bottom')

            plt.xlabel('Time per Hour (Hour of the Day)')
            plt.ylabel('Frequency of Trains (minutes between trains)')
            plt.title(f'Train Frequency Predictions for {line} - {day_type}')
            plt.xticks(rotation=90)  # Rotate the x-axis labels for readability
            plt.tight_layout()  # Adjust layout to avoid label overlap

        # Save the plot to a BytesIO object
        img = BytesIO()
        try:
            plt.savefig(img, format='png')
        except Exception as e:
            print(f"Error saving plot: {e}")
            return None  # Return None if an error occurs

        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()  # Convert image to base64
        plt.close()  # Ensure the plot is properly closed after saving

        return plot_url










    


    


    




        

'''
with app.app_context():
    #calculate_congestion.calculate()
    # Example usage
    
    start_station = 'BP3'  #keat Hong
    end_station = 'TE27' #Marine Terrace MRT Station (TE27)

    stations = calculate_congestion.find_shortest_path(start_station, end_station)
    print(stations)
    #print(len(stations) * 2.5)
'''

'''
with app.app_context():
    print(calculate_congestion.get_predicted_congestion(Hour=0))
'''

'''
with app.app_context():
    calculate_congestion.process_data()
    #calculate_congestion.get_graph()
'''
'''
with app.app_context():
    print(calculate_congestion.get_proportions())
'''

'''
with app.app_context():
    #print(calculate_congestion.tap_discrepancy())
    print(calculate_congestion.busiest_stations_top5())
'''
'''
with app.app_context():
    print(TrainDatabaseInterface.get_data(4))
'''

'''
with app.app_context():
    print(calculate_congestion.congestion_predictions())
'''

'''
with app.app_context():
    print(calculate_congestion.train_frequency_predictions())
'''