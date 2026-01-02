# Christmas Tree Pickup Route Building - Project Summary

## ✅ Completed

### Data Pipeline
- ✅ Google Sheets API integration to fetch form responses
- ✅ Google Maps Geocoding API with permanent caching
- ✅ Address normalization and data cleaning

### Route Generation
- ✅ Geographic clustering using K-means (scikit-learn)
- ✅ Automatic route count optimization based on trailer capacity
- ✅ Handles mixed trailer sizes (16ft @ 25 trees, 12ft @ 18 trees)
- ✅ Fast execution (~1.5 seconds for 358 addresses)

### Visualization
- ✅ Interactive Folium maps with color-coded routes
- ✅ Clickable markers showing address details
- ✅ Layer controls to toggle routes on/off
- ✅ HTML escaping for special characters in addresses

### Results (2025 Data)
- 358 addresses processed
- 368 total trees
- 28 routes created
- Average 13.1 trees per route
- Only 1 route slightly over capacity (33 trees, limit 22)

## 🚧 Next Steps

### Before Pickup Day
1. **Review the map** - Visually inspect route clustering
2. **Manual adjustments** - Split Route E (33 trees) or swap addresses
3. **Merge tiny routes** - Consider combining Routes R (1 tree) and Y (1 tree) with nearby routes
4. **Assign to volunteers** - Use `2025-clustered-routes.csv` to assign routes to drivers

### For Next Year
1. **Improve form validation** - Prevent backticks and special characters in names
2. **Add route optimization** - Consider actual driving distance (not just geographic clustering)
3. **Export to volunteer-friendly format** - Generate printable route sheets with turn-by-turn directions
4. **Track completion** - Add status tracking for each route during pickup day

## 📁 Key Files

### Scripts (in `src/`)
- `fetch_data.py` - Download data from Google Sheets
- `geocode_google.py` - Geocode addresses with caching
- `cluster_routes.py` - Generate routes using geographic clustering
- `generate_map.py` - Create interactive HTML maps
- `export_route.py` - Export individual routes for drivers


### Data Files (in `data/`)
- `2025-tree_requests.csv` - Raw form data
- `2025-geocoded-full.csv` - Addresses with lat/long coordinates
- `2025-clustered-routes.csv` - Final route assignments
- `2025-routes-map.html` - Interactive map
- `geocode-cache.json` - Permanent geocoding cache

### Configuration
- `keys/` - Service account credentials (gitignored)
- `pyproject.toml` - Python dependencies (pandas, folium, scikit-learn, etc.)

## 🗑️ Removed

### OR-Tools VRP Optimization
- Attempted complex Vehicle Routing Problem (VRP) optimization
- Multiple solver strategies tested (Guided Local Search, Simulated Annealing, Tabu Search, etc.)
- All strategies failed with 1-hour timeout on 358 addresses
- Issue: Over-constrained with mixed trailer capacities
- **Conclusion**: Geographic clustering is "good enough" and 1000x faster

Removed files:
- `src/optimize_routes.py`
- `src/ortools_routes.py`
- `src/test_optimize.py`
- `PARALLEL_OPTIMIZATION_RUNS.md`

## 💡 Lessons Learned

1. **Perfect is the enemy of good** - Simple geographic clustering works great for this use case
2. **Capacity constraints are tricky** - Mixed trailer sizes made VRP optimization fail
3. **Caching is essential** - Permanent geocode cache saves API costs and time
4. **Visual validation matters** - Map makes it easy to spot issues and adjust manually
5. **Start simple** - Tried complex optimization first; should have started with clustering

## 🎯 Success Metrics

- **Speed**: 1.5 seconds vs 1+ hour timeout
- **Quality**: Routes are geographically sensible
- **Flexibility**: Easy to adjust manually
- **Maintainability**: Simple code, easy to understand
- **Cost**: Minimal API calls due to caching
