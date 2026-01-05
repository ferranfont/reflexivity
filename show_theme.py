import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import sys
import webbrowser
import subprocess
import time

load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "reflexivity_db")

BASE_DIR = Path(__file__).parent
HTML_DIR = BASE_DIR / "html"
HTML_DIR.mkdir(exist_ok=True)
DATA_DIR = BASE_DIR / "data" / "all_themes"

def find_theme_csv(theme_name):
    if not DATA_DIR.exists():
        return None
    target = theme_name.lower().replace(' ', '_')
    target_and = target.replace('&', 'and')
    for f in DATA_DIR.iterdir():
        if f.suffix.lower() == '.csv':
            name = f.stem.lower()
            if name == target or name.replace('-', '_') == target or name == target_and or name.replace('-', '_') == target_and:
                return f
    # fallback: search CSVs for a theme column match
    for f in DATA_DIR.glob('*.csv'):
        try:
            df = pd.read_csv(f, nrows=5)
            if 'theme' in df.columns:
                if df['theme'].astype(str).str.lower().str.contains(theme_name.lower()).any():
                    return f
            # some CSVs have a filename that is the theme; accept fuzzy
            if theme_name.lower().replace(' ', '_') in f.stem.lower():
                return f
        except Exception:
            continue
    return None

def load_theme(theme_name):
    csv = find_theme_csv(theme_name)
    if not csv:
        print(f"Theme CSV for '{theme_name}' not found in {DATA_DIR}")
        return None
    df = pd.read_csv(csv, on_bad_lines='skip')
    # ensure columns
    df.columns = [c.strip() for c in df.columns]
    # expected: symbol, name, rank, description maybe
    df['symbol'] = df.get('symbol') if 'symbol' in df.columns else df.iloc[:,0]
    df['name'] = df.get('name') if 'name' in df.columns else df.get('company_name', df['symbol'])
    if 'rank' not in df.columns:
        df['rank'] = range(1, len(df)+1)
    df = df[['symbol', 'name', 'rank'] + [c for c in df.columns if c not in ('symbol','name','rank')]]
    
    # Sanitize Rank: Coerce to numeric, fill NaNs with safe defaults
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce').fillna(0).astype(int)
    # If all ranks are 0 (bad parse), regenerate
    if (df['rank'] == 0).all():
        df['rank'] = range(1, len(df) + 1)
        
    return df

def get_company_info(symbol):
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    q = text("SELECT symbol, name, description FROM companies WHERE symbol = :s LIMIT 1")
    with engine.connect() as conn:
        row = conn.execute(q, {"s": symbol}).fetchone()
        if row is None:
            return None
        keys = ['symbol', 'name', 'description']
        return dict(zip(keys, row))

def get_evidence_for_symbols(symbols):
    if not symbols:
        return []
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    # build parameterized IN clause safely
    placeholders = ','.join([':s'+str(i) for i in range(len(symbols))])
    params = { 's'+str(i): symbols[i] for i in range(len(symbols)) }
    q = text(f"SELECT symbol, head_title, evidence, evidenceSources, source_date FROM evidence WHERE symbol IN ({placeholders}) ORDER BY source_date DESC")
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params=params)
    if df.empty:
        return []
    df['source_date'] = pd.to_datetime(df['source_date'])
    return df.to_dict('records')

def get_industry_for_theme(theme_name):
    """Find the industry for a given theme from the summary file."""
    summary_path = BASE_DIR / "data" / "industry_summary_offline.csv"
    if summary_path.exists():
        try:
            df = pd.read_csv(summary_path)
            # Fuzzy match or exact match
            match = df[df['Theme'].str.lower() == theme_name.lower()]
            if not match.empty:
                return match.iloc[0]['Industry']
        except:
            pass
    return "Investment Theme"

def generate_theme_html(theme_name):
    df_theme = load_theme(theme_name)
    if df_theme is None:
        return None

    industry_name = get_industry_for_theme(theme_name)
    
    symbols = [s.upper() for s in df_theme['symbol'].astype(str).tolist()]
    companies = []
    for _, r in df_theme.sort_values('rank').iterrows():
        sym = str(r['symbol']).upper()
        info = get_company_info(sym)
        companies.append({
            'symbol': sym,
            'name': info['name'] if info and info.get('name') else r.get('name', sym),
            'description': info.get('description','')[:150] + '...' if info and info.get('description') else 'No description available.',
            'rank': int(r['rank']) if not pd.isnull(r['rank']) else ''
        })

    # --- FETCH EVIDENCE ---
    evidences = get_evidence_for_symbols(symbols)

    html_path = HTML_DIR / f"{theme_name.lower().replace(' ','_')}_detail.html"

    NEW_CSS = """
    :root {
        --header-bg: #2c3e50;
        --header-text: #ffffff;
        --body-bg: #f5f7fa; 
        --accent-color: #3498db;
        --text-color: #333;
        --info-bar-bg: #e3f2fd;
        --info-bar-text: #1565c0;
    }
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin:0; background: var(--body-bg); color: var(--text-color); }
    
    .main-header {
        background-color: var(--header-bg);
        color: var(--header-text);
        padding: 25px 40px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .main-title { font-size: 2rem; font-weight: 700; margin: 0; }
    .sub-title { font-size: 1rem; color: #bdc3c7; margin-top: 5px; font-weight: 400; }
    
    .container { max-width: 1200px; margin: 0 auto; padding: 30px 40px; }
    
    .nav-bar { margin-bottom: 25px; }
    .btn-browse {
        background-color: #2c3e50;
        color: white;
        padding: 10px 20px;
        text-decoration: none;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: background 0.2s;
    }
    .btn-browse:hover { background-color: #34495e; }
    
    .info-bar {
        background-color: var(--info-bar-bg);
        color: var(--info-bar-text);
        padding: 15px 20px;
        border-radius: 6px;
        border-left: 5px solid #2196f3;
        margin-bottom: 30px;
        font-size: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .info-bar strong { font-weight: 700; color: #0d47a1; }

    .count-badge { background-color: #3498db; color: white; border-radius: 12px; padding: 4px 10px; font-size: 0.85rem; font-weight: 600; }
    
    .content-box {
        background-color: white;
        padding: 25px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin-bottom: 35px;
        border: 1px solid #e1e4e8;
    }
    
    .section-header-clean {
        display: flex;
        align-items: center;
        gap: 12px;
        padding-bottom: 15px;
        border-bottom: 2px solid #3498db;
        margin-bottom: 25px;
    }
    
    .header-text {
        font-size: 1.4rem;
        font-weight: 700;
        color: #2c3e50;
    }
    
    .symbol-text { font-weight: 700; color: #2c3e50; }
    .company-name { font-weight: 600; color: #2c3e50; }
    .company-desc { font-size: 0.9rem; color: #666; line-height: 1.5; }
    
    .action-link {
        color: var(--accent-color);
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9rem;
        display: block;
        margin-bottom: 4px;
    }
    .action-link:hover { text-decoration: underline; }

    .search-input {
        width: 100%;
        padding: 12px 15px;
        border: 1px solid #ddd;
        border-radius: 6px;
        font-size: 1rem;
        outline: none;
        transition: border-color 0.2s;
        box-sizing: border-box;
    }
    .search-input:focus { border-color: #3498db; }
    
    .evidence-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
    .evidence-table th { text-align: left; padding: 12px; border-bottom: 2px solid #eee; color: #7f8c8d; font-weight: 600; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; }
    .evidence-table td { padding: 16px 12px; border-bottom: 1px solid #eee; vertical-align: top; }
    .evidence-table tr:hover { background-color: #fcfcfc; }
    .evidence-table tr:last-child td { border-bottom: none; }

    .btn-view-chart {
        background-color: #3498db;
        color: white;
        padding: 6px 15px;
        border-radius: 4px;
        text-decoration: none;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        transition: background-color 0.2s;
        margin-left: auto;
    }
    .btn-view-chart:hover {
        background-color: #2980b9;
    }
    """

    # --- CHART GENERATION LOGIC ---
    chart_filename = f"equity_{theme_name.lower().replace(' ', '_').replace('-', '_')}.html"
    chart_path = HTML_DIR / chart_filename
    
    generate_chart = True
    if chart_path.exists():
        # Check if modified within last 24 hours
        if (time.time() - os.path.getmtime(chart_path)) < 86400:
            generate_chart = False
            
    if generate_chart:
        print(f"Generating chart for {theme_name}...")
        try:
            subprocess.run([sys.executable, str(BASE_DIR / "plot_theme_chart.py"), theme_name], check=True)
        except Exception as e:
            print(f"Error generating chart: {e}")

    # Fallback if chart still missing (script failed or other issue)
    chart_html_block = ""
    if chart_path.exists():
        chart_html_block = f"""
    <!-- Theme Chart Section -->
    <div class="content-box">
        <div class="section-header-clean">
            <span class="header-text">Theme Chart</span>
             <a href="{chart_filename}" target="_blank" class="btn-view-chart">View Full Chart ↗</a>
        </div>
        <div class="box-body" style="height: 500px; overflow:hidden;">
            <iframe src="{chart_filename}" style="width:100%; height:100%; border:none; overflow:hidden;"></iframe>
        </div>
    </div>
        """

    html = f"""
<!doctype html>
<html>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>{theme_name} - Need to Know</title>
<style>{NEW_CSS}</style>
</head>
<body>

  <!-- Header -->
  <div class="main-header">
    <div class="main-title">{theme_name}</div>
    <div class="sub-title">Investment Theme Detail - {industry_name} Industry</div>
  </div>

  <div class="container">
  
    <!-- Navigation -->
    <div class="nav-bar">
        <a href="http://localhost:8000/industry_explorer.html" class="btn-browse">← Browse All Trends</a>
    </div>
    
    <!-- Info Bar -->
    <div class="info-bar">
        <strong>Theme:</strong> {theme_name} &nbsp;|&nbsp; 
        <strong>Industry:</strong> {industry_name} &nbsp;|&nbsp; 
        <strong>Total Companies:</strong> {len(companies)}
    </div>

    {chart_html_block}



    <!-- Companies Section -->
    <div class="content-box">
        <div class="section-header-clean">
            <span class="header-text">Companies</span>
            <span class="count-badge">{len(companies)}</span>
        </div>
        
        <table style="width:100%; border-collapse: collapse;">
            <thead>
                <tr>
                    <th style="padding:10px; text-align:left; color:#7f8c8d; font-weight:600; font-size:0.85rem; text-transform:uppercase; border-bottom:2px solid #eee;">Rank</th>
                    <th style="padding:10px; text-align:left; color:#7f8c8d; font-weight:600; font-size:0.85rem; text-transform:uppercase; border-bottom:2px solid #eee;">Symbol</th>
                    <th style="padding:10px; text-align:left; color:#7f8c8d; font-weight:600; font-size:0.85rem; text-transform:uppercase; border-bottom:2px solid #eee;">Company Name</th>
                    <th style="padding:10px; text-align:left; color:#7f8c8d; font-weight:600; font-size:0.85rem; text-transform:uppercase; border-bottom:2px solid #eee;">Description</th>
                    <th style="padding:10px; text-align:left; color:#7f8c8d; font-weight:600; font-size:0.85rem; text-transform:uppercase; border-bottom:2px solid #eee;">Action</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for c in companies:
        html += f"""
        <tr>
            <td style="padding:15px 10px; border-bottom:1px solid #eee;">{c['rank']}</td>
            <td style="padding:15px 10px; border-bottom:1px solid #eee;"><span class="symbol-text">{c['symbol']}</span></td>
            <td style="padding:15px 10px; border-bottom:1px solid #eee;"><div class="company-name">{c['name']}</div></td>
            <td style="padding:15px 10px; border-bottom:1px solid #eee;"><div class="company-desc">{c['description']}</div></td>
            <td style="padding:15px 10px; border-bottom:1px solid #eee;">
                <a href="http://localhost:8000/profile/{c['symbol']}" target="_blank" title="View Profile" style="text-decoration:none; display:inline-block; color:#586069;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="border: 1px solid #d1d5da; border-radius: 4px; padding: 4px; transition: all 0.2s;">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                </a>
            </td>
        </tr>

        """
        
    html += f"""
            </tbody>
        </table>
    </div>
    
    <!-- All Evidence Section -->
    <div class="content-box">
        <div class="section-header-clean">
            <span class="header-text">All Evidence</span>
            <span class="count-badge">{len(evidences)}</span>
        </div>
        
        <p style="color: #666; margin-bottom: 20px; margin-top:0;">
            All evidence entries sorted by date. Filter by company below.
        </p>
        
        <input type="text" id="evidenceFilter" class="search-input" placeholder="Find Evidence by Company (symbol or name)..." onkeyup="filterEvidence()">
        
        <table class="evidence-table">
            <thead>
                <tr>
                    <th style="width:120px;">Date</th>
                    <th style="width:100px;">Symbol</th>
                    <th style="width:200px;">Company</th>
                    <th>Evidence</th>
                </tr>
            </thead>
            <tbody id="evidenceList">
    """

    for ev in evidences:
        sd = ev.get('source_date')
        date_str = ''
        if sd is not None and sd != '' and pd.notna(sd):
            try:
                dt = pd.to_datetime(sd, errors='coerce')
                if pd.notna(dt):
                    date_str = dt.strftime('%Y-%m-%d')
            except:
                date_str = ''
        
        head = ev.get('head_title', '')
        symbol = ev.get('symbol','')
        company_name = ''
        # optimized lookup
        found_comp = next((x for x in companies if x['symbol'] == symbol), None)
        if found_comp:
            company_name = found_comp['name']
        if not company_name:
             ci = get_company_info(symbol)
             if ci: company_name = ci.get('name','')
             
        evidence_text = (ev.get('evidence') or '')
        evidence_snip = evidence_text[:300].replace('\n',' ') + ('...' if len(evidence_text) > 300 else '')
        
        html += f"""
        <tr class="evidence-item" data-symbol="{symbol}" data-company="{company_name}">
            <td style="color: #666; font-size: 0.9rem;">{date_str}</td>
            <td><span class="symbol-text action-link" style="font-size:1rem;">{symbol}</span></td>
            <td><div style="color: #444; font-size: 0.9rem;">{company_name}</div></td>
            <td>
                <div style="font-weight: 700; color: #2c3e50; margin-bottom: 4px;">{head}</div>
                <div style="color: #555; font-size: 0.9rem; line-height: 1.5;">{evidence_snip}</div>
            </td>
        </tr>
        """
        
    html += """
            </tbody>
        </table>
    </div>
    
    <div style="margin-top: 40px; color: #999; font-size: 0.8rem; text-align: center;">
        Reflexivity Investment System &copy; 2026
    </div>

  </div>
  
  <script>
    function filterEvidence() {
      var q = document.getElementById('evidenceFilter').value.toLowerCase();
      var rows = document.querySelectorAll('#evidenceList tr.evidence-item');
      rows.forEach(function(row){
        var sym = (row.getAttribute('data-symbol')||'').toLowerCase();
        var comp = (row.getAttribute('data-company')||'').toLowerCase();
        if (sym.indexOf(q) !== -1 || comp.indexOf(q) !== -1 || q === ''){
          row.style.display = 'table-row';
        } else { 
          row.style.display = 'none'; 
        }
      });
    }
  </script>
</body>
</html>
    """

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Theme page written to: {html_path}")
    return html_path


def main():
    theme = 'Accelerated Computing'
    if len(sys.argv) > 1:
        theme = sys.argv[1]
    path = generate_theme_html(theme)
    if path:
        # Use localhost link if server assumed running, else file
        # We'll just open file for now, but the internal links point to /profile/
        webbrowser.open(f'file://{os.path.abspath(path)}')

if __name__ == '__main__':
    main()
