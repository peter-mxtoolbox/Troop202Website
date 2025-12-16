#!/usr/bin/env python3
"""Quick test of route optimization with small dataset."""

import sys
sys.path.insert(0, 'src')

from optimize_routes import load_geocoded_data, solve_vrp

# Load test data
print("Loading test data...")
df = load_geocoded_data('data/2025-geocoded-test.csv')

print(f"\n5 addresses loaded, {df['Number of Trees'].sum():.0f} total trees")

# Test with 2 routes, 3 trees capacity each
print("\nTesting with 2 routes:")
print("  - Route 1: 3 tree capacity (large)")
print("  - Route 2: 3 tree capacity (large)")

trailer_capacities = [3, 3]

df_result = solve_vrp(
    df,
    num_vehicles=2,
    time_limit_seconds=10,
    trailer_capacities=trailer_capacities
)

if df_result['optimized_route'].notna().any():
    print("\n✓ Test successful!")
    print("\nRoute assignments:")
    for idx, row in df_result.iterrows():
        if row['optimized_route']:
            print(f"  Route {row['optimized_route']}: {row['Name']} ({row['Number of Trees']:.0f} trees)")
else:
    print("\n✗ Test failed - no solution found")
