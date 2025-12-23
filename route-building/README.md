# Christmas Tree Pickup - Route Building

Automated route building using geographic clustering.

## Quick Start

### 1. Fetch Latest Data
```bash
uv run python src/fetch_data.py
```

### 2. Geocode Addresses
```bash
uv run python src/geocode_google.py
```

### 3. Generate Routes
```bash
uv run python src/cluster_routes.py
```

### 4. Visualize Routes
```bash
uv run python src/generate_map.py
open data/2025-routes-map.html
```

## How It Works

1. **Data Collection**: Fetches form responses from Google Sheets
2. **Geocoding**: Converts addresses to coordinates using Google Maps API (with caching)
3. **Clustering**: Groups nearby addresses into routes using K-means
4. **Auto-sizing**: Automatically finds optimal number of routes based on trailer capacity
5. **Visualization**: Generates interactive map with color-coded routes

## Configuration

Trailer capacities (in `src/cluster_routes.py`):
- Large (16-foot) trailers: 25 trees per route
- Small (12-foot) trailers: 18 trees per route
- Default capacity limit: 22 trees per route

## Output Files

- `data/2025-clustered-routes.csv` - Route assignments
- `data/2025-routes-map.html` - Interactive map
- `data/2025-geocoded-full.csv` - Geocoded addresses

See [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) for detailed project information.

---

# Historical Documentation

## Table of Contents

1. [Old Manual Instructions](#old-manual-instructions)
2. [Old Docker Instructions](#old-docker-instructions)
3. [GitHub Repository Information](#github-repository-information)
4. [Additional Notes](#additional-notes)

---

## Old Manual Instructions

### Route and Map Creation Process

This was the traditional manual process used in previous years:

#### Initial Setup

1. **Make copy of responses spreadsheet for working copy**
   - All edits should be made on this working copy
   - Add new column E after "Subdivision" for "Route"
   
2. **Add second Sheet (copy from prior year)**
   - This sheet sums up tree totals for each route
   - Used to help assign trailers to routes

#### Map Creation

1. **Download spreadsheet as a .csv**

2. **Create new map in Google Maps**
   - Import the CSV file
   - Use house number, street and city for pin location
   - Use name for label

3. **Configure map display**
   - Once imported, select "uniform style" and "group places" by Route
   - Select Name as label

4. **Assign routes**
   - Using map pins, decide on route grouping
   - Assign route letter (or number) in route column of spreadsheet

5. **Iterate and refine**
   - Every so often, re-export spreadsheet and recreate the map using same steps
   - This will color code each route (limit 20)
   - Makes it much easier to see mistakes

#### Troubleshooting

**Address Mapping Errors:**
- You can select "show table" to see exact error lines
- Most often can be resolved by tweaking the address format:
  - `Av.` instead of `AVE`
  - `St.` instead of `Street`
  - etc.

#### After Thursday Planning Session

- New submissions can be manually copied to working spreadsheet from live master
- Re-map and it should be obvious which route to add each new pin to
- Search function can be used in the map to find a name
- Once submissions are disabled and all addresses added to routes, this process is complete

---

## Old Docker Instructions

### Description

The Docker-based system was designed to break up the large file from Google Forms (XLSX) into multiple files - one set of files for each route.

### First Time Setup

```bash
# 1. Clone the repository
git clone https://github.com/mr-ice/233treerecycling.git

# 2. Change to the directory
cd 233treerecycling

# 3. Build the Docker container
./dockerbuild
# OR on Windows:
# dockerbuild.cmd
```

### Re-Setup

Do this if returning after any significant time or when you know there may be changes:

```bash
# 1. Navigate to the directory
cd 233treerecycling

# 2. Pull latest changes
git pull

# 3. Rebuild the Docker container
./dockerbuild
# OR on Windows:
# dockerbuild.cmd
```

### Split the Tree Recycling Routes

1. **Download the Google Docs as an XLSX**
   - Example: `2020TreeRecyclingRequests.xlsx`

2. **Convert to plain .xls format** (old format)
   - Note: Some .xlsx files often fail, so converting to .xls is recommended

3. **Run the split command:**
   ```bash
   ./splitfile 2020TreeRecyclingRequests.xls
   ```

4. **Generate PDFs:**
   ```bash
   ./genpdfs 2020TreeRecyclingRequests.xls
   ```

#### Optional Output Directory

You can append `--output 2020-Routes` to change the name of the output directory to `2020-Routes`. 

The default is `%Y-Routes` using the current year (typically the year of pick-up, not the year of the Christmas/fundraising season).

**Important:** Make sure to use the same arguments for both scripts.

---

## GitHub Repository Information

### Repository Details

- **Repository URL:** [https://github.com/mr-ice/233treerecycling](https://github.com/mr-ice/233treerecycling)
- **Owner:** mr-ice
- **Primary Language:** Jupyter Notebook (97.8%), Python (1.3%)

### Description

Script to aid the Tree Recycling planning session. This tool breaks up the large file from Google Forms (CSV) into multiple files - one file for each route. It saves output in PDF, HTML, CSV, and XLSX formats.

### Alternative Installation Method (Python Virtual Environment)

If you prefer not to use Docker, you can install directly using Python:

```bash
# 1. Clone the repository
git clone https://github.com/mr-ice/233treerecycling.git

# 2. Change to the Tree Recycling directory
cd 233treerecycling

# 3. Create a virtual environment
python3 -m venv venv

# 4. Activate the virtual environment
source venv/bin/activate
# OR on Windows:
# venv\Scripts\activate

# 5. Install requirements
pip install -r requirements.txt
```

### Usage Instructions (Jupyter Notebook Method)

```bash
# 0. Activate virtual environment
source venv/bin/activate

# 1. Start Jupyter Notebook
jupyter notebook

# 2. Click on "ParseTreePickupMasterList.ipynb"

# 3. Update the file name in block 2 to match the master list

# 4. Select Cell -> Run All
```

You should now have CSV, HTML, PDF, and XLSX versions of each route.

### Usage Instructions (Splitter Script Method)

```bash
# 0. Activate virtual environment
source venv/bin/activate

# 1. Change input filename on line 5

# 2. Change output directory name on lines 18, 34, 36, 38

# 3. Create output directory
mkdir $output_directory

# 4. Run the splitter
python3 splitter
```

You should now have CSV, HTML, PDF, and XLSX versions of each route.

---

## What Changed From Previous Years

### Old System (Manual)
- Copy data from Google Sheets to local spreadsheet
- Manually assign routes by eyeballing addresses
- Copy/paste into multiple tools
- Generate maps manually

### New System (Automated) ✓
- Automatically fetch data from Google Sheets
- Geographic clustering assigns routes
- One-command map generation
- Geocoding cache eliminates repeated API calls

### Benefits
- **Speed**: Routes created in 1-2 seconds (vs hours of manual work)
- **Consistency**: Same addresses always geocoded identically  
- **Scalability**: Automatically adjusts number of routes based on volume
- **Visualization**: Interactive HTML maps with route toggles
- **Training Phase:** Train volunteers on new system

### Technical Approach

The new system will:
- Use the existing Python/Jupyter Notebook codebase as a foundation
- Add automated route assignment algorithms based on geographic proximity
- Integrate with Google Maps API for address validation and mapping
- Provide a web interface for easier access (no Docker/command line knowledge required)
- Generate real-time updates as new submissions are received

---

## Additional Notes

### Best Practices

- Always work on a copy of the live spreadsheet
- Test route assignments before finalizing
- Keep track of total trees per route for trailer assignment
- Document any address format issues for future reference
- Maintain communication with route leaders during the planning phase

### Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| Address not mapping correctly | Try variations: Ave/Avenue, St/Street, Rd/Road |
| Too many routes (>20) | Combine smaller adjacent routes |
| Uneven distribution | Use the tree total summary sheet to balance routes |
| New submissions after planning | Manually add to appropriate route based on map location |

### File Naming Conventions

- Master spreadsheet: `YYYYTreeRecyclingRequests.xlsx`
- Working copy: `YYYYTreeRecyclingRequests-Working.xlsx`
- Output directory: `YYYY-Routes/`
- Individual route files: `Route-X.{csv,html,pdf,xlsx}`

### Contact Information

For questions about the route building process, contact the event coordinator or check the main project documentation.

---

**Last Updated:** December 2, 2025
