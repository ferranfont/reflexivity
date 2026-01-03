import pandas as pd
from sqlalchemy import create_engine, text
import os

# --- CONFIGURATION ---
DB_USER = "root"
DB_PASS = "Plus7070"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "reflexivity"
TABLE_NAME = "theme_summary"

CSV_FILE = "data/industry_summary_offline.csv"

def upload_summary_to_db():
    print("--- Uploading Industry Summary to MySQL ---")
    
    # 1. Check CSV existence
    if not os.path.exists(CSV_FILE):
        print(f"Error: CSV file not found at {CSV_FILE}")
        return

    # 2. Read CSV
    print(f"Reading {CSV_FILE}...")
    try:
        df = pd.read_csv(CSV_FILE)
        print(f"Read {len(df)} rows.")
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # 3. Connect to Database using SQLAlchemy
    # Format: mysql+mysqlconnector://user:password@host:port/database
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        engine = create_engine(connection_string)
        
        # 4. Upload Data
        # if_exists='replace' drops the table and recreates it. 
        # Use 'append' if you want to add to it.
        print(f"Uploading to table '{TABLE_NAME}' in database '{DB_NAME}'...")
        
        df.to_sql(name=TABLE_NAME, con=engine, if_exists='replace', index=False)
        
        print("Success! Data uploaded.")
        
        # Verify
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {TABLE_NAME}"))
            count = result.fetchone()[0]
            print(f"Table '{TABLE_NAME}' now has {count} rows.")
            
    except Exception as e:
        print(f"Database Error: {e}")
        print("Ensure MySQL is running and mysql-connector-python is installed.")

if __name__ == "__main__":
    upload_summary_to_db()
