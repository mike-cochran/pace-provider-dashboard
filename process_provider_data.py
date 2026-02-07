import pandas as pd
import os

def process_provider_data():
    print("Loading data...")
    # 1. Load Zip Mapping
    zip_map = pd.read_csv('outputs/ca_zip_county.csv')
    # Use Zip as string to ensure matching
    zip_map['zipcode'] = zip_map['zipcode'].astype(str)
    
    # 2. Load Enrollment Data to get Target Counties and Enrollment counts
    try:
        enrollment_df = pd.read_excel('outputs/Combined enrollment.xlsx', engine='openpyxl')
        # Get latest enrollment per county
        latest_date = enrollment_df['DATE'].max()
        latest_enrollment = enrollment_df[enrollment_df['DATE'] == latest_date]
        # Summarize by County
        county_enrollment = latest_enrollment.groupby('COUNTY')['ENROLLED'].sum().reset_index()
        
        # Identify Top 10 Counties
        top_counties = county_enrollment.sort_values('ENROLLED', ascending=False).head(10)['COUNTY'].tolist()
        print(f"Top 10 Counties: {top_counties}")
        
    except Exception as e:
        print(f"Error loading enrollment: {e}")
        return

    # 2b. Load Total MA Enrollment Data for Gap Analysis
    try:
        ma_enrollment_df = pd.read_excel('outputs/MA_Enrollment_Total.xlsx', engine='openpyxl')
        # Get latest enrollment per county
        latest_ma_date = ma_enrollment_df['DATE'].max()
        latest_ma_enrollment = ma_enrollment_df[ma_enrollment_df['DATE'] == latest_ma_date]
        # Summarize by County
        ma_county_enrollment = latest_ma_enrollment.groupby('COUNTY')['ENROLLED'].sum().reset_index()
        ma_county_enrollment.rename(columns={'ENROLLED': 'MA_ENROLLED'}, inplace=True)
        
        ma_county_enrollment.to_csv('outputs/ma_county_enrollment.csv', index=False)
        print("Saved Total MA Enrollment to 'outputs/ma_county_enrollment.csv'")
        
    except Exception as e:
        print(f"Error loading MA enrollment: {e}")
        # Use existing enrollment as fallback if MA file missing (should not happen if processed correctly)
        county_enrollment.rename(columns={'ENROLLED': 'MA_ENROLLED'}, inplace=True)
        county_enrollment.to_csv('outputs/ma_county_enrollment.csv', index=False)

    # 3. Load Provider Data
    # Use chunking if file is huge, but let's try reading relevant columns first
    # Columns needed: Rndrng_Prvdr_Zip5, Rndrng_Prvdr_State_Abrvtn, Rndrng_Prvdr_Type, Tot_Benes, Tot_Mdcr_Pymt_Amt, Rndrng_NPI, Rndrng_Prvdr_Last_Org_Name, Rndrng_Prvdr_First_Name
    cols = [
        'Rndrng_NPI', 'Rndrng_Prvdr_Last_Org_Name', 'Rndrng_Prvdr_First_Name', 
        'Rndrng_Prvdr_Zip5', 'Rndrng_Prvdr_State_Abrvtn', 'Rndrng_Prvdr_Type', 
        'Tot_Benes', 'Tot_Mdcr_Pymt_Amt'
    ]
    
    provider_file = 'raw_data/mc_phys_prov.csv'
    if not os.path.exists(provider_file):
        print(f"File not found: {provider_file}")
        return

    print("Reading provider data...")
    # Check text encoding? Default utf-8 usually works or latin1
    try:
        df_prov = pd.read_csv(provider_file, usecols=cols, low_memory=False, encoding='ISO-8859-1') # CMS data often has encoding issues
    except:
        df_prov = pd.read_csv(provider_file, usecols=cols, low_memory=False)

    print(f"Total Providers loaded: {len(df_prov)}")

    # 4. Filter for CA
    df_ca = df_prov[df_prov['Rndrng_Prvdr_State_Abrvtn'] == 'CA'].copy()
    print(f"CA Providers: {len(df_ca)}")
    
    # 5. Map Zip to County
    # Ensure Zip is string and 5 digits
    df_ca['zipcode'] = df_ca['Rndrng_Prvdr_Zip5'].astype(str).str.zfill(5)
    
    # Merge
    # zip_map has 'zipcode', 'county'
    df_merged = pd.merge(df_ca, zip_map[['zipcode', 'county']], on='zipcode', how='left')
    
    # Filter for Target Counties
    df_target = df_merged[df_merged['county'].isin(top_counties)].copy()
    print(f"Providers in Target Counties: {len(df_target)}")
    
    # Save Detailed Data for Dashboard Interactivity
    # Columns to keep
    keep_cols = ['Rndrng_NPI', 'Rndrng_Prvdr_Last_Org_Name', 'Rndrng_Prvdr_First_Name', 
                 'Rndrng_Prvdr_Type', 'county', 'zipcode', 'Tot_Mdcr_Pymt_Amt', 'Tot_Benes']
    
    df_target[keep_cols].to_csv('outputs/provider_data_detailed.csv', index=False)
    print("Saved detailed provider data to 'outputs/provider_data_detailed.csv'")

    # --- KPI CALCULATIONS (STATE BENCHMARKS ONLY) ---
    
    # We only need pre-calculated STATE stats. Local stats will be dynamic in Dash.
    # Calculate weighted average cost per bene for CA (All CA providers)
    ca_specialty = df_merged.groupby('Rndrng_Prvdr_Type')[['Tot_Mdcr_Pymt_Amt', 'Tot_Benes']].sum().reset_index()
    ca_specialty['State_Avg_Cost'] = ca_specialty['Tot_Mdcr_Pymt_Amt'] / ca_specialty['Tot_Benes']
    
    ca_specialty.to_csv('outputs/kpi_state_benchmarks.csv', index=False)
    print("Saved state benchmarks to 'outputs/kpi_state_benchmarks.csv'")
    
    print("Processing complete.")

if __name__ == "__main__":
    process_provider_data()
