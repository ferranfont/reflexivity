"""
Simple stock price chart with plot_day.py style colors.
Downloads data from MySQL stock_prices table and plots a clean line chart.
"""
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
import os
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- CONFIGURATION ---
SYMBOL = "AAPL"

# Database configuration (matching upload_stock_prices.py)
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
TABLE_NAME = "stock_prices"

# Output directory
OUTPUT_DIR = Path(__file__).parent / "html"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_stock_data(symbol):
    """
    Load stock data from MySQL database.

    Parameters:
    -----------
    symbol : str
        Stock ticker symbol (e.g., 'AAPL')

    Returns:
    --------
    pd.DataFrame
        DataFrame with columns: date, close
    """
    print(f"Loading data for {symbol} from MySQL...")

    # Create database connection
    connection_string = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    engine = create_engine(connection_string)

    # Query data
    query = f"""
    SELECT date, close
    FROM {TABLE_NAME}
    WHERE symbol = :symbol
    ORDER BY date ASC
    """

    with engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"symbol": symbol.upper()})

    if df.empty:
        raise ValueError(f"No data found for symbol: {symbol}")

    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    print(f"✅ Loaded {len(df)} rows")
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

    return df


def plot_stock_chart(df, symbol):
    """
    Create a simple stock price chart using plot_day.py color style.

    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with 'date' and 'close' columns
    symbol : str
        Stock ticker symbol for the title

    Returns:
    --------
    str
        Path to output HTML file
    """
    print(f"\nCreating chart for {symbol}...")

    # Create figure
    fig = go.Figure()

    # Add base fill (darker gradient at bottom for 3D effect)
    trace_fill = go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='none',
        fill='tozeroy',
        fillgradient=dict(
            type='vertical',
            colorscale=[
                [0, 'rgba(144, 238, 144, 0.1)'],      # Bottom: very light (near zero)
                [0.5, 'rgba(144, 238, 144, 0.4)'],    # Middle: medium
                [1, 'rgba(144, 238, 144, 0.7)']       # Top: more intense (near price)
            ]
        ),
        showlegend=False,
        hoverinfo='skip'
    )
    fig.add_trace(trace_fill)

    # Add price line (pastel green, solid)
    trace_price = go.Scatter(
        x=df['date'],
        y=df['close'],
        mode='lines',
        name='Close Price',
        line=dict(color='rgb(144, 238, 144)', width=1),  # Light pastel green
        hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Price:</b> $%{y:.2f}<extra></extra>',
        showlegend=False
    )
    fig.add_trace(trace_price)

    # Layout configuration (matching plot_day.py template='plotly_white' style)
    fig.update_layout(
        title=f'{symbol.upper()} - Historical Price Chart',
        template='plotly_white',
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Arial", size=12, color="#333333"),
        showlegend=False,
        height=800,
        xaxis_title="",
        yaxis_title=""
    )

    # Configure Y axis with 2 decimals (xxx.xx format)
    fig.update_yaxes(
        showgrid=True,
        gridcolor='#e0e0e0',
        gridwidth=0.5,
        showline=True,
        linewidth=1,
        linecolor='#d3d3d3',
        tickcolor='gray',
        tickfont=dict(color='gray'),
        tickformat=',.2f'  # 2 decimals: xxx.xx
    )

    # Configure X axis
    fig.update_xaxes(
        showgrid=False,
        showline=True,
        linewidth=1,
        linecolor='#d3d3d3',
        tickangle=-45
    )

    # Save chart
    output_path = OUTPUT_DIR / f'{symbol.lower()}_chart.html'
    print(f"Saving chart to: {output_path}")
    fig.write_html(str(output_path))
    print(f"✅ Chart saved successfully")

    return str(output_path)


def main():
    """Main execution function"""
    try:
        # Load data from MySQL
        df = load_stock_data(SYMBOL)

        # Create chart
        output_path = plot_stock_chart(df, SYMBOL)

        # Open in browser
        print(f"\nOpening chart in browser...")
        webbrowser.open(f'file://{os.path.abspath(output_path)}')
        print(f"✅ Done!")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
