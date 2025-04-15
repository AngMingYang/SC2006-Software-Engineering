import pandas as pd
from collections import defaultdict
from Train_Database_Interface import TrainDatabaseInterface

#aadi

class calculate_monthly_report:
    @staticmethod
    def generate_monthly_report():
        """
        Analyzes tap-in/out OD data from TRAIN_DATA (API 7) and returns
        structured summaries including:
        - Peak Hour Traffic
        - Origin-Destination Matrix
        - Station Congestion Ranking
        - Time-of-Day Distribution

        Returns:
            dict: Aggregated report data ready for rendering or charting.
        """
        try:
            raw_data = TrainDatabaseInterface.get_data()
            if not raw_data:
                return {"error": "No train data found in TRAIN_DATA."}

            # Unpack data into DataFrame
            cols = ['YEAR_MONTH', 'DAY_TYPE', 'TIME_PER_HOUR', 'PT_TYPE', 'ORIGIN_PT_CODE', 'DESTINATION_PT_CODE', 'TOTAL_TRIPS']
            df = pd.DataFrame(raw_data, columns=cols)

            # Filter to current month (latest one in DB)
            latest_month = df['YEAR_MONTH'].max()
            df = df[df['YEAR_MONTH'] == latest_month].copy()

            # Convert TOTAL_TRIPS and TIME_PER_HOUR to int
            df['TOTAL_TRIPS'] = df['TOTAL_TRIPS'].astype(int)
            df['TIME_PER_HOUR'] = df['TIME_PER_HOUR'].astype(int)

            # 1. Peak Hour Traffic
            peak_traffic = df.groupby('TIME_PER_HOUR')['TOTAL_TRIPS'].sum().sort_values(ascending=False).head(5)
            peak_hour_analysis = peak_traffic.reset_index().rename(columns={"TOTAL_TRIPS": "TotalTrips"}).to_dict(orient='records')

            # 2. Origin-Destination Matrix
            od_matrix = df.groupby(['ORIGIN_PT_CODE', 'DESTINATION_PT_CODE'])['TOTAL_TRIPS'].sum().reset_index()
            od_matrix_top = od_matrix.sort_values(by='TOTAL_TRIPS', ascending=False).head(10).to_dict(orient='records')

            # 3. Station Congestion Ranking (Top 10 origin tap-ins)
            station_congestion = df.groupby('ORIGIN_PT_CODE')['TOTAL_TRIPS'].sum().sort_values(ascending=False).head(10)
            station_congestion_ranking = station_congestion.reset_index().rename(columns={"TOTAL_TRIPS": "TotalDepartures"}).to_dict(orient='records')

            # 4. Time-of-Day Traffic Distribution
            def map_time_bucket(hour):
                if 0 <= hour < 6:
                    return "Late Night"
                elif 6 <= hour < 12:
                    return "Morning"
                elif 12 <= hour < 18:
                    return "Afternoon"
                elif 18 <= hour < 24:
                    return "Evening"
                return "Unknown"

            df['TimeBucket'] = df['TIME_PER_HOUR'].apply(map_time_bucket)
            time_bucket_dist = df.groupby('TimeBucket')['TOTAL_TRIPS'].sum().reset_index().rename(columns={"TOTAL_TRIPS": "TotalTrips"}).to_dict(orient='records')

            return {
                "source": "API 7 OD Tap-in/Out Database",
                "month": latest_month,
                "peak_hour_traffic": peak_hour_analysis,
                "od_matrix_top_10": od_matrix_top,
                "top_congested_stations": station_congestion_ranking,
                "time_bucket_distribution": time_bucket_dist
            }

        except Exception as e:
            return {"error": f"Failed to generate monthly report: {str(e)}"}
        
'''
print(calculate_monthly_report.generate_monthly_report())'
'''