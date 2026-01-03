# Route Building - Quick Reference

1. Pull in the data:
   ```bash
   uv run src/fetch_data.py
   ```

2. Geocode:
   ```bash
   uv run src/geocode_google.py
   ```

3. Generate routes:
   ```bash
   uv run src/cluster_routes.py
   ```

4. Generate map:
   ```bash
   uv run src/generate_map.py
   ```

5. Sync to S3 and view:
   ```bash
   cd ../website && AWS_PROFILE=730335414034_AdministratorAccess aws s3 sync routes/ s3://prod-troop202-website-730335414034/routes/ --delete
   ```
   
   Then open: https://troop202.org/routes/2026/2026-routes-map.html

6. Adjust routes (optional):
   ```bash
   uv run src/adjust_routes.py
   ```

7. Export all routes for drivers:
   ```bash
   uv run src/export_route.py --all
   ```

8. Sync routes to S3:
   ```bash
   cd ../website && AWS_PROFILE=730335414034_AdministratorAccess aws s3 sync routes/2026/ s3://prod-troop202-website-730335414034/routes/2026/
   ```

---

## Testing with 2025 Data

1. Generate routes:
   ```bash
   uv run src/cluster_routes.py --test
   ```

2. Generate map:
   ```bash
   uv run src/generate_map.py --test
   ```

3. Sync to S3 and view:
   ```bash
   cd ../website && AWS_PROFILE=730335414034_AdministratorAccess aws s3 sync routes/ s3://prod-troop202-website-730335414034/routes/
   ```
   
   Then open: https://troop202.org/routes/2025/2025-routes-map.html

---

## Route Adjustment & Export

**Adjust routes interactively:**
```bash
uv run src/adjust_routes.py
```

Menu options:
- Move a customer to a different route
- Merge two routes into one
- Show problem routes (>24 or <10 trees)
- Regenerate map
- Quit

**Export pickup sheet for a specific route:**
```bash
uv run src/export_route.py <ROUTE_LETTER>
```

Example:
```bash
uv run src/export_route.py A
**Export all routes:**
```bash
uv run src/export_route.py --all
```

Creates HTML files with:
- QR code for Google Maps navigation
- Link to Google Maps
- Table with all addresses and tracking fields
- Located in: `../website/routes/2026/Route-<LETTER>.html`

**Sync to S3:**
```bash
cd ../website && AWS_PROFILE=730335414034_AdministratorAccess aws s3 sync routes/2026/ s3://prod-troop202-website-730335414034/routes/2026/
```

Then routes are accessible at: https://troop202.org/routes/2026/Route-A.html (replace A with any route letter)
- Table with all addresses and tracking fields
- Located in: `data/route-exports/Route-A-PickupSheet.pdf`
