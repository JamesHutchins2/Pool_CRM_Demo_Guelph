import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Pool CRM - Listings",
    layout="wide"
)

# Helper functions
@st.cache_data
def load_listings_data():
    """Load all listings CSV files"""
    base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app_data')
    
    matched_current = pd.read_csv(os.path.join(base_path, 'matched_current_listings.csv'))
    matched_removed = pd.read_csv(os.path.join(base_path, 'matched_removed_listings.csv'))
    deduped_current = pd.read_csv(os.path.join(base_path, 'deduped_current_less_matched.csv'))
    deduped_removed = pd.read_csv(os.path.join(base_path, 'deduped_removed_less_matched.csv'))
    
    return matched_current, matched_removed, deduped_current, deduped_removed



def display_listings_table(df, title, tab_key=""):
    """Display a listings table with filtering options"""
    st.subheader(title)
    st.caption(f"Total: {len(df)} listings")
    
    if len(df) == 0:
        st.info("No listings in this category.")
        return
    
    # Add filters
    with st.expander("Filters", expanded=False):
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        
        with filter_col1:
            if 'price' in df.columns:
                price_min = float(df['price'].min())
                price_max = float(df['price'].max())
                price_range = st.slider(
                    "Price Range",
                    min_value=price_min,
                    max_value=price_max,
                    value=(price_min, price_max),
                    key=f"price_{tab_key}"
                )
        
        with filter_col2:
            if 'bedrooms' in df.columns:
                bedrooms = sorted(df['bedrooms'].dropna().unique())
                selected_beds = st.multiselect(
                    "Bedrooms",
                    options=bedrooms,
                    default=bedrooms,
                    key=f"beds_{tab_key}"
                )
        
        with filter_col3:
            if 'municipality' in df.columns:
                municipalities = sorted(df['municipality'].dropna().unique())
                selected_munis = st.multiselect(
                    "Municipality",
                    options=municipalities,
                    default=municipalities,
                    key=f"muni_{tab_key}"
                )
        
        with filter_col4:
            if 'removal_date' in df.columns:
                # Convert to datetime for filtering
                df_dates = pd.to_datetime(df['removal_date'], errors='coerce')
                if not df_dates.isna().all():
                    min_date = df_dates.min().date()
                    max_date = df_dates.max().date()
                    date_range = st.date_input(
                        "Sold Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date,
                        key=f"date_{tab_key}"
                    )
                else:
                    date_range = None
    
    # Apply filters
    filtered_df = df.copy()
    if 'price' in df.columns:
        filtered_df = filtered_df[
            (filtered_df['price'] >= price_range[0]) & 
            (filtered_df['price'] <= price_range[1])
        ]
    if 'bedrooms' in df.columns and selected_beds:
        filtered_df = filtered_df[filtered_df['bedrooms'].isin(selected_beds)]
    if 'municipality' in df.columns and selected_munis:
        filtered_df = filtered_df[filtered_df['municipality'].isin(selected_munis)]
    if 'removal_date' in df.columns and date_range is not None:
        if len(date_range) == 2:
            start_date, end_date = date_range
            filtered_df_dates = pd.to_datetime(filtered_df['removal_date'], errors='coerce')
            filtered_df = filtered_df[
                (filtered_df_dates.dt.date >= start_date) & 
                (filtered_df_dates.dt.date <= end_date)
            ]
    
    st.caption(f"Filtered: {len(filtered_df)} listings")
    
    # Display data table
    # Select relevant columns for display
    if 'removal_date' in filtered_df.columns:
        # For removed listings, include removal date
        display_cols = [
            'mls_id', 'address_number', 'street_name', 'municipality',
            'price', 'bedrooms', 'bathrooms', 'size_sqft', 'house_cat',
            'pool_mentioned', 'removal_date'
        ]
    else:
        # For current listings
        display_cols = [
            'mls_id', 'address_number', 'street_name', 'municipality',
            'price', 'bedrooms', 'bathrooms', 'size_sqft', 'house_cat',
            'pool_mentioned', 'date_collected'
        ]
    
    display_cols = [col for col in display_cols if col in filtered_df.columns]
    
    # Format the dataframe for display
    display_df = filtered_df[display_cols].copy()
    
    # Format price
    if 'price' in display_df.columns:
        display_df['price'] = display_df['price'].apply(
            lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A"
        )
    
    # Format dates
    if 'removal_date' in display_df.columns:
        display_df['removal_date'] = display_df['removal_date'].apply(
            lambda x: str(x)[:10] if pd.notna(x) else ""
        )
    
    # Display table
    column_config = {
        "mls_id": "MLS ID",
        "address_number": "Address #",
        "street_name": "Street",
        "municipality": "Municipality",
        "price": "Price",
        "bedrooms": "Beds",
        "bathrooms": "Baths",
        "size_sqft": "Sq Ft",
        "house_cat": "Type",
        "pool_mentioned": "Pool Mentioned",
        "date_collected": "Date Collected",
        "removal_date": "Sold Date"
    }
    
    st.dataframe(
        display_df,
        hide_index=True,
        column_config=column_config
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label=f"Download {title} (CSV)",
        data=csv,
        file_name=f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        key=f"download_{tab_key}"
    )


# Main app
st.title("Pool Listings Management")
st.markdown("---")

# Load data
matched_current, matched_removed, deduped_current, deduped_removed = load_listings_data()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    f"Recently Sold (Matched) - {len(matched_removed)}",
    f"Recently Sold (Probable) - {len(deduped_removed)}",
    f"Currently Listed (Matched) - {len(matched_current)}",
    f"Currently Listed (Probable) - {len(deduped_current)}"
])

with tab1:
    st.markdown("""
    **Matched Removed Listings**: Properties that were recently sold (within 365 days) 
    AND are confirmed in our pool database. These are high-confidence leads.
    """)
    display_listings_table(
        matched_removed,
        "Recently Sold - Confirmed Pool Addresses",
        tab_key="matched_removed"
    )

with tab2:
    st.markdown("""
    **Probable Removed Listings**: Properties that mention pools in their listing 
    description but are not yet in our database. These are potential new pool discoveries.
    """)
    display_listings_table(
        deduped_removed,
        "Recently Sold - Pool Probable",
        tab_key="deduped_removed"
    )

with tab3:
    st.markdown("""
    **Matched Current Listings**: Properties currently on the market 
    that are confirmed in our pool database. Monitor for price changes or removal.
    """)
    display_listings_table(
        matched_current,
        "Currently Listed - Confirmed Pool Addresses",
        tab_key="matched_current"
    )

with tab4:
    st.markdown("""
    **Probable Current Listings**: Properties currently on the market that mention pools.
    These could be added to our database once verified.
    """)
    display_listings_table(
        deduped_current,
        "Currently Listed - Pool Probable",
        tab_key="deduped_current"
    )

# Footer
st.markdown("---")
st.info("""
**Tips**: 
- Use date range filter to focus on recently sold properties
- Download filtered data as CSV for external analysis
- Data is refreshed weekly when the collection script runs
- Focus on properties sold within the last 60-90 days for best results
""")
