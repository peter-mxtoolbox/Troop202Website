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

5. Open map:
   ```bash
   open data/2025-routes-map.html
   ```

6. Adjust routes (optional):
   ```bash
   uv run src/adjust_routes.py
   ```

7. Export route for driver:
   ```bash
   uv run src/export_route.py A
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

3. Open map:
   ```bash
   open data/2025-test-routes-map.html
   ```

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
```

Creates PDF with:
- QR code for Google Maps navigation
- Table with all addresses and tracking fields
- Located in: `data/route-exports/Route-A-PickupSheet.pdf`
