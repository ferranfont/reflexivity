import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import sys
import webbrowser
import subprocess
import time
import plotly.graph_objects as go
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta

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
        
    # Pre-check: Look up in industry_summary_offline.csv
    summary_path = BASE_DIR / "data" / "industry_summary_offline.csv"
    if summary_path.exists():
        try:
            # Optimize: read only needed columns if large, but file is small
            df_sum = pd.read_csv(summary_path)
            # strict case-insensitive match
            match = df_sum[df_sum['Theme'].astype(str).str.lower() == theme_name.lower()]
            if not match.empty:
                fname = match.iloc[0]['Filename']
                if isinstance(fname, str) and fname.strip():
                    file_path = DATA_DIR / fname.strip()
                    if file_path.exists():
                        return file_path
        except Exception:
            pass # Fallback to fuzzy search

    target = theme_name.lower().replace(' ', '_')
    target_and = target.replace('&', 'and')

    # First pass: exact matches
    for f in DATA_DIR.iterdir():
        if f.suffix.lower() == '.csv':
            name = f.stem.lower()
            if name == target or name.replace('-', '_') == target or name == target_and or name.replace('-', '_') == target_and:
                return f

    # Second pass: fuzzy matching using similarity score
    # Handle cases like "biologic" vs "biological"
    best_match = None
    best_score = 0

    for f in DATA_DIR.iterdir():
        if f.suffix.lower() == '.csv':
            name = f.stem.lower().replace('-', '_')

            # Simple similarity: ratio of matching characters in order
            # Count how many characters from target appear in name in the same order
            target_parts = target.split('_')
            name_parts = name.split('_')

            # Check if all parts of target are in name (allowing for longer versions)
            matches = 0
            for tp in target_parts:
                for np in name_parts:
                    if tp in np or np in tp:  # "biologic" in "biological"
                        if len(tp) >= 3:  # Avoid short word false matches
                            matches += 1
                        break

            score = matches / len(target_parts) if target_parts else 0

            if score > best_score and score >= 0.8:  # 80% match threshold
                best_score = score
                best_match = f

    if best_match:
        return best_match

    # Third pass: search CSVs for a theme column match
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

def get_spy_data(start_date, end_date):
    """Loads SPY data for benchmark."""
    spy_path = BASE_DIR / "data" / "spy_benchmark.csv"
    df = None
    if spy_path.exists():
        try:
            df = pd.read_csv(spy_path)
            df['date'] = pd.to_datetime(df['date'])
        except: pass
            
    # Check if download needed
    need_download = False
    if df is None:
        need_download = True
    else:
        if df['date'].max() < pd.to_datetime(end_date) - pd.Timedelta(days=5):
            need_download = True
            
    if need_download:
        try:
            ticker = yf.Ticker("SPY")
            hist = ticker.history(start="2000-01-01")
            hist.reset_index(inplace=True)
            hist['date'] = hist['Date'].dt.tz_localize(None)
            df = hist[['date', 'Close']].rename(columns={'Close': 'spy_val'})
            df.to_csv(spy_path, index=False)
        except: pass

    if df is not None:
        mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
        return df.loc[mask].copy().sort_values('date')
    return None

def generate_breakdown_assets(theme_name, all_symbols):
    """
    Generates the Breakdown Chart and returns the data for the Performance Table.
    Returns: (chart_filename, table_rows_list)
    """
    print(f"Generating Breakdown Assets for {len(all_symbols)} symbols...")
    
    # 1. Fetch Data
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)
    
    price_data = {}
    with engine.connect() as conn:
        for sym in all_symbols:
            try:
                q = text("SELECT date, close FROM stock_prices WHERE symbol = :s ORDER BY date ASC")
                df = pd.read_sql(q, conn, params={"s": sym})
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    price_data[sym] = df['close']
            except: pass
            
    if not price_data:
        return None, []

    full_df = pd.concat(price_data, axis=1)
    full_df = full_df.ffill().dropna(how='all')
    
    # Filter 3 Years
    start_filter = pd.Timestamp.now() - pd.DateOffset(years=3)
    if full_df.index.min() > start_filter:
        start_filter = full_df.index.min()
    full_df = full_df[full_df.index >= start_filter]
    
    if full_df.empty: return None, []

    # 2. Calculate ROI & Rank
    roi_map = []
    for sym in full_df.columns:
        series = full_df[sym]
        valid_idx = series.first_valid_index()
        last_idx = series.last_valid_index()
        if valid_idx is not None and last_idx is not None:
            start_val = series.loc[valid_idx]
            end_val = series.loc[last_idx]
            if start_val > 0:
                roi = ((end_val - start_val) / start_val) * 100
                roi_map.append({
                    'symbol': sym, 
                    'roi': roi, 
                    'start_price': start_val, 
                    'end_price': end_val
                })
            else:
                roi_map.append({'symbol': sym, 'roi': -999, 'start_price': 0, 'end_price': 0})
        else:
             roi_map.append({'symbol': sym, 'roi': -999, 'start_price': 0, 'end_price': 0})
             
    roi_map.sort(key=lambda x: x['roi'], reverse=True)
    
    top_10 = [x['symbol'] for x in roi_map[:10]]
    others = [x['symbol'] for x in roi_map[10:]]
    
    # 3. Normalize for Chart (Start at 0%)
    normalized_df = pd.DataFrame(index=full_df.index)
    
    def get_norm_series(series):
        valid = series.first_valid_index()
        if valid is None: return series * np.nan
        base = series.iloc[0] # Base on CHART start
        if pd.isna(base) or base == 0: return series * np.nan
        return ((series / base) - 1) * 100

    # Top 10
    for sym in top_10:
        if sym in full_df.columns:
            normalized_df[sym] = get_norm_series(full_df[sym])
            
    # Others
    others_cols = [c for c in others if c in full_df.columns]
    if others_cols:
        others_data = []
        for osym in others_cols:
             others_data.append(get_norm_series(full_df[osym]))
        if others_data:
            others_df = pd.concat(others_data, axis=1)
            normalized_df['Others'] = others_df.mean(axis=1)

    # SPY
    spy_df = get_spy_data(full_df.index.min(), full_df.index.max())
    if spy_df is not None:
        spy_df.set_index('date', inplace=True)
        aligned_spy = spy_df['spy_val'].reindex(full_df.index, method='ffill')
        normalized_df['SPY'] = get_norm_series(aligned_spy)
        # Spy ROI for table
        spy_start = aligned_spy.iloc[0]
        spy_end = aligned_spy.iloc[-1]
        spy_roi = ((spy_end - spy_start)/spy_start)*100
    else:
        spy_roi = 0

    # 4. Plot
    fig = go.Figure()
    COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    # SPY
    if 'SPY' in normalized_df.columns:
        fig.add_trace(go.Scatter(x=normalized_df.index, y=normalized_df['SPY'], mode='lines', name='S&P 500 (SPY)', line=dict(color='black', width=3), hovertemplate='SPY: %{y:+.1f}%'))
        
    # Top 10
    for i, sym in enumerate(top_10):
        if sym in normalized_df.columns:
            fig.add_trace(go.Scatter(x=normalized_df.index, y=normalized_df[sym], mode='lines', name=sym, line=dict(color=COLORS[i%len(COLORS)], width=1), hovertemplate=f'{sym}: %{{y:+.1f}}%'))
            
    # Others
    if 'Others' in normalized_df.columns:
        fig.add_trace(go.Scatter(x=normalized_df.index, y=normalized_df['Others'], mode='lines', name='Others (Avg)', line=dict(color='lightgrey', width=1, dash='dot'), hovertemplate='Others: %{y:+.1f}%'))
        
    fig.update_layout(
        title=dict(
            text=f"Theme Breakdown: {theme_name} (Top 10 Performers vs Others)",
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#333', family="Segoe UI"),
            pad=dict(b=40)  # Extra padding below title for legend separation
        ),
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        height=500,  # Reduced height to prevent scrollbar
        margin=dict(t=80, l=30, r=30, b=30), # Adjusted margins
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(type="date", showgrid=False, showline=True, linecolor='#e0e0e0', linewidth=1, title=None),
        yaxis=dict(showgrid=True, gridcolor='#f5f5f5', showline=False, zeroline=True, zerolinecolor='#d3d3d3', title=None, tickformat="+.0f", ticksuffix="%")
    )
    
    # Save Chart
    chart_filename = f"breakdown_{theme_name.lower().replace(' ', '_')}.html"
    chart_path = HTML_DIR / chart_filename
    
    # Write styled HTML with dynamic height adjustment
    fig.write_html(chart_path, include_plotlyjs='cdn', full_html=True)
    with open(chart_path, 'r', encoding='utf-8') as f: html_c = f.read()
    
    custom_assets = """
    <style>
        body { background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 10px; overflow: hidden; } 
        .plotly-graph-div { 
            margin: 0 auto !important; 
            width: 98% !important; 
            max-width: 1400px !important; 
            box-shadow: none !important; 
            border-radius: 8px; 
        }
    </style>
    <script>
        document.addEventListener("DOMContentLoaded", function() {
            // Check if inside iframe
            var inIframe = true;
            try { inIframe = window.self !== window.top; } catch (e) { inIframe = true; }
            
            var plotDiv = document.getElementsByClassName('plotly-graph-div')[0];
            
            if (!inIframe) {
                // Standalone Mode (Full Chart View) - Increase Height
                document.body.style.overflow = 'auto'; // Enable scroll in full view
                document.body.style.padding = '20px';
                if (plotDiv) {
                    plotDiv.style.height = '850px';
                    plotDiv.style.width = '95%';
                    plotDiv.style.boxShadow = '0 4px 20px rgba(0,0,0,0.08)';
                    Plotly.relayout(plotDiv, {height: 850});
                }
            }
        });
    </script>
    """
    with open(chart_path, 'w', encoding='utf-8') as f: f.write(html_c.replace("</head>", f"{custom_assets}</head>"))
    
    # 5. Prepare Table Data
    table_data = []
    for i, item in enumerate(roi_map[:10]):
        table_data.append({
            'symbol': item['symbol'],
            'rank': 'Top 10',
            'start': item['start_price'],
            'end': item['end_price'],
            'roi': item['roi']
        })
        
    # Append Others Agg
    others_start_roi = 0
    others_end_roi = normalized_df['Others'].iloc[-1] if 'Others' in normalized_df.columns else 0
    table_data.append({'symbol': 'OTHERS', 'rank': 'Agg', 'start': 0, 'end': 0, 'roi': others_end_roi, 'is_agg': True})
    
    # Append SPY
    table_data.append({'symbol': 'SPY', 'rank': 'Bench', 'start': 0, 'end': 0, 'roi': spy_roi, 'is_agg': True})
    
    return chart_filename, table_data

def generate_theme_html(theme_name):
    df_theme = load_theme(theme_name)
    if df_theme is None:
        return None

    industry_name = get_industry_for_theme(theme_name)
    
    symbols = [s.upper() for s in df_theme['symbol'].astype(str).tolist()]

    # --- AUTO-GENERATE MISSING PROFILES ---
    print(f"Verifying {len(symbols)} company profiles...")
    for sym in symbols:
        p_path = HTML_DIR / f"{sym}_profile.html"
        should_gen = False
        if not p_path.exists():
            should_gen = True
        else:
            # Check if older than 24 hours
            if (time.time() - os.path.getmtime(p_path)) > 86400:
                should_gen = True
        
        if should_gen:
            print(f"Generating profile for {sym}...")
            try:
                subprocess.run([sys.executable, str(BASE_DIR / "show_company_profile.py"), sym, "--no-browser"], check=False)
            except Exception as e:
                print(f"Error generating profile for {sym}: {e}")
    # --------------------------------------
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
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .header-content { flex: 1; }
    .main-title { font-size: 2rem; font-weight: 700; margin: 0; }
    .sub-title { font-size: 1rem; color: #bdc3c7; margin-top: 5px; font-weight: 400; }

    .home-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border-radius: 50%;
        text-decoration: none;
        transition: all 0.3s ease;
        border: 2px solid rgba(255, 255, 255, 0.3);
    }

    .home-button:hover {
        background-color: rgba(255, 255, 255, 0.25);
        border-color: rgba(255, 255, 255, 0.5);
        transform: scale(1.1);
    }

    .home-button svg {
        width: 24px;
        height: 24px;
    }
    
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
        <div class="box-body" style="height: 600px; overflow:hidden;">
            <iframe src="{chart_filename}" style="width:100%; height:100%; border:none; display:block;"></iframe>
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
    <div class="header-content">
      <div class="main-title">{theme_name}</div>
      <div class="sub-title">Investment Theme Detail - {industry_name} Industry</div>
    </div>
    <a href="main_trends.html" class="home-button" title="Return to Main Dashboard">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
        <polyline points="9 22 9 12 15 12 15 22"></polyline>
      </svg>
    </a>
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

    <!-- --- THEME BREAKDOWN SECTION --- -->
    """
    
    # Generate Breakdown Assets
    breakdown_chart_file, perf_table_data = generate_breakdown_assets(theme_name, symbols)
    
    if breakdown_chart_file:
        html += f"""
        <!-- Breakdown Chart -->
        <div class="content-box">
            <div class="section-header-clean">
                <span class="header-text">Theme Breakdown (Winners vs Losers)</span>
                 <a href="{breakdown_chart_file}" target="_blank" class="btn-view-chart">View Full Chart ↗</a>
            </div>
            <div class="box-body" style="height: 520px; overflow:hidden;">
                <iframe src="{breakdown_chart_file}" scrolling="no" style="width:100%; height:100%; border:none; display:block; overflow:hidden;"></iframe>
            </div>
        </div>
        
        <!-- Performance Table -->
        <div class="content-box">
             <div class="section-header-clean">
                <span class="header-text">Performance Table (Top 10 Performers)</span>
            </div>
            <p style="color:#666; margin-top:0;">Detailed performance contribution of top assets over the last 3 years.</p>
            
            <table style="width:100%; border-collapse: collapse; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9rem;">
                <thead style="border-bottom: 2px solid #333; border-top: 2px solid #333;">
                    <tr>
                        <th style="text-align:left; padding:10px;">SYMBOL</th>
                        <th style="text-align:left; padding:10px;">RANK</th>
                        <th style="text-align:left; padding:10px;">START PRICE</th>
                        <th style="text-align:left; padding:10px;">END PRICE</th>
                        <th style="text-align:left; padding:10px;">CHANGE %</th>
                        <th style="text-align:center; padding:10px;">ACTION</th>
                    </tr>
                </thead>
                <tbody>
        """
        for row in perf_table_data:
            style = "border-bottom: 1px solid #eee;"
            if row.get('is_agg'): style = "border-bottom: 1px solid #333; font-weight:bold; background-color:#f9f9f9;"
            
            start_fmt = f"${row['start']:,.2f}" if row['start'] > 0 else "(Start 0%)"
            end_fmt = f"${row['end']:,.2f}" if row['end'] > 0 else "N/A"
            roi_fmt = f"{row['roi']:+.2f}%"
            roi_color = "green" if row['roi'] >= 0 else "red"
            
            # Action Button Logic
            action_html = ""
            if not row.get('is_agg'):
                 action_html = f"""
                 <a href="{row['symbol']}_profile.html" target="_blank" title="View Profile" style="text-decoration:none; display:inline-block; color:#586069;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="border: 1px solid #d1d5da; border-radius: 4px; padding: 4px; transition: all 0.2s;">
                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <line x1="10" y1="14" x2="21" y2="3"></line>
                    </svg>
                </a>
                 """
            
            html += f"""
                    <tr style="{style}">
                        <td style="padding:8px 10px;">{row['symbol']}</td>
                        <td style="padding:8px 10px;">{row['rank']}</td>
                        <td style="padding:8px 10px;">{start_fmt}</td>
                        <td style="padding:8px 10px;">{end_fmt}</td>
                        <td style="padding:8px 10px; color:{roi_color};">{roi_fmt}</td>
                        <td style="padding:8px 10px; text-align:center;">{action_html}</td>
                    </tr>
            """
        html += """
                </tbody>
            </table>
        </div>
        """
    
    html += """



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
                <a href="{c['symbol']}_profile.html" target="_blank" title="View Profile" style="text-decoration:none; display:inline-block; color:#586069;">
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
            <td><a href="{symbol}_profile.html" class="symbol-text action-link" style="font-size:1rem; text-decoration:none;">{symbol}</a></td>
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

    print(f"Theme page written to: {html_path}")
    return html_path


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--all':
        print("Model Batch: Regenerating ALL themes...")
        summary_path = BASE_DIR / "data" / "industry_summary_offline.csv"
        if not summary_path.exists():
            print(f"[ERROR] Summary file not found at {summary_path}")
            return
            
        try:
            df = pd.read_csv(summary_path)
            themes = sorted(df['Theme'].dropna().unique())
            total = len(themes)
            print(f"Found {total} themes. Starting batch processing...")
            
            for i, theme in enumerate(themes):
                print(f"[{i+1}/{total}] Processing: {theme}")
                try:
                    generate_theme_html(theme)
                except Exception as e:
                    print(f"[ERROR] Failed to process {theme}: {e}")
                    
            print(f"\n[DONE] Successfully processed all {total} themes.")
            
        except Exception as e:
            print(f"[CRITICAL] Batch processing failed: {e}")
            
    else:
        # Single Theme Mode
        theme = 'Accelerated Computing'
        if len(sys.argv) > 1:
            theme = sys.argv[1]
            
        path = generate_theme_html(theme)
        
        if path and "--no-browser" not in sys.argv:
            # Use localhost link if server assumed running, else file
            # We'll just open file for now, but the internal links point to /profile/
            webbrowser.open(f'file://{os.path.abspath(path)}')

if __name__ == '__main__':
    main()
