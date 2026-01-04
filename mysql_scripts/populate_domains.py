import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "companies"

def get_company_domain(symbol):
    """
    Get company website domain using yfinance
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # Get website URL
        website = info.get('website', None)
        
        if website:
            # Extract domain from URL
            # Remove http://, https://, www.
            domain = website.replace('https://', '').replace('http://', '').replace('www.', '')
            # Remove trailing slash and path
            domain = domain.split('/')[0]
            return domain
        
        return None
        
    except Exception as e:
        print(f"  Error for {symbol}: {e}")
        return None

def populate_domains():
    """
    Populate domain column for all companies in database
    """
    print(f"\n{'='*60}")
    print("Populating Company Domains")
    print(f"{'='*60}\n")
    
    # Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # Get all symbols
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT symbol FROM `{TABLE_NAME}` WHERE domain IS NULL OR domain = ''"))
        symbols = [row[0] for row in result]
    
    print(f"Found {len(symbols)} companies without domain")
    print(f"Starting domain extraction...\n")
    
    success = 0
    failed = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {symbol}...", end=" ")
        
        domain = get_company_domain(symbol)
        
        if domain:
            # Update database
            with engine.connect() as conn:
                conn.execute(
                    text(f"UPDATE `{TABLE_NAME}` SET domain = :domain WHERE symbol = :symbol"),
                    {"domain": domain, "symbol": symbol}
                )
                conn.commit()
            print(f"✓ {domain}")
            success += 1
        else:
            print(f"✗ No domain found")
            failed += 1
        
        # Small delay to avoid rate limiting
        if i % 10 == 0:
            time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  ✓ Success: {success}")
    print(f"  ✗ Failed: {failed}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    populate_domains()
