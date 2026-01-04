import requests
import os
from sqlalchemy import create_engine, text
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
LOGO_DEV_API_KEY = os.getenv("LOGO_DEV_API_KEY")

def download_and_save_logo(domain, symbol, engine):
    """
    Download logo from logo.dev and save to MySQL database
    
    Args:
        domain: Company domain (e.g., 'verizon.com')
        symbol: Stock symbol (e.g., 'VZ')
        engine: SQLAlchemy engine
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not domain or not LOGO_DEV_API_KEY:
        return False
    
    # Construct logo.dev URL
    logo_url = f"https://img.logo.dev/{domain}?token={LOGO_DEV_API_KEY}&size=120"
    
    try:
        # Download logo
        response = requests.get(logo_url, timeout=10)
        
        if response.status_code == 200:
            logo_data = response.content
            
            # Save to database
            with engine.connect() as conn:
                conn.execute(
                    text("UPDATE companies SET logo = :logo WHERE symbol = :symbol"),
                    {"logo": logo_data, "symbol": symbol}
                )
                conn.commit()
            
            return True
        else:
            print(f"  ✗ HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def download_all_logos_to_db():
    """
    Download logos for all companies with domains and save to MySQL
    """
    print(f"\n{'='*60}")
    print("Downloading Company Logos to MySQL Database")
    print(f"{'='*60}\n")
    
    if not LOGO_DEV_API_KEY:
        print("❌ ERROR: LOGO_DEV_API_KEY not found in .env file")
        return
    
    # Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # Get all companies with domains but without logos
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT symbol, domain 
            FROM companies 
            WHERE domain IS NOT NULL 
            AND domain != '' 
            AND (logo IS NULL OR LENGTH(logo) = 0)
        """))
        companies = [(row[0], row[1]) for row in result]
    
    print(f"Found {len(companies)} companies needing logos")
    print(f"Saving logos to MySQL database...\n")
    
    success = 0
    failed = 0
    
    for i, (symbol, domain) in enumerate(companies, 1):
        print(f"[{i}/{len(companies)}] {symbol} ({domain})...", end=" ")
        
        if download_and_save_logo(domain, symbol, engine):
            print(f"✓ Saved to DB")
            success += 1
        else:
            failed += 1
        
        # Small delay to avoid rate limiting
        if i % 10 == 0:
            time.sleep(1)
            print(f"  (Pausing 1s to avoid rate limit...)")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  ✓ Downloaded & Saved: {success}")
    print(f"  ✗ Failed: {failed}")
    print(f"  💾 Logos stored in MySQL 'companies.logo' column")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    download_all_logos_to_db()
