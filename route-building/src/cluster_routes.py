#!/usr/bin/env python3
"""
Simple geographic clustering for route assignment.

Instead of complex VRP optimization, just group nearby addresses together.
This is much faster and "good enough" for practical use.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from typing import Optional
import time


def load_geocoded_data(csv_path: str = 'data/2026-geocoded-full.csv') -> pd.DataFrame:
    """Load geocoded data."""
    file_path = Path(csv_path)
    if not file_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    df = pd.read_csv(file_path)
    df_valid = df[df['latitude'].notna() & df['longitude'].notna()].copy()
    
    print(f"Loaded {len(df_valid)} geocoded addresses from {csv_path}")
    return df_valid


def get_route_letter(i):
    """Convert route index to letter (A, B, C... AA, AB, AC...)"""
    if i < 26:
        return chr(65 + i)
    else:
        return chr(65 + i // 26 - 1) + chr(65 + i % 26)


def cluster_addresses(df: pd.DataFrame, num_routes: int = 18, capacity_per_route: Optional[int] = None):
    """
    Cluster addresses geographically into routes.
    
    Uses K-means clustering on lat/long coordinates to group nearby addresses.
    Optionally balances by tree count if capacity is specified.
    """
    print(f"\nClustering {len(df)} addresses into {num_routes} routes...")
    
    # Get coordinates
    coords = df[['latitude', 'longitude']].values
    
    # Simple K-means clustering
    print("Running K-means clustering...")
    start_time = time.time()
    
    kmeans = KMeans(
        n_clusters=num_routes,
        random_state=42,
        n_init=10,
        max_iter=300
    )
    
    df['cluster_route'] = kmeans.fit_predict(coords)
    df['optimized_route'] = df['cluster_route'].apply(get_route_letter)
    
    elapsed = time.time() - start_time
    print(f"✓ Clustering completed in {elapsed:.2f} seconds!")
    
    # Check capacity balance and return stats
    route_stats = []
    for route in sorted(df['optimized_route'].unique()):
        route_df = df[df['optimized_route'] == route]
        num_pickups = len(route_df)
        num_trees = int(route_df['Number of Trees'].sum())
        
        route_stats.append({
            'route': route,
            'pickups': num_pickups,
            'trees': num_trees
        })
    
    return df, pd.DataFrame(route_stats)


def print_route_summary(stats_df: pd.DataFrame, capacity_per_route: Optional[int] = None):
    """Print route assignment summary."""
    print("\n" + "="*60)
    print("ROUTE ASSIGNMENTS")
    print("="*60)
    
    for _, row in stats_df.iterrows():
        status = ""
        if capacity_per_route and row['trees'] > capacity_per_route:
            status = f" ⚠️  OVER by {int(row['trees'] - capacity_per_route)}"
        
        print(f"Route {row['route']}: {row['pickups']:3d} pickups, {row['trees']:3d} trees{status}")
    
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"Average pickups per route: {stats_df['pickups'].mean():.1f} ± {stats_df['pickups'].std():.1f}")
    print(f"Average trees per route: {stats_df['trees'].mean():.1f} ± {stats_df['trees'].std():.1f}")
    print(f"Min/Max pickups: {stats_df['pickups'].min()}/{stats_df['pickups'].max()}")
    print(f"Min/Max trees: {stats_df['trees'].min()}/{stats_df['trees'].max()}")
    
    # Check for capacity violations
    if capacity_per_route:
        over_capacity = stats_df[stats_df['trees'] > capacity_per_route]
        if len(over_capacity) > 0:
            print(f"\n⚠️  {len(over_capacity)} routes are over capacity!")
            return False
        else:
            print(f"\n✓ All routes are within {capacity_per_route} tree capacity")
            return True
    return True


def main():
    """Main execution function."""
    print("="*60)
    print("Simple Geographic Clustering for Routes")
    print("="*60)
    
    # Parse arguments
    test_mode = '--test' in sys.argv
    min_routes = 18
    max_capacity = 25  # Default to large trailer capacity
    
    for arg in sys.argv:
        if arg.startswith('--routes='):
            min_routes = int(arg.split('=')[1])
        elif arg.startswith('--capacity='):
            max_capacity = int(arg.split('=')[1])
    
    # Load data
    if test_mode:
        df = load_geocoded_data('data/2025-geocoded-full.csv')
        print("\n🧪 TEST MODE: Using 2025 dataset")
    else:
        df = load_geocoded_data()
        # Real trailer capacities:
        # - 16-foot trailer: 25 trees
        # - 12-foot trailer: 18 trees
        # Use the average/conservative value
        max_capacity = 22  # Conservative capacity (between 18 and 25)
        print(f"\nUsing capacity limit: {max_capacity} trees per route")
        print("  (Based on trailer sizes: 16ft=25 trees, 12ft=18 trees)")
    
    total_trees = int(df['Number of Trees'].sum())
    print(f"Total addresses: {len(df)}")
    print(f"Total trees: {total_trees}")
    
    # Auto-increment routes until all fit within capacity
    num_routes = min_routes
    max_routes = min_routes + 10  # Don't go crazy
    
    print(f"\nFinding optimal number of routes (starting at {min_routes})...")
    
    best_df = None
    best_stats = None
    
    for num_routes in range(min_routes, max_routes + 1):
        print(f"\n{'─'*60}")
        print(f"Trying {num_routes} routes...")
        
        df_test, stats_df = cluster_addresses(df.copy(), num_routes, max_capacity)
        
        # Check if all routes fit
        over_capacity = stats_df[stats_df['trees'] > max_capacity]
        
        if len(over_capacity) == 0:
            print(f"✓ Found solution with {num_routes} routes!")
            best_df = df_test
            best_stats = stats_df
            break
        else:
            print(f"  {len(over_capacity)} routes still over capacity")
            best_df = df_test  # Keep trying
            best_stats = stats_df
    
    if best_df is None or best_stats is None:
        print(f"\n⚠️  Could not find solution within {max_routes} routes!")
        return
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"FINAL SOLUTION: {num_routes} ROUTES")
    print(f"{'='*60}")
    
    print_route_summary(best_stats, max_capacity)
    
    # Save results
    if test_mode:
        output_path = 'data/2025-clustered-routes.csv'
    else:
        output_path = 'data/2026-clustered-routes.csv'
    
    best_df.to_csv(output_path, index=False)
    print(f"\n✓ Routes saved to: {output_path}")
    
    print(f"\n{'='*60}")
    print("NEXT STEPS")
    print(f"{'='*60}")
    print("\n1. Generate map to visualize routes:")
    if test_mode:
        print("   uv run python src/generate_map.py --test")
    else:
        print("   uv run python src/generate_map.py")
    print("\n2. Review the map and adjust manually if needed")
    print("\n3. Use the CSV file to assign routes to volunteers")


if __name__ == '__main__':
    main()
