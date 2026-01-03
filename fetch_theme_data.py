import requests
import json
import pandas as pd
import time
import os

# Create outputs directory if it doesn't exist
output_dir = "outputs"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# --- CONFIGURATION FROM CURL ---
url = 'https://ndcdyn.interactivebrokers.com/tws.proxy/knowledge-graph/ui/theme'

# Parameters from the query string
params = {
    'key': '642f1812-8766-41bd-bbe9-35347732526d',
    'max': '30',
    'lang': 'es'
}

# Headers from the cURL
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
    'x-ccp-session-id': '',
    'x-client-app': 'web',
    'x-client-label': 'IB',
    'x-request-id': '1501',
    'x-service': 'AM.LOGIN',
    'x-session-id': '0.5cf6df3cd73eb8.1767392357159.906a16ff'
}

# Cookies from the cURL (extracted manually for Python format)
cookies = {
    'x-sess-uuid': '0.5dcd5a68.1767392829.320e9cc2',
    'SBID': 'pz2ada1l3fpme0wfo91',
    'Campus_tag_ga': 'GA1.1.760243602.1767047593',
    'Campus_tag_ga_3DZW8R5ZLR': 'GS2.1.s1767132400$o3$g0$t1767132408$j52$l0$h0',
    'client_app': 'TWS',
    'JSESSIONID': '0A7B03373BB5166B6BC0090D27611F3A.ny5wwwsso3',
    'AKA_A2': 'A',
    'IB_PRIV_PREFS': '0%7C0%7C0',
    'PHPSESSID': 'ac1em1h8abljag2lu7fo7crasu',
    'web': '3446759953',
    'XYZAB_AM.LOGIN': '7bc2305aca3992f3627c39eeb91a9adbdcbf15a1',
    'XYZAB': '7bc2305aca3992f3627c39eeb91a9adbdcbf15a1',
    'USERID': '49703865',
    'CP_VER': 'v1',
    'RT': '"z=1&dm=interactivebrokers.com&si=b050e094-218a-4cfe-9326-0b8c08ba12cd&ss=mjxfcdem&sl=1&tt=pd&rl=1"',
    'cp': '2d3ba92d78beacff5f70404394a4d5a7',
    'cp.lb': 'n4.7bc2305aca3992f3627c39eeb91a9adbdcbf15a1',
    # Note: The second x-sess-uuid (0.5dcd5a68.1767392336.32090f8e) appeared in the string.
    # Python requests dict only supports unique keys. 
    # Usually the last one or the most specific one matters. 
    # We will prioritize the first one seen which seemed more recent/relevant or try to combine if needed.
    # But usually `requests` handles this via the CookieJar if we passed the string directly.
    # Here we manually set the one that looks newer or valid.
    # Let's try passing the full cookie string in headers instead to be safer 
    # since duplicate keys in dicts are tricky.
}

# ALTERNATIVE: PASS COOKIES AS HEADER STRING TO PRESERVE EXACT FORMAT
headers['Cookie'] = 'x-sess-uuid=0.5dcd5a68.1767392829.320e9cc2; SBID=pz2ada1l3fpme0wfo91; Campus_tag_ga=GA1.1.760243602.1767047593; Campus_tag_ga_3DZW8R5ZLR=GS2.1.s1767132400$o3$g0$t1767132408$j52$l0$h0; client_app=TWS; JSESSIONID=0A7B03373BB5166B6BC0090D27611F3A.ny5wwwsso3; AKA_A2=A; IB_PRIV_PREFS=0%7C0%7C0; PHPSESSID=ac1em1h8abljag2lu7fo7crasu; web=3446759953; XYZAB_AM.LOGIN=7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; XYZAB=7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; USERID=49703865; CP_VER=v1; RT="z=1&dm=interactivebrokers.com&si=b050e094-218a-4cfe-9326-0b8c08ba12cd&ss=mjxfcdem&sl=1&tt=pd&rl=1"; cp=2d3ba92d78beacff5f70404394a4d5a7; cp.lb=n4.7bc2305aca3992f3627c39eeb91a9adbdcbf15a1; x-sess-uuid=0.5dcd5a68.1767392336.32090f8e; ibcust=b3fc937a75d5a6fa6b2d81b6256c79b0; IS_MASTER=false; pastandalone=""; ROUTEIDD=.ny5japp1'

print(f"Requesting data for Theme Key: {params['key']}...")

try:
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    data = response.json()
    
    # Check if we have the expected structure
    print("Response received!")
    theme_name = data.get('name', 'Unknown Theme')
    print(f"Theme Name: {theme_name}")
    print(f"Description: {data.get('description', '')[:100]}...")
    
    linked_companies = data.get('linked_companies', [])
    print(f"Found {len(linked_companies)} companies.")
    
    if linked_companies:
        # Extract relevant fields
        processed_companies = []
        for company in linked_companies:
            # The structure from the screenshot showed `key` which looks like ISIN/Tickers
            # We'll dump all fields to be safe, then select key ones
            processed_companies.append(company)
            
        df = pd.DataFrame(processed_companies)
        
        # timestamp for filename
        ts = int(time.time())
        filename = f"{output_dir}/reflexivity_theme_{theme_name.replace(' ', '_')}_{ts}.csv"
        
        df.to_csv(filename, index=False)
        print(f"Data saved to: {filename}")
        print("\nFirst 5 companies:")
        print(df[['name', 'ticker']].head() if 'ticker' in df.columns else df.head())
        
    else:
        print("No companies found in this theme.")
        print("Full response keys:", data.keys())

except requests.exceptions.RequestException as e:
    print(f"Error making request: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response Status: {e.response.status_code}")
        print(f"Response Body: {e.response.text}")
except json.JSONDecodeError:
    print("Error decoding JSON. Response content:")
    print(response.text)
