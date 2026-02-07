
import pandas as pd
import json
from urllib.request import urlopen

# Load Enrollment Data
try:
    print("Loading enrollment data...")
    df = pd.read_excel('outputs/Combined enrollment.xlsx', engine='openpyxl')
    unique_counties = sorted(df['COUNTY'].unique().astype(str))
    print(f"Loaded {len(unique_counties)} unique counties from Excel.")
    print("Sample counties:", unique_counties[:5])
except Exception as e:
    print(f"Error loading Excel: {e}")
    unique_counties = []

# Load GeoJSON
try:
    print("\nLoading GeoJSON...")
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/california-counties.geojson'
    with urlopen(url) as response:
        geojson = json.load(response)
    
    geojson_names = sorted([feature['properties']['name'] for feature in geojson['features']])
    print(f"Loaded {len(geojson_names)} counties from GeoJSON.")
    print("Sample GeoJSON names:", geojson_names[:5])
    
    # Check intersection
    intersection = set(unique_counties).intersection(set(geojson_names))
    print(f"\nMatching counties: {len(intersection)}")
    
    missing_in_geojson = set(unique_counties) - set(geojson_names)
    if missing_in_geojson:
        print(f"Counties in Excel but NOT in GeoJSON: {len(missing_in_geojson)}")
        print(list(missing_in_geojson)[:10])
    
    missing_in_excel = set(geojson_names) - set(unique_counties)
    if missing_in_excel:
        print(f"Counties in GeoJSON but NOT in Excel: {len(missing_in_excel)}")
        print(list(missing_in_excel)[:10])

except Exception as e:
    print(f"Error loading GeoJSON: {e}")
