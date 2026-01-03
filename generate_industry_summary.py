import requests
import json
import pandas as pd
import os
import re
from fuzzywuzzy import process

# --- CONFIGURATION ---
OUTPUT_FILE = "outputs/themes_by_industry.csv"
CSV_DIR = "data/all_themes"

# Headers for IBKR API (Same as before)
headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9', # Requesting English explicitly
    'content-type': 'application/json; charset=utf-8',
    'priority': 'u=1, i',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'x-client-app': 'web',
    'x-client-label': 'IB',
    'x-request-id': '1',
    'x-service': 'AM.LOGIN',
    'x-session-id': '0.6419ad437b2ba.1767393502318.d155b00c'
}

# Cookie string
cookie_string = 'x-sess-uuid=0.57cd5a68.1767393347.34df6f02; SBID=pz2ada1l3fpme0wfo91; Campus_tag_ga=GA1.1.760243602.1767047593; Campus_tag_ga_3DZW8R5ZLR=GS2.1.s1767132400$o3$g0$t1767132408$j52$l0$h0; client_app=TWS; JSESSIONID=0A7B03373BB5166B6BC0090D27611F3A.ny5wwwsso3; AKA_A2=A; IB_PRIV_PREFS=0%7C0%7C0; PHPSESSID=ac1em1h8abljag2lu7fo7crasu; web=3446759953; XYZAB_AM.LOGIN=7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; XYZAB=7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; USERID=49703865; CP_VER=v1; cp=2d3ba92d78beacff5f70404394a4d5a7; cp.lb=n4.7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; x-sess-uuid=0.5dcd5a68.1767392336.32090f8e; IS_MASTER=false; pastandalone=""; ROUTEIDD=.ny5japp1; RT="z=1&dm=interactivebrokers.com&si=b050e094-218a-4cfe-9326-0b8c08ba12cd&ss=mjxfrfvf&sl=2&tt=2uq&obo=1&rl=1&ld=p1vl"; ibcust=2780efb37bfb464428db9873c4638792'
headers['Cookie'] = cookie_string

def get_english_taxonomy():
    """Fetch the master list in English to get the Sector -> Theme hierarchy."""
    url = 'https://ndcdyn.interactivebrokers.com/tws.proxy/knowledge-graph/meta/themes'
    params = {'lang': 'en'} # ENGLISH
    
    print("Fetching English Taxonomy...")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        print(f"Error fetching taxonomy: {e}")
        return None

def flatten_taxonomy(node, parent_sector="Uncategorized", result_list=None):
    """
    Recursively traverse the JSON to find relationships: Sector -> Theme.
    The structure is often:
    [
        { name: "Automotive", nodes: [ { name: "EV", ... }, ... ] },
        ...
    ]
    """
    if result_list is None:
        result_list = []

    if isinstance(node, list):
        for item in node:
            flatten_taxonomy(item, parent_sector, result_list)
    
    elif isinstance(node, dict):
        # Check if this node is a Theme (has 'key') or a Sector (has 'nodes' but maybe no key?)
        # Usually checking if it has children 'nodes' means it's a category/sector.
        
        node_name = node.get('name', 'Unknown')
        
        if 'nodes' in node and node['nodes']:
            # It's a Category/Sector (e.g., "Agriculture")
            # Recurse with THIS node as the new parent sector
            flatten_taxonomy(node['nodes'], node_name, result_list)
        else:
            # It's a Leaf/Theme (e.g., "Precision Agriculture")
            # Or it's a theme that happens to have no sub-nodes.
            if 'key' in node: # Stronger indicator it's a theme
                result_list.append({
                    'Industry': parent_sector,
                    'Theme': node_name,
                    'Key': node.get('key')
                })

    return result_list

def count_file_rows(filepath):
    """Counts lines in a csv file minus header."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1 # Minus header
    except:
        return 0

def match_and_count_files(taxonomy_list):
    """
    Matches API themes (English) to local CSV files (English normalized)
    and counts the companies.
    """
    # Get all local files
    try:
        local_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    except FileNotFoundError:
        print(f"Directory {CSV_DIR} not found.")
        return []
    
    final_data = []
    
    print(f"Matching {len(taxonomy_list)} themes against {len(local_files)} local files...")
    
    for item in taxonomy_list:
        theme_name = item['Theme']
        
        # Normalize theme name to match filename format: "Automotive Parts" -> "automotive_parts.csv"
        # We need to be careful with translation discrepancies (Google Trans vs Official)
        # But user requested renamed files to English, so hopefully they are close.
        
        # Heuristic 1: Exact match normalized
        target_name = theme_name.lower().replace(" ", "_") + ".csv"
        target_name_clean = "".join([c for c in target_name if c.isalnum() or c == '_' or c == '.'])
        
        match_file = None
        
        if target_name_clean in local_files:
            match_file = target_name_clean
        else:
            # Heuristic 2: Fuzzy match
            # The google translation might have been "agribusiness.csv" vs official "agriculture_business.csv"
            # We search in local_files for the best match
            best_match, score = process.extractOne(target_name_clean, local_files)
            if score > 80: # Confidence threshold
                match_file = best_match
        
        count = 0
        if match_file:
            count = count_file_rows(os.path.join(CSV_DIR, match_file))
        
        final_data.append({
            'Industry': item['Industry'],
            'Theme': theme_name,
            'Companies_Count': count,
            'Matched_File': match_file if match_file else "Not Found"
        })
        
    return final_data

# --- MAIN ---
taxonomy_data = get_english_taxonomy()

if taxonomy_data:
    # 1. Build the mapping
    flat_list = flatten_taxonomy(taxonomy_data)
    print(f"Extracted {len(flat_list)} themes from taxonomy.")
    
    # 2. Match with files and count
    final_rows = match_and_count_files(flat_list)
    
    # 3. Save
    df = pd.DataFrame(final_rows)
    # Sort by Industry then Theme
    df = df.sort_values(by=['Industry', 'Theme'])
    
    # Reorder columns as requested
    df = df[['Industry', 'Theme', 'Companies_Count']]
    
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Successfully saved summary to: {OUTPUT_FILE}")
    print(df.head(10))
else:
    print("Failed to retrieve taxonomy.")
