import pandas as pd
import time
import sys
import os

# Add mysql_scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mysql_scripts'))

from upload_stock_prices import download_and_upload_stock_data, create_table_if_not_exists
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DB_USER = "root"
DB_PASS = "Plus7070"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "reflexivity"
TABLE_NAME = "stock_prices"
SYMBOLS_FILE = "data/unique_symbols.csv"
DELAY_SECONDS = 30

def sort_stock_prices_table():
    """
    Sort the stock_prices table by symbol and date
    """
    print(f"\n{'='*60}")
    print("Sorting stock_prices table by symbol and date...")
    print(f"{'='*60}\n")
    
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        # Create a temporary sorted table
        print("Creating sorted copy...")
        conn.execute(text(f"""
            CREATE TABLE `{TABLE_NAME}_sorted` LIKE `{TABLE_NAME}`;
        """))
        
        conn.execute(text(f"""
            INSERT INTO `{TABLE_NAME}_sorted` 
            SELECT * FROM `{TABLE_NAME}` 
            ORDER BY symbol, date;
        """))
        
        # Drop original and rename
        print("Replacing original table...")
        conn.execute(text(f"DROP TABLE `{TABLE_NAME}`;"))
        conn.execute(text(f"RENAME TABLE `{TABLE_NAME}_sorted` TO `{TABLE_NAME}`;"))
        
        conn.commit()
        
    print("✅ Table sorted successfully\n")

def download_all_symbols():
    """
    Download stock data for all symbols in unique_symbols.csv
    """
    print(f"\n{'='*60}")
    print("BULK STOCK DATA DOWNLOAD")
    print(f"{'='*60}\n")
    
    # Load symbols
    if not os.path.exists(SYMBOLS_FILE):
        print(f"❌ Symbols file not found: {SYMBOLS_FILE}")
        return
    
    symbols_df = pd.read_csv(SYMBOLS_FILE)
    symbols = symbols_df['symbol'].tolist()
    
    print(f"Found {len(symbols)} symbols to process")
    print(f"Delay between requests: {DELAY_SECONDS} seconds\n")
    
    # Create table if needed
    create_table_if_not_exists()
    
    # Statistics
    successful = 0
    failed = 0
    skipped = 0
    
    # Process each symbol
    for i, symbol in enumerate(symbols, 1):
        print(f"\n{'─'*60}")
        print(f"[{i}/{len(symbols)}] Processing: {symbol}")
        print(f"{'─'*60}")
        
        try:
            success = download_and_upload_stock_data(symbol)
            
            if success:
                successful += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ Unexpected error for {symbol}: {e}")
            failed += 1
        
        # Show progress
        print(f"\nProgress: ✅ {successful} | ❌ {failed} | Remaining: {len(symbols) - i}")
        
        # Delay before next request (except for last symbol)
        if i < len(symbols):
            print(f"⏳ Waiting {DELAY_SECONDS} seconds before next request...")
            time.sleep(DELAY_SECONDS)
    
    # Final summary
    print(f"\n{'='*60}")
    print("DOWNLOAD COMPLETE")
    print(f"{'='*60}")
    print(f"Total symbols: {len(symbols)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"{'='*60}\n")
    
    # Sort the table
    if successful > 0:
        sort_stock_prices_table()
    
    print(f"\n{'='*60}")
    print("✅ ALL DONE!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Confirm before starting
    print(f"\n{'='*60}")
    print("⚠️  WARNING: This will download data for ALL symbols")
    print(f"   Total symbols: ~2429")
    print(f"   Estimated time: ~20 hours (with 30s delay)")
    print(f"{'='*60}\n")
    
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        download_all_symbols()
    else:
        print("\n❌ Operation cancelled by user\n")
