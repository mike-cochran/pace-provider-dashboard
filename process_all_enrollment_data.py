# Set up libraries
import os

# Import functions for processing
from enrollment_processing import download_and_unzip, clean_and_combine

######################################
# GEOGRAPHY INCLUSION SPECIFICATION #
######################################

# SELECT STATES. WILL AUTOMATICALLY INCLUDE ALL COUNTIES IN EACH STATE UNLESS OTHERWISE SPECIFIED
states = ['CA']

######################################
# FILE INCLUSION SPECIFICATION #
######################################

# Select years/months to process enrollment data from
enrl_files = [
                    '202301', '202302', '202303', '202304', '202305', '202306', '202307', '202308', '202309',
                    '202310', '202311', '202312', '202401', '202402', '202403', '202404', '202405', '202406',
                    '202407', '202408', '202409', '202410', '202411', '202412', '202501', '202502', '202503',
                    '202504', '202505', '202506', '202507', '202508', '202509', '202510', '202511', '202512',
                    ]

# Set current working directory to the directory containing the scripts being executed
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Get current working directory from parentfolder of folder containing scripts
directory = os.getcwd()
print(directory)

# Create "Outputs" folder
os.makedirs(os.path.join(directory, 'outputs'), exist_ok=True)

######################################
# DOWNLOAD DATA FROM CMS WEBSITE #
######################################

download_and_unzip(enrl_files)

######################################
# PROCESS UNZIPPED DATA #
######################################
combined_enrl = clean_and_combine(enrl_files, states)


print('\n---------Processing complete. Enrollment file is ready!---------')