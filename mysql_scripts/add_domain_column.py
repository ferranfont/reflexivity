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

def add_domain_column():
    """
    Add 'domain' column to companies table
    """
    print(f"--- Adding 'domain' column to {TABLE_NAME} table ---")
    
    # Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text(f"SHOW COLUMNS FROM `{TABLE_NAME}` LIKE 'domain';"))
        column_exists = result.fetchone() is not None
        
        if column_exists:
            print(f"ℹ️  Column 'domain' already exists in {TABLE_NAME}")
        else:
            # Add domain column
            print(f"Adding 'domain' column...")
            conn.execute(text(f"""
                ALTER TABLE `{TABLE_NAME}` 
                ADD COLUMN `domain` VARCHAR(255) NULL AFTER `name`;
            """))
            conn.commit()
            print(f"✅ Column 'domain' added successfully")
        
        # Create index for faster lookups
        try:
            conn.execute(text(f"CREATE INDEX idx_domain ON `{TABLE_NAME}` (domain);"))
            conn.commit()
            print(f"✅ Index created on 'domain' column")
        except Exception as e:
            if "Duplicate key name" in str(e):
                print(f"ℹ️  Index on 'domain' already exists")
            else:
                print(f"⚠️  Could not create index: {e}")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    add_domain_column()
