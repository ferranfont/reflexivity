
import streamlit as st
import pandas as pd
import os

# --- Configuration ---
# Path setup assuming this script is in d:/PYTHON/ALGOS/reflexivity/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SUMMARY_FILE = os.path.join(BASE_DIR, 'data', 'industry_summary_offline.csv')
THEMES_DIR = os.path.join(BASE_DIR, 'data', 'all_themes')

st.set_page_config(layout="wide", page_title="Reflexivity Explorer")

# --- Styles ---
st.markdown("""
    <style>
    .big-font {
        font-size:24px !important;
        font-weight: bold;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data
def load_summary():
    if not os.path.exists(SUMMARY_FILE):
        return pd.DataFrame()
    return pd.read_csv(SUMMARY_FILE)

def load_theme_data(filename):
    file_path = os.path.join(THEMES_DIR, filename)
    if not os.path.exists(file_path):
        return None
    try:
        # Robust reading similar to our cleaning scripts
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
        # Clean columns
        df.columns = df.columns.str.strip()
        # Clean string data
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        return df
    except Exception as e:
        st.error(f"Error reading file {filename}: {e}")
        return None

# --- Main App ---
def main():
    st.sidebar.title("Reflexivity 🚀")
    
    summary_df = load_summary()
    
    if summary_df.empty:
        st.error("Summary file not found. Please ensure 'outputs/industry_summary_offline.csv' exists.")
        return

    # --- Sidebar Filters ---
    
    # 1. Search Box
    search_query = st.sidebar.text_input("🔍 Search Theme", "")
    
    # Filter Logic
    if search_query:
        filtered_summary = summary_df[
            summary_df['Theme'].str.contains(search_query, case=False, na=False) |
            summary_df['Industry'].str.contains(search_query, case=False, na=False)
        ]
        if filtered_summary.empty:
            st.sidebar.warning("No matches found.")
        
        # If searching, show a flattened list or grouped by remaining industries
        available_industries = sorted(filtered_summary['Industry'].unique())
        
    else:
        filtered_summary = summary_df
        available_industries = sorted(summary_df['Industry'].unique())

    # 2. Industry Selection
    selected_industry = st.sidebar.selectbox("📂 Select Industry", available_industries)
    
    # 3. Theme Selection
    # Filter themes for this industry (respected search query as well)
    themes_in_industry = filtered_summary[filtered_summary['Industry'] == selected_industry]
    
    if themes_in_industry.empty:
        st.write("No themes match your criteria in this industry.")
        return

    # Sort themes
    themes_in_industry = themes_in_industry.sort_values('Theme')
    
    # Create valid options list
    theme_options = themes_in_industry['Theme'].tolist()
    
    selected_theme_name = st.sidebar.radio(
        "Select Theme", 
        theme_options,
        format_func=lambda x: f"{x} ({themes_in_industry[themes_in_industry['Theme']==x]['Companies_Count'].values[0]})"
    )

    # --- Main Content Area ---
    if selected_theme_name:
        # Get metadata
        theme_row = themes_in_industry[themes_in_industry['Theme'] == selected_theme_name].iloc[0]
        filename = theme_row['Filename']
        count = theme_row['Companies_Count']
        
        st.title(f"{selected_theme_name}")
        st.caption(f"Industry: {selected_industry} | File: {filename}")
        
        # Load Data
        df = load_theme_data(filename)
        
        if df is not None:
            col1, col2 = st.columns([1, 4])
            with col1:
                st.metric("Total Companies", len(df))
            
            # Display Table
            st.subheader("Companies List")
            
            # Select relevant columns if they exist
            desired_cols = ['name', 'symbol', 'currency', 'rank', 'description', 'exchange', 'type']
            cols_to_show = [c for c in desired_cols if c in df.columns]
            
            # Search within the table
            table_search = st.text_input("Filter companies within this table...", "")
            if table_search:
                df = df[
                    df.astype(str).apply(lambda x: x.str.contains(table_search, case=False)).any(axis=1)
                ]
            
            st.dataframe(
                df[cols_to_show] if cols_to_show else df,
                use_container_width=True,
                height=600,
                hide_index=True
            )
            
        else:
            st.warning("Could not load company data for this theme.")

if __name__ == "__main__":
    main()
