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
OUTPUT_DIR = BASE_DIR / "html"
SPY_PATH = DATA_DIR / "spy_benchmark.csv"

# Ensure directories exist
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

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
        print("⬇️ Bajando datos actualizados del SPY (Yahoo Finance)...")
        try:
            ticker = yf.Ticker("SPY")
            # Using 1970 to align with theme chart robustness
            hist = ticker.history(start="1970-01-01", end=datetime.today().strftime('%Y-%m-%d'))
            hist.reset_index(inplace=True)
            hist['date'] = hist['Date'].dt.tz_localize(None)
            df = hist[['date', 'Close']].rename(columns={'Close': 'spy_val'})
            df.to_csv(SPY_PATH, index=False)
        except Exception as e:
            print(f"❌ Error bajando SPY: {e}")
            if df is not None: return df # Return what we have
            return None

    # Filter by date range
    mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
    return df.loc[mask].copy().sort_values('date')

def plot_interactive_chart(equity_df, ticker):
    """
    Generates HTML with JavaScript for dynamic re-normalization and axis scaling.
    Comparison: Stock vs SPY (Benchmark).
    """
    # Debug: Check SPY data
    if 'spy_val' in equity_df.columns:
        spy_min = equity_df['spy_val'].min()
        spy_max = equity_df['spy_val'].max()
        print(f"DEBUG: SPY Data Range: {spy_min} to {spy_max}")
        if pd.isna(spy_min) or spy_min == spy_max:
             print("⚠️ WARN: SPY data seems flat or empty.")
    
    # Prepare data (Base 0 for calculations)
    t0 = equity_df['portfolio'].iloc[0]
    equity_df['roi'] = (equity_df['portfolio'] / t0 - 1) * 100
    
    if 'spy_val' in equity_df.columns:
        # Avoid division by zero/NaN
        s0 = equity_df['spy_val'].iloc[0]
        if pd.isna(s0) or s0 == 0:
            # Try to find first valid
            valid_spy = equity_df['spy_val'].dropna()
            if not valid_spy.empty:
                s0 = valid_spy.iloc[0]
            else:
                s0 = 1
        
        equity_df['spy_roi'] = (equity_df['spy_val'] / s0 - 1) * 100
        # Determine performance color based on current diff for initial render
        diff_init = equity_df['roi'].iloc[-1] - equity_df['spy_roi'].iloc[-1]
        c_init = '#00c853' if diff_init >= 0 else '#ff1744'
        sign_init = '+' if diff_init >= 0 else ''
        subtitle_init = f"Performance: <span style='color:{c_init}'>{sign_init}{diff_init:,.0f}% vs Benchmark</span>"
    else:
        equity_df['spy_roi'] = 0
        subtitle_init = "Performance: N/A"

    fig = go.Figure()

    # --- TRACES ---
    # Trace 0: Invisible Line (just for Fill Gradient)
    fig.add_trace(go.Scatter(
        x=equity_df['date'], y=equity_df['roi'],
        mode='none',
        fill='tozeroy',
        fillcolor='rgba(0, 200, 83, 0.05)',
        fillgradient=dict(
            type='vertical', 
            colorscale=[
                [0, 'rgba(0, 200, 83, 0.05)'], 
                [1, 'rgba(0, 200, 83, 0.6)']
            ]
        ),
        hoverinfo='skip',
        showlegend=False
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
        name=ticker.upper(),
        line=dict(color='#00c853', width=2),
        hovertemplate=f'{ticker.upper()}: %{{y:,.2f}}%<extra></extra>'
    ))

    # --- LAYOUT ---
    fig.update_layout(
        title=dict(
            text=f"Stock Performance: {ticker.upper()} vs Benchmark (ROI %)<br><sub>{subtitle_init}</sub>",
            x=0.5, xanchor='center',
            font=dict(size=24, color='#333')
        ),
        template='plotly_white',
        plot_bgcolor='white',
        hovermode='x unified',
        margin=dict(t=180, l=60, r=40, b=60), 
        
        # X-Axis: No Grid, LightGrey Line
        xaxis=dict(
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
        
        # Y-Axis: Horizontal Grid Only, LightGrey Line
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

    # --- JAVASCRIPT INJECTION ---
    js_script = """
    <script>
    var gd = document.getElementsByClassName('plotly-graph-div')[0];
    var debounceTimer;

    function setupLogic() {
        if(!gd || !gd.data) { setTimeout(setupLogic, 200); return; }
        
        // Match traces: 0=Fill, 1=SPY, 2=Stock
        if (gd.data.length < 3) return;
        
        gd._origTheme = gd.data[2].y.slice();
        gd._origSpy = gd.data[1].y.slice();
        
        gd.on('plotly_relayout', function(eventdata){
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(recalc, 50);
        });
        
        recalc();
    }
    
    function recalc() {
        var xrange = gd.layout.xaxis.range;
        if(!xrange || !gd._origTheme) return;
        
        var startDate = new Date(xrange[0]).getTime();
        var endDate = new Date(xrange[1]).getTime();
        var xData = gd.data[2].x; 
        
        // Find visible indices
        var startIdx = 0;
        
        for(var i=0; i<xData.length; i++) {
            if(new Date(xData[i]).getTime() >= startDate) {
                startIdx = i;
                break;
            }
        }
        
        // Rebase Calculation
        var t0 = gd._origTheme[startIdx]; 
        var s0 = gd._origSpy[startIdx];   
        
        if (s0 === undefined || s0 === null) s0 = 0;

        // Base divisors (Value at T0)
        var themeBase = (t0/100) + 1;
        var spyBase = (s0/100) + 1;
        
        // Recalculate series relative to T0
        var newTheme = gd._origTheme.map(v => ( ((v/100+1)/themeBase) - 1 ) * 100);
        var newSpy = gd._origSpy.map(function(v) {
             if (v === undefined || v === null) return 0;
             return ( ((v/100+1)/spyBase) - 1 ) * 100;
        });
        
        // Auto-Scale finding
        var minVal = Infinity;
        var maxVal = -Infinity;
        var finalIdx = startIdx;

        for(var i=0; i<xData.length; i++) {
            var t = new Date(xData[i]).getTime();
            if(t >= startDate && t <= endDate) {
                var v1 = newTheme[i];
                var v2 = newSpy[i];
                
                if(v1 < minVal) minVal = v1;
                if(v1 > maxVal) maxVal = v1;
                if(v2 < minVal) minVal = v2;
                if(v2 > maxVal) maxVal = v2;
                
                finalIdx = i;
            }
        }
        
        if (minVal === Infinity) { minVal = 0; maxVal = 10; }
        
        // Tight padding logic
        var range = maxVal - minVal;
        var padding = range * 0.05; 
        if (padding === 0) padding = 1;
        
        // Final Performance text
        if (finalIdx >= newTheme.length) finalIdx = newTheme.length - 1;
        
        var finalTheme = newTheme[finalIdx];
        var finalSpy = newSpy[finalIdx];
        var diff = finalTheme - finalSpy;
        var color = diff >= 0 ? '#00c853' : '#ff1744';
        var sign = diff >= 0 ? '+' : '';
        var subtitle = 'Performance: <span style="color:'+color+'">' + sign + diff.toFixed(0) + '% vs Benchmark</span>';
        
        // Apply Updates
        Plotly.relayout(gd, {
            'title.text': 'Stock Performance: """ + ticker.upper() + """ vs Benchmark (ROI %)<br><sub>' + subtitle + '</sub>',
            'yaxis.range': [minVal - padding, maxVal + padding]
        });
        
        Plotly.restyle(gd, {
            y: [newTheme, newSpy, newTheme] 
        }, [0, 1, 2]);
    }
    
    var checkExist = setInterval(function() {
       if (document.getElementsByClassName('plotly-graph-div').length) {
          gd = document.getElementsByClassName('plotly-graph-div')[0];
          setupLogic();
          clearInterval(checkExist);
       }
    }, 100);
    </script>
    """

    filename = f"stock_chart_{ticker.lower()}.html"
    filepath = OUTPUT_DIR / filename
    
    # Save basic HTML then append JS
    fig.write_html(filepath, include_plotlyjs='cdn', full_html=True)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    final_content = content.replace("</body>", f"{js_script}</body>")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"✅ Gráfico interactivo guardado: {filepath}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_stock_chart.py \"TICKER\"")
        return

    ticker = sys.argv[1].upper()
    print(f"Generando Chart para Stock: {ticker}")

    engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    
    print(f"Obteniendo datos de {ticker}...")
    try:
        q = text("SELECT date, close FROM stock_prices WHERE symbol = :s ORDER BY date ASC")
        with engine.connect() as conn:
            df = pd.read_sql(q, conn, params={"s": ticker})
    except Exception as e:
        print(f"Error conectando DB: {e}")
        return

    if df.empty:
        print(f"❌ No hay datos de precios para {ticker} en DB local.")
        return

    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date').rename(columns={'close': 'portfolio'}) # 'portfolio' is just the column name expected by plotter
    
    # --- Data Cleaning (Fix for Unadjusted Splits) ---
    # Calculate daily returns
    daily_ret = df['portfolio'].pct_change()
    
    # Filter out extreme outliers (>300% daily return) which are likely data errors or splits
    daily_ret = daily_ret.mask(daily_ret > 3.0, 0.0)
    
    # Reconstruct the price curve
    start_price = df['portfolio'].iloc[0]
    daily_ret = daily_ret.fillna(0)
    df['portfolio'] = start_price * (1 + daily_ret).cumprod()
    # -------------------------------------------------

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
        
        final = pd.merge_asof(portfolio_df, spy_df, on='date', direction='backward')
        
        # Gap fill logic
        final['spy_val'] = final['spy_val'].ffill().bfill() 
    else:
        final = portfolio_df.copy()
        
    plot_interactive_chart(final, ticker)

if __name__ == "__main__":
    main()
