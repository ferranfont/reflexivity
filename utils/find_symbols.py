import pandas as pd
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DB_USER = "root"
DB_PASS = "Plus7070"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "reflexivity"

def find_unique_symbols():
    """
    Query MySQL database to get unique symbols from companies table
    and return as a pandas DataFrame/list
    """
    print("--- Finding Unique Symbols from MySQL ---")
    
    # 1. Connect to DB
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    # 2. Query unique symbols
    query = """
    SELECT DISTINCT symbol 
    FROM companies 
    WHERE symbol IS NOT NULL 
    ORDER BY symbol
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        symbols = [row[0] for row in result]
    
    # 3. Create DataFrame
    symbols_df = pd.DataFrame(symbols, columns=['symbol'])
    
    print(f"Found {len(symbols_df)} unique symbols")
    print(f"\nFirst 10 symbols:")
    print(symbols_df.head(10))
    
    return symbols_df

if __name__ == "__main__":
    # Get unique symbols as DataFrame
    symbols_df = find_unique_symbols()
    
    # You can also get it as a list
    symbols_list = symbols_df['symbol'].tolist()
    
    print(f"\nSymbols available as:")
    print(f"  - DataFrame: symbols_df ({len(symbols_df)} rows)")
    print(f"  - List: symbols_list ({len(symbols_list)} items)")
    
    # Optional: Save to CSV
    output_file = "data/unique_symbols.csv"
    symbols_df.to_csv(output_file, index=False)
    print(f"\nSaved to: {output_file}")
