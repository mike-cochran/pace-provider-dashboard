## SCRIPT TO DOWNLOAD AND PROCESS ALL CMS ENROLLMENT FILES AND COMBINE THEM INTO ONE FILE

import pandas as pd
import requests
import zipfile
import os
import glob
import re

from dicts.enrollment_dicts import enrl_file_dict

# Get current working directory from parentfolder of folder containing scripts
directory = os.getcwd()

# Create function to download and unzip pfs files from CMS website
def download_and_unzip(file_list):

    # Loop through the list of files and download and unzip each one
    for file in file_list:
        file_name = enrl_file_dict[file]
        print(f'Downloading enrollment for: {file_name}')

        save_path = directory + fr'\raw_data\enrollment\{file}'
        print(save_path)
        os.makedirs(save_path, exist_ok=True)

        try:
            # Set CMS url
            if int(file) >= 202510 or file == '202307':
                url = 'https://www.cms.gov/files/zip/' + file_name
            else:
                url = 'https://www.cms.gov/files/zip/ma-enrollment-state/county/' + file_name

            # Send the HTTP request to download the file
            print(url)
            response = requests.get(url)
            response.raise_for_status()
            # Define the complete path including the file name
            complete_save_path = os.path.join(save_path, file_name)

            # Open the specified file path in binary write mode and save the content
            if os.path.exists(complete_save_path):
                print(f"File already exists at {complete_save_path}")
            else:
                with open(complete_save_path, 'wb') as file_name:
                    file_name.write(response.content)
                print(f"File successfully downloaded and saved to {complete_save_path}")

            # Define the extraction path
            extract_path = save_path
            # Check if the zip file has already been unzipped
            if os.path.exists(extract_path):
                non_zip_files_exist = any(
                    entry for entry in os.scandir(extract_path)
                    if entry.is_file() and not entry.name.endswith('.zip')
                )
                if non_zip_files_exist:
                    print(f"Files already extracted to {extract_path}")
                    continue

            # Check if the file is a zip file
            if zipfile.is_zipfile(complete_save_path):
                with zipfile.ZipFile(complete_save_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                    print(f"File successfully unzipped to {extract_path}")
            else:
                print(f"{complete_save_path} is not a zip file")

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")

def clean_and_combine(file_list, states):

    # Create empty dataframe for appending
    combined_enrl = pd.DataFrame()
    combined_total_ma = pd.DataFrame()
    combined_national_ma = pd.DataFrame()

    # Process each ratebooks file and combine
    for enrl_file in file_list:
        year = enrl_file[:4]
        month = enrl_file[4:]
        print(enrl_file)

        # Read in csv
        if enrl_file == '202312': name = f'SCC_Enrollment_MA_{year}_{month}'
        else: name = f'SCP_Enrollment_MA_{year}_{month}'
        file_name = (directory + f'/raw_data/enrollment/{enrl_file}/{name}/{name}.csv')
        enrl_df = pd.read_csv(file_name)

        # Process enrollment file
        enrl_df.columns = enrl_df.columns.str.upper()

        # Limit to relevant columns
        keep_cols = ['STATE', 'COUNTY', 'PLAN TYPE', 'ENROLLED']
        enrl_df = enrl_df[keep_cols]
        
        # Clean up zero enrolled values for calculation
        enrl_df['ENROLLED'] = pd.to_numeric(enrl_df['ENROLLED'].replace('.',0), errors='coerce').fillna(0)
        
        # --- Process Total MA Enrollment (NATIONAL & STATE) ---
        # 1. State Level (for CA)
        state_ma_df = enrl_df[enrl_df['STATE'].isin(states)].groupby(['STATE', 'COUNTY'], as_index=False)['ENROLLED'].sum()
        state_ma_df['DATE'] = pd.to_datetime(f"{year}-{month}-01")
        combined_total_ma = pd.concat([combined_total_ma, state_ma_df], ignore_index=True)
        
        # 2. National Level
        national_ma_sum = enrl_df['ENROLLED'].sum()
        # Create a tiny DF to append
        nat_df = pd.DataFrame({'DATE': [pd.to_datetime(f"{year}-{month}-01")], 'NATIONAL_MA_ENROLLED': [national_ma_sum]})
        combined_national_ma = pd.concat([combined_national_ma, nat_df], ignore_index=True)
        # -----------------------------------

        # Limit to selected states and localities
        enrl_df = enrl_df[enrl_df['STATE'].isin(states)]

        # Limit to PACE
        enrl_df = enrl_df[enrl_df['PLAN TYPE'] == 'National PACE']

        # Create DATE column
        enrl_df['DATE'] = pd.to_datetime(f"{year}-{month}-01")

        # Create combined pfs df
        combined_enrl = pd.concat([combined_enrl, enrl_df], ignore_index=True)
        print(enrl_file + " enrollment file processed")

    # Deal with duplicate rows by summing enrollment
    combined_enrl = combined_enrl.groupby(['STATE', 'COUNTY', 'PLAN TYPE', 'DATE'], as_index=False)['ENROLLED'].sum()
    combined_total_ma = combined_total_ma.groupby(['STATE', 'COUNTY', 'DATE'], as_index=False)['ENROLLED'].sum()
    combined_national_ma = combined_national_ma.groupby('DATE', as_index=False)['NATIONAL_MA_ENROLLED'].sum()

    # Save combined results
    combined_enrl.to_excel(directory + r'\outputs\Combined enrollment.xlsx', index=False)
    combined_total_ma.to_excel(directory + r'\outputs\MA_Enrollment_Total.xlsx', index=False)
    combined_national_ma.to_csv(directory + r'\outputs\MA_Enrollment_National.csv', index=False)
    print("Saved National MA Enrollment to outputs/MA_Enrollment_National.csv")
    print(combined_enrl)

    return combined_enrl