import requests
import json
import pandas as pd
import time
import os
import random

# --- CONFIGURATION ---
OUTPUT_DIR = "outputs/all_themes"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Headers from the NEW cURL (Master List)
# We will use these for both requests, as they share the same session context
headers = {
    'accept': '*/*',
    'accept-language': 'es-ES,es;q=0.9,ca;q=0.8,en;q=0.7,fr;q=0.6,it;q=0.5',
    'content-type': 'application/json; charset=utf-8',
    'priority': 'u=1, i',
    'referer': 'https://ndcdyn.interactivebrokers.com/portal/?loginType=1&action=ACCT_MGMT_MAIN&mid=001&clt=1',
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'x-client-app': 'web',
    'x-client-label': 'IB',
    'x-request-id': '1',
    'x-service': 'AM.LOGIN',
    # Updated Session ID from the latest cURL
    'x-session-id': '0.6419ad437b2ba.1767393502318.d155b00c'
}

# Updated Cookies from the latest cURL
# Using a string format for simplicity and robustness
cookie_string = 'x-sess-uuid=0.57cd5a68.1767393347.34df6f02; SBID=pz2ada1l3fpme0wfo91; Campus_tag_ga=GA1.1.760243602.1767047593; Campus_tag_ga_3DZW8R5ZLR=GS2.1.s1767132400$o3$g0$t1767132408$j52$l0$h0; client_app=TWS; JSESSIONID=0A7B03373BB5166B6BC0090D27611F3A.ny5wwwsso3; AKA_A2=A; IB_PRIV_PREFS=0%7C0%7C0; PHPSESSID=ac1em1h8abljag2lu7fo7crasu; web=3446759953; XYZAB_AM.LOGIN=7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; XYZAB=7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; USERID=49703865; CP_VER=v1; cp=2d3ba92d78beacff5f70404394a4d5a7; cp.lb=n4.7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; x-sess-uuid=0.5dcd5a68.1767392336.32090f8e; IS_MASTER=false; pastandalone=""; ROUTEIDD=.ny5japp1; RT="z=1&dm=interactivebrokers.com&si=b050e094-218a-4cfe-9326-0b8c08ba12cd&ss=mjxfrfvf&sl=2&tt=2uq&obo=1&rl=1&ld=p1vl"; ibcust=2780efb37bfb464428db9873c4638792'
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
        
        # We need to recursively find all objects that have a 'key' and 'name'
        # because the structure might be nested (A-Z > Category > Theme)
        found_themes = []
        
        def extract_themes(node):
            if isinstance(node, dict):
                if 'key' in node and 'name' in node:
                    found_themes.append({
                        'name': node['name'],
                        'key': node['key']
                    })
                # Search in all values
                for v in node.values():
                    extract_themes(v)
            elif isinstance(node, list):
                for item in node:
                    extract_themes(item)
                    
        extract_themes(data)
        
        # Remove duplicates based on key
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
        'max': '100', # Try to get more
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

# --- MAIN EXECUTION ---
all_themes = get_all_themes()
print(f"Found {len(all_themes)} potential themes.")

if all_themes:
    # --- SAFETY BRAKE ---
    # Retrieve only the first 5 for now to test. 
    # Change this to endpoints = all_themes to run everything.
    # Retrieve ALL themes
    endpoints = all_themes 
    
    print(f"Processing first {len(endpoints)} themes as a test...")
    
    for i, theme in enumerate(endpoints):
        t_name = theme['name']
        t_key = theme['key']
        
        print(f"[{i+1}/{len(endpoints)}] Downloading: {t_name}...")
        
        df = get_theme_companies(t_name, t_key)
        
        if df is not None and not df.empty:
            # Clean filename
            safe_name = "".join([c if c.isalnum() else "_" for c in t_name])
            filename = f"{OUTPUT_DIR}/{safe_name}.csv"
            df.to_csv(filename, index=False)
            print(f"   -> Saved {len(df)} companies to {filename}")
        else:
            print("   -> No data found or empty.")
            
        # Be polite to the server
        time.sleep(random.uniform(1.0, 2.5))

    print("\nDone! Check the 'outputs/all_themes' folder.")
    print("To download ALL themes, edit the script and change 'endpoints = all_themes[:5]' to 'endpoints = all_themes'")
else:
    print("Could not find any themes in the master list response.")
