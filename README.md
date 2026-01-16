# Pool CRM Streamlit Application

A customer relationship management (CRM) system for pool supply and service companies to track real estate listings with pools in the Greater Toronto Area.

## Features

### Page 1: Overview
- **Market Statistics Dashboard**: Key metrics including total pool addresses, current listings, recent sales, and market activity
- **Interactive Geographic Map**: 
  - Bounding box showing data collection area
  - Blue dots: Known pool addresses in database
  - Orange dots (50% opacity): Currently listed properties with pools
  - Red dots (100% opacity): Recently sold properties with pools (last 365 days)
  - Hover tooltips with property details
- **Insights Panel**: Opportunity scores and sales lead summaries

### Page 2: Listings Management
Four categorized tabs for different listing types:
1. **Recently Sold (Matched)**: Confirmed pool addresses that recently sold
2. **Recently Sold (Probable)**: Properties mentioning pools that recently sold
3. **Currently Listed (Matched)**: Confirmed pool addresses on the market
4. **Currently Listed (Probable)**: Properties mentioning pools currently listed

Features per tab:
- Advanced filtering (price, bedrooms, municipality)
- Sortable data tables
- **Outreach Tracking** for sold listings:
  - Checkbox to mark properties as "reached out"
  - Automatic date stamping
  - Persistent storage across sessions
  - Recommended reach-out dates (60 days post-sale)
- CSV download functionality

## Installation

### Prerequisites
- Python 3.8+
- PostgreSQL database access (for data collection)

### Setup

1. Install required packages:
```bash
pip install -r requirements.txt
```

2. Configure environment variables in `app_data/utils/.env`:
```env
LAT_MIN = 43.7
LAT_MAX = 43.9
LON_MIN = -80.5
LON_MAX = -79.5
DATABASE_URL=postgresql://user:password@host/database
DISTILLED_URL=postgresql://user:password@localhost/master_pool_db_distilled
```

## Usage

### Running the Application

Start the Streamlit app:
```bash
cd app
streamlit run app.py
```

The application will be available at:
- Local: http://localhost:8501
- Network: http://[your-ip]:8501

### Data Collection

The application uses static CSV files that are refreshed weekly. To update data:

```bash
cd app/app_data/utils
python get_listings_data.py
```

This script will:
1. Fetch current and removed listings from the real estate database
2. Cross-reference with known pool addresses
3. Preserve existing user interaction data (reached_out flags)
4. Generate updated CSV files and summary JSON
5. Include pool metadata (type, cover type, discovery date)

### Data Files

Generated data files in `app/app_data/`:
- `listings_summary.json`: Aggregate statistics and bounding box
- `address_df.csv`: All pool addresses with metadata
- `matched_current_listings.csv`: Currently listed, confirmed pools
- `matched_removed_listings.csv`: Recently sold, confirmed pools
- `deduped_current_less_matched.csv`: Currently listed, probable pools
- `deduped_removed_less_matched.csv`: Recently sold, probable pools
- `user_interactions.json`: User outreach tracking data (persists across refreshes)

## Architecture

```
streamlit_demo_app/app/
├── app.py                          # Main page (Overview)
├── pages/
│   └── listings.py                 # Listings management page
├── app_data/
│   ├── *.csv                       # Data files
│   ├── listings_summary.json       # Summary statistics
│   ├── user_interactions.json      # User tracking data
│   └── utils/
│       ├── .env                    # Configuration
│       └── get_listings_data.py    # Data collection script
├── requirements.txt
└── README.md
```

## Workflow

### Weekly Data Refresh Process

1. Run data collection script:
   ```bash
   python app_data/utils/get_listings_data.py
   ```

2. Script automatically:
   - Fetches latest listings
   - Merges with existing user interactions
   - Updates all CSV files
   - Preserves "reached out" flags

3. Application automatically loads new data on next visit
   - User tracking persists across refreshes
   - No manual intervention needed

### User Interaction Flow

1. Navigate to "Listings" page
2. Open "Recently Sold" tabs
3. Review properties and filter as needed
4. Check "Reached Out" for contacted properties
5. Click "💾 Save Outreach Data" to persist changes
6. Data survives weekly refreshes

## Technologies

- **Streamlit**: Web application framework
- **PyDeck**: Interactive map visualization (deck.gl)
- **Pandas**: Data manipulation
- **PostgreSQL**: Data source
- **SQLAlchemy**: Database ORM

## Map Visualization

The map uses PyDeck (deck.gl) with:
- **ScatterplotLayer**: For property markers
- **PolygonLayer**: For bounding box outline
- Dynamic coloring based on listing status
- Interactive tooltips with property details
- Auto-centering and zoom based on data extent

## Color Coding

- 🔵 **Blue**: Pool addresses in database
- 🟠 **Orange** (50% opacity): Currently listed properties
- 🔴 **Red** (100% opacity): Recently sold properties

## Business Use Case

This CRM helps pool service companies:

1. **Identify Sales Opportunities**: Track properties with pools that recently sold
2. **Time Outreach**: Recommended contact dates (60 days post-sale)
3. **Market Intelligence**: Monitor current listings and market activity
4. **Lead Management**: Organize and track customer outreach
5. **Database Growth**: Discover new pool addresses from listings

## Support

For issues or questions, contact your development team or review the source code in the repository.

## License

Internal use only - Pool Service CRM
# Demo-Pool-CRM-BWP
# Pool_CRM_Demo_Guelph
# Pool_CRM_Demo_Guelph
