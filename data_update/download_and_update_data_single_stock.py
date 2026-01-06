import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Set pandas display options for better terminal output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 20)

def download_stock_data(symbol, period="max"):
    """
    Download daily stock data for a given symbol
    """
    print(f"\n{'='*60}")
    print(f"Downloading data for: {symbol}")
    print(f"Period: {period}")
    print(f"{'='*60}\n")
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            print(f"❌ No data found for symbol: {symbol}")
            return None
        
        df.reset_index(inplace=True)
        return df
        
    except Exception as e:
        print(f"❌ Error downloading data for {symbol}: {e}")
        return None

if __name__ == "__main__":
    upload_to_mysql = False
    
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        period = sys.argv[2] if len(sys.argv) > 2 else "max"
        if '--upload' in sys.argv or '-u' in sys.argv:
            upload_to_mysql = True
    else:
        symbol = input("Enter stock symbol: ").upper()
        period = "max"
        upload_to_mysql = True # Default to true for interactive
    
    df = download_stock_data(symbol, period)
    
    if df is not None and upload_to_mysql:
        print("Uploading to MySQL...")
        sys.path.insert(0, str(Path(__file__).parent.parent / 'mysql_scripts'))
        from upload_stock_prices import download_and_upload_stock_data, create_table_if_not_exists
        create_table_if_not_exists()
        download_and_upload_stock_data(symbol)
