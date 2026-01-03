import requests
import json
import pandas as pd
import time
import os
import random

# --- CONFIGURATION ---
# Save directly to the main data folder
OUTPUT_DIR = "../data/all_themes"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Headers from the latest session (You may need to update 'Cookie' and 'x-session-id' in the future)
headers = {
    'accept': '*/*',
    'accept-language': 'es-ES,es;q=0.9,ca;q=0.8,en;q=0.7,fr;q=0.6,it;q=0.5',
    'content-type': 'application/json; charset=utf-8',
    'priority': 'u=1, i',
    'referer': 'https://ndcdyn.interactivebrokers.com/portal/?loginType=1&action=ACCT_MGMT_MAIN&mid=001&clt=1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'x-client-app': 'web',
    'x-client-label': 'IB',
    'x-request-id': '1',
    'x-service': 'AM.LOGIN',
    # NOTE: These values expire! Update them from a logged-in browser session if script fails.
    'x-session-id': '0.6419ad437b2ba.1767393502318.d155b00c'
}

cookie_string = 'x-sess-uuid=0.57cd5a68.1767393347.34df6f02; SBID=pz2ada1l3fpme0wfo91; ... (UPDATE ME)'
headers['Cookie'] = cookie_string

def get_all_themes():
    """Fetch the master list of themes."""
    url = 'https://ndcdyn.interactivebrokers.com/tws.proxy/knowledge-graph/meta/themes'
    params = {'lang': 'es'}
    
    print("Fetching Master Theme List...")
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        found_themes = []
        
        def extract_themes(node):
            if isinstance(node, dict):
                if 'key' in node and 'name' in node:
                    found_themes.append({
                        'name': node['name'],
                        'key': node['key']
                    })
                for v in node.values():
                    extract_themes(v)
            elif isinstance(node, list):
                for item in node:
                    extract_themes(item)
                    
        extract_themes(data)
        unique_themes = {t['key']: t for t in found_themes}.values()
        return list(unique_themes)

    except Exception as e:
        print(f"Error fetching master list: {e}")
        return []

def get_theme_companies(theme_name, theme_key):
    """Fetch companies for a specific theme key."""
    url = 'https://ndcdyn.interactivebrokers.com/tws.proxy/knowledge-graph/ui/theme'
    params = {
        'key': theme_key,
        'max': '100',
        'lang': 'es'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"Failed to get data for {theme_name}: Status {response.status_code}")
            return None
            
        data = response.json()
        linked = data.get('linked_companies', [])
        
        if not linked:
            return None
            
        df = pd.DataFrame(linked)
        return df
        
    except Exception as e:
        print(f"Error for {theme_name}: {e}")
        return None

if __name__ == "__main__":
    print("--- Theme Downloader ---")
    print("WARNING: This script requires an active IBKR Brokerage Session ID and Cookies.")
    print("If it fails (401/403), update the 'headers' dictionary in the script.")
    
    all_themes = get_all_themes()
    print(f"Found {len(all_themes)} potential themes.")
    
    if all_themes:
        # Default: Process ALL
        endpoints = all_themes
        
        print(f"Processing {len(endpoints)} themes...")
        
        for i, theme in enumerate(endpoints):
            t_name = theme['name']
            t_key = theme['key']
            
            print(f"[{i+1}/{len(endpoints)}] Downloading: {t_name}...")
            
            df = get_theme_companies(t_name, t_key)
            
            if df is not None and not df.empty:
                safe_name = "".join([c if c.isalnum() else "_" for c in t_name])
                filename = f"{OUTPUT_DIR}/{safe_name}.csv"
                df.to_csv(filename, index=False)
                print(f"   -> Saved {len(df)} companies to {filename}")
            else:
                print("   -> No data found or empty.")
                
            time.sleep(random.uniform(1.0, 2.5))

    else:
        print("Could not find any themes.")
