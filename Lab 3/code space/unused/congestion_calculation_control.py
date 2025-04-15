class CongestionCalculationControl:

    columns = ['hour', 'station', 'congestion lvl']
    congestion = pd.DataFrame(columns=columns)

    @staticmethod
    def replace_code(station, multi_code_stations):
        return multi_code_stations.get(station, station)
    
    @staticmethod
    def get_station_count_enhanced(ew_station, hour): 
        # Change code if needed
        ew_station = CongestionCalculationControl.replace_code(ew_station, multi_code_stations)

        # Filter transport node data (tap-in and tap-out volumes)
        filtered_node_data = node_data[ 
            (node_data["DAY_TYPE"] == "WEEKDAY") &
            (node_data["PT_CODE"] == ew_station) & 
            (node_data["TIME_PER_HOUR"] == hour)
        ]
        tap_in_out_count = filtered_node_data["TOTAL_TAP_IN_VOLUME"].sum() + filtered_node_data["TOTAL_TAP_OUT_VOLUME"].sum()

        # Filter origin-destination data for trips involving the station
        filtered_od_origin = od_data[
            (od_data["DAY_TYPE"] == "WEEKDAY") &
            (od_data["ORIGIN_PT_CODE"] == ew_station) &
            (od_data["TIME_PER_HOUR"] == hour)
        ]
        filtered_od_destination = od_data[
            (od_data["DAY_TYPE"] == "WEEKDAY") &
            (od_data["DESTINATION_PT_CODE"] == ew_station) &
            (od_data["TIME_PER_HOUR"] == hour)
        ]
        trips_from_station = filtered_od_origin["TOTAL_TRIPS"].sum()
        trips_to_station = filtered_od_destination["TOTAL_TRIPS"].sum()

        # Total estimated people at the station
        total_people = max(0, tap_in_out_count + trips_to_station - trips_from_station)

        return total_people
    
    @staticmethod
    def congestion_percentage(hour):
        for i in range(1, 34):
            station = f"EW{i}"
            num = CongestionCalculationControl.get_station_count_enhanced(station, hour)

            if station in multi_code_stations:
                if station == "EW16":
                    congestion_lvl = ((num) / (1700 * 30 * 2 * 3)) * 100
                else:
                    congestion_lvl = ((num) / (1700 * 30 * 2 * 2)) * 100
            else:
                congestion_lvl = ((num) / (1700 * 30 * 2)) * 100

            if congestion_lvl > 100:
                congestion_lvl = 100

            new_row = pd.DataFrame({'hour': [hour], 'station': [station], 'congestion lvl': [congestion_lvl]})
            CongestionCalculationControl.congestion = pd.concat([CongestionCalculationControl.congestion, new_row], ignore_index=True)
        
        return CongestionCalculationControl.congestion

    @staticmethod
    def get_color(value):
        if value <= 50:
            return "green"
        elif value <= 80:
            return "yellow"
        else:
            return "red"

    @staticmethod
    def get_heatmap():
        # Ensure stations are sorted properly
        CongestionCalculationControl.congestion["station"] = pd.Categorical(CongestionCalculationControl.congestion["station"], 
                                                                             categories=[f"EW{i}" for i in range(1, 34)], 
                                                                             ordered=True)
        CongestionCalculationControl.congestion = CongestionCalculationControl.congestion.sort_values("station")

        # Set up the figure
        fig = plt.figure(figsize=(12, 6))  # Create figure

        # Create a barplot with congestion levels
        colors = [CongestionCalculationControl.get_color(x) for x in CongestionCalculationControl.congestion["congestion lvl"]]
        bars = plt.bar(CongestionCalculationControl.congestion["station"], CongestionCalculationControl.congestion["congestion lvl"], color=colors)

        # Labels and styling
        plt.xlabel("Stations", fontsize=12)
        plt.ylabel("Congestion (%)", fontsize=12)
        plt.title("MRT Station Congestion Levels", fontsize=14)
        plt.xticks(rotation=90)
        plt.ylim(0, max(CongestionCalculationControl.congestion["congestion lvl"]) + 10)

        legend_patches = [
            Patch(color="green", label="Low (0-50%)"),
            Patch(color="yellow", label="Moderate (50-80%)"),
            Patch(color="red", label="High (>80%)")
        ]
        plt.legend(handles=legend_patches, loc="upper left")

        # Display the hour at the right side
        hour = CongestionCalculationControl.congestion["hour"].iloc[0]  # Extract the hour from the dataframe
        plt.text(len(CongestionCalculationControl.congestion["station"]), max(CongestionCalculationControl.congestion["congestion lvl"]), f"Hour = {hour}", 
                fontsize=14, fontweight="bold", ha="right", va="top", color="black")

        # Save the plot to a BytesIO buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)  # Rewind the buffer to the beginning
        # Save the image to the static folder
        image_dir = "static"
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)

        image_path = os.path.join(image_dir, "congestion_heatmap.png")
        with open(image_path, "wb") as f:
            f.write(buf.getbuffer())
        # Close the plot (important to avoid memory issues)
        plt.close(fig)  # Close the figure properly

        return buf  # Return the buffer containing the image
