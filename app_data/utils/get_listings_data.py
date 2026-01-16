from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

#load the .env file
load_dotenv()



DATABASE_URL = (
    "postgresql://neondb_owner:npg_Ss2uYoZeUHt3"
    "@ep-misty-bread-a4s7ya4s-pooler.us-east-1.aws.neon.tech/"
    "neondb?sslmode=require&channel_binding=require"
)

lat_max = os.getenv("LAT_MAX")
lat_min = os.getenv("LAT_MIN")
lon_max = os.getenv("LON_MAX")
lon_min = os.getenv("LON_MIN")
BOUNDING_BOX = {
    "lat_max": float(lat_max),
    "lat_min": float(lat_min),
    "lon_max": float(lon_max),
    "lon_min": float(lon_min),
}
LAT_MAX = BOUNDING_BOX["lat_max"]
LAT_MIN = BOUNDING_BOX["lat_min"]
LON_MAX = BOUNDING_BOX["lon_max"]
LON_MIN = BOUNDING_BOX["lon_min"]




def query_listings_in_bbox(min_lat, max_lat, min_lon, max_lon, days_back=365):
    """
    Query listings within a bounding box.
    
    Args:
        min_lat: Minimum latitude
        max_lat: Maximum latitude
        min_lon: Minimum longitude
        max_lon: Maximum longitude
        days_back: Days to look back for removed listings (default 30)
    
    Returns:
        tuple: (current_listings_df, removed_listings_df)
    """
    conn = psycopg2.connect(DATABASE_URL)
    
    try:
        # Query current listings
        current_query = """
            SELECT 
                mls_id,
                date_collected,
                description,
                bedrooms,
                bathrooms,
                size_sqft,
                stories,
                house_cat,
                price,
                address_number,
                street_name,
                full_street_name,
                locality,
                municipality,
                province_state,
                postal_code,
                pool_mentioned,
                lat,
                lon
            FROM listing
            WHERE lat BETWEEN %s AND %s
              AND lon BETWEEN %s AND %s
            ORDER BY date_collected DESC;
        """
        
        current_listings = pd.read_sql_query(
            current_query,
            conn,
            params=(min_lat, max_lat, min_lon, max_lon)
        )
        
        # Query recently removed listings from the listing_removal table
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        removed_query = """
            SELECT 
                l.mls_id,
                l.date_collected,
                l.description,
                l.bedrooms,
                l.bathrooms,
                l.size_sqft,
                l.stories,
                l.house_cat,
                l.price,
                l.address_number,
                l.street_name,
                l.full_street_name,
                l.locality,
                l.municipality,
                l.province_state,
                l.postal_code,
                l.pool_mentioned,
                l.lat,
                l.lon,
                r.removal_id,
                r.removal_date
            FROM listing_removal r
            JOIN listing l ON l.mls_id = r.mls_id
            WHERE r.removal_date >= %s
              AND l.lat BETWEEN %s AND %s
              AND l.lon BETWEEN %s AND %s
            ORDER BY r.removal_date DESC;
        """
        
        removed_listings = pd.read_sql_query(
            removed_query,
            conn,
            params=(cutoff_date, min_lat, max_lat, min_lon, max_lon)
        )
        
        return current_listings, removed_listings
        
    finally:
        conn.close()


# Example usage - adjust bounding box for your area of interest
# Toronto downtown area example
def get_current_and_removed_listings():

    current, removed = query_listings_in_bbox(LAT_MIN, LAT_MAX, LON_MIN, LON_MAX, days_back=365)
    removed_with_pool = removed[removed['pool_mentioned'] == True]
    def drop_duplicates(df):
        #if street name contains letters and numbers, and they are the same (standardized to lower case) except for case, consider them duplicates and drop one of them.
        df['street_name_std'] = df['street_name'].str.lower()
        df_deduped = df.drop_duplicates(subset=['street_name_std'])
        return df_deduped
    deduped_removed = drop_duplicates(removed_with_pool)

    #add a reccomended reachout date by taking removal_date and adding 60 days to it
    deduped_removed['recommended_reachout_date'] = deduped_removed['removal_date'] + pd.Timedelta(days=60)
    
    deduped_current = drop_duplicates(current)
    
    return deduped_current, deduped_removed

DISTILLED_DB = "master_pool_db_distilled"
DISTILLED_URL = f"postgresql://james:147896@localhost/{DISTILLED_DB}"
engine_distilled = create_engine(DISTILLED_URL)

def get_pool_addresses():
    engine_distilled = create_engine(DISTILLED_URL)
    with engine_distilled.connect() as conn:
        # Get addresses with pool information
        addresses_df = pd.read_sql_query(
            text("""
            SELECT a.*, p.pool_type, p.cover_type, p.discovery_date
            FROM addresses a
            LEFT JOIN pool p ON a.pool_id = p.pool_id
            WHERE a.lat BETWEEN :min_lat AND :max_lat
            AND a.lon BETWEEN :min_lon AND :max_lon
            """),
            conn,
            params={
                'min_lat': LAT_MIN,
                'max_lat': LAT_MAX,
                'min_lon': LON_MIN,
                'max_lon': LON_MAX
            }
        )
    addresses_df['address_std'] = addresses_df['address_number'].astype(str) + ' ' + addresses_df['street_name'].str.lower()

    return addresses_df

def cross_reference_removed_with_addresses(deduped_removed, addresses_df):
    matched_addresses = deduped_removed[deduped_removed['street_name_std'].isin(addresses_df['address_std'])]
    return matched_addresses

def get_listings_less_matched(deduped_removed, matched_addresses):
    deduped_removed_less_matched = deduped_removed[~deduped_removed['street_name_std'].isin(matched_addresses['street_name_std'])]
    return deduped_removed_less_matched


def load_user_interactions():
    """Load user interaction data (reached_out flags)"""
    interactions_file = os.path.join(os.path.dirname(__file__), '..', 'user_interactions.json')
    if os.path.exists(interactions_file):
        with open(interactions_file, 'r') as f:
            return json.load(f)
    return {}


def save_user_interactions(interactions):
    """Save user interaction data"""
    interactions_file = os.path.join(os.path.dirname(__file__), '..', 'user_interactions.json')
    with open(interactions_file, 'w') as f:
        json.dump(interactions, f, indent=4, default=str)


def apply_reached_out_flag(removed_df):
    """Apply reached_out flag from user interactions to removed listings"""
    interactions = load_user_interactions()
    removed_df['reached_out'] = removed_df['mls_id'].apply(
        lambda x: interactions.get(str(x), {}).get('reached_out', False)
    )
    removed_df['date_reached'] = removed_df['mls_id'].apply(
        lambda x: interactions.get(str(x), {}).get('date_reached', None)
    )
    return removed_df



if __name__ == "__main__":
    current_listings, removed_listings = get_current_and_removed_listings()
    addresses_df = get_pool_addresses()
    
    # Apply reached_out flags from previous user interactions
    removed_listings = apply_reached_out_flag(removed_listings)
    
    matched_addresses = cross_reference_removed_with_addresses(removed_listings, addresses_df)
    deduped_removed_less_matched = get_listings_less_matched(removed_listings, matched_addresses)

    matched_addresses_current_listings = cross_reference_removed_with_addresses(current_listings, addresses_df)
    deduped_current_less_matched = get_listings_less_matched(current_listings, matched_addresses_current_listings)

    #calculate summary values
    summary = {
        'total_current_listings_pool_probable': len(deduped_current_less_matched),
        'total_removed_listings_pool_probable': len(deduped_removed_less_matched),
        'total_matched_addresses_current_listings': len(matched_addresses_current_listings),
        'total_matched_addresses_removed_listings': len(matched_addresses),
        'total_addresses_in_db': len(addresses_df),
        'proportion_addresses_listed_and_recently_sold': (len(matched_addresses) + len(matched_addresses_current_listings)) / len(addresses_df) if len(addresses_df) > 0 else 0,
        'bbox': {
            'lat_min': LAT_MIN,
            'lat_max': LAT_MAX,
            'lon_min': LON_MIN,
            'lon_max': LON_MAX
        }
    }

    import json

    summary_json = json.dumps(summary, indent=4, default=str)
    #write to json file in ../
    with open(os.path.join(os.path.dirname(__file__), '..', 'listings_summary.json'), 'w') as f:
        f.write(summary_json)

    #write matched_addresses to csv in ../
    matched_addresses.to_csv(os.path.join(os.path.dirname(__file__), '..', 'matched_removed_listings.csv'), index=False)
    matched_addresses_current_listings.to_csv(os.path.join(os.path.dirname(__file__), '..', 'matched_current_listings.csv'), index=False)
    deduped_removed_less_matched.to_csv(os.path.join(os.path.dirname(__file__), '..', 'deduped_removed_less_matched.csv'), index=False)
    deduped_current_less_matched.to_csv(os.path.join(os.path.dirname(__file__),'..', 'deduped_current_less_matched.csv'), index=False)
    addresses_df.to_csv(os.path.join(os.path.dirname(__file__), '..', 'address_df.csv'), index=False)