from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "companies"

def add_logo_column():
    """
    Add 'logo' BLOB column to companies table for storing logo images
    """
    print(f"--- Adding 'logo' column to {TABLE_NAME} table ---")
    
    # Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text(f"SHOW COLUMNS FROM `{TABLE_NAME}` LIKE 'logo';"))
        column_exists = result.fetchone() is not None
        
        if column_exists:
            print(f"ℹ️  Column 'logo' already exists in {TABLE_NAME}")
        else:
            # Add logo column (MEDIUMBLOB can store up to 16MB)
            print(f"Adding 'logo' column (MEDIUMBLOB)...")
            conn.execute(text(f"""
                ALTER TABLE `{TABLE_NAME}` 
                ADD COLUMN `logo` MEDIUMBLOB NULL AFTER `domain`;
            """))
            conn.commit()
            print(f"✅ Column 'logo' added successfully")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    add_logo_column()
