#!/usr/bin/env python3
"""
Fetch data from Google Sheets for tree recycling route building.

This script connects to the Google Sheets API and downloads
the current tree recycling requests data.
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from pathlib import Path
from typing import Optional
import sys


# Google Sheets API scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Configuration
CREDENTIALS_FILE = 'credentials.json'

# Spreadsheet IDs - Use ID from URL for reliability
# Production (2026 season - January 2026 pickup)
SPREADSHEET_ID_2026 = '16LJKmKXEXrI-rB8jySMdxGkiLL3rPlhUNbQRftTELBU'
# Testing (2025 season - January 2025 pickup, historical data)
SPREADSHEET_ID_2025 = '1KtLUxqvsdbQvS6_bmLbxziPWwbWnQCCH7U42294gteg'  # Add 2025 spreadsheet ID here

# Active spreadsheet - change this to switch between prod/test
ACTIVE_SPREADSHEET = SPREADSHEET_ID_2026  # Change to SPREADSHEET_ID_2025 for testing


def get_credentials(credentials_path: str = CREDENTIALS_FILE) -> Credentials:
    """
    Load credentials from service account JSON file.
    
    Args:
        credentials_path: Path to the credentials JSON file
        
    Returns:
        Authorized credentials object
        
    Raises:
        FileNotFoundError: If credentials file doesn't exist
    """
    creds_file = Path(credentials_path)
    if not creds_file.exists():
        raise FileNotFoundError(
            f"Credentials file not found: {credentials_path}\n"
            "Please follow the setup instructions in NEW README.md"
        )
    
    creds = Credentials.from_service_account_file(
        credentials_path,
        scopes=SCOPES
    )
    return creds


def fetch_sheet_data(
    spreadsheet_id: str = ACTIVE_SPREADSHEET,
    worksheet_index: int = 0,
    credentials_path: str = CREDENTIALS_FILE
) -> tuple[pd.DataFrame, str]:
    """
    Fetch data from Google Sheets and return as a pandas DataFrame.
    
    Args:
        spreadsheet_id: ID of the Google Spreadsheet (defaults to ACTIVE_SPREADSHEET)
        worksheet_index: Index of the worksheet (0 = first sheet)
        credentials_path: Path to credentials file
        
    Returns:
        Tuple of (DataFrame containing the sheet data, year string for file naming)
    """
    print(f"Authenticating with Google Sheets API...")
    creds = get_credentials(credentials_path)
    client = gspread.authorize(creds)
    
    # Determine which year/environment
    if spreadsheet_id == SPREADSHEET_ID_2026:
        env = "PRODUCTION (2026)"
        year = "2026"
    elif spreadsheet_id == SPREADSHEET_ID_2025:
        env = "TESTING (2025)"
        year = "2025"
    else:
        env = "CUSTOM"
        year = "custom"
    
    print(f"Environment: {env}")
    print(f"Opening spreadsheet: {spreadsheet_id}")
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"Error: Spreadsheet with ID '{spreadsheet_id}' not found.")
        print("Make sure:")
        print("1. The spreadsheet ID is correct")
        print("2. The spreadsheet is shared with your service account email")
        print("   (found in credentials.json as 'client_email')")
        sys.exit(1)
    
    # Get the worksheet
    worksheet = spreadsheet.get_worksheet(worksheet_index)
    print(f"Fetching data from worksheet: {worksheet.title}")
    
    # Get all records as list of dictionaries
    records = worksheet.get_all_records()
    
    # Convert to DataFrame
    df = pd.DataFrame(records)
    
    print(f"Successfully fetched {len(df)} rows")
    return df, year


def save_local_copy(df: pd.DataFrame, year: str, output_path: Optional[str] = None) -> None:
    """
    Save a local copy of the data as CSV.
    
    Args:
        df: DataFrame to save
        year: Year string (e.g., '2025' or '2026') for file naming
        output_path: Path where to save the CSV file (defaults to data/{year}-tree_requests.csv)
    """
    if output_path is None:
        output_path = f'data/{year}-tree_requests.csv'
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_file, index=False)
    print(f"Data saved to: {output_file}")


def check_syntax_errors(df: pd.DataFrame) -> None:
    """
    Check for data syntax errors and quality issues.
    
    Checks for:
    1. Numbers in the Street column (should be in House # column)
    2. Empty required fields
    
    Args:
        df: DataFrame to check
    """
    print("\n" + "=" * 60)
    print("SYNTAX & DATA QUALITY CHECK")
    print("=" * 60)
    
    issues_found = False
    
    # Check for numbers at the start of Street column
    if 'Street' in df.columns:
        df_temp = df.copy()
        df_temp['Street'] = df_temp['Street'].astype(str)
        
        # Find streets that start with digits
        streets_with_numbers = df_temp[df_temp['Street'].str.match(r'^\d', na=False)]
        
        if len(streets_with_numbers) > 0:
            issues_found = True
            print(f"\n⚠️  Found {len(streets_with_numbers)} entries with numbers at start of Street column:")
            print("   (House numbers should be in the 'House #' column, not 'Street' column)")
            for _, row in streets_with_numbers.iterrows():
                print(f"    - {row['Name']}: House #='{row.get('House #', '')}', Street='{row['Street']}'")
        else:
            print("\n✓ No numbers found at start of Street column")
    
    # Check for empty House # when Street has data
    if 'House #' in df.columns and 'Street' in df.columns:
        df_temp = df.copy()
        df_temp['House #'] = df_temp['House #'].astype(str)
        df_temp['Street'] = df_temp['Street'].astype(str)
        
        missing_house_num = df_temp[
            (df_temp['House #'].isin(['', 'nan', 'None'])) & 
            (~df_temp['Street'].isin(['', 'nan', 'None']))
        ]
        
        if len(missing_house_num) > 0:
            issues_found = True
            print(f"\n⚠️  Found {len(missing_house_num)} entries missing House # but have Street:")
            for _, row in missing_house_num.iterrows():
                print(f"    - {row['Name']}: Street='{row['Street']}', City='{row.get('City', '')}'")
        else:
            print("✓ All entries with streets have house numbers")
    
    if not issues_found:
        print("\n✓ All syntax checks passed")
    
    print("\n" + "=" * 60)


def check_duplicates(df: pd.DataFrame) -> None:
    """
    Check for duplicate entries in the data.
    
    Checks for duplicates based on:
    1. Full address (House #, Street, City)
    2. Name
    3. Exact duplicate rows
    
    Args:
        df: DataFrame to check for duplicates
    """
    print("\n" + "=" * 60)
    print("DUPLICATE DETECTION")
    print("=" * 60)
    
    # Check for exact duplicate rows
    exact_dupes = df[df.duplicated(keep=False)]
    if len(exact_dupes) > 0:
        print(f"\n⚠️  Found {len(exact_dupes)} exact duplicate rows:")
        print(exact_dupes[['Name', 'House #', 'Street', 'City', 'Number of Trees']].to_string())
    else:
        print("\n✓ No exact duplicate rows found")
    
    # Check for duplicate addresses
    address_cols = ['House #', 'Street', 'City']
    if all(col in df.columns for col in address_cols):
        # Create full address for comparison
        df_temp = df.copy()
        df_temp['_full_address'] = (
            df_temp['House #'].astype(str) + ' ' + 
            df_temp['Street'].astype(str) + ', ' + 
            df_temp['City'].astype(str)
        )
        
        address_dupes = df_temp[df_temp.duplicated(subset=['_full_address'], keep=False)]
        if len(address_dupes) > 0:
            print(f"\n⚠️  Found {len(address_dupes)} entries with duplicate addresses:")
            for address in address_dupes['_full_address'].unique():
                dupes = address_dupes[address_dupes['_full_address'] == address]
                print(f"\n  Address: {address}")
                for _, row in dupes.iterrows():
                    print(f"    - {row['Name']}: {row['Number of Trees']} tree(s)")
        else:
            print("✓ No duplicate addresses found")
    
    # Check for duplicate names
    if 'Name' in df.columns:
        name_dupes = df[df.duplicated(subset=['Name'], keep=False)]
        if len(name_dupes) > 0:
            print(f"\n⚠️  Found {len(name_dupes)} entries with duplicate names:")
            for name in name_dupes['Name'].unique():
                dupes = name_dupes[name_dupes['Name'] == name]
                print(f"\n  Name: {name}")
                for _, row in dupes.iterrows():
                    addr = f"{row.get('House #', '')} {row.get('Street', '')}, {row.get('City', '')}"
                    print(f"    - {addr}: {row.get('Number of Trees', '?')} tree(s)")
        else:
            print("✓ No duplicate names found")
    
    print("\n" + "=" * 60)


def main():
    """Main execution function."""
    print("=" * 60)
    print("Tree Recycling Data Fetcher")
    print("=" * 60)
    
    try:
        # Fetch the data
        df, year = fetch_sheet_data()
        
        # Display summary
        print("\nData Summary:")
        print(f"Total records: {len(df)}")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Show first few rows
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        # Check for syntax errors and data quality
        check_syntax_errors(df)
        
        # Check for duplicates
        check_duplicates(df)
        
        # Save local copy
        save_local_copy(df, year)
        
        print("\n✓ Data fetch completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
