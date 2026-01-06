import pandas as pd
import time
import sys
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from root
BASE_DIR = Path(__file__).parent.parent
load_dotenv(BASE_DIR / ".env")

# Add mysql_scripts to path
sys.path.insert(0, str(BASE_DIR / 'mysql_scripts'))

from upload_stock_prices import download_and_upload_stock_data, create_table_if_not_exists
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "stock_prices"
# Adjusted path for symbols file
SYMBOLS_FILE = str(BASE_DIR / "data/unique_symbols.csv")
DELAY_SECONDS = 0.5 # Faster for updates

def sort_stock_prices_table():
    """
    Sort the stock_prices table by symbol and date
    """
    print("Sorting stock_prices table...")
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        conn.execute(text(f"CREATE TABLE `{TABLE_NAME}_sorted` LIKE `{TABLE_NAME}`;"))
        conn.execute(text(f"INSERT INTO `{TABLE_NAME}_sorted` SELECT * FROM `{TABLE_NAME}` ORDER BY symbol, date;"))
        conn.execute(text(f"DROP TABLE `{TABLE_NAME}`;"))
        conn.execute(text(f"RENAME TABLE `{TABLE_NAME}_sorted` TO `{TABLE_NAME}`;"))
        conn.commit()
    print("✅ Table sorted")

def download_all_symbols():
    """
    Download stock data for all symbols in unique_symbols.csv
    """
    if not os.path.exists(SYMBOLS_FILE):
        print(f"❌ Symbols file not found: {SYMBOLS_FILE}")
        return
    
    symbols_df = pd.read_csv(SYMBOLS_FILE)
    symbols = symbols_df['symbol'].tolist()
    
    print(f"Found {len(symbols)} symbols to update")
    create_table_if_not_exists()
    
    successful = 0
    failed = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}...", end=' ')
        try:
            success = download_and_upload_stock_data(symbol)
            if success:
                print("OK")
                successful += 1
            else:
                print("FAIL")
                failed += 1
        except Exception as e:
            print(f"ERR: {e}")
            failed += 1
        
        # if i < len(symbols):
        # time.sleep(DELAY_SECONDS) 
    
    if successful > 0:
        sort_stock_prices_table()
    
    print(f"Done. Success: {successful}, Failed: {failed}")

if __name__ == "__main__":
    download_all_symbols()
