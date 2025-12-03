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

### Google Cloud Setup (First Time or New Keys)

This section walks you through setting up Google Cloud APIs from scratch. You'll need this when:
- Setting up the project for the first time
- Getting a new API key issued
- Onboarding a new volunteer to manage the system

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your dedicated Gmail account (e.g., `troop202trees@gmail.com`)
3. Click the project dropdown (top left, next to "Google Cloud")
4. Click "New Project"
   - **Project Name:** `Tree Recycling Routes` (or similar)
   - **Organization:** Leave blank or select if you have one
   - Click "Create"
5. Wait for the project to be created (takes ~30 seconds)
6. Select your new project from the dropdown

#### Step 2: Enable Required APIs

1. In the left sidebar, go to **"APIs & Services"** > **"Library"**
2. Search for and enable each of these APIs:
   
   **For Google Sheets access:**
   - Search: `Google Sheets API`
   - Click on it, then click **"Enable"**
   - Search: `Google Drive API`
   - Click on it, then click **"Enable"**
   
   **For geocoding addresses:**
   - Search: `Geocoding API`
   - Click on it, then click **"Enable"**

#### Step 3: Create Service Account (for Google Sheets)

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ Create Credentials"** > **"Service Account"**
3. Fill in the details:
   - **Service account name:** `tree-recycling-service`
   - **Service account ID:** (auto-filled, leave as-is)
   - **Description:** `Service account for tree recycling route automation`
4. Click **"Create and Continue"**
5. **Grant this service account access to project:**
   - Select role: **"Editor"**
   - Click **"Continue"**, then **"Done"**
6. Find your new service account in the list
7. Click on the service account name
8. Go to the **"Keys"** tab
9. Click **"Add Key"** > **"Create new key"**
10. Select **"JSON"** format
11. Click **"Create"**
12. A JSON file will download automatically
13. Rename it to `credentials.json` and move it to your `route-building/` directory

#### Step 4: Create API Key (for Google Maps Geocoding)

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ Create Credentials"** > **"API Key"**
3. A key will be created and shown in a popup - **copy this key!**
4. (Optional but recommended) Click **"Restrict Key"** to secure it:
   - **Name:** `Tree Recycling Geocoding Key`
   - Under **"API restrictions"**:
     - Select **"Restrict key"**
     - Check only: ☑️ **Geocoding API**
   - Click **"Save"**

5. **Store the API key securely:**
   
   Option A - Environment Variable (Recommended):
   ```bash
   # Add to your ~/.zshrc or ~/.bash_profile
   export GOOGLE_MAPS_API_KEY="your_api_key_here"
   
   # Then reload your shell
   source ~/.zshrc
   ```
   
   Option B - Config file (make sure it's in .gitignore):
   ```bash
   # Create a config file
   echo "GOOGLE_MAPS_API_KEY=your_api_key_here" > route-building/.env
   ```

#### Step 5: Share Spreadsheets with Service Account

1. Open your `credentials.json` file
2. Find the `"client_email"` field (looks like: `tree-recycling-service@project-id.iam.gserviceaccount.com`)
3. Copy this email address
4. Open your Google Sheet (both 2025 and 2026)
5. Click **"Share"** button (top right)
6. Paste the service account email
7. Give it **"Editor"** permissions
8. Uncheck **"Notify people"** (it's a service account, not a person)
9. Click **"Share"**

#### Step 6: Verify Setup

Run this test to verify everything works:

```bash
cd route-building
uv run src/fetch_data.py
```

You should see data being fetched successfully!

---

### Billing & Free Tier Limits

**Google Sheets API:** Completely free, no limits for our usage

**Google Drive API:** Completely free, no limits for our usage

**Geocoding API:**
- **Free tier:** 40,000 requests per month (more than enough!)
- **Cost after free tier:** $5 per 1,000 requests
- **Our usage:** ~358 addresses per year = well under free tier
- **With caching:** Addresses are cached forever, so you'll only geocode NEW addresses

💡 **Tip:** With our permanent cache, you'll likely never geocode the same address twice across multiple years!

---

### Troubleshooting

**"Credentials not found"**
- Make sure `credentials.json` is in the `route-building/` directory
- Check that the file is valid JSON (open it in a text editor)

**"Spreadsheet not found"**
- Make sure you shared the spreadsheet with the service account email
- Check that the spreadsheet ID in `src/fetch_data.py` is correct

**"API not enabled"**
- Go back to Google Cloud Console > APIs & Services > Library
- Make sure all three APIs are enabled (Sheets, Drive, Geocoding)

**"Geocoding failed" or "API key invalid"**
- Make sure you enabled the Geocoding API
- Verify your API key is correct: `echo $GOOGLE_MAPS_API_KEY`
- Check that API restrictions allow Geocoding API

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
- **Never commit `credentials.json` to git** - It's already in `.gitignore`
- **Never commit API keys to git** - Use environment variables or `.env` file (also in `.gitignore`)
- Store credentials securely - Consider using a password manager for the service account JSON
- The dedicated Gmail account should have a strong password and 2FA enabled
- API keys should be restricted to only the APIs they need
- Service accounts should have minimal permissions (Editor for sheets only)

---

**Last Updated:** December 3, 2025
