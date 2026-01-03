import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# --- CONFIGURATION ---
DB_USER = "root"
DB_PASS = "Plus7070"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "reflexivity"
TABLE_NAME = "stock_prices"

def download_and_upload_stock_data(symbol):
    """
    Download stock data from Yahoo Finance and upload to MySQL
    
    Parameters:
    -----------
    symbol : str
        Stock ticker symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
    --------
    bool
        True if successful, False otherwise
    """
    
    print(f"\n{'='*60}")
    print(f"Processing: {symbol}")
    print(f"{'='*60}")
    
    try:
        # Download data using yfinance
        print(f"Downloading data from Yahoo Finance...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="max")
        
        if df.empty:
            print(f"⚠️  No data found for symbol: {symbol}")
            return False
        
        # Reset index to make Date a column
        df.reset_index(inplace=True)
        
        # Rename columns to lowercase
        df.columns = [col.lower().replace(' ', '_') for col in df.columns]
        
        # Add symbol column as first column
        df.insert(0, 'symbol', symbol.upper())
        
        # Select only the columns we want
        columns_to_keep = ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume', 'dividends', 'stock_splits']
        
        # Keep only columns that exist
        df = df[[col for col in columns_to_keep if col in df.columns]]
        
        print(f"✅ Downloaded {len(df)} rows")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print(f"   Columns: {list(df.columns)}")
        
        # Connect to MySQL
        connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        engine = create_engine(connection_string)
        
        # Check existing data to avoid duplicates
        with engine.connect() as conn:
            # Check if symbol already has data
            check_query = text(f"SELECT COUNT(*) as cnt FROM `{TABLE_NAME}` WHERE symbol = :symbol")
            result = conn.execute(check_query, {"symbol": symbol.upper()})
            existing_count = result.scalar()
            
            if existing_count > 0:
                print(f"ℹ️  Found {existing_count} existing rows for {symbol}")
                # Get the latest date
                latest_query = text(f"SELECT MAX(date) FROM `{TABLE_NAME}` WHERE symbol = :symbol")
                result = conn.execute(latest_query, {"symbol": symbol.upper()})
                latest_date = result.scalar()
                print(f"   Latest date in DB: {latest_date}")
        
        # Upload to MySQL using INSERT IGNORE to skip duplicates
        print(f"Uploading to MySQL table '{TABLE_NAME}'...")
        
        # We'll use a custom approach to handle duplicates
        # First, try to append
        rows_before = len(df)
        
        # Use if_exists='append' but we'll handle duplicates at DB level with PRIMARY KEY
        df.to_sql(name=TABLE_NAME, con=engine, if_exists='append', index=False, chunksize=1000, method='multi')
        
        # Count actual rows added (MySQL will reject duplicates due to PRIMARY KEY)
        with engine.connect() as conn:
            count_query = text(f"SELECT COUNT(*) FROM `{TABLE_NAME}` WHERE symbol = :symbol")
            result = conn.execute(count_query, {"symbol": symbol.upper()})
            total_count = result.scalar()
        
        new_rows = total_count - existing_count if existing_count > 0 else total_count
        
        print(f"✅ Upload complete:")
        print(f"   Attempted: {rows_before} rows")
        print(f"   New rows added: {new_rows}")
        print(f"   Total rows for {symbol}: {total_count}")
        return True
        
    except Exception as e:
        print(f"❌ Error processing {symbol}: {e}")
        return False

def create_table_if_not_exists():
    """
    Create the stock_prices table if it doesn't exist
    """
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        # Check if table exists
        result = conn.execute(text(f"SHOW TABLES LIKE '{TABLE_NAME}';"))
        table_exists = result.fetchone() is not None
        
        if not table_exists:
            print(f"Creating table '{TABLE_NAME}'...")
            # Create table with proper schema
            create_table_sql = f"""
            CREATE TABLE `{TABLE_NAME}` (
                `symbol` VARCHAR(50) NOT NULL,
                `date` DATETIME NOT NULL,
                `open` FLOAT,
                `high` FLOAT,
                `low` FLOAT,
                `close` FLOAT,
                `volume` BIGINT,
                `dividends` FLOAT,
                `stock_splits` FLOAT,
                PRIMARY KEY (`symbol`, `date`),
                INDEX idx_symbol (`symbol`),
                INDEX idx_date (`date`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            conn.execute(text(create_table_sql))
            conn.commit()
            print(f"✅ Table '{TABLE_NAME}' created successfully")
        else:
            print(f"ℹ️  Table '{TABLE_NAME}' already exists")

if __name__ == "__main__":
    import sys
    
    # Create table if needed
    create_table_if_not_exists()
    
    if len(sys.argv) > 1:
        # Use symbol from command line argument
        symbol = sys.argv[1].upper()
    else:
        # Interactive mode
        symbol = input("Enter stock symbol (e.g., AAPL, MSFT, GOOGL): ").upper()
    
    # Download and upload
    success = download_and_upload_stock_data(symbol)
    
    if success:
        print(f"\n{'='*60}")
        print(f"✅ SUCCESS: {symbol} data uploaded to MySQL")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}")
        print(f"❌ FAILED: Could not process {symbol}")
        print(f"{'='*60}\n")
