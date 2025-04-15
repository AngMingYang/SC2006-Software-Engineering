import sqlite3
from flask import Flask

app = Flask(__name__)

class TrainDatabaseInterface:
    db_path = 'Train_Database.db'

    stations = [
        'BP1', 'BP10', 'BP11', 'BP12', 'BP13', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7', 'BP8', 'BP9', 'CC1', 
        'CC10', 'CC11', 'CC12', 'CC13', 'CC14', 'CC15', 'CC16', 'CC17', 'CC19', 'CC2', 'CC20', 'CC21', 'CC22', 
        'CC23', 'CC24', 'CC25', 'CC26', 'CC27', 'CC28', 'CC29', 'CC3', 'CC4', 'CC5', 'CC6', 'CC7', 'CC8', 'CC9', 
        'CE1', 'CE2', 'CG1', 'CG2', 'DT1', 'DT10', 'DT11', 'DT12', 'DT13', 'DT14', 'DT15', 'DT16', 'DT17', 'DT18', 
        'DT19', 'DT2', 'DT20', 'DT21', 'DT22', 'DT23', 'DT24', 'DT25', 'DT26', 'DT27', 'DT28', 'DT29', 'DT3', 
        'DT30', 'DT31', 'DT32', 'DT33', 'DT34', 'DT35', 'DT5', 'DT6', 'DT7', 'DT8', 'DT9', 'EW1', 'EW10', 'EW11', 
        'EW12', 'EW13', 'EW14', 'EW15', 'EW16', 'EW17', 'EW18', 'EW19', 'EW2', 'EW20', 'EW21', 'EW22', 'EW23', 
        'EW24', 'EW25', 'EW26', 'EW27', 'EW28', 'EW29', 'EW3', 'EW30', 'EW31', 'EW32', 'EW33', 'EW4', 'EW5', 'EW6', 
        'EW7', 'EW8', 'EW9', 'NE1', 'NE10', 'NE11', 'NE12', 'NE13', 'NE14', 'NE15', 'NE16', 'NE17', 'NE18', 'NE3', 
        'NE4', 'NE5', 'NE6', 'NE7', 'NE8', 'NE9', 'NS1', 'NS10', 'NS11', 'NS12', 'NS13', 'NS14', 'NS15', 'NS16', 
        'NS17', 'NS18', 'NS19', 'NS2', 'NS20', 'NS21', 'NS22', 'NS23', 'NS24', 'NS25', 'NS26', 'NS27', 'NS28', 
        'NS3', 'NS4', 'NS5', 'NS7', 'NS8', 'NS9', 'PE1', 'PE2', 'PE3', 'PE4', 'PE5', 'PE6', 'PE7', 'PTC', 'PW1', 
        'PW2', 'PW3', 'PW4', 'PW5', 'PW6', 'PW7', 'SE1', 'SE2', 'SE3', 'SE4', 'SE5', 'STC', 'SW1', 'SW2', 'SW3', 
        'SW4', 'SW5', 'SW6', 'SW7', 'SW8', 'TE1', 'TE11', 'TE12', 'TE13', 'TE14', 'TE15', 'TE16', 'TE17', 'TE18', 
        'TE19', 'TE2', 'TE20', 'TE22', 'TE23', 'TE24', 'TE25', 'TE26', 'TE27', 'TE28', 'TE29', 'TE3', 'TE4', 'TE5', 
        'TE6', 'TE7', 'TE8', 'TE9'
    ]

    @staticmethod
    def get_db():
        """Return a new database connection (No Flask g)."""
        return sqlite3.connect(TrainDatabaseInterface.db_path, check_same_thread=False)

    @staticmethod
    def initialise_database():
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            cursor.execute('''CREATE TABLE IF NOT EXISTS TRAIN_DATA (
                YEAR_MONTH TEXT, 
                DAY_TYPE TEXT, 
                TIME_PER_HOUR TEXT, 
                PT_TYPE TEXT, 
                ORIGIN_PT_CODE TEXT, 
                DESTINATION_PT_CODE TEXT, 
                TOTAL_TRIPS TEXT,
                PRIMARY KEY (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, ORIGIN_PT_CODE, DESTINATION_PT_CODE)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS TRAIN_MOVEMENT (
                YEAR_MONTH TEXT, 
                DAY_TYPE TEXT, 
                TIME_PER_HOUR TEXT, 
                PT_TYPE TEXT, 
                PT_CODE TEXT, 
                TOTAL_TAP_IN_VOLUME TEXT, 
                TOTAL_TAP_OUT_VOLUME TEXT,
                PRIMARY KEY (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_CODE)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS TODAY_CONGESTION (
            Date TEXT, 
            Station TEXT, 
            Start TEXT, 
            CrowdLevel TEXT,
            PRIMARY KEY (Date, Station, Start)
            )''')

            cursor.execute('''CREATE TABLE IF NOT EXISTS PROCESSED_DATA (
            YEAR_MONTH TEXT, 
            DAY_TYPE TEXT, 
            TIME_PER_HOUR TEXT, 
            LOAD INTEGER,
            PRIMARY KEY (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR)
            )''')
            #note, need daytype as primary key else they would think its a duplicate and remove
            
            db.commit()
            db.close()
            print("Database table created or already exists.")
        except sqlite3.Error as e:
            print(f"Error initializing database: {e}")


    '''
    @staticmethod
    def insert_data(year_month, day_type, time_per_hour, pt_type, origin_pt_code, destination_pt_code, total_trips):
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            query = ''' '''
                INSERT OR IGNORE INTO TRAIN_DATA 
                (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, ORIGIN_PT_CODE, DESTINATION_PT_CODE, TOTAL_TRIPS)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''' '''
            cursor.execute(query, (year_month, day_type, time_per_hour, pt_type, origin_pt_code, destination_pt_code, total_trips))
            db.commit()
            db.close()
            print("Data inserted successfully.")
        except sqlite3.Error as e:
            print(f"Error inserting data: {e}")

    
    @staticmethod
    def insert_multiple_data(data):
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            query = ''' '''
                INSERT OR IGNORE INTO TRAIN_DATA 
                (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, ORIGIN_PT_CODE, DESTINATION_PT_CODE, TOTAL_TRIPS)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''' '''
            cursor.executemany(query, data)
            db.commit()
            db.close()
            print(f"Successfully inserted {len(data)} rows, duplicates ignored.")
        except sqlite3.Error as e:
            print(f"Error inserting multiple data: {e}")

    @staticmethod
    def get_data():
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM TRAIN_DATA")
            data = cursor.fetchall()
            db.close()

            # Convert fetched rows to list of lists
            return [list(row) for row in data]
        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")
            return []

    @staticmethod
    def delete_table():
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()
            cursor.execute(''' '''DROP TABLE IF EXISTS TRAIN_DATA ''' ''')
            db.commit()
            db.close()
            print("Table deleted successfully.")
        except sqlite3.Error as e:
            print(f"Error deleting table: {e}")


    @staticmethod
    def insert_train_movement_data(year_month, day_type, time_per_hour, pt_type, origin_pt_code, destination_pt_code, movement_status):
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            query = ''' '''
                INSERT OR IGNORE INTO TRAIN_MOVEMENT 
                (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, ORIGIN_PT_CODE, DESTINATION_PT_CODE, MOVEMENT_STATUS)
                VALUES (?, ?, ?, ?, ?, ?, ?) ''' '''
            cursor.execute(query, (year_month, day_type, time_per_hour, pt_type, origin_pt_code, destination_pt_code, movement_status))
            db.commit()
            db.close()
            print("Train movement data inserted successfully.")
        except sqlite3.Error as e:
            print(f"Error inserting train movement data: {e}")

    @staticmethod
    def insert_multiple_train_movement_data(data):
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            query = ''' '''
                INSERT OR IGNORE INTO TRAIN_MOVEMENT 
                (YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_TYPE, ORIGIN_PT_CODE, DESTINATION_PT_CODE, MOVEMENT_STATUS)
                VALUES (?, ?, ?, ?, ?, ?, ?) ''' '''
            cursor.executemany(query, data)
            db.commit()
            db.close()
            print(f"Successfully inserted {len(data)} rows into TRAIN_MOVEMENT, duplicates ignored.")
        except sqlite3.Error as e:
            print(f"Error inserting multiple train movement data: {e}")

    @staticmethod
    def get_train_movement_data():
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM TRAIN_MOVEMENT")
            data = cursor.fetchall()
            db.close()

            return [list(row) for row in data]
        except sqlite3.Error as e:
            print(f"Error fetching train movement data: {e}")
            return []
    '''    

    @staticmethod
    def get_columns(table_name):
        """Fetch the columns of a given table dynamically."""
        db = TrainDatabaseInterface.get_db()
        cursor = db.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        db.close()
        return columns

    @staticmethod
    def get_data(mode):
        if mode == 1 :
            table_name = 'TRAIN_DATA'  
        elif mode == 2:
            table_name = "TRAIN_MOVEMENT" 
        elif mode == 3:
            table_name = "TODAY_CONGESTION" 
        elif mode == 4:
            table_name = "PROCESSED_DATA" 
        columns = TrainDatabaseInterface.get_columns(table_name)
        
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()
            cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name}")
            data = cursor.fetchall()
            db.close()

            return [list(row) for row in data]
        except sqlite3.Error as e:
            print(f"Error fetching data: {e}")
            return []
        
    @staticmethod
    def insert_multiple_data(data, mode=1):  #doesnt accept pandas dataframe, only lists.
        TrainDatabaseInterface.initialise_database()

        """Insert multiple rows into the database dynamically."""
        # Set columns and table name based on the mode
        tables = {1: 'TRAIN_DATA', 2: 'TRAIN_MOVEMENT', 3: 'TODAY_CONGESTION', 4: 'PROCESSED_DATA'}
        table_name = tables.get(mode)
        
        if not table_name:
            raise ValueError("Invalid mode. Mode should be either 1, 2, or 3.")
        
        # Get the columns dynamically from the database schema
        columns = TrainDatabaseInterface.get_columns(table_name)

        

        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            # Prepare the query with placeholders for columns
            placeholders = ', '.join(['?'] * len(columns))
            column_names = ', '.join(columns)

            query = f'''INSERT OR IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})'''

            # If the data is a list of dictionaries (for mode 3), convert it to tuples
            if isinstance(data, list) and isinstance(data[0], dict):
                data = [tuple(d[column] for column in columns) for d in data]

            
            #print(len(data))

            
            cursor.executemany(query, data)
            db.commit()
            db.close()
            print(f"Successfully inserted {len(data)} rows into {table_name}, duplicates ignored.")
        except sqlite3.Error as e:
            print(f"Error inserting multiple data into {table_name}: {e}")

    @staticmethod
    def delete_table(table_name):
        try:
            db = TrainDatabaseInterface.get_db()
            cursor = db.cursor()

            # Create dynamic SQL to delete the specified table
            query = f"DROP TABLE IF EXISTS {table_name}"
            cursor.execute(query)
            db.commit()
            db.close()
            print(f"Table {table_name} deleted successfully.")
        except sqlite3.Error as e:
            print(f"Error deleting table {table_name}: {e}")




    

# Example Usage inside application context
'''
with app.app_context():
    TrainDatabaseInterface.initialise_database()
    
    # Example of inserting data
    #TrainDatabaseInterface.insert_data("2025-03", "Weekday", "08:00", "Train", "ST1", "ST2", 100)

    # Example of inserting multiple rows
    data = [
        ("2025-03", "Weekend", "09:00", "Train", "ST2", "ST3", 150),
        ("2025-03", "Weekday", "10:00", "Train", "ST3", "ST4", 200)
    ]
    #TrainDatabaseInterface.insert_multiple_data(data)
    
    # Example of fetching all data
    all_data = TrainDatabaseInterface.get_data()
    print("All Train Data:", all_data)

    # Example of deleting the table
    #TrainDatabaseInterface.delete_table()

'''
# The connection will be automatically closed at the end of the app context.

'''
with app.app_context():
    TrainDatabaseInterface.initialise_database()
    data = [["2025-02","9","DT6","1000"]]
    TrainDatabaseInterface.insert_processed_data(data)
    TrainDatabaseInterface.delete_processed_data()
'''


'''
with app.app_context():
    TrainDatabaseInterface.initialise_database()
    data = [["2025-02","9","DT6","1000"]]
    print(TrainDatabaseInterface.get_data(3))
'''
'''
with app.app_context():
    data = [["2025-02","WEEKDAY","10","TRAIN","BP10","1278.0"]]
    TrainDatabaseInterface.insert_multiple_data(data,4)
'''
'''
stations = [
        'BP1', 'BP10', 'BP11', 'BP12', 'BP13', 'BP2', 'BP3', 'BP4', 'BP5', 'BP6', 'BP7', 'BP8', 'BP9', 'CC1', 
        'CC10', 'CC11', 'CC12', 'CC13', 'CC14', 'CC15', 'CC16', 'CC17', 'CC19', 'CC2', 'CC20', 'CC21', 'CC22', 
        'CC23', 'CC24', 'CC25', 'CC26', 'CC27', 'CC28', 'CC29', 'CC3', 'CC4', 'CC5', 'CC6', 'CC7', 'CC8', 'CC9', 
        'CE1', 'CE2', 'CG1', 'CG2', 'DT1', 'DT10', 'DT11', 'DT12', 'DT13', 'DT14', 'DT15', 'DT16', 'DT17', 'DT18', 
        'DT19', 'DT2', 'DT20', 'DT21', 'DT22', 'DT23', 'DT24', 'DT25', 'DT26', 'DT27', 'DT28', 'DT29', 'DT3', 
        'DT30', 'DT31', 'DT32', 'DT33', 'DT34', 'DT35', 'DT5', 'DT6', 'DT7', 'DT8', 'DT9', 'EW1', 'EW10', 'EW11', 
        'EW12', 'EW13', 'EW14', 'EW15', 'EW16', 'EW17', 'EW18', 'EW19', 'EW2', 'EW20', 'EW21', 'EW22', 'EW23', 
        'EW24', 'EW25', 'EW26', 'EW27', 'EW28', 'EW29', 'EW3', 'EW30', 'EW31', 'EW32', 'EW33', 'EW4', 'EW5', 'EW6', 
        'EW7', 'EW8', 'EW9', 'NE1', 'NE10', 'NE11', 'NE12', 'NE13', 'NE14', 'NE15', 'NE16', 'NE17', 'NE18', 'NE3', 
        'NE4', 'NE5', 'NE6', 'NE7', 'NE8', 'NE9', 'NS1', 'NS10', 'NS11', 'NS12', 'NS13', 'NS14', 'NS15', 'NS16', 
        'NS17', 'NS18', 'NS19', 'NS2', 'NS20', 'NS21', 'NS22', 'NS23', 'NS24', 'NS25', 'NS26', 'NS27', 'NS28', 
        'NS3', 'NS4', 'NS5', 'NS7', 'NS8', 'NS9', 'PE1', 'PE2', 'PE3', 'PE4', 'PE5', 'PE6', 'PE7', 'PTC', 'PW1', 
        'PW2', 'PW3', 'PW4', 'PW5', 'PW6', 'PW7', 'SE1', 'SE2', 'SE3', 'SE4', 'SE5', 'STC', 'SW1', 'SW2', 'SW3', 
        'SW4', 'SW5', 'SW6', 'SW7', 'SW8', 'TE1', 'TE11', 'TE12', 'TE13', 'TE14', 'TE15', 'TE16', 'TE17', 'TE18', 
        'TE19', 'TE2', 'TE20', 'TE22', 'TE23', 'TE24', 'TE25', 'TE26', 'TE27', 'TE28', 'TE29', 'TE3', 'TE4', 'TE5', 
        'TE6', 'TE7', 'TE8', 'TE9'
    ]
'''