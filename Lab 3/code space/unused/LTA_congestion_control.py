import pandas as pd
from Api_Mall_Interface import ApiMallInterface

class calculate_congestion:
    @staticmethod
    def get_congestion_data():
        """
        Retrieves real-time station congestion data from API 24,
        performs load balancing analysis by counting how many stations
        fall into each CrowdLevel (e.g., Low, Moderate, High).

        Returns:
            dict: A summary of station congestion grouped by level.
        """
        try:
            # Step 1: Get API 24 real-time crowd data
            data = ApiMallInterface.get_api_url("24")
            if not data:
                return {"error": "No congestion data returned from API."}

            # Step 2: Convert to DataFrame
            df = pd.DataFrame(data)
            if 'Station' not in df.columns or 'CrowdLevel' not in df.columns:
                return {"error": "Missing expected fields in API data."}

            # Step 3: Load Balancing Analysis
            load_balance = df['CrowdLevel'].value_counts().reset_index()
            load_balance.columns = ['CrowdLevel', 'StationCount']

            # Step 4: Group stations by crowd level
            station_imbalance = df.groupby('CrowdLevel')['Station'].apply(list).to_dict()

            return {
                "source": "API 24 - Real-Time Station Crowd Data",
                "load_balance_summary": load_balance.to_dict(orient='records'),
                "station_imbalance": station_imbalance
            }

        except Exception as e:
            return {"error": str(e)}
        
print(calculate_congestion.get_congestion_data())