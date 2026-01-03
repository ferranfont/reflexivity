import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# Set pandas display options for better terminal output
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 20)

def download_stock_data(symbol, period="max"):
    """
    Download daily stock data for a given symbol
    
    Parameters:
    -----------
    symbol : str
        Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    period : str
        Data period. Valid values: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        Default: 'max' (maximum available data)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with columns: Date, Open, High, Low, Close, Volume, Adj Close
    """
    
    print(f"\n{'='*60}")
    print(f"Downloading data for: {symbol}")
    print(f"Period: {period}")
    print(f"{'='*60}\n")
    
    try:
        # Download data using yfinance
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            print(f"❌ No data found for symbol: {symbol}")
            return None
        
        # Reset index to make Date a column
        df.reset_index(inplace=True)
        
        # Display summary
        print(f"✅ Successfully downloaded {len(df)} days of data")
        print(f"Date range: {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
        print(f"\nColumns available: {list(df.columns)}")
        
        # Display statistics
        print(f"\n{'─'*60}")
        print("DATA SUMMARY:")
        print(f"{'─'*60}")
        print(df.describe())
        
        # Display first few rows
        print(f"\n{'─'*60}")
        print("FIRST 5 ROWS:")
        print(f"{'─'*60}")
        print(df.head())
        
        # Display last few rows
        print(f"\n{'─'*60}")
        print("LAST 5 ROWS:")
        print(f"{'─'*60}")
        print(df.tail())
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading data for {symbol}: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    import sys
    
    # Check if we should upload to MySQL
    upload_to_mysql = False
    
    if len(sys.argv) > 1:
        # Use symbol from command line argument
        symbol = sys.argv[1].upper()
        period = sys.argv[2] if len(sys.argv) > 2 else "max"
        # Check for --upload flag
        if '--upload' in sys.argv or '-u' in sys.argv:
            upload_to_mysql = True
    else:
        # Default example
        symbol = input("Enter stock symbol (e.g., AAPL, MSFT, GOOGL): ").upper()
        period = input("Enter period (default: max): ").strip() or "max"
        upload_choice = input("Upload to MySQL? (y/n, default: n): ").strip().lower()
        upload_to_mysql = upload_choice == 'y'
    
    # Download and display data
    df = download_stock_data(symbol, period)
    
    if df is not None:
        print(f"\n{'='*60}")
        print(f"Data successfully loaded into DataFrame variable 'df'")
        print(f"Shape: {df.shape} (rows, columns)")
        print(f"{'='*60}\n")
        
        # Upload to MySQL if requested
        if upload_to_mysql:
            print(f"\n{'='*60}")
            print("Uploading to MySQL...")
            print(f"{'='*60}\n")
            
            # Import the upload function
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mysql_scripts'))
            from upload_stock_prices import download_and_upload_stock_data, create_table_if_not_exists
            
            # Create table if needed
            create_table_if_not_exists()
            
            # Upload
            success = download_and_upload_stock_data(symbol)
            
            if success:
                print(f"\n{'='*60}")
                print(f"✅ Data uploaded to MySQL successfully!")
                print(f"{'='*60}\n")

