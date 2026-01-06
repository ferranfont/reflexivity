"""
Company Profile HTML Generator
Creates a standalone HTML page with company information from MySQL database.
Matches the aesthetic of show_trends.py with integrated price chart.
"""
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import sys
import os
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "reflexivity_db")
LOGO_DEV_API_KEY = os.getenv("LOGO_DEV_API_KEY")

# Output directory
OUTPUT_DIR = Path(__file__).parent / "html"
OUTPUT_DIR.mkdir(exist_ok=True)

# --- CSS matching show_trends.py ---
CSS_STYLES = """
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
    color: var(--text-color);
    background-color: #fff;
}

.header {
    padding: 20px 30px;
    background-color: var(--primary-color);
    color: white;
    font-size: 1.5rem;
    font-weight: bold;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-content {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 15px;
}

.header-logo {
    width: 60px;
    height: 60px;
    object-fit: contain;
    background-color: white;
    border-radius: 8px;
    padding: 5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

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
    flex-shrink: 0;
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

.company-subtitle {
    font-size: 0.9rem;
    font-weight: normal;
    opacity: 0.9;
    margin-top: 5px;
}

.company-subtitle a {
    color: white;
    text-decoration: none;
    border-bottom: 1px dashed rgba(255,255,255,0.5);
    transition: all 0.3s;
}

.company-subtitle a:hover {
    border-bottom: 1px solid white;
    opacity: 1;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.section {
    background-color: white;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    margin-bottom: 20px;
    overflow: hidden;
}

.section-header {
    padding: 15px 20px;
    background-color: #f8f9fa;
    border-bottom: 2px solid var(--border-color);
    font-weight: 600;
    font-size: 1.1rem;
    color: var(--secondary-color);
}

.section-content {
    padding: 20px;
}

/* Chart Section */
#chart-container {
    background-color: white;
    padding: 0;
}

/* Info Cards Grid */
.info-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.info-card {
    background-color: var(--light-bg);
    padding: 15px;
    border-radius: 4px;
    border-left: 4px solid var(--accent-color);
}

.info-label {
    font-size: 0.85rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 5px;
}

.info-value {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-color);
}

/* Description */
.description-text {
    line-height: 1.6;
    color: #555;
    font-size: 0.95rem;
}

/* Rankings Table */
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

.rank-badge {
    background-color: var(--accent-color);
    color: white;
    padding: 4px 10px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.85rem;
    display: inline-block;
}

.rank-top3 {
    background-color: #27ae60;
}

.rank-top10 {
    background-color: #3498db;
}

.rank-other {
    background-color: #95a5a6;
}

.check-icon {
    color: #27ae60;
    font-size: 1.2rem;
}

.no-icon {
    color: #ccc;
    font-size: 1.2rem;
}

/* Evidence Accordion */
.evidence-item {
    border: 1px solid #eee;
    border-radius: 4px;
    margin-bottom: 10px;
    overflow: hidden;
}

.evidence-header {
    padding: 12px 15px;
    background-color: #f9f9f9;
    cursor: pointer;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    transition: background-color 0.2s;
    gap: 10px;
}

.evidence-header span:first-child {
    flex: 1;
    word-wrap: break-word;
    overflow-wrap: break-word;
    line-height: 1.4;
}

.evidence-header:hover {
    background-color: #f0f0f0;
}

.evidence-content {
    padding: 15px;
    background-color: white;
    line-height: 1.6;
    color: #555;
    font-size: 0.9rem;
    display: none;
}

.evidence-content.active {
    display: block;
}

.toggle-icon {
    transition: transform 0.3s;
}

.toggle-icon.active {
    transform: rotate(180deg);
}

.no-data {
    text-align: center;
    padding: 40px;
    color: #999;
    font-style: italic;
}
"""


def get_company_info(symbol):
    """Get company basic information from companies table"""
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    query = text("SELECT * FROM companies WHERE symbol = :symbol")

    with engine.connect() as conn:
        result = conn.execute(query, {"symbol": symbol.upper()})
        row = result.fetchone()

        if row is None:
            return None

        # Convert to dict
        columns = result.keys()
        return dict(zip(columns, row))


def get_company_ranks(symbol):
    """Get company rankings across all themes"""
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    query = text("SELECT theme, `rank` FROM `rank` WHERE symbol = :symbol ORDER BY `rank` ASC")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"symbol": symbol.upper()})

    return df.to_dict('records')


def get_company_evidence(symbol):
    """Get all evidence entries for a company with sources, dates, and titles"""
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    query = text("SELECT evidence, evidenceSources, source_date, head_title FROM evidence WHERE symbol = :symbol")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"symbol": symbol.upper()})

    return df.to_dict('records') if not df.empty else []


def calculate_performance_metrics(symbol):
    """
    Calculate performance metrics for a stock symbol.
    """
    from datetime import datetime, timedelta
    import numpy as np

    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    # Get all stock prices ordered by date
    query = text("SELECT date, close FROM stock_prices WHERE symbol = :symbol ORDER BY date DESC")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"symbol": symbol.upper()})

    if df.empty:
        return None

    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date', ascending=False).reset_index(drop=True)

    # Get latest data point
    last_close = df.iloc[0]['close']
    last_date = df.iloc[0]['date']

    # Previous day close (if available)
    prev_close = df.iloc[1]['close'] if len(df) > 1 else last_close
    day_change_pct = ((last_close - prev_close) / prev_close * 100) if prev_close != 0 else 0

    # Helper function to get close price closest to target date
    def get_close_near_date(target_date):
        # Find closest date before or equal to target
        past_df = df[df['date'] <= target_date]
        if past_df.empty:
            return None
        return past_df.iloc[0]['close']

    # Calculate reference dates
    thirty_days_ago = last_date - timedelta(days=30)
    year_start = datetime(last_date.year, 1, 1)
    one_year_ago = last_date - timedelta(days=365)
    three_years_ago = last_date - timedelta(days=365*3)
    one_month_ago = last_date - timedelta(days=30)

    # Get prices at reference dates
    month_close = get_close_near_date(one_month_ago)
    ytd_close = get_close_near_date(year_start)
    year_close = get_close_near_date(one_year_ago)
    three_year_close = get_close_near_date(three_years_ago)

    # Calculate performance percentages
    month_performance = ((last_close - month_close) / month_close * 100) if month_close else None
    ytd_performance = ((last_close - ytd_close) / ytd_close * 100) if ytd_close else None
    year_performance = ((last_close - year_close) / year_close * 100) if year_close else None
    three_year_performance = ((last_close - three_year_close) / three_year_close * 100) if three_year_close else None

    # Calculate volatilities (annualized standard deviation)
    ninety_days_ago = last_date - timedelta(days=90)
    one_eighty_days_ago = last_date - timedelta(days=180)

    # 30-day volatility
    df_30d = df[df['date'] >= thirty_days_ago].copy()
    if len(df_30d) > 1:
        df_30d['returns'] = df_30d['close'].pct_change()
        volatility_30d = df_30d['returns'].std() * np.sqrt(252) * 100  # Annualized
    else:
        volatility_30d = None

    # 90-day volatility
    df_90d = df[df['date'] >= ninety_days_ago].copy()
    if len(df_90d) > 1:
        df_90d['returns'] = df_90d['close'].pct_change()
        volatility_90d = df_90d['returns'].std() * np.sqrt(252) * 100  # Annualized
    else:
        volatility_90d = None

    # 180-day volatility
    df_180d = df[df['date'] >= one_eighty_days_ago].copy()
    if len(df_180d) > 1:
        df_180d['returns'] = df_180d['close'].pct_change()
        volatility_180d = df_180d['returns'].std() * np.sqrt(252) * 100  # Annualized
    else:
        volatility_180d = None

    # 1-year volatility (252 trading days)
    df_1y = df[df['date'] >= one_year_ago].copy()
    if len(df_1y) > 1:
        df_1y['returns'] = df_1y['close'].pct_change()
        volatility_1y = df_1y['returns'].std() * np.sqrt(252) * 100  # Annualized
    else:
        volatility_1y = None

    # Calculate 52-week high and low
    df_52w = df[df['date'] >= one_year_ago]
    if not df_52w.empty:
        week_52_high = df_52w['close'].max()
        week_52_low = df_52w['close'].min()
        distance_from_high = ((last_close - week_52_high) / week_52_high * 100)
    else:
        week_52_high = None
        week_52_low = None
        distance_from_high = None

    return {
        'last_close': last_close,
        'prev_close': prev_close,
        'day_change_pct': day_change_pct,
        'month_performance': month_performance,
        'ytd_performance': ytd_performance,
        'year_performance': year_performance,
        'three_year_performance': three_year_performance,
        'volatility_30d': volatility_30d,
        'volatility_90d': volatility_90d,
        'volatility_180d': volatility_180d,
        'volatility_1y': volatility_1y,
        'week_52_high': week_52_high,
        'week_52_low': week_52_low,
        'distance_from_high': distance_from_high
    }


# --- FUZZY MATCHING HELPERS ---
DATA_DIR = Path(__file__).parent / "data"

def load_known_themes():
    """Load canonical theme names from industry summary CSV."""
    summary_file = DATA_DIR / "industry_summary_offline.csv"
    if not summary_file.exists():
        return []
    
    try:
        df = pd.read_csv(summary_file)
        if 'Theme' in df.columns:
            return df['Theme'].dropna().unique().tolist()
    except:
        pass
    return []

def fuzzy_match_theme(target, choices):
    """
    Find best matching theme name from choices.
    Returns the canonical name if a good match is found, else None.
    """
    if not choices:
        return None
        
    import difflib
    
    # 1. Exact match (case insensitive)
    target_lower = target.lower().strip()
    for choice in choices:
        if choice.lower().strip() == target_lower:
            return choice
            
    # 2. Fuzzy match
    matches = difflib.get_close_matches(target, choices, n=1, cutoff=0.7)
    if matches:
        return matches[0]
        
    return None

SPY_PATH = Path(__file__).parent / "data/spy_benchmark.csv"

def get_spy_data(start_date, end_date):
    """
    Loads SPY data.
    """
    import yfinance as yf
    from datetime import datetime
    
    df = None
    if SPY_PATH.exists():
        try:
            df = pd.read_csv(SPY_PATH)
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Remove any rows with invalid dates
            df = df.dropna(subset=['date'])
        except Exception:
            df = None
            pass

    # If missing or doesn't cover range, download
    need_download = False
    if df is None or len(df) == 0:
        need_download = True
    else:
        if df['date'].min() > pd.to_datetime(start_date) + pd.Timedelta(days=10):
            need_download = True
        if df['date'].max() < pd.to_datetime(end_date) - pd.Timedelta(days=5):
            need_download = True

    if need_download:
        print("Downloading updated SPY data (Yahoo Finance)...")
        try:
            ticker = yf.Ticker("SPY")
            # Using 1970 to align with theme chart robustness
            hist = ticker.history(start="1970-01-01", end=datetime.today().strftime('%Y-%m-%d'))
            hist.reset_index(inplace=True)
            hist['date'] = hist['Date'].dt.tz_localize(None)
            df = hist[['date', 'Close']].rename(columns={'Close': 'spy_val'})
            df.to_csv(SPY_PATH, index=False)
        except Exception as e:
            print(f"ERROR downloading SPY: {e}")
            if df is not None: return df # Return what we have
            return None

    mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
    return df.loc[mask].copy().sort_values('date')



def generate_interactive_stock_chart(symbol, height=450):
    """
    Generate embedded plotly chart HTML with SPY comparison and dynamic re-normalization.
    Also saves a standalone full-screen version.
    """
    # Load data from MySQL
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    query = text("SELECT date, close FROM stock_prices WHERE symbol = :symbol ORDER BY date ASC")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"symbol": symbol.upper()})

    if df.empty:
        return ('<div class="no-data">No price data available for chart</div>', None)

    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').rename(columns={'close': 'portfolio'})
    
    portfolio_df = df.reset_index()

    # SPY Benchmark
    min_date = portfolio_df['date'].min()
    max_date = portfolio_df['date'].max()
    
    spy_df = get_spy_data(min_date, max_date)
    
    # Explicitly ensure dates are Datetime64[ns] without timezone
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date']).dt.tz_localize(None)
    
    if spy_df is not None:
        spy_df['date'] = pd.to_datetime(spy_df['date']).dt.tz_localize(None)
        
        portfolio_df = portfolio_df.sort_values('date')
        spy_df = spy_df.sort_values('date')
        
        equity_df = pd.merge_asof(portfolio_df, spy_df, on='date', direction='backward')
        equity_df['spy_val'] = equity_df['spy_val'].ffill().bfill() 
    else:
        equity_df = portfolio_df.copy()

    # Calculation
    t0 = equity_df['portfolio'].iloc[0]
    equity_df['roi'] = (equity_df['portfolio'] / t0 - 1) * 100
    
    subtitle_init = "Performance: N/A"
    
    if 'spy_val' in equity_df.columns:
        s0 = equity_df['spy_val'].iloc[0]
        if pd.isna(s0) or s0 == 0:
            valid_spy = equity_df['spy_val'].dropna()
            if not valid_spy.empty:
                s0 = valid_spy.iloc[0]
            else:
                s0 = 1
        
        equity_df['spy_roi'] = (equity_df['spy_val'] / s0 - 1) * 100
        
        diff_init = equity_df['roi'].iloc[-1] - equity_df['spy_roi'].iloc[-1]
        c_init = '#00c853' if diff_init >= 0 else '#ff1744'
        sign_init = '+' if diff_init >= 0 else ''
        subtitle_init = f"Performance: <span style='color:{c_init}'>{sign_init}{diff_init:,.2f}% vs Benchmark</span>"
    else:
        equity_df['spy_roi'] = 0

    # Plot
    fig = go.Figure()

    # Trace 0: Invisible Line (just for Fill Gradient)
    fig.add_trace(go.Scatter(
        x=equity_df['date'], y=equity_df['roi'],
        mode='none',
        fill='tozeroy',
        fillcolor='rgba(0, 200, 83, 0.05)',  # Green with transparency
        fillgradient=dict(
            type='vertical', 
            colorscale=[
                [0, 'rgba(0, 200, 83, 0.05)'], 
                [1, 'rgba(0, 200, 83, 0.6)']
            ]
        ),
        showlegend=False,
        hoverinfo='skip'
    ))

    # Trace 1: Benchmark SPY
    fig.add_trace(go.Scatter(
        x=equity_df['date'], y=equity_df['spy_roi'],
        mode='lines',
        name='Benchmark (SP500)',
        line=dict(color='#000000', width=1.5), 
        hovertemplate='Benchmark: %{y:,.2f}%<extra></extra>'
    ))

    # Trace 2: Stock Line (Primary)
    fig.add_trace(go.Scatter(
        x=equity_df['date'], y=equity_df['roi'],
        mode='lines',
        name=symbol.upper(),
        line=dict(color='#00c853', width=2), # Strong Green
        hovertemplate=f'{symbol.upper()}: %{{y:,.2f}}%<extra></extra>'
    ))

    # Layout
    
    # Calculate Default 10Y Range
    max_d = equity_df['date'].max()
    min_d = equity_df['date'].min()
    start_10y = max_d - pd.DateOffset(years=10)
    if start_10y < min_d:
        start_10y = min_d

    fig.update_layout(
        title=dict(
            text=f"Stock Performance: {symbol.upper()} vs Benchmark (ROI %)<br><sub>{subtitle_init}</sub>",
            x=0.5, xanchor='center',
            font=dict(size=24, color='#333')
        ),
        template='plotly_white',
        plot_bgcolor='white',
        hovermode='x unified',
        height=height,
        margin=dict(t=180, l=60, r=40, b=60),
        
        xaxis=dict(
            range=[start_10y, max_d], # Default to 10Y
            type="date",
            showgrid=False,
            showline=True,
            linewidth=1,
            linecolor='lightgrey',
            mirror=False, 
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1M", step="month", stepmode="backward"),
                    dict(count=6, label="6M", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1Y", step="year", stepmode="backward"),
                    dict(count=2, label="2Y", step="year", stepmode="backward"),
                    dict(count=3, label="3Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX")
                ]),
                font=dict(size=12),
                bgcolor="#f4f4f4",
                y=0.98
            )
        ),
        
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            showline=True,
            linewidth=1,
            linecolor='lightgrey',
            mirror=False,
            tickformat="+.0f", 
            ticksuffix="%",
            zeroline=True,
            zerolinecolor='#d3d3d3',
            zerolinewidth=1
        ),
        
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    # --- SAVE STANDALONE CHART ---
    standalone_filename = f"stock_chart_{symbol.lower()}.html"
    standalone_path = OUTPUT_DIR / standalone_filename
    
    # Temporarily remove fixed height and allow autosize for standalone
    fig.update_layout(height=None, autosize=True)

    # Generic Class-Based JS for Standalone + CSS for Centered 80% View
    js_standalone = f"""
    <style>
        body, html {{ 
            margin: 0; 
            padding: 0; 
            height: 100%; 
            background-color: #f5f5f5; 
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .plotly-graph-div {{ 
            height: 85vh !important; 
            width: 85vw !important; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            background-color: white;
            border-radius: 8px;
        }}
    </style>
    <script>
    var gd = document.getElementsByClassName('plotly-graph-div')[0];
    var debounceTimer;

    function setupLogic() {{
        if(!gd || !gd.data) {{ setTimeout(setupLogic, 200); return; }}
        if (gd.data.length < 3) return;
        
        gd._origTheme = gd.data[2].y.slice();
        gd._origSpy = gd.data[1].y.slice();
        
        gd.on('plotly_relayout', function(eventdata){{
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(recalc, 50);
        }});
        recalc();
    }}
    
    function recalc() {{
        var xrange = gd.layout.xaxis.range;
        if(!xrange || !gd._origTheme) return;
        
        var startDate = new Date(xrange[0]).getTime();
        var endDate = new Date(xrange[1]).getTime();
        var xData = gd.data[2].x; 
        
        var startIdx = 0;
        for(var i=0; i<xData.length; i++) {{
            if(new Date(xData[i]).getTime() >= startDate) {{
                startIdx = i;
                break;
            }}
        }}
        
        var t0 = gd._origTheme[startIdx]; 
        var s0 = gd._origSpy[startIdx];   
        if (s0 === undefined || s0 === null) s0 = 0;

        var themeBase = (t0/100) + 1;
        var spyBase = (s0/100) + 1;
        
        var newTheme = gd._origTheme.map(v => ( ((v/100+1)/themeBase) - 1 ) * 100);
        var newSpy = gd._origSpy.map(function(v) {{
             if (v === undefined || v === null) return 0;
             return ( ((v/100+1)/spyBase) - 1 ) * 100;
        }});
        
        var minVal = Infinity;
        var maxVal = -Infinity;
        var finalIdx = startIdx;

        for(var i=0; i<xData.length; i++) {{
            var t = new Date(xData[i]).getTime();
            if(t >= startDate && t <= endDate) {{
                var v1 = newTheme[i];
                var v2 = newSpy[i];
                if(v1 < minVal) minVal = v1;
                if(v1 > maxVal) maxVal = v1;
                if(v2 < minVal) minVal = v2;
                if(v2 > maxVal) maxVal = v2;
                finalIdx = i;
            }}
        }}
        
        if (minVal === Infinity) {{ minVal = 0; maxVal = 10; }}
        
        var range = maxVal - minVal;
        var padding = range * 0.05; 
        if (padding === 0) padding = 1;
        
        if (finalIdx >= newTheme.length) finalIdx = newTheme.length - 1;
        var finalTheme = newTheme[finalIdx];
        var finalSpy = newSpy[finalIdx];
        var diff = finalTheme - finalSpy;
        var color = diff >= 0 ? '#00c853' : '#ff1744';
        var sign = diff >= 0 ? '+' : '';
        var subtitle = 'Performance: <span style="color:'+color+'">' + sign + diff.toFixed(2) + '% vs Benchmark</span>';
        
        Plotly.relayout(gd, {{
            'title.text': 'Stock Performance: {symbol.upper()} vs Benchmark (ROI %)<br><sub>' + subtitle + '</sub>',
            'yaxis.range': [minVal - padding, maxVal + padding]
        }});
        
        Plotly.restyle(gd, {{
            y: [newTheme, newSpy, newTheme] 
        }}, [0, 1, 2]);
    }}
    
    var checkExist = setInterval(function() {{
       if (document.getElementsByClassName('plotly-graph-div').length) {{
          gd = document.getElementsByClassName('plotly-graph-div')[0];
          setupLogic();
          clearInterval(checkExist);
       }}
    }}, 100);
    </script>
    """

    # Generate Full HTML for standalone
    fig.write_html(standalone_path, include_plotlyjs='cdn', full_html=True)
    # Inject JS and CSS
    with open(standalone_path, 'r', encoding='utf-8') as f:
        content = f.read()
    final_content = content.replace("</body>", f"{js_standalone}</body>")
    with open(standalone_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"[OK] Saved standalone chart: {standalone_path}")

    # --- RESTORE FIXED HEIGHT/MARGINS FOR EMBEDDED ---
    # Update title font size and margins for tighter embedded view
    # Enable autosize so it fills the container width (fitting the box)
    fig.update_layout(
        height=height, 
        width=None,
        autosize=True,
        margin=dict(t=60, l=30, r=20, b=40),
        title=dict(font=dict(size=16), y=0.95) # Smaller title, slightly lower
    )

    # --- GENERATE EMBEDDED DIV ---
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='interactive-chart',
        full_html=False,
        config={'displayModeBar': False, 'responsive': True} 
    )
    
    # ID-Based JS for Embedded
    js_embedded = f"""
    <script>
    (function() {{
        var gd = document.getElementById('interactive-chart');
        var debounceTimer;

        function setupLogic() {{
            if(!gd || !gd.data) {{ setTimeout(setupLogic, 200); return; }}
            // Match traces: 0=Fill, 1=SPY, 2=Stock
            if (gd.data.length < 3) return;
            
            gd._origTheme = gd.data[2].y.slice();
            gd._origSpy = gd.data[1].y.slice();
            
            gd.on('plotly_relayout', function(eventdata){{
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(recalc, 50);
            }});
            recalc();
        }}
        
        function recalc() {{
            var xrange = gd.layout.xaxis.range;
            if(!xrange || !gd._origTheme) return;
            
            var startDate = new Date(xrange[0]).getTime();
            var endDate = new Date(xrange[1]).getTime();
            var xData = gd.data[2].x; 
            
            var startIdx = 0;
            for(var i=0; i<xData.length; i++) {{
                if(new Date(xData[i]).getTime() >= startDate) {{
                    startIdx = i;
                    break;
                }}
            }}
            
            var t0 = gd._origTheme[startIdx]; 
            var s0 = gd._origSpy[startIdx];   
            if (s0 === undefined || s0 === null) s0 = 0;

            var themeBase = (t0/100) + 1;
            var spyBase = (s0/100) + 1;
            
            var newTheme = gd._origTheme.map(v => ( ((v/100+1)/themeBase) - 1 ) * 100);
            var newSpy = gd._origSpy.map(function(v) {{
                 if (v === undefined || v === null) return 0;
                 return ( ((v/100+1)/spyBase) - 1 ) * 100;
            }});
            
            var minVal = Infinity;
            var maxVal = -Infinity;
            var finalIdx = startIdx;

            for(var i=0; i<xData.length; i++) {{
                var t = new Date(xData[i]).getTime();
                if(t >= startDate && t <= endDate) {{
                    var v1 = newTheme[i];
                    var v2 = newSpy[i];
                    if(v1 < minVal) minVal = v1;
                    if(v1 > maxVal) maxVal = v1;
                    if(v2 < minVal) minVal = v2;
                    if(v2 > maxVal) maxVal = v2;
                    finalIdx = i;
                }}
            }}
            
            if (minVal === Infinity) {{ minVal = 0; maxVal = 10; }}
            
            var range = maxVal - minVal;
            var padding = range * 0.05; 
            if (padding === 0) padding = 1;
            
            if (finalIdx >= newTheme.length) finalIdx = newTheme.length - 1;
            var finalTheme = newTheme[finalIdx];
            var finalSpy = newSpy[finalIdx];
            var diff = finalTheme - finalSpy;
            var color = diff >= 0 ? '#00c853' : '#ff1744';
            var sign = diff >= 0 ? '+' : '';
            var subtitle = 'Performance: <span style="color:'+color+'">' + sign + diff.toFixed(2) + '% vs Benchmark</span>';
            
            Plotly.relayout(gd, {{
                'title.text': 'Stock Performance: {symbol.upper()} vs Benchmark (ROI %)<br><sub>' + subtitle + '</sub>',
                'yaxis.range': [minVal - padding, maxVal + padding]
            }});
            
            Plotly.restyle(gd, {{
                y: [newTheme, newSpy, newTheme] 
            }}, [0, 1, 2]);
        }}
        
        var checkExist = setInterval(function() {{
           if (document.getElementById('interactive-chart')) {{
              gd = document.getElementById('interactive-chart');
              setupLogic();
              clearInterval(checkExist);
           }}
        }}, 100);
    }})();
    </script>
    """

    return (chart_html + js_embedded, standalone_filename)


def generate_company_profile_html(symbol):
    """
    Generate complete company profile HTML page
    """
    print(f"\n{'='*60}")
    print(f"Generating Company Profile for: {symbol.upper()}")
    print(f"{'='*60}\n")

    # Get data
    print("Fetching company information...")
    company_info = get_company_info(symbol)

    if company_info is None:
        print(f"[ERROR] Error: Company {symbol.upper()} not found in database")
        return None

    print(f"[OK] Found: {company_info.get('name', 'N/A')}")

    print("Fetching rankings...")
    ranks = get_company_ranks(symbol)
    print(f"[OK] Found {len(ranks)} theme rankings")

    print("Fetching evidence...")
    evidence_list = get_company_evidence(symbol)
    print(f"[OK] Found {len(evidence_list)} evidence entries")

    print("Generating price chart...")
    chart_html, chart_filename = generate_interactive_stock_chart(symbol, height=450)
    print("[OK] Chart generated")

    print("Calculating performance metrics...")
    performance = calculate_performance_metrics(symbol)
    if performance:
        print("[OK] Performance metrics calculated")
    else:
        print("[WARN] No performance data available")

    # Build HTML
    company_name = company_info.get('name', 'Unknown Company')
    company_domain = company_info.get('domain', None)
    company_logo_blob = company_info.get('logo', None)
    description = company_info.get('description', None)
    
    # Prepare logo URL/data
    logo_html = ''
    if company_domain:
        if company_logo_blob and len(company_logo_blob) > 0:
            # Use logo from database (convert BLOB to base64)
            import base64
            logo_base64 = base64.b64encode(company_logo_blob).decode('utf-8')
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="{company_name} Logo" class="header-logo" />'
        elif LOGO_DEV_API_KEY:
            # Fallback to logo.dev API
            logo_html = f'<img src="https://img.logo.dev/{company_domain}?token={LOGO_DEV_API_KEY}&size=120" alt="{company_name} Logo" class="header-logo" onerror="this.style.display=\'none\'" />'

    # Handle missing description
    if description is None or description == '' or str(description).lower() == 'nan':
        description = 'No description available.'

    currency = company_info.get('currency', 'N/A')
    exchange = company_info.get('exchange', 'N/A')
    asset_type = company_info.get('assetType', 'N/A')

    # Helper function to format percentage with color
    def format_performance(value):
        if value is None:
            return '<span style="color: #999;">N/A</span>'
        color = '#27ae60' if value >= 0 else '#e74c3c'  # Green for positive, red for negative
        sign = '+' if value >= 0 else ''
        return f'<span style="color: {color}; font-weight: bold;">{sign}{value:.2f}%</span>'

    # Build info cards HTML - First row: Basic company info
    info_cards_html = f"""
    <div class="info-grid">
        <div class="info-card">
            <div class="info-label">Symbol</div>
            <div class="info-value">{symbol.upper()}</div>
        </div>"""

    # Add Last Close with special styling if performance data exists
    if performance:
        last_close = performance['last_close']
        info_cards_html += f"""
        <div class="info-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <div class="info-label" style="color: rgba(255,255,255,0.9);">Last Close</div>
            <div class="info-value" style="color: white; font-size: 1.4rem;">${last_close:.2f}</div>
        </div>"""

    info_cards_html += f"""
        <div class="info-card">
            <div class="info-label">Currency</div>
            <div class="info-value">{currency}</div>
        </div>
        <div class="info-card">
            <div class="info-label">Exchange</div>
            <div class="info-value">{exchange}</div>
        </div>
        <div class="info-card">
            <div class="info-label">Asset Type</div>
            <div class="info-value">{asset_type}</div>
        </div>
    </div>
    """

    # Build performance metrics section - Second row
    if performance:
        day_change = format_performance(performance['day_change_pct'])
        month_perf = format_performance(performance['month_performance'])
        ytd_perf = format_performance(performance['ytd_performance'])
        year_perf = format_performance(performance['year_performance'])
        three_year_perf = format_performance(performance['three_year_performance'])

        # Additional metrics
        volatility_30 = f"{performance['volatility_30d']:.2f}%" if performance['volatility_30d'] else "N/A"
        volatility_90 = f"{performance['volatility_90d']:.2f}%" if performance['volatility_90d'] else "N/A"
        volatility_180 = f"{performance['volatility_180d']:.2f}%" if performance['volatility_180d'] else "N/A"
        volatility_1y = f"{performance['volatility_1y']:.2f}%" if performance['volatility_1y'] else "N/A"
        week_52_high = f"${performance['week_52_high']:.2f}" if performance['week_52_high'] else "N/A"
        week_52_low = f"${performance['week_52_low']:.2f}" if performance['week_52_low'] else "N/A"
        dist_from_high = format_performance(performance['distance_from_high']) if performance['distance_from_high'] is not None else "N/A"

        performance_html = f"""
        <div style="margin-top: 25px; padding-top: 20px; border-top: 2px solid #ecf0f1;">
            <h3 style="margin: 0 0 15px 0; font-size: 1.1rem; color: var(--primary-color);">Performance Metrics</h3>
            <div class="info-grid">
                <div class="info-card">
                    <div class="info-label">Day Change</div>
                    <div class="info-value">{day_change}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">1 Month</div>
                    <div class="info-value">{month_perf}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Year to Date</div>
                    <div class="info-value">{ytd_perf}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">12 Months</div>
                    <div class="info-value">{year_perf}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">3 Years</div>
                    <div class="info-value">{three_year_perf}</div>
                </div>
            </div>
            <h3 style="margin: 20px 0 15px 0; font-size: 1.1rem; color: var(--primary-color);">Volatility (Annualized)</h3>
            <div class="info-grid">
                <div class="info-card">
                    <div class="info-label">30 Days</div>
                    <div class="info-value" style="color: #e67e22;">{volatility_30}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">90 Days</div>
                    <div class="info-value" style="color: #e67e22;">{volatility_90}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">180 Days</div>
                    <div class="info-value" style="color: #e67e22;">{volatility_180}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">1 Year</div>
                    <div class="info-value" style="color: #e67e22;">{volatility_1y}</div>
                </div>
            </div>
            <h3 style="margin: 20px 0 15px 0; font-size: 1.1rem; color: var(--primary-color);">52-Week Range</h3>
            <div class="info-grid">
                <div class="info-card">
                    <div class="info-label">52-Week High</div>
                    <div class="info-value" style="color: #27ae60;">{week_52_high}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">52-Week Low</div>
                    <div class="info-value" style="color: #e74c3c;">{week_52_low}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">From 52w High</div>
                    <div class="info-value">{dist_from_high}</div>
                </div>
            </div>
        </div>
        """
    else:
        performance_html = '<div class="no-data" style="margin-top: 20px;">No performance data available</div>'

    # Load known themes for fuzzy matching
    known_themes = load_known_themes()

    # Build rankings table HTML
    if ranks:
        rank_rows_html = ""
        for r in ranks:
            theme = r['theme']
            rank_num = r['rank']

            # Fuzzy match to ensure correct filename
            matched_theme = fuzzy_match_theme(theme, known_themes)
            
            # Determine badge class
            if rank_num <= 3:
                badge_class = "rank-badge rank-top3"
            elif rank_num <= 10:
                badge_class = "rank-badge rank-top10"
            else:
                badge_class = "rank-badge rank-other"

            # Check if evidence exists for this theme
            has_evidence = len(evidence_list) > 0  # Simplified check
            evidence_icon = '<span class="check-icon">✓</span>' if has_evidence else '<span class="no-icon">—</span>'

            # Create theme link (Relative link to HTML file)
            # Use matched theme if available, otherwise fallback to simple conversion
            target_theme = matched_theme if matched_theme else theme
            theme_url = target_theme.lower().replace(' ', '_').replace('-', '_').replace('&', 'and')
            
            # Point to relative HTML file
            theme_link = f"{theme_url}_detail.html"

            rank_rows_html += f"""
            <tr>
                <td>{theme}</td>
                <td style="text-align: center;">
                    <a href="{theme_link}" class="action-link" title="View {theme} theme details" style="font-size: 1.2rem; text-decoration: none;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle;">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                            <polyline points="15 3 21 3 21 9"></polyline>
                            <line x1="10" y1="14" x2="21" y2="3"></line>
                        </svg>
                    </a>
                </td>
                <td><span class="{badge_class}">#{rank_num}</span></td>
                <td style="text-align: center;">{evidence_icon}</td>
            </tr>
            """

        rankings_table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>Theme Name</th>
                    <th style="text-align: center; width: 60px;">Theme</th>
                    <th>Rank</th>
                    <th style="text-align: center;">Evidence</th>
                </tr>
            </thead>
            <tbody>
                {rank_rows_html}
            </tbody>
        </table>
        """
    else:
        rankings_table_html = '<div class="no-data">No ranking data available</div>'

    # Build evidence accordion HTML with sources and titles
    if evidence_list:
        evidence_html = ""
        for idx, ev_data in enumerate(evidence_list):
            evidence_text = ev_data.get('evidence', 'No evidence text')
            source_date = ev_data.get('source_date', None)
            evidence_sources = ev_data.get('evidenceSources', None)
            head_title = ev_data.get('head_title', None)

            # Format date
            date_str = ""
            if source_date:
                try:
                    # Format date as "Q3 2024" or similar
                    from datetime import datetime
                    dt = datetime.strptime(str(source_date), '%Y-%m-%d')
                    # Determine quarter
                    month = dt.month
                    if month <= 3:
                        quarter_str = f"Q1 {dt.year}"
                    elif month <= 6:
                        quarter_str = f"Q2 {dt.year}"
                    elif month <= 9:
                        quarter_str = f"Q3 {dt.year}"
                    else:
                        quarter_str = f"Q4 {dt.year}"
                    date_str = f'<span style="color: #666; font-size: 0.9rem; margin-left: 10px;">({quarter_str})</span>'
                except:
                    date_str = f'<span style="color: #666; font-size: 0.9rem; margin-left: 10px;">({source_date})</span>'

            # Parse sources for links
            sources_html = ""
            if evidence_sources and str(evidence_sources) != 'nan':
                try:
                    import json
                    import ast
                    try:
                        sources = json.loads(evidence_sources)
                    except:
                        sources = ast.literal_eval(evidence_sources)

                    if isinstance(sources, list) and sources:
                        sources_html = '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee;">'
                        sources_html += '<strong style="font-size: 0.9rem; color: #666;">Source Documents:</strong><br>'
                        for src in sources:
                            if isinstance(src, dict) and 'url' in src:
                                name = src.get('name', 'Document')
                                url = src['url']
                                sources_html += f'<a href="{url}" target="_blank" style="display: inline-block; margin: 5px 5px 5px 0; padding: 5px 10px; background-color: var(--accent-color); color: white; text-decoration: none; border-radius: 4px; font-size: 0.85rem;">📄 {name}</a>'
                        sources_html += '</div>'
                except:
                    pass

            # Build title display
            title_display = ""
            if head_title and str(head_title) != 'nan':
                title_display = f'<span style="color: #2c3e50; font-weight: 500; margin-left: 5px;">- {head_title}</span>'

            evidence_html += f"""
            <div class="evidence-item">
                <div class="evidence-header" onclick="toggleEvidence({idx})">
                    <span>Evidence #{idx + 1} {date_str}{title_display}</span>
                    <span class="toggle-icon" id="icon-{idx}">▼</span>
                </div>
                <div class="evidence-content" id="content-{idx}">
                    {evidence_text}
                    {sources_html}
                </div>
            </div>
            """
    else:
        evidence_html = '<div class="no-data">No evidence details available</div>'

    # Build Header Button for Chart
    chart_btn_html = ""
    if chart_filename:
        chart_btn_html = f'<a href="{chart_filename}" target="_blank" style="float: right; font-size: 0.85rem; background-color: var(--accent-color); color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; margin-top: -3px;">View Full Chart ⤢</a>'

    # Complete HTML template
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{symbol.upper()} - Company Profile</title>
    <style>
        {CSS_STYLES}
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            {logo_html}
            <div>
                <div>{symbol.upper()} - {company_name}</div>
                <div class="company-subtitle">
                    {f'<a href="https://{company_domain}" target="_blank">🌐 {company_domain}</a>' if company_domain else 'Company Investment Profile'}
                </div>
            </div>
        </div>
        <a href="main_trends.html" class="home-button" title="Back to Home">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="9 22 9 12 15 12 15 22" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </a>
    </div>

    <div class="container">
        <!-- Price Chart Section -->
        <div class="section" id="chart-container">
            <div class="section-header">
                Price Chart
                {chart_btn_html}
            </div>
            {chart_html}
        </div>

        <!-- Company Details Section -->
        <div class="section">
            <div class="section-header">Company Details and Performance</div>
            <div class="section-content">
                {info_cards_html}
                {performance_html}
            </div>
        </div>

        <!-- Description Section -->
        <div class="section">
            <div class="section-header">Description</div>
            <div class="section-content">
                <div class="description-text">{description}</div>
            </div>
        </div>

        <!-- Rankings Section -->
        <div class="section">
            <div class="section-header">Theme Rankings ({len(ranks)} themes)</div>
            <div class="section-content" style="padding: 0;">
                {rankings_table_html}
            </div>
        </div>

        <!-- Evidence Section -->
        <div class="section">
            <div class="section-header">Evidence Details ({len(evidence_list)} entries)</div>
            <div class="section-content">
                {evidence_html}
            </div>
        </div>
    </div>

    <script>
        function toggleEvidence(idx) {{
            const content = document.getElementById('content-' + idx);
            const icon = document.getElementById('icon-' + idx);

            if (content.classList.contains('active')) {{
                content.classList.remove('active');
                icon.classList.remove('active');
            }} else {{
                content.classList.add('active');
                icon.classList.add('active');
            }}
        }}
    </script>
</body>
</html>
    """

    # Save HTML
    output_path = OUTPUT_DIR / f'{symbol.upper()}_profile.html'
    print(f"\nSaving HTML to: {output_path}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)

    print(f"[OK] HTML saved successfully")

    return str(output_path)


def main():
    """Main execution function"""
    if len(sys.argv) < 2:
        symbol = input("Enter stock symbol (e.g., AAPL): ").upper()
    else:
        symbol = sys.argv[1].upper()

    try:
        output_path = generate_company_profile_html(symbol)

        if output_path:
            print(f"\n{'='*60}")
            print(f"[OK] SUCCESS: Company profile generated")
            print(f"{'='*60}\n")

            # Open in browser
            if "--no-browser" not in sys.argv:
                print(f"Opening in browser...")
                webbrowser.open(f'file://{os.path.abspath(output_path)}')
                print("[OK] Done!")
            else:
                print("[INFO] Browser opening skipped (--no-browser).")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[ERROR] ERROR: {e}")
        print(f"{'='*60}\n")
        raise


if __name__ == "__main__":
    main()
