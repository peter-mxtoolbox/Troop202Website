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
