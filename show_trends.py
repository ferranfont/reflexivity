
# -*- coding: utf-8 -*-
"""show_trends.py

Updates the browser visualization to use the offline industry classification
and display company details for each theme.
"""

import os
import pandas as pd
import json
import webbrowser
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
DATA_THEMES_DIR = BASE_DIR / "data" / "all_themes"
SUMMARY_FILE = BASE_DIR / "data" / "industry_summary_offline.csv"
HTML_DIR = BASE_DIR / "html"
HTML_FILE = HTML_DIR / "industry_explorer.html"

# --- HTML Template ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reflexivity: Industry Explorer</title>
    <style>
        :root {
            --primary-color: #2c3e50;
            --secondary-color: #34495e;
            --accent-color: #3498db;
            --light-bg: #ecf0f1;
            --border-color: #bdc3c7;
            --text-color: #2c3e50;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            height: 100vh;
            color: var(--text-color);
            overflow: hidden;
        }

        /* Sidebar: Industries & Themes */
        #sidebar {
            width: 350px;
            background-color: var(--light-bg);
            border-right: 1px solid var(--border-color);
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        .sidebar-header {
            padding: 20px;
            background-color: var(--primary-color);
            color: white;
            font-size: 1.2rem;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .industry-group {
            border-bottom: 1px solid var(--border-color);
        }

        .industry-title {
            padding: 15px 20px;
            cursor: pointer;
            font-weight: 600;
            background-color: #fff;
            transition: background-color 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .industry-title:hover {
            background-color: #f9f9f9;
        }

        .industry-title.active {
            background-color: #e8f4fc;
            color: var(--accent-color);
            border-left: 4px solid var(--accent-color);
        }
        
        .company-count-badge {
            background-color: #eee;
            color: #666;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
        }

        .theme-list {
            display: none;
            background-color: #fcfcfc;
        }

        .theme-item {
            padding: 10px 20px 10px 40px;
            cursor: pointer;
            font-size: 0.95rem;
            border-bottom: 1px solid #f0f0f0;
            transition: all 0.2s;
        }

        .theme-item:hover {
            background-color: #fff;
            color: var(--accent-color);
            padding-left: 45px;
        }
        
        .theme-item.selected {
            background-color: var(--accent-color);
            color: white;
        }

        /* Main Content: Company Table */
        #main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        #header-bar {
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            background-color: white;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        #current-selection {
            font-size: 1.4rem;
            font-weight: bold;
            color: var(--primary-color);
        }

        #table-container {
            flex: 1;
            overflow: auto;
            padding: 20px;
            background-color: #fff;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
        }

        th, td {
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid #eee;
        }

        th {
            background-color: #f8f9fa;
            position: sticky;
            top: 0;
            font-weight: 600;
            color: var(--secondary-color);
            border-bottom: 2px solid var(--border-color);
        }

        tr:hover {
            background-color: #f1f1f1;
        }

        .stats-card {
            display: inline-block;
            margin-right: 20px;
            font-size: 0.9rem;
            color: #666;
        }
        
        #empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #999;
            text-align: center;
        }
        
        .search-box {
            padding: 10px;
            margin: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 90%;
        }

    </style>
</head>
<body>

    <div id="sidebar">
        <div class="sidebar-header">Reflexivity Explorer</div>
        <input type="text" id="filter-input" class="search-box" placeholder="Filter industries or themes..." onkeyup="filterSidebar()">
        <div id="industry-list">
            <!-- Content injected by JS -->
        </div>
    </div>

    <div id="main-content">
        <div id="header-bar">
            <div id="current-selection">Select a Theme</div>
            <div id="stats-container"></div>
        </div>
        <div id="table-container">
            <div id="empty-state">
                <h2>Welcome to the Investment Theme Explorer</h2>
                <p>Select an Industry and a Theme from the sidebar to view companies.</p>
            </div>
            <table id="company-table" style="display:none;">
                <thead>
                    <tr id="table-head-row">
                        <!-- Headers injected by JS -->
                    </tr>
                </thead>
                <tbody id="table-body">
                    <!-- Rows injected by JS -->
                </tbody>
            </table>
        </div>
    </div>

    <script>
        // --- DATA INJECTION POINT ---
        const ALL_DATA = {{JSON_DATA}};
        // ----------------------------

        const industryListEl = document.getElementById('industry-list');
        const companyTableEl = document.getElementById('company-table');
        const tableHeadRowEl = document.getElementById('table-head-row');
        const tableBodyEl = document.getElementById('table-body');
        const currentSelectionEl = document.getElementById('current-selection');
        const emptyStateEl = document.getElementById('empty-state');
        const statsContainerEl = document.getElementById('stats-container');

        // Initial Render
        renderSidebar(ALL_DATA);

        function renderSidebar(data) {
            industryListEl.innerHTML = '';
            
            // Sort industries alphabetically
            const industries = Object.keys(data).sort();
            
            industries.forEach(indName => {
                // Determine total companies in industry for badge (approx)
                let indCompanyCount = 0;
                Object.values(data[indName]).forEach(themeArray => indCompanyCount += themeArray.length);

                const groupDiv = document.createElement('div');
                groupDiv.className = 'industry-group';
                
                // Title Row
                const titleDiv = document.createElement('div');
                titleDiv.className = 'industry-title';
                titleDiv.innerHTML = `
                    <span>${indName}</span>
                    <span class="company-count-badge">${indCompanyCount}</span>
                `;
                titleDiv.onclick = () => toggleIndustry(groupDiv);
                
                // Theme List Container
                const themeListDiv = document.createElement('div');
                themeListDiv.className = 'theme-list';
                
                // Sort themes
                const themes = Object.keys(data[indName]).sort();
                
                themes.forEach(themeName => {
                    const themeItem = document.createElement('div');
                    themeItem.className = 'theme-item';
                    const compCount = data[indName][themeName].length;
                    themeItem.innerText = `${themeName} (${compCount})`;
                    themeItem.onclick = (e) => {
                        e.stopPropagation();
                        selectTheme(themeItem, indName, themeName, data[indName][themeName]);
                    };
                    themeListDiv.appendChild(themeItem);
                });

                groupDiv.appendChild(titleDiv);
                groupDiv.appendChild(themeListDiv);
                industryListEl.appendChild(groupDiv);
            });
        }

        function toggleIndustry(groupDiv) {
            const list = groupDiv.querySelector('.theme-list');
            const title = groupDiv.querySelector('.industry-title');
            
            // Close others (optional, maybe keep multi-open)
            // document.querySelectorAll('.theme-list').forEach(el => el.style.display = 'none');
            
            if (list.style.display === 'block') {
                list.style.display = 'none';
                title.classList.remove('active');
            } else {
                list.style.display = 'block';
                title.classList.add('active');
            }
        }

        function selectTheme(el, industry, theme, companies) {
            // Highlight styling
            document.querySelectorAll('.theme-item').forEach(i => i.classList.remove('selected'));
            el.classList.add('selected');

            // Update Header
            currentSelectionEl.innerText = `${industry} > ${theme}`;
            emptyStateEl.style.display = 'none';
            companyTableEl.style.display = 'table';
            
            // Build Table
            buildTable(companies);
        }

        function buildTable(companies) {
            tableHeadRowEl.innerHTML = '';
            tableBodyEl.innerHTML = '';

            if (!companies || companies.length === 0) {
                tableBodyEl.innerHTML = '<tr><td colspan="5">No data available</td></tr>';
                return;
            }

            // Define columns we want to show
            // available: type, key, name, rank, description, evidence, conid, currency, symbol, exchange, assetType, ...
            const columns = ['name', 'symbol', 'currency', 'rank', 'description'];
            const headers = ['Company Name', 'Symbol', 'Currency', 'Rank', 'Description'];

            headers.forEach(h => {
                const th = document.createElement('th');
                th.innerText = h;
                tableHeadRowEl.appendChild(th);
            });

            companies.forEach(company => {
                const tr = document.createElement('tr');
                columns.forEach(col => {
                    const td = document.createElement('td');
                    td.innerText = company[col] || '';
                    if (col === 'description' && company[col] && company[col].length > 100) {
                        td.title = company[col]; // tooltip
                        td.innerText = company[col].substring(0, 100) + '...';
                    }
                    tr.appendChild(td);
                });
                tableBodyEl.appendChild(tr);
            });
            
            statsContainerEl.innerText = `${companies.length} Companies`;
        }
        
        function filterSidebar() {
            const term = document.getElementById('filter-input').value.toLowerCase();
            const industryGroups = document.querySelectorAll('.industry-group');
            
            industryGroups.forEach(group => {
                const industryName = group.querySelector('.industry-title span').innerText.toLowerCase();
                const themeItems = group.querySelectorAll('.theme-item');
                let hasVisibleTheme = false;
                
                themeItems.forEach(item => {
                    const txt = item.innerText.toLowerCase();
                    if (txt.includes(term)) {
                        item.style.display = 'block';
                        hasVisibleTheme = true;
                    } else {
                        item.style.display = 'none';
                    }
                });
                
                if (industryName.includes(term) || hasVisibleTheme) {
                    group.style.display = 'block';
                    // Auto expand if searching
                    if (term.length > 0) {
                        group.querySelector('.theme-list').style.display = 'block';
                    } else {
                        group.querySelector('.theme-list').style.display = 'none';
                    }
                } else {
                    group.style.display = 'none';
                }
            });
        }
    </script>
</body>
</html>
"""

def generate_explorer():
    print("Generating Offline Industry Explorer...")
    
    # 1. Load Summary Structure
    if not SUMMARY_FILE.exists():
        print(f"Error: {SUMMARY_FILE} not found. Run classify_themes_offline.py first.")
        return

    summary_df = pd.read_csv(SUMMARY_FILE)
    
    # 2. Build the Big Data Object
    # Structure: { "IndustryName": { "ThemeName": [ {company_data}, ... ] } }
    
    final_data = {}
    
    total_files = len(summary_df)
    print(f"Processing {total_files} themes...")
    
    for idx, row in summary_df.iterrows():
        industry = row['Industry']
        theme = row['Theme']
        filename = row['Filename']
        
        if pd.isna(filename) or filename == "Not Found":
            continue
            
        csv_path = DATA_THEMES_DIR / filename
        
        companies_list = []
        if csv_path.exists():
            try:
                # Read company CSV
                # Ensure we handle bad lines just in case
                comp_df = pd.read_csv(csv_path, on_bad_lines='skip')
                # Clean column headers (strip whitespace)
                comp_df.columns = comp_df.columns.str.strip()
                # Convert to record list
                companies_list = comp_df.to_dict(orient='records')
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        
        if industry not in final_data:
            final_data[industry] = {}
        
        final_data[industry][theme] = companies_list

    # 3. Inject to HTML
    json_str = json.dumps(final_data, ensure_ascii=False) # allow unicode
    
    html_content = HTML_TEMPLATE.replace("{{JSON_DATA}}", json_str)
    
    if not HTML_DIR.exists():
        HTML_DIR.mkdir()
        
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Successfully generated: {HTML_FILE}")
    print(f"Total Industries: {len(final_data)}")
    
    # 4. Open in Browser
    folder_path = HTML_FILE.resolve().parent
    print(f"Opening {HTML_FILE.name}...")
    webbrowser.open(HTML_FILE.as_uri())

if __name__ == "__main__":
    generate_explorer()
