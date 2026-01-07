
import os
import pandas as pd
import plotly.graph_objects as go
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path
import yfinance as yf
from datetime import datetime
import numpy as np

# Load environment variables
load_dotenv()

# DB Config
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "reflexivity_db")

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
THEMES_DIR = DATA_DIR / "all_themes"
OUTPUT_DIR = BASE_DIR / "html"
SPY_PATH = DATA_DIR / "spy_benchmark.csv"

# Colors for Top 10
COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]

def get_spy_data(start_date, end_date):
    """
    Loads SPY data.
    """
    df = None
    if SPY_PATH.exists():
        try:
            df = pd.read_csv(SPY_PATH)
            df['date'] = pd.to_datetime(df['date'])
        except Exception:
            pass
    
    # If missing or doesn't cover range, download
    need_download = False
    if df is None:
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

def get_theme_info(theme_name):
    """
    Finds the CSV and returns (filename, dataframe with symbols and ranks).
    """
    target = theme_name.lower().replace(" ", "_").replace("-", "_")
    
    best_match = None
    if THEMES_DIR.exists():
         # First pass: exact
        for f in os.listdir(THEMES_DIR):
             if f.lower().endswith(".csv"):
                fname = f.lower()[:-4].replace("-", "_")
                if fname == target:
                    best_match = f
                    break
        
        # Fuzzy if needed
        if not best_match:
             for f in os.listdir(THEMES_DIR):
                if f.lower().endswith(".csv") and target in f.lower():
                    best_match = f
                    break
    
    if best_match:
        try:
            df = pd.read_csv(THEMES_DIR / best_match, on_bad_lines='skip')
            # Clean columns
            df.columns = [c.strip().lower() for c in df.columns]
            # Ensure we have symbol and rank
            if 'symbol' in df.columns:
                return best_match, df
        except:
            pass
            
    return None, None

def plot_breakdown_chart(df_normalized, top_10_symbols, theme_name):
    """
    Plots the breakdown chart.
    df_normalized: Index is date, Columns are symbols + 'Others' + 'SPY' (all normalized to 100)
    """
    fig = go.Figure()

    # 1. Plot SPY (Black, Benchmark)
    if 'SPY' in df_normalized.columns:
        fig.add_trace(go.Scatter(
            x=df_normalized.index, 
            y=df_normalized['SPY'],
            mode='lines',
            name='S&P 500 (SPY)',
            line=dict(color='black', width=3),
            hovertemplate='SPY: %{y:+.1f}%'
        ))

    # 2. Plot Top 10
    color_idx = 0
    for sym in top_10_symbols:
        if sym in df_normalized.columns:
            fig.add_trace(go.Scatter(
                x=df_normalized.index, 
                y=df_normalized[sym],
                mode='lines',
                name=sym,
                line=dict(color=COLORS[color_idx % len(COLORS)], width=1),
                hovertemplate=f'{sym}: %{{y:+.1f}}%'
            ))
            color_idx += 1

    # 3. Plot Others (Grey)
    if 'Others' in df_normalized.columns:
        fig.add_trace(go.Scatter(
            x=df_normalized.index, 
            y=df_normalized['Others'],
            mode='lines',
            name='Others (Avg)',
            line=dict(color='lightgrey', width=1, dash='dot'),
            hovertemplate='Others: %{y:+.1f}%'
        ))

    # Layout
    fig.update_layout(
        title=dict(
            text=f"Theme Breakdown: {theme_name} (Top 10 Performers vs Others)",
            x=0.5,
            xanchor='center',
            font=dict(size=20, color='#333', family="Segoe UI")
        ),
        template='plotly_white',
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='x unified',
        height=800,  # Reduced by 50px
        margin=dict(t=100, l=50, r=50, b=50),
        
        # Legend styling
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        
        # X-Axis Styling (Clean, no title, no grid)
        xaxis=dict(
            type="date",
            showgrid=False,  # No Vertical Grid
            showline=True,
            linecolor='#e0e0e0',
            linewidth=1,
            title=None      # No Title
        ),
        
        # Y-Axis Styling (Clean, horizontal grid only)
        yaxis=dict(
            showgrid=True,
            gridcolor='#f5f5f5',  # Light horizontal grid
            showline=False,
            zeroline=True,
            zerolinecolor='#d3d3d3',
            zerolinewidth=1,
            title=None,      # No Title
            tickformat="+.0f",
            ticksuffix="%"
        )
    )

    filename = f"breakdown_{theme_name.lower().replace(' ', '_')}.html"
    filepath = OUTPUT_DIR / filename
    
    # Generate HTML with custom CSS for centering/container
    fig.write_html(filepath, include_plotlyjs='cdn', full_html=True)
    
    # Inject cleaner CSS for the "Framed" look
    with open(filepath, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    custom_css = """
    <style>
    body {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 40px;
    }
    .plotly-graph-div {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin: 0 auto !important;
        max-width: 1600px;
        width: 100% !important;
    }
    </style>
    """
    
    final_html = html_content.replace("</head>", f"{custom_css}</head>")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    print(f"Chart saved to: {filepath}")
    
    import webbrowser
    webbrowser.open(filepath.absolute().as_uri()) 

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_theme_breakdown.py \"Theme Name\"")
        return

    theme_name = " ".join(sys.argv[1:])
    print(f"Analyzing breakdown for: {theme_name}")

    # 1. Get Theme Data
    csv_file, theme_df = get_theme_info(theme_name)
    if theme_df is None:
        print(f"❌ Theme not found: {theme_name}")
        return
    
    # Extract symbols and ranks
    # Handle cases where rank might be missing or non-numeric
    if 'rank' not in theme_df.columns:
        theme_df['rank'] = 999
    
    # Clean symbols
    theme_df = theme_df.dropna(subset=['symbol'])
    theme_df['symbol'] = theme_df['symbol'].astype(str).str.upper().str.strip()
    
    # Sort by rank initially (just to get all_symbols)
    theme_df = theme_df.sort_values('rank')
    
    all_symbols = theme_df['symbol'].unique().tolist()
    print(f"Total Companies in theme: {len(all_symbols)}")

    # 2. Fetch Data from DB
    engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    print("Fetching historical data...")
    price_data = {}
    
    with engine.connect() as conn:
        for sym in all_symbols:
            try:
                # Optimized query for speed
                q = text("SELECT date, close FROM stock_prices WHERE symbol = :s ORDER BY date ASC")
                df = pd.read_sql(q, conn, params={"s": sym})
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    price_data[sym] = df['close']
            except Exception as e:
                pass

    if not price_data:
        print("❌ No price data found in database.")
        return

    # 3. Create Unified DataFrame
    full_df = pd.concat(price_data, axis=1)
    full_df = full_df.ffill().dropna(how='all')
    
    # Start Filter (3 Years Default)
    start_filter = pd.Timestamp.now() - pd.DateOffset(years=3)
    if full_df.index.min() > start_filter:
        start_filter = full_df.index.min()
        
    full_df = full_df[full_df.index >= start_filter]

    # --- Data Cleaning: Filter Unadjusted Splits ---
    print("Applying outlier filter to prevent split errors...")
    try:
        daily_rets = full_df.pct_change()
        # Filter outliers (>300% daily return)
        daily_rets = daily_rets.mask(daily_rets > 3.0, 0.0)
        
        # Reconstruct each column
        for col in full_df.columns:
            valid_idx = full_df[col].first_valid_index()
            if valid_idx is not None:
                start_price = full_df.loc[valid_idx, col]
                # Get relevant returns
                series_rets = daily_rets.loc[valid_idx:, col].fillna(0)
                # Reconstruct: Price_t = Price_0 * CumProd(1+r)
                full_df.loc[valid_idx:, col] = start_price * (1 + series_rets).cumprod()
    except Exception as e:
        print(f"Warning: Data cleaning failed: {e}")
    # -------------------------------------------------
    
    # 4. Calculate ROI for Ranking (Performance Contribution)
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
                roi_map.append((sym, roi))
            else:
                roi_map.append((sym, -999))
        else:
            roi_map.append((sym, -999))
            
    # Sort by ROI descending
    roi_map.sort(key=lambda x: x[1], reverse=True)
    
    ranked_symbols = [x[0] for x in roi_map]
    top_10 = ranked_symbols[:10]
    others = ranked_symbols[10:]
    
    print(f"Companies with data in period: {len(ranked_symbols)}")
    print("🏆 Top 10 Performers (Contribution Winners):")
    for i, sym in enumerate(top_10):
        roi_val = next(x[1] for x in roi_map if x[0] == sym)
        print(f"  {i+1}. {sym} (+{roi_val:,.0f}%)")
        
    if others:
        print(f"Others: {len(others)} companies (aggregated)")
    # Check if we have data that far back
    if full_df.index.min() > start_filter:
        start_filter = full_df.index.min()
        
    full_df = full_df[full_df.index >= start_filter]
    
    # 4. Handle "Others"
    # Calculate average price performance for 'others'
    # We can't average prices (Scale differs). We must average Normalized performance.
    # So we normalize EVERYTHING first.
    
    # Base Normalized DF (100 at start)
    normalized_df = pd.DataFrame(index=full_df.index)
    
    # Rebase function
    def normalize_series(series):
        # Find first valid index
        valid_idx = series.first_valid_index()
        if valid_idx is None: return series * np.nan
        base_val = series.loc[valid_idx]
        if base_val == 0: return series * np.nan
        
        # Calculate ROI %: ((Price / StartPrice) - 1) * 100
        # Start point becomes 0%
        base = series.iloc[0] 
        if pd.isna(base): return series * np.nan # Can't normalize if not present at start
        return ((series / base) - 1) * 100

    # Calculate Top 10 Normalized
    for sym in top_10:
        if sym in full_df.columns:
            normalized_df[sym] = normalize_series(full_df[sym])
            
    # Calculate Others Normalized
    others_cols = [c for c in others if c in full_df.columns]
    if others_cols:
        # Normalize each 'other' individually first
        others_norm_list = []
        for osym in others_cols:
             norm = normalize_series(full_df[osym])
             others_norm_list.append(norm)
        
        if others_norm_list:
            others_df = pd.concat(others_norm_list, axis=1)
            # Average of normalized curves
            normalized_df['Others'] = others_df.mean(axis=1)

    # 5. Add SPY
    spy_df = get_spy_data(full_df.index.min(), full_df.index.max())
    if spy_df is not None:
        spy_df.set_index('date', inplace=True)
        # Align
        aligned_spy = spy_df['spy_val'].reindex(full_df.index, method='ffill')
        normalized_df['SPY'] = normalize_series(aligned_spy)

    # Clean NaNs for plotting (Plotly handles gaps, but leading NaNs are fine)
    # Remove columns that are all NaN
    normalized_df.dropna(axis=1, how='all', inplace=True)

    # 6. Terminal Table
    print("\n" + "="*80)
    print(f"PERFORMANCE TABLE (Period: {full_df.index.min().date()} to {full_df.index.max().date()})")
    print("="*80)
    print(f"{'SYMBOL':<10} {'RANK':<10} {'START PRICE':<15} {'END PRICE':<15} {'CHANGE %':<10}")
    print("-" * 80)
    
    # Combine Top 10 + Others + SPY for table
    table_items = []
    
    # Process Top 10
    for sym in top_10:
        if sym in full_df.columns:
            s_price = full_df[sym].iloc[0]
            e_price = full_df[sym].iloc[-1]
            if pd.notna(s_price) and s_price != 0:
                chg = ((e_price - s_price) / s_price) * 100
                table_items.append((sym, "Top 10", s_price, e_price, chg))
    
    # Sort by performance
    table_items.sort(key=lambda x: x[4], reverse=True)
    
    for item in table_items:
        print(f"{item[0]:<10} {item[1]:<10} ${item[2]:<14.2f} ${item[3]:<14.2f} {item[4]:+.2f}%")
        
    if 'Others' in normalized_df.columns:
        chg_o = normalized_df['Others'].iloc[-1]
        print(f"{'OTHERS':<10} {'Agg':<10} {'(Start 0%)':<15} {'N/A':<15} {chg_o:+.2f}%")
        
    if 'SPY' in normalized_df.columns:
        chg_spy = normalized_df['SPY'].iloc[-1]
        print(f"{'SPY':<10} {'Bench':<10} {'(Start 0%)':<15} {'N/A':<15} {chg_spy:+.2f}%")

    print("="*80 + "\n")

    # 7. Plot
    plot_breakdown_chart(normalized_df, top_10, theme_name)

if __name__ == "__main__":
    main()
