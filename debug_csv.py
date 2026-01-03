
import pandas as pd
import json

path = r'd:/PYTHON/ALGOS/reflexivity/data/all_themes/car_rental_integration.csv'

try:
    df = pd.read_csv(path, encoding='utf-8', on_bad_lines='error') # Strict mode to find errors
    print("Columns:", df.columns.tolist())
    records = df.to_dict(orient='records')
    print("First record keys:", list(records[0].keys()))
    print("First record name:", records[0].get('name'))
    print("Read success. Rows:", len(df))
except Exception as e:
    print("Error reading CSV:", e)
