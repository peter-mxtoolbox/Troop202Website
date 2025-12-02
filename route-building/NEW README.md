# Route Building Automation - 2025/2026 Season

Modern automated system for managing Christmas tree recycling pickup routes.

---

## Overview

This project automates the route building process for Christmas tree recycling, replacing the manual Google Maps and spreadsheet workflow with a Python-based automation system.

**Tech Stack:**
- Python 3.x
- Google Sheets API
- Google Forms (data collection)
- Dedicated Gmail account for authentication

---

## Step 1: Data Fetching from Google Sheets

### Recommended Approach: Google Sheets API (gspread)

The **`gspread`** library is the best option for this project because:

✅ **Direct API access** - No need to download/upload files  
✅ **Real-time data** - Always get the latest submissions  
✅ **Read and write** - Can update the spreadsheet programmatically  
✅ **Service account support** - Works with dedicated Gmail account  
✅ **Pythonic and well-maintained** - Clean API, active development  

### Alternative Options Considered

| Method | Pros | Cons |
|--------|------|------|
| **gspread** | Real-time access, read/write, easy auth | Requires API setup |
| **pandas + Google Sheets** | Familiar pandas interface | Read-only via published links |
| **Google Drive API** | Full file access | More complex, overkill for sheets |
| **Manual CSV export** | Simple, no setup | Not automated, manual work |

### Installation

We use `uv` for fast dependency management:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
cd route-building
uv sync
```

**Legacy pip method** (if needed):
```bash
pip install gspread google-auth pandas
```

### Authentication Setup

1. **Enable Google Sheets API**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable "Google Sheets API" and "Google Drive API"

2. **Create Service Account**
   - Navigate to "IAM & Admin" > "Service Accounts"
   - Create service account
   - Generate JSON key file
   - Save as `credentials.json` (keep secure, add to .gitignore)

3. **Share Spreadsheet**
   - Open your Google Sheet
   - Share with the service account email (found in credentials.json)
   - Give "Editor" permissions

### Basic Usage Example

```python
import gspread
from google.oauth2.service_account import Credentials

# Define the scope
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Authenticate
creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
client = gspread.authorize(creds)

# Open the spreadsheet
spreadsheet = client.open('Troop 202 2026 Tree Recycling Requests (Responses)')
# OR by key:
# spreadsheet = client.open_by_key('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms')

# Get the first worksheet
worksheet = spreadsheet.sheet1

# Get all records as a list of dictionaries
data = worksheet.get_all_records()

# Work with the data
for row in data:
    print(f"Name: {row['Name']}, Address: {row['Address']}")
```

### Data Access Patterns

```python
# Get all data as list of lists
all_data = worksheet.get_all_values()

# Get all records as list of dictionaries (uses first row as keys)
records = worksheet.get_all_records()

# Get specific cell
cell_value = worksheet.acell('B1').value

# Get a range
range_data = worksheet.get('A1:E10')

# Get a specific column
column_data = worksheet.col_values(1)  # First column

# Get a specific row
row_data = worksheet.row_values(1)  # First row
```

### Integration with Pandas

For data analysis and manipulation:

```python
import pandas as pd

# Convert to DataFrame
df = pd.DataFrame(worksheet.get_all_records())

# Now you can use all pandas functionality
print(df.head())
print(df.describe())
```

---

## Project Structure

```
route-building/
├── NEW README.md          # This file
├── README.md              # Historical documentation
├── pyproject.toml         # Project config & dependencies (uv)
├── .gitignore            # Git ignore rules
├── credentials.json       # Google API credentials (DO NOT COMMIT)
├── data/                  # Local data cache (ignored by git)
│   └── tree_requests.csv
└── src/
    ├── fetch_data.py     # Download data from Google Sheets
    ├── process_routes.py # Route assignment logic (TODO)
    └── generate_maps.py  # Map generation (TODO)
```

## Quick Start

```bash
# 1. Install dependencies
uv sync

# 2. Run the data fetcher
uv run src/fetch_data.py
```

---

## Next Steps

- [ ] Set up Google Cloud project and service account
- [x] Install required Python packages (uv)
- [x] Create `fetch_data.py` script to download spreadsheet
- [ ] Update `SPREADSHEET_NAME` in `fetch_data.py` with actual name
- [ ] Test data fetching with current spreadsheet
- [ ] Design route assignment algorithm
- [ ] Implement automated mapping

## Usage

### Fetch Latest Data

```bash
# Run the fetch script
uv run src/fetch_data.py
```

This will:
1. Authenticate with Google Sheets API
2. Download the latest data
3. Save a local CSV copy to `data/tree_requests.csv`
4. Display a summary of the data

---

## Security Notes

⚠️ **Important:**
- Never commit `credentials.json` to git
- Add to `.gitignore` immediately
- Store credentials securely
- Consider using environment variables for sensitive data
- Use service account (not personal OAuth) for automation

---

**Last Updated:** December 2, 2025
