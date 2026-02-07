import pandas as pd
import requests
import io

def download_zip_mapping():
    url = "https://raw.githubusercontent.com/scpike/us-state-county-zip/master/geo-data.csv"
    try:
        print(f"Downloading data from {url}...")
        response = requests.get(url)
        response.raise_for_status()
        
        # Read into dataframe
        df = pd.read_csv(io.StringIO(response.text))
        
        # Filter for CA
        # The columns seem to be state_fips,state,state_abbr,zipcode,county,city
        # Let's check headers if possible, but based on repo description:
        # state_fips,state,state_abbr,zipcode,county,city
        
        # If headers are different, we might need to adjust. Let's inspect first few lines
        print("Columns:", df.columns.tolist())
        
        ca_df = df[df['state'] == 'CA'].copy() # attempting 'state' or 'state_abbr'
        if ca_df.empty:
             ca_df = df[df['state_abbr'] == 'CA'].copy()
        
        if ca_df.empty:
            print("Could not filter for CA. Check column names.")
            print(df.head())
            return

        # Save to csv
        ca_df.to_csv('outputs/ca_zip_county.csv', index=False)
        print("Saved CA zip mapping to outputs/ca_zip_county.csv")
        print(ca_df.head())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    download_zip_mapping()
