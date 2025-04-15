import requests
import zipfile
import os
import csv
import io

#https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf

class ApiMallInterface:

    #static attirbutes
    #two api keys i have:
    #u35GvcV6RWOoKlGoM4YRZw==
    #hWKHIXOiTuGEwgVocbhIAA==
    __api_key = "hWKHIXOiTuGEwgVocbhIAA==" #privated attribute

    train_line = "EWL"


    '''
    api_url_7 = "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain" 
    #2.7PASSENGER VOLUME BY ORIGIN DESTINATION TRAIN STATIONS
    #Update Freq, 10th of every month

    api_url_8 = "https://datamall2.mytransport.sg/ltaodataservice/PV/Train"
    #2.8 PASSENGER VOLUME BY TRAIN STATIONS
    #Update Freq, 10th of every month
    
    #api_url_11 = "https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts?TrainLine=EWL"
    api_url_11 = "https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts" #generic no station specified
    #2.11 TRAIN SERVICE ALERTS
    #Update Freq Ad hoc

    api_url_24 = "https://datamall2.mytransport.sg/ltaodataservice/PCDRealTime?TrainLine=EWL"       
    #api_url_24 = "https://datamall2.mytransport.sg/ltaodataservice/PCDRealTime" #generic no station specified
    #2.24 STATION CROWD DENSITY REAL TIME
    #Update Freq 10 minutes

    api_url_25 = "https://datamall2.mytransport.sg/ltaodataservice/PCDForecast"
    #2.25 STATION CROWD DENSITY FORECAST
    #Update Freq 24 hours

    '''
    @staticmethod
    def check_fault(data):
        return "fault" in data

    @staticmethod
    def get_api_url(url, line="EWL"):
        url = str(url)

        api_urls = {
            "7": ApiMallInterface.api_url_7(),
            "8": ApiMallInterface.api_url_8(),
            "11": ApiMallInterface.api_url_11(line),
            "24": ApiMallInterface.api_url_24(line),
            "25": ApiMallInterface.api_url_25(line),
        }

        if url not in api_urls:
            print("Invalid URL")
            return -1

        data = requests.get(api_urls[url], headers={
            "AccountKey": ApiMallInterface.__api_key,
            "accept": "application/json"
        }).json()

        if ApiMallInterface.check_fault(data):
            print("Error 401: Rate limit quota exceeded. Please try again later.")
            return []

        return ApiMallInterface.process_data(data, url, line)

    


    @staticmethod
    def process_data(data, mode,line=None):
        if "value" not in data:
            print("No 'value' field found in the response.")
            return []

        if mode == "7" or mode == "8":
            download_link = data["value"][0]["Link"]
            print(f"Downloading from: {download_link}")

            zip_filename = f"data_{mode}.zip"  # Unique ZIP filename per mode
            extract_folder = f"data_{mode}"  # Unique extraction folder per mode

            if os.path.exists(zip_filename):
                os.remove(zip_filename)
                print(f"Removed previous {zip_filename}")

            # Download ZIP file
            zip_response = requests.get(download_link)
            with open(zip_filename, "wb") as f:
                f.write(zip_response.content)

            # Extract ZIP file
            if os.path.exists(extract_folder):
                for file in os.listdir(extract_folder):
                    os.remove(os.path.join(extract_folder, file))
            else:
                os.makedirs(extract_folder)

            with zipfile.ZipFile(zip_filename, "r") as zip_ref:
                zip_ref.extractall(extract_folder)

            # Read CSV file
            extracted_files = os.listdir(extract_folder)
            if not extracted_files:
                print("No extracted CSV files found.")
                return []

            csv_filename = extracted_files[0]  # Get first extracted file
            csv_file_path = os.path.join(extract_folder, csv_filename)

            with open(csv_file_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile)
                data_list = list(reader)

            print(f"CSV data extracted from: {csv_filename}")
            return data_list  # Return CSV data
        else:
            print(f"Returning JSON 'value' field for mode {mode}")
            return data["value"]

    @staticmethod
    def api_url_7():
        return "https://datamall2.mytransport.sg/ltaodataservice/PV/ODTrain"

    @staticmethod
    def api_url_8():
        return "https://datamall2.mytransport.sg/ltaodataservice/PV/Train"

    @staticmethod
    def api_url_11(train_line="EWL"):
        return f"https://datamall2.mytransport.sg/ltaodataservice/TrainServiceAlerts?TrainLine={train_line}"

    @staticmethod
    def api_url_24(train_line="EWL"):
        return f"https://datamall2.mytransport.sg/ltaodataservice/PCDRealTime?TrainLine={train_line}"

    @staticmethod
    def api_url_25(train_line="EWL"):
        return f"https://datamall2.mytransport.sg/ltaodataservice/PCDForecast?TrainLine={train_line}"


   


#print(help(request))
#print(help(get))
#print(ApiMallInterface.get_api_url("8"))
#   7 : ['YEAR_MONTH', 'DAY_TYPE', 'TIME_PER_HOUR', 'PT_TYPE', 'ORIGIN_PT_CODE', 'DESTINATION_PT_CODE', 'TOTAL_TRIPS']  #this is people in train
#   8: ['YEAR_MONTH', 'DAY_TYPE', 'TIME_PER_HOUR', 'PT_TYPE', 'ORIGIN_PT_CODE', 'DESTINATION_PT_CODE', 'TOTAL_TRIPS'] #this is people taped in and tapped at at which station.


#print(ApiMallInterface.get_api_url("24"))
#print(ApiMallInterface.get_api_url("25"))
