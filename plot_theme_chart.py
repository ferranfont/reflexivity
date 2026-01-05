
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
            hist = ticker.history(start="1970-01-01", end=datetime.today().strftime('%Y-%m-%d'))
            hist.reset_index(inplace=True)
            hist['date'] = hist['Date'].dt.tz_localize(None)
            df = hist[['date', 'Close']].rename(columns={'Close': 'spy_val'})
            df.to_csv(SPY_PATH, index=False)
        except Exception as e:
            print(f"❌ Error bajando SPY: {e}")
            if df is not None: return df # Return what we have
            return None

    mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
    return df.loc[mask].copy().sort_values('date')

def get_theme_symbols(theme_name):
    target = theme_name.lower().replace(" ", "_").replace("-", "_")
    
    if THEMES_DIR.exists():
        for f in os.listdir(THEMES_DIR):
            if f.lower().endswith(".csv"):
                fname = f.lower()[:-4].replace("-", "_")
                if fname == target or theme_name.lower() in fname:
                    try:
                        df = pd.read_csv(THEMES_DIR / f, on_bad_lines='skip')
                        # Flexible column search
                        for col in df.columns:
                            if 'symbol' in col.lower() or 'ticker' in col.lower():
                                return df[col].dropna().unique().tolist()
                    except: continue
    print(f"❌ No se encontró archivo CSV para: {theme_name}")
    return []

def plot_interactive_chart(equity_df, theme_name):
    """
    Generates HTML with JavaScript for dynamic re-normalization and axis scaling.
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
        fillcolor='rgba(0, 123, 255, 0.05)',
        fillgradient=dict(
            type='vertical', 
            colorscale=[
                [0, 'rgba(0, 123, 255, 0.05)'], 
                [1, 'rgba(0, 123, 255, 0.6)']
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

    # Trace 2: Theme Line (Primary)
    fig.add_trace(go.Scatter(
        x=equity_df['date'], y=equity_df['roi'],
        mode='lines',
        name=theme_name.title(),
        line=dict(color='#007bff', width=2),
        hovertemplate='Theme: %{y:,.2f}%<extra></extra>'
    ))

    # --- LAYOUT ---
    fig.update_layout(
        title=dict(
            text=f"Theme Performance: {theme_name.title()} vs Benchmark (ROI %)<br><sub>{subtitle_init}</sub>",
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
        
        // Match traces: 0=Fill, 1=SPY, 2=Theme
        // Ensure we copy data correctly
        if (gd.data.length < 3) return;
        
        gd._origTheme = gd.data[2].y.slice();
        gd._origSpy = gd.data[1].y.slice();
        
        gd.on('plotly_relayout', function(eventdata){
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(recalc, 50);
        });
        
        // Force recalc on load
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
        
        // Protect against zero or null s0
        if (s0 === undefined || s0 === null) s0 = 0;

        // Base divisors (Value at T0)
        // Original data is in %. Convert to factor (1 + val/100)
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
        var padding = range * 0.05; // 5% padding
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
            'title.text': 'Theme Performance: """ + theme_name.title() + """ vs Benchmark (ROI %)<br><sub>' + subtitle + '</sub>',
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

    filename = f"equity_{theme_name.lower().replace(' ', '_').replace('-', '_')}.html"
    filepath = OUTPUT_DIR / filename
    
    fig.write_html(filepath, include_plotlyjs='cdn', full_html=True)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Inject CSS for "Framed" look
    custom_css = """
    <style>
    body { 
        background-color: #f5f7fa !important; 
        font-family: 'Segoe UI', sans-serif; 
        padding: 40px;
        margin: 0;
    }
    .plotly-graph-div {
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-radius: 8px;
        padding: 20px;
        max-width: 1200px;
        margin: 0 auto !important; /* Center using margin */
        width: 100% !important;   /* Take up available space up to max-width */
        height: 85vh !important;
        box-sizing: border-box;   /* Ensure padding doesn't affect width */
        overflow: hidden;         /* Fix for corner artifacts/scrollbars */
    }
    </style>
    """
    
    final_content = content.replace("</head>", f"{custom_css}</head>").replace("</body>", f"{js_script}</body>")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    print(f"✅ Gráfico interactivo guardado: {filepath}")
    
    # Open in browser
    import webbrowser
    # webbrowser.open(f'file://{os.path.abspath(filepath)}')


def main():
    if len(sys.argv) < 2:
        print("Usage: python plot_theme_chart.py \"Theme Name\"")
        return

    theme_name = " ".join(sys.argv[1:])
    print(f"Generando Chart para: {theme_name}")

    symbols = get_theme_symbols(theme_name)
    if not symbols: return

    engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    data_frames = []
    
    print(f"Obteniendo datos de {len(symbols)} empresas...")
    with engine.connect() as conn:
        for sym in symbols:
            try:
                # Use SQL to get data for specific dates? No, grab all.
                # Optimization: Could filter by min date if we knew it.
                q = text("SELECT date, close FROM stock_prices WHERE symbol = :s ORDER BY date ASC")
                df = pd.read_sql(q, conn, params={"s": sym})
                if not df.empty:
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date').rename(columns={'close': sym})
                    data_frames.append(df)
            except: pass
            
    if not data_frames:
        print("❌ No hay datos de precios.")
        return

    # Calculate Portfolio
    full = pd.concat(data_frames, axis=1).sort_index()
    full = full.ffill() 
    
    # Trim to when we have at least 1 valid stock?
    # full.dropna(how='all', inplace=True) but we want continuous
    
    daily_ret = full.pct_change()
    avg_daily_ret = daily_ret.mean(axis=1).fillna(0)
    equity_curve = (1 + avg_daily_ret).cumprod()
    
    portfolio_df = pd.DataFrame({
        'date': equity_curve.index,
        'portfolio': equity_curve.values
    })
    
    # Filter flat start
    portfolio_df = portfolio_df[portfolio_df['portfolio'] != 1.0]
    if portfolio_df.empty:
        # If absolutely no change, show header at least
        print("⚠️ No portfolio movement detected.")
        return

    # SPY Benchmark
    # Ensure timezone naivity match
    min_date = portfolio_df['date'].min()
    max_date = portfolio_df['date'].max()
    
    spy_df = get_spy_data(min_date, max_date)
    
    # Explicitly ensure dates are Datetime64[ns] without timezone
    portfolio_df['date'] = pd.to_datetime(portfolio_df['date']).dt.tz_localize(None)
    if spy_df is not None:
        spy_df['date'] = pd.to_datetime(spy_df['date']).dt.tz_localize(None)
        
        # Merge
        # merge_asof requires sorted 'on' column.
        portfolio_df = portfolio_df.sort_values('date')
        spy_df = spy_df.sort_values('date')
        
        final = pd.merge_asof(portfolio_df, spy_df, on='date', direction='backward')
        
        # If SPY starts later than portfolio, we might have NaNs at the start.
        # Backfill just for the start? Or ffill?
        # Better: Ratio relative to first VALID point.
        # Let's simple ffill for gaps.
        final['spy_val'] = final['spy_val'].ffill().bfill() 
        # bfill ensures s0 is not NaN if portfolio starts a bit before SPY data day (unlikely but possible)
        
    else:
        final = portfolio_df.copy()
        
    plot_interactive_chart(final, theme_name)

if __name__ == "__main__":
    main()
