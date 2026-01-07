
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
import yfinance as yf
from datetime import datetime
import numpy as np

# --- Configuration & Setup ---
st.set_page_config(layout="wide", page_title="Reflexivity Explorer", page_icon="🚀")

# Load environment variables
load_dotenv()
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "reflexivity_db")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
THEMES_DIR = DATA_DIR / "all_themes"
SUMMARY_FILE = DATA_DIR / "industry_summary_offline.csv"
SPY_PATH = DATA_DIR / "spy_benchmark.csv"

# Ensure directories
DATA_DIR.mkdir(exist_ok=True)

# --- CSS Styling ---
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        font-weight: 700;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #7f8c8d;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .metric-box {
        text-align: center;
        padding: 10px;
        background: white;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .metric-label { font-size: 0.9rem; color: #666; }
    .metric-value { font-size: 1.8rem; font-weight: bold; color: #2980b9; }
    
    tbody tr:hover {
        background-color: #f1f1f1 !important;
    }
    </style>
    """, unsafe_allow_html=True)


# --- Helper Functions ---

@st.cache_resource
def get_db_engine():
    """Returns a cached SQLAlchemy engine connection."""
    return create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

@st.cache_data
def load_summary():
    """Loads the industry summary CSV."""
    if not SUMMARY_FILE.exists():
        return pd.DataFrame()
    return pd.read_csv(SUMMARY_FILE)

def get_theme_symbols_from_file(filename):
    """Reads a theme CSV and returns list of symbols."""
    file_path = THEMES_DIR / filename
    if not file_path.exists():
        return [], pd.DataFrame()
    
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
        # Cleanup headers and data
        df.columns = df.columns.astype(str).str.strip().str.lower()
        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
        
        # Identify symbol column
        sym_col = next((c for c in df.columns if c in ['symbol', 'ticker']), None)
        if sym_col:
            symbols = df[sym_col].dropna().unique().tolist()
            # Clean symbols
            symbols = [str(s).strip().upper() for s in symbols]
            return symbols, df
        return [], df
    except Exception as e:
        st.error(f"Error reading {filename}: {e}")
        return [], pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache SPY data for 1 hour
def get_spy_data(start_date=None, end_date=None):
    """Fetches SPY benchmark data, handling local cache and download."""
    df = None
    if SPY_PATH.exists():
        try:
            df = pd.read_csv(SPY_PATH)
            df['date'] = pd.to_datetime(df['date'])
        except: pass
    
    # Simple check: if file is old (older than 1 day), re-download
    should_download = False
    if df is None:
        should_download = True
    elif datetime.now().timestamp() - SPY_PATH.stat().st_mtime > 86400:
        should_download = True
        
    if should_download:
        try:
            ticker = yf.Ticker("SPY")
            hist = ticker.history(period="10y") # Get last 10 years
            hist.reset_index(inplace=True)
            hist['date'] = hist['Date'].dt.tz_localize(None)
            df = hist[['date', 'Close']].rename(columns={'Close': 'spy_val'})
            df.to_csv(SPY_PATH, index=False)
        except Exception:
            pass # Use whatever we have or fail gracefully

    if df is not None:
        df = df.sort_values('date')
        if start_date and end_date:
            mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
            return df.loc[mask].copy()
        return df
    return None

def get_historical_prices(symbols):
    """Fetches historical prices for a list of symbols from MySQL."""
    if not symbols: return pd.DataFrame()
    
    engine = get_db_engine()
    prices = {}
    
    # Optimization: Chunk the query if too many symbols, but usually < 100
    # SQL IN clause
    placeholders = ','.join([':s'+str(i) for i in range(len(symbols))])
    params = { 's'+str(i): s for i, s in enumerate(symbols) }
    
    query = text(f"SELECT date, symbol, close FROM stock_prices WHERE symbol IN ({placeholders}) ORDER BY date ASC")
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        if df.empty: return pd.DataFrame()
        
        df['date'] = pd.to_datetime(df['date'])
        
        # Pivot: Date as Index, Symbol as Column
        pivot_df = df.pivot(index='date', columns='symbol', values='close')
        return pivot_df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

def calculate_portfolio_performance(price_df):
    """Calculates an equal-weight portfolio equity curve."""
    if price_df.empty: return pd.DataFrame()
    
    # 1. Fill forward missing data (last known price)
    price_df = price_df.ffill()
    
    # 2. Daily Returns
    daily_ret = price_df.pct_change()
    
    # --- SANITY CHECK / CLEANING ---
    # Filter out extreme outliers that likely indicate bad data (e.g., unadjusted reverse splits)
    # A >300% daily move in a single stock is rare and usually a data error in this context.
    # We replace these with 0% return for that day to preserve the rest of the series.
    daily_ret = daily_ret.mask(daily_ret > 3.0, 0.0) 
    
    # 3. Average Daily Return (Equal Weight)
    avg_ret = daily_ret.mean(axis=1).fillna(0)
    
    # 4. Cumulative Sum (Equity Curve)
    equity_curve = (1 + avg_ret).cumprod()
    
    # 5. Start at 1.0 (or 100)
    # Handle the very first starting point
    if not equity_curve.empty:
        equity_curve.iloc[0] = 1.0
    
    return equity_curve

# --- Page: Home ---
def render_home(summary_df):
    st.markdown('<div class="main-header">Reflexivity Explorer 🚀</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Advanced Investment Theme Analysis & Tracking</div>', unsafe_allow_html=True)
    
    if summary_df.empty:
        st.warning("No summary data available.")
        return

    # High Level Stats
    total_themes = len(summary_df)
    total_industries = summary_df['Industry'].nunique()
    total_companies = summary_df['Companies_Count'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Investment Themes", total_themes, delta_color="off")
    c2.metric("Industries Covered", total_industries, delta_color="off")
    c3.metric("Total Companies Tracked", int(total_companies), delta_color="off")
    
    st.markdown("---")
    
    st.subheader("Discovery")
    
    # Top Industries Chart
    ind_counts = summary_df['Industry'].value_counts().head(10)
    fig = go.Figure(data=[go.Bar(
        x=ind_counts.index, 
        y=ind_counts.values,
        marker_color='#3498db'
    )])
    fig.update_layout(title="Top Industries by Number of Themes", height=400)
    st.plotly_chart(fig, use_container_width=True)


# --- Page: Theme Explorer ---
def render_theme_explorer(summary_df):
    st.markdown("## 🌍 Theme Explorer")
    
    if summary_df.empty: return
    
    # Sidebar Filters for this page
    industries = sorted(summary_df['Industry'].unique())
    selected_ind = st.sidebar.selectbox("Filter by Industry", ["All"] + list(industries))
    
    if selected_ind != "All":
        filtered_df = summary_df[summary_df['Industry'] == selected_ind]
    else:
        filtered_df = summary_df
        
    theme_list = filtered_df.sort_values('Theme')['Theme'].tolist()
    selected_theme = st.sidebar.selectbox("Select Theme", theme_list)
    
    if selected_theme:
        # Get Theme Details
        row = filtered_df[filtered_df['Theme'] == selected_theme].iloc[0]
        filename = row['Filename']
        
        st.markdown(f"### {selected_theme} <span style='font-size:1rem;color:grey'>({row['Industry']})</span>", unsafe_allow_html=True)
        
        # Load Symbols
        symbols, details_df = get_theme_symbols_from_file(filename)
        
        if not symbols:
            st.warning("No symbols found for this theme.")
            return

        # TABS
        tab_perf, tab_holdings, tab_breakdown = st.tabs(["📈 Performance & Chart", "📋 Holdings & Ranks", "📊 Winners/Losers"])
        
        # --- PRE-FETCH DATA ---
        with st.spinner("Loading Market Data..."):
            price_df = get_historical_prices(symbols)
        
        if price_df.empty:
            st.error("No pricing data found in database for these symbols.")
            return

        # --- TAB 1: PEFORMANCE ---
        with tab_perf:
            # Calculate Portfolio
            equity_series = calculate_portfolio_performance(price_df)
            
            # Get SPY
            spy_df = get_spy_data(equity_series.index.min(), equity_series.index.max())
            
            # Normalize SPY to match timeframe
            if spy_df is not None:
                # Merge logic
                pf_df = pd.DataFrame(equity_series).rename(columns={0: 'Portfolio'})
                pf_df.index = pd.to_datetime(pf_df.index)
                
                # Reindex SPY to Portfolio dates (ffill)
                spy_indexed = spy_df.set_index('date').reindex(pf_df.index, method='ffill')
                
                # Normalize SPY to start at 1.0 (same as portfolio)
                valid_start = spy_indexed.first_valid_index()
                if valid_start:
                    base_val = spy_indexed.loc[valid_start, 'spy_val']
                    pf_df['SPY'] = spy_indexed['spy_val'] / base_val
                else:
                    pf_df['SPY'] = 1.0
            else:
                pf_df = pd.DataFrame(equity_series).rename(columns={0: 'Portfolio'})
            
            # Plot
            fig = go.Figure()
            
            # Theme Trace
            fig.add_trace(go.Scatter(
                x=pf_df.index, 
                y=(pf_df['Portfolio'] - 1) * 100,
                mode='lines',
                name=selected_theme,
                line=dict(color='#2980b9', width=2)
            ))
            
            # SPY Trace
            if 'SPY' in pf_df.columns:
                fig.add_trace(go.Scatter(
                    x=pf_df.index, 
                    y=(pf_df['SPY'] - 1) * 100,
                    mode='lines',
                    name='S&P 500 (SPY)',
                    line=dict(color='gray', width=1, dash='dot')
                ))
                
            fig.update_layout(
                title="Historical Performance (ROI %)",
                yaxis_title="Return (%)",
                xaxis_title="Date",
                template="plotly_white",
                hovermode="x unified",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Metrics
            total_ret = (pf_df['Portfolio'].iloc[-1] - 1) * 100
            
            # Calculate CAGR
            start_date = pf_df.index.min()
            end_date = pf_df.index.max()
            years = (end_date - start_date).days / 365.25
            
            if years > 0 and pf_df['Portfolio'].iloc[-1] > 0:
                cagr = ((pf_df['Portfolio'].iloc[-1]) ** (1/years) - 1) * 100
            else:
                cagr = 0
                
            if 'SPY' in pf_df.columns:
                spy_ret = (pf_df['SPY'].iloc[-1] - 1) * 100
                if years > 0 and pf_df['SPY'].iloc[-1] > 0:
                    spy_cagr = ((pf_df['SPY'].iloc[-1]) ** (1/years) - 1) * 100
                else: spy_cagr = 0
                alpha = total_ret - spy_ret
            else:
                spy_ret = 0
                spy_cagr = 0
                alpha = 0
                
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Return", f"{total_ret:+.2f}%")
            m2.metric("CAGR (Annual)", f"{cagr:.2f}%")
            m3.metric("Benchmark (SPY)", f"{spy_ret:+.2f}%")
            m4.metric("Alpha", f"{alpha:+.2f}%", delta_color="normal")
            
        # --- TAB 2: HOLDINGS ---
        with tab_holdings:
            st.dataframe(details_df, use_container_width=True, hide_index=True)
            
        # --- TAB 3: BREAKDOWN ---
        with tab_breakdown:
            st.markdown("#### Individual Asset Performance (Top 10)")
            # Calculate total return for each column in price_df
            
            # Filter to same timeframe
            rois = []
            for col in price_df.columns:
                series = price_df[col].dropna()
                if len(series) > 0:
                    start_p = series.iloc[0]
                    end_p = series.iloc[-1]
                    if start_p > 0:
                        roi = ((end_p - start_p)/start_p) * 100
                        rois.append({'Symbol': col, 'ROI': roi, 'Start': start_p, 'End': end_p})
            
            roi_df = pd.DataFrame(rois).sort_values('ROI', ascending=False)
            
            top_10 = roi_df.head(10)
            bottom_5 = roi_df.tail(5)
            
            st.subheader("🏆 Top Performers")
            st.table(top_10.style.format({'ROI': "{:+.2f}%", 'Start': "${:.2f}", 'End': "${:.2f}"}))
            
            st.subheader("📉 Laggards")
            st.table(bottom_5.style.format({'ROI': "{:+.2f}%", 'Start': "${:.2f}", 'End': "${:.2f}"}))


# --- Page: Company Search ---
def render_company_search():
    st.markdown("## 🔍 Company Intelligence")
    
    query = st.text_input("Enter Ticker Symbol (e.g. NVDA, TSLA)", "").strip().upper()
    
    if query:
        engine = get_db_engine()
        
        # 1. Company Info
        with engine.connect() as conn:
            # Fetch Info
            res = conn.execute(text("SELECT * FROM companies WHERE symbol = :s"), {"s": query}).mappings().fetchone()
            
            if not res:
                st.warning(f"Company '{query}' not found in database.")
                # Maybe fallback to yfinance info?
                try:
                    t = yf.Ticker(query)
                    info = t.info
                    res = {
                        'name': info.get('longName', query),
                        'description': info.get('longBusinessSummary', 'No description found via Yahoo Finance.'),
                        'industry': info.get('industry', 'Unknown'),
                        'sector': info.get('sector', 'Unknown')
                    }
                    st.info("Fetched data from Yahoo Finance (not yet in local DB).")
                except:
                    return
            
            # Display Header
            st.markdown(f"### {res.get('name', query)} ({query})")
            st.markdown(f"**Sector:** {res.get('sector','-')} | **Industry:** {res.get('industry','-')}")
            st.write(res.get('description', ''))
            
            st.divider()

            # 2. Evidence / News
            st.subheader("🧠 Reflexivity Evidence (News & Signals)")
            
            ev_query = text("""
                SELECT source_date, head_title, evidence, evidenceSources 
                FROM evidence 
                WHERE symbol = :s 
                ORDER BY source_date DESC 
                LIMIT 50
            """)
            ev_df = pd.read_sql(ev_query, conn, params={"s": query})
            
            if not ev_df.empty:
                for idx, row in ev_df.iterrows():
                    with st.expander(f"{row['source_date']} - {row['head_title'] or 'No Title'}"):
                        st.write(row['evidence'])
                        if row['evidenceSources']:
                            st.caption(f"Source: {row['evidenceSources']}")
            else:
                st.info("No gathered evidence/news for this company.")
            
            st.divider()
            
            # 3. Price History
            st.subheader("Price History")
            price_query = text("SELECT date, close FROM stock_prices WHERE symbol = :s ORDER BY date ASC")
            p_df = pd.read_sql(price_query, conn, params={"s": query})
            
            if not p_df.empty:
                p_df['date'] = pd.to_datetime(p_df['date'])
                p_df.set_index('date', inplace=True)
                st.line_chart(p_df['close'])
            else:
                st.write("No price data available.")


# --- Main Router ---
def main():
    summary_df = load_summary()
    
    # Sidebar Nav
    page = st.sidebar.radio("Navigation", ["Home", "Theme Explorer", "Company Search"])
    
    st.sidebar.markdown("---")
    st.sidebar.image("https://img.icons8.com/color/96/000000/python--v1.png", width=50)
    st.sidebar.caption("Reflexivity Engine v2.0")
    
    if page == "Home":
        render_home(summary_df)
    elif page == "Theme Explorer":
        render_theme_explorer(summary_df)
    elif page == "Company Search":
        render_company_search()

if __name__ == "__main__":
    main()
