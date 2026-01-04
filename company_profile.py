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
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
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
    align-items: center;
    transition: background-color 0.2s;
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

    Returns dict with:
        - last_close: Latest closing price
        - prev_close: Previous day close
        - day_change_pct: % change from previous day
        - month_performance: % change last month
        - ytd_performance: % change year-to-date
        - year_performance: % change last 12 months
        - three_year_performance: % change last 3 years
        - volatility_30d: 30-day volatility (standard deviation)
        - week_52_high: 52-week high
        - week_52_low: 52-week low
        - distance_from_high: % distance from 52-week high
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
    one_month_ago = last_date - timedelta(days=30)
    year_start = datetime(last_date.year, 1, 1)
    one_year_ago = last_date - timedelta(days=365)
    three_years_ago = last_date - timedelta(days=365*3)

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


def generate_mini_chart(symbol, height=300):
    """
    Generate embedded plotly chart HTML matching plot_chart.py style

    Returns:
        str: HTML div with embedded chart
    """
    # Load data from MySQL
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    query = text("SELECT date, close FROM stock_prices WHERE symbol = :symbol ORDER BY date ASC")

    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"symbol": symbol.upper()})

    if df.empty:
        return '<div class="no-data">No price data available for chart</div>'

    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Create figure (matching plot_chart.py style)
    fig = go.Figure()

    # Add base fill (gradient for 3D effect)
    trace_fill = go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='none',
        fill='tozeroy',
        fillgradient=dict(
            type='vertical',
            colorscale=[
                [0, 'rgba(144, 238, 144, 0.1)'],      # Bottom: very light
                [0.5, 'rgba(144, 238, 144, 0.4)'],    # Middle: medium
                [1, 'rgba(144, 238, 144, 0.7)']       # Top: more intense
            ]
        ),
        showlegend=False,
        hoverinfo='skip'
    )
    fig.add_trace(trace_fill)

    # Add price line (pastel green)
    trace_price = go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        name='Close Price',
        line=dict(color='rgb(144, 238, 144)', width=1),
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> $%{y:.2f}<extra></extra>',
        showlegend=False
    )
    fig.add_trace(trace_price)

    # Layout configuration
    fig.update_layout(
        title='',
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12, color="#333333"),
        showlegend=False,
        height=height,
        margin=dict(l=50, r=20, t=20, b=50),
        xaxis_title="",
        yaxis_title=""
    )

    # Configure Y axis with 2 decimals
    fig.update_yaxes(
        showgrid=True,
        gridcolor='#e0e0e0',
        gridwidth=0.5,
        showline=True,
        linewidth=1,
        linecolor='#d3d3d3',
        tickcolor='gray',
        tickfont=dict(color='gray'),
        tickformat=',.2f'
    )

    # Configure X axis
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#d3d3d3',
        tickangle=-45
    )

    # Convert to HTML div (use CDN for plotly.js)
    chart_html = fig.to_html(
        include_plotlyjs='cdn',
        div_id='price-chart',
        config={'displayModeBar': False}
    )

    return chart_html


def generate_company_profile_html(symbol):
    """
    Generate complete company profile HTML page

    Args:
        symbol: Stock ticker symbol

    Returns:
        str: Path to generated HTML file
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
    chart_html = generate_mini_chart(symbol, height=350)
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

    # Build rankings table HTML
    if ranks:
        rank_rows_html = ""
        for r in ranks:
            theme = r['theme']
            rank_num = r['rank']

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

            rank_rows_html += f"""
            <tr>
                <td>{theme}</td>
                <td><span class="{badge_class}">#{rank_num}</span></td>
                <td style="text-align: center;">{evidence_icon}</td>
            </tr>
            """

        rankings_table_html = f"""
        <table>
            <thead>
                <tr>
                    <th>Theme Name</th>
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
            {symbol.upper()} - {company_name}
            <div class="company-subtitle">
                {f'<a href="https://{company_domain}" target="_blank">🌐 {company_domain}</a>' if company_domain else 'Company Investment Profile'}
            </div>
        </div>
        {logo_html}
    </div>

    <div class="container">
        <!-- Price Chart Section -->
        <div class="section" id="chart-container">
            <div class="section-header">Price Chart</div>
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
            print(f"Opening in browser...")
            webbrowser.open(f'file://{os.path.abspath(output_path)}')
            print("[OK] Done!")

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"[ERROR] ERROR: {e}")
        print(f"{'='*60}\n")
        raise


if __name__ == "__main__":
    main()
