import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import os

# Page configuration
st.set_page_config(
    page_title="Pool CRM - Overview",
    layout="wide"
)

# Data loading with caching
@st.cache_data
def load_data():
    """Load all data files"""
    base_path = os.path.join(os.path.dirname(__file__), 'app_data')
    
    # Load summary
    with open(os.path.join(base_path, 'listings_summary.json'), 'r') as f:
        summary = json.load(f)
    
    # Load CSV files
    address_df = pd.read_csv(os.path.join(base_path, 'address_df.csv'))
    matched_current = pd.read_csv(os.path.join(base_path, 'matched_current_listings.csv'))
    matched_removed = pd.read_csv(os.path.join(base_path, 'matched_removed_listings.csv'))
    deduped_current = pd.read_csv(os.path.join(base_path, 'deduped_current_less_matched.csv'))
    deduped_removed = pd.read_csv(os.path.join(base_path, 'deduped_removed_less_matched.csv'))
    
    return summary, address_df, matched_current, matched_removed, deduped_current, deduped_removed

# Load data
summary, address_df, matched_current, matched_removed, deduped_current, deduped_removed = load_data()

# Title and header
st.title("Pool CRM - Overview")
st.markdown("---")

# Metrics row
col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Total Pool Addresses", f"{summary['total_addresses_in_db']:,}")

with col2:
    st.metric("Current Listings", summary['total_current_listings_pool_probable'])

with col3:
    st.metric("Recent Sales (365d)", summary['total_removed_listings_pool_probable'])

with col4:
    st.metric("Listed (Matched)", summary['total_matched_addresses_current_listings'])

with col5:
    st.metric("Sold (Matched)", summary['total_matched_addresses_removed_listings'])

with col6:
    market_activity = summary['proportion_addresses_listed_and_recently_sold'] * 100
    st.metric("Market Activity", f"{market_activity:.2f}%")

st.markdown("---")

# Prepare map data
def prepare_map_data():
    """Prepare unified dataframe for map visualization"""
    
    # All pool addresses (blue)
    all_pools = address_df.copy()
    all_pools['category'] = 'Pool Address'
    all_pools['color'] = [[70, 130, 180, 180]] * len(all_pools)  # Steel blue
    all_pools['tooltip'] = all_pools.apply(
        lambda row: f"{row['address_number']} {row['street_name']}<br>"
                   f"Type: {row.get('pool_type', 'Unknown')}<br>"
                   f"Cover: {row.get('cover_type', 'Unknown')}", 
        axis=1
    )
    all_pools['radius'] = 30
    
    # Matched current listings (orange, 50% opacity)
    matched_curr = matched_current.copy()
    matched_curr['category'] = 'Currently Listed'
    matched_curr['color'] = [[255, 165, 0, 128]] * len(matched_curr)  # Orange, 50% opacity
    
    def create_current_tooltip(row):
        try:
            addr_num = row.get('address_number', 'N/A')
            street = row.get('street_name', 'N/A')
            price = row.get('price', 0)
            beds = row.get('bedrooms', 'N/A')
            baths = row.get('bathrooms', 'N/A')
            
            return (f"{addr_num} {street}<br>"
                   f"Price: ${float(price):,.0f}<br>"
                   f"Beds: {beds} | Baths: {baths}<br>"
                   f"LISTED")
        except:
            return f"{row.get('address_number', 'N/A')} {row.get('street_name', 'N/A')}<br>LISTED"
    
    matched_curr['tooltip'] = matched_curr.apply(create_current_tooltip, axis=1)
    matched_curr['radius'] = 50
    
    # Matched removed listings (red, 100% opacity)
    matched_rem = matched_removed.copy()
    matched_rem['category'] = 'Recently Sold'
    matched_rem['color'] = [[220, 20, 60, 255]] * len(matched_rem)  # Crimson, 100% opacity
    
    def create_removed_tooltip(row):
        try:
            addr_num = row.get('address_number', 'N/A')
            street = row.get('street_name', 'N/A')
            price = row.get('price', 0)
            beds = row.get('bedrooms', 'N/A')
            baths = row.get('bathrooms', 'N/A')
            removal_date = str(row.get('removal_date', 'N/A'))[:10]
            
            return (f"{addr_num} {street}<br>"
                   f"Last Price: ${float(price):,.0f}<br>"
                   f"Beds: {beds} | Baths: {baths}<br>"
                   f"Sold: {removal_date}")
        except:
            return f"{row.get('address_number', 'N/A')} {row.get('street_name', 'N/A')}<br>SOLD"
    
    matched_rem['tooltip'] = matched_rem.apply(create_removed_tooltip, axis=1)
    matched_rem['radius'] = 50
    
    # Combine all data
    combined = pd.concat([
        all_pools[['lat', 'lon', 'category', 'color', 'tooltip', 'radius']],
        matched_curr[['lat', 'lon', 'category', 'color', 'tooltip', 'radius']],
        matched_rem[['lat', 'lon', 'category', 'color', 'tooltip', 'radius']]
    ], ignore_index=True)
    
    return combined

map_data = prepare_map_data()

# Create bounding box polygon
bbox = summary.get('bbox', {
    'lat_min': 43.481386,
    'lat_max': 43.627526,
    'lon_min': -80.333707,
    'lon_max': -80.105133
})

bbox_polygon = pd.DataFrame([{
    'polygon': [
        [bbox['lon_min'], bbox['lat_min']],
        [bbox['lon_max'], bbox['lat_min']],
        [bbox['lon_max'], bbox['lat_max']],
        [bbox['lon_min'], bbox['lat_max']],
        [bbox['lon_min'], bbox['lat_min']]
    ]
}])

# Calculate center point for map
center_lat = (bbox['lat_min'] + bbox['lat_max']) / 2
center_lon = (bbox['lon_min'] + bbox['lon_max']) / 2

# Create pydeck layers
scatterplot_layer = pdk.Layer(
    "ScatterplotLayer",
    data=map_data,
    get_position=["lon", "lat"],
    get_fill_color="color",
    get_radius="radius",
    pickable=True,
    auto_highlight=True,
)

polygon_layer = pdk.Layer(
    "PolygonLayer",
    data=bbox_polygon,
    get_polygon="polygon",
    get_fill_color=[0, 0, 0, 0],
    get_line_color=[255, 255, 255, 200],
    line_width_min_pixels=3,
    pickable=False,
)

# Set up view state
view_state = pdk.ViewState(
    latitude=center_lat,
    longitude=center_lon,
    zoom=10.5,
    pitch=0,
)

# Create deck
deck = pdk.Deck(
    layers=[polygon_layer, scatterplot_layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>{tooltip}</b>",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    },
    map_style="road",
)

# Display map
st.subheader("Geographic Distribution")
st.pydeck_chart(deck)

# Legend
st.markdown("### Legend")
col_leg1, col_leg2, col_leg3 = st.columns(3)

with col_leg1:
    st.markdown("**Pool Address** - Known pool location in database (Blue)")

with col_leg2:
    st.markdown("**Currently Listed** - Pool property on market (Orange, 50% opacity)")

with col_leg3:
    st.markdown("**Recently Sold** - Sold within last 365 days (Red)")

st.markdown("---")

# Additional insights
st.subheader("Insights")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.info(f"""
    **Opportunity Score**: {summary['total_removed_listings_pool_probable']} properties with pools sold recently 
    are potential leads for pool maintenance contracts or upgrades.
    """)

with insights_col2:
    total_opportunities = (
        summary['total_matched_addresses_removed_listings'] + 
        summary['total_removed_listings_pool_probable']
    )
    st.success(f"""
    **Total Sales Leads**: {total_opportunities} properties (matched + probable) 
    available for outreach campaigns.
    """)
