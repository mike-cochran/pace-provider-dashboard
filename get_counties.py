import pandas as pd
import openpyxl

def get_top_counties():
    file_path = 'outputs/Combined enrollment.xlsx'
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        # Sum enrollment by county
        county_totals = df.groupby('COUNTY')['ENROLLED'].sum().sort_values(ascending=False)
        top_counties = county_totals.head(10).index.tolist()
        print("Top Counties:", top_counties)
        return top_counties
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_top_counties()
