
import os
import pandas as pd
import webbrowser
import sys
import socket
import subprocess
import time
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
HTML_DIR = BASE_DIR / "html"
SUMMARY_FILE = DATA_DIR / "industry_summary_offline.csv"
OUTPUT_FILE = HTML_DIR / "main_trends.html"

# Ensure HTML dir exists
HTML_DIR.mkdir(exist_ok=True)

# CSS Styles
CSS = """
:root {
    --primary-color: #2c3e50;
    --accent-color: #3498db;
    --bg-color: #f4f6f9;
    --card-bg: #ffffff;
    --text-color: #333;
    --muted-text: #666;
    --search-header-bg-start: #667eea;
    --search-header-bg-end: #764ba2;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    background-color: var(--bg-color);
    color: var(--text-color);
}

/* Navbar */
.navbar {
    background-color: var(--primary-color);
    color: white;
    padding: 15px 0; /* Centered content needs zero H padding here, applied to inner wrapper */
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.navbar-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    align-items: center;
}
.navbar-brand {
    font-size: 2.5rem;
    font-weight: 700;
}
.navbar-subtitle {
    margin-left: 20px;
    font-size: 0.9rem;
    color: #bdc3c7;
    font-weight: 400;
}

/* Main Container */
.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 30px 20px;
}

/* Search Banner */
.search-banner {
    background: linear-gradient(135deg, var(--search-header-bg-start) 0%, var(--search-header-bg-end) 100%);
    padding: 40px;
    color: white;
    border-radius: 8px;
    margin-bottom: 40px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
}
.search-banner h2 { margin-top: 0; font-size: 1.5rem; }
.search-banner p { margin-bottom: 20px; opacity: 0.9; }

.search-container {
    display: flex;
    gap: 10px;
    max-width: 600px;
}
.search-input-lg {
    flex: 1;
    padding: 12px 15px;
    border-radius: 4px;
    border: none;
    font-size: 1rem;
    outline: none;
}
.btn-search {
    background-color: #2c3e50;
    color: white;
    border: none;
    padding: 12px 25px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 600;
    font-size: 1rem;
    transition: background 0.2s;
}
.btn-search:hover { background-color: #34495e; }

/* Sections */
.section-container {
    margin-bottom: 40px;
}
.section-header {
    display: flex;
    align-items: center;
    border-bottom: 2px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 20px;
}
.section-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--primary-color);
    margin: 0;
}
.badge {
    background-color: var(--accent-color);
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-left: 10px;
}

.browse-btn {
    display: inline-block;
    background-color: var(--primary-color);
    color: white;
    padding: 8px 18px;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: 20px;
}
.browse-btn:hover { background-color: #34495e; }

/* Grid Layouts */
.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); /* Slightly tighter columns */
    gap: 15px; /* Tighter gap */
}

.card {
    background-color: var(--card-bg);
    border: 1px solid #e1e4e8;
    border-left: 4px solid var(--accent-color); /* The requested colored side */
    border-radius: 4px; /* More rectangular */
    padding: 15px 20px;
    transition: transform 0.2s, box-shadow 0.2s;
    text-decoration: none;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    height: 50px; /* More compact height */
}
.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.08);
}
.card-title {
    font-weight: 600;
    font-size: 0.95rem;
}

/* Filter Input */
.filter-input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
    margin-bottom: 20px;
    box-sizing: border-box;
}
"""

JS = """
<script>
function filterThemes() {
    var input = document.getElementById('themeFilter');
    var filter = input.value.toLowerCase();
    var grid = document.getElementById('themesGrid');
    var cards = grid.getElementsByClassName('card');

    for (var i = 0; i < cards.length; i++) {
        var card = cards[i];
        var txt = card.textContent || card.innerText;
        if (txt.toLowerCase().indexOf(filter) > -1) {
            card.style.display = "";
        } else {
            card.style.display = "none";
        }
    }
}

function searchProfile() {
    var input = document.getElementById('profileInput');
    var symbol = input.value.trim().toUpperCase();
    if (symbol) {
        window.location.href = '/profile/' + symbol;
    }
}

// Allow Enter key in search box
document.getElementById('profileInput').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        searchProfile();
    }
});
</script>
"""

def generate_html(industries, themes):
    # Determine local server URL just in case, but we use relative or root-relative paths
    
    # Industries Cards
    # For now, linking to Industry Explorer. 
    # Ideally link to: industry_explorer.html
    
    ind_html = ""
    for ind in industries:
        # Link to explorer (simple)
        ind_html += f"""
        <a href="industry_explorer.html?industry={ind}" class="card">
            <div class="card-title">{ind}</div>
        </a>
        """

    # Themes Cards
    # Link to detail page. Filename convention from show_theme.py:
    # f"{theme_name.lower().replace(' ','_')}_detail.html"
    thm_html = ""
    for theme in themes:
        # Use the dynamic server route so pages are auto-generated if missing
        # The server expects /theme/Theme_Name and will replace _ with space to run the script
        # We replace '&' with 'and' to ensure robust filenames and URLs
        safe_theme = theme.replace(' & ', ' and ').replace('&', 'and')
        route_name = safe_theme.replace(' ', '_').replace('-', '_')
        
        thm_html += f"""
        <a href="/theme/{route_name}" class="card theme-card" title="{theme}">
            <div class="card-title">{theme}</div>
        </a>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reflexivity Trends - Main</title>
    <style>{CSS}</style>
</head>
<body>

    <!-- Navbar -->
    <div class="navbar">
        <div class="navbar-content">
            <div class="navbar-brand">Reflexivity Trends</div>
            <div class="navbar-subtitle">Explore investment themes, industries, and company profiles</div>
        </div>
    </div>

    <!-- Main Container -->
    <div class="main-container">

        <!-- Search Banner -->
        <div class="search-banner">
            <h2>Company Profile Search</h2>
            <p>Enter a company ticker symbol to view detailed investment profile and analysis</p>
            <div class="search-container">
                <input type="text" id="profileInput" class="search-input-lg" placeholder="Enter ticker symbol (e.g., AAPL, MSFT, TSLA...)">
                <button class="btn-search" onclick="searchProfile()">View Profile</button>
            </div>
        </div>

        <!-- Themes Section -->
        <div class="section-container">
            <div class="section-header">
                <h2 class="section-title">All Themes</h2>
                <span class="badge">{len(themes)}</span>
            </div>
            <p style="color:#666; margin-bottom:15px;">Explore all investment themes. Click on a theme to view detailed analysis.</p>
            
            <a href="industry_explorer.html" class="browse-btn">Browse Trends Explorer</a>
            <br>
            
            <input type="text" id="themeFilter" class="filter-input" placeholder="Filter themes..." onkeyup="filterThemes()">
            
            <div class="grid" id="themesGrid">
                {thm_html}
            </div>
        </div>

        <!-- Industries Section -->
        <div class="section-container">
            <div class="section-header">
                <h2 class="section-title">All Industries</h2>
                <span class="badge">{len(industries)}</span>
            </div>
            <p style="color:#666; margin-bottom:15px;">Browse companies by industry sector. Click on an industry to explore all investment themes.</p>
            


            <div class="grid">
                {ind_html}
            </div>
        </div>
    
    </div> <!-- /main-container -->

    {JS}
</body>
</html>
"""
    return html

def main():
    print("Generating Main Dashboard...")
    if not SUMMARY_FILE.exists():
        print(f"Error: {SUMMARY_FILE} not found. Cannot generate dashboard.")
        return

    df = pd.read_csv(SUMMARY_FILE)
    
    # Get Lists
    industries = sorted(df['Industry'].dropna().unique())
    themes = sorted(df['Theme'].dropna().unique())
    
    html_content = generate_html(industries, themes)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Dashboard generated: {OUTPUT_FILE}")

    # Server Start Logic (copied from show_trends.py)
    server_port = 8000
    server_url = f"http://localhost:{server_port}/main_trends.html"

    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    if not is_port_in_use(server_port):
        print(f"Starting background server on port {server_port}...")
        try:
            subprocess.Popen([sys.executable, str(BASE_DIR / "reflexivity_server.py")], 
                             cwd=BASE_DIR)
            print("Waiting for server to start...")
            time.sleep(2)
        except Exception as e:
            print(f"Error starting server: {e}")
            print(f"Opening local file: {OUTPUT_FILE}")
            webbrowser.open(OUTPUT_FILE.as_uri())
            return
    else:
        print(f"Server already running on port {server_port}")

    print(f"Opening {server_url}...")
    webbrowser.open(server_url)

if __name__ == "__main__":
    main()
