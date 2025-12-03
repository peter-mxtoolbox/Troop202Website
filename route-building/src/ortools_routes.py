#!/usr/bin/env python3
"""
Route optimization using Google OR-Tools.

This script uses the OR-Tools library to optimize tree pickup routes
based on geographic clustering and distance minimization.
"""

import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time
from typing import List, Tuple, Optional
import sys


def load_data(csv_path: str = 'data/2025-tree_requests.csv') -> pd.DataFrame:
    """Load the tree requests data."""
    file_path = Path(csv_path)
    if not file_path.exists():
        print(f"Error: File not found: {csv_path}")
        sys.exit(1)
    
    df = pd.read_csv(file_path)
    print(f"Loaded {len(df)} requests from {csv_path}")
    return df


def geocode_addresses(df: pd.DataFrame, limit: Optional[int] = None) -> pd.DataFrame:
    """
    Geocode addresses to get latitude/longitude coordinates.
    
    Args:
        df: DataFrame with address columns
        limit: Limit number of addresses to geocode (for testing)
    
    Returns:
        DataFrame with added 'latitude' and 'longitude' columns
    """
    print("\nGeocoding addresses...")
    
    # Initialize geocoder (using free OpenStreetMap/Nominatim)
    geolocator = Nominatim(user_agent="tree_recycling_routes")
    
    # Create full address string
    df['full_address'] = (
        df['House #'].astype(str) + ' ' + 
        df['Street'].astype(str) + ', ' + 
        df['City'].astype(str) + ', TX'  # Assuming Texas
    )
    
    # Limit for testing if specified
    if limit:
        df_to_geocode = df.head(limit).copy()
        print(f"Geocoding first {limit} addresses for testing...")
    else:
        df_to_geocode = df.copy()
    
    latitudes = []
    longitudes = []
    
    for idx, row in df_to_geocode.iterrows():
        try:
            location = geolocator.geocode(row['full_address'])
            if location:
                latitudes.append(location.latitude)
                longitudes.append(location.longitude)
                print(f"  [{idx+1}/{len(df_to_geocode)}] ✓ {row['Name']}: {row['full_address']}")
            else:
                latitudes.append(None)
                longitudes.append(None)
                print(f"  [{idx+1}/{len(df_to_geocode)}] ✗ Failed: {row['full_address']}")
            
            # Rate limiting - Nominatim requires 1 request per second
            time.sleep(1.1)
            
        except Exception as e:
            print(f"  [{idx+1}/{len(df_to_geocode)}] Error: {e}")
            latitudes.append(None)
            longitudes.append(None)
            time.sleep(1.1)
    
    df_to_geocode['latitude'] = latitudes
    df_to_geocode['longitude'] = longitudes
    
    successful = df_to_geocode['latitude'].notna().sum()
    print(f"\nGeocoding complete: {successful}/{len(df_to_geocode)} successful")
    
    return df_to_geocode


def analyze_existing_routes(df: pd.DataFrame) -> None:
    """Analyze the existing route assignments from 2025."""
    print("\n" + "="*60)
    print("EXISTING 2025 ROUTE ANALYSIS")
    print("="*60)
    
    # Get unique routes
    routes = df['Route'].dropna().unique()
    print(f"\nTotal routes: {len(routes)}")
    print(f"Routes: {sorted(routes)}")
    
    # Summary by route
    print(f"\n{'Route':<10} {'Count':<10} {'Trees':<10}")
    print("-" * 30)
    
    for route in sorted(routes):
        route_df = df[df['Route'] == route]
        count = len(route_df)
        # Handle different column name variations
        tree_col = 'Number of Trees' if 'Number of Trees' in df.columns else 'Number of Trees'
        total_trees = route_df[tree_col].sum()
        print(f"{route:<10} {count:<10} {total_trees:<10.0f}")
    
    print("-" * 30)
    print(f"{'TOTAL':<10} {len(df):<10} {df[tree_col].sum():<10.0f}")


def create_distance_matrix(df: pd.DataFrame) -> List[List[float]]:
    """
    Create a distance matrix between all locations.
    
    Args:
        df: DataFrame with latitude and longitude columns
        
    Returns:
        2D list of distances in meters
    """
    print("\nCreating distance matrix...")
    
    # Filter out any rows without coordinates
    df_valid = df[df['latitude'].notna() & df['longitude'].notna()].copy()
    
    n = len(df_valid)
    distance_matrix = [[0.0] * n for _ in range(n)]
    
    coords = list(zip(df_valid['latitude'], df_valid['longitude']))
    
    for i in range(n):
        for j in range(i+1, n):
            # Calculate geodesic distance in meters
            dist = geodesic(coords[i], coords[j]).meters
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist
    
    print(f"Distance matrix created: {n}x{n}")
    return distance_matrix, df_valid


def simple_clustering_demo(df: pd.DataFrame, num_routes: int = 10) -> None:
    """
    Demonstrate simple geographic clustering as a starting point.
    
    Args:
        df: DataFrame with geocoded addresses
        num_routes: Number of routes to create
    """
    from sklearn.cluster import KMeans
    import numpy as np
    
    print("\n" + "="*60)
    print(f"SIMPLE CLUSTERING DEMO ({num_routes} routes)")
    print("="*60)
    
    # Filter valid coordinates
    df_valid = df[df['latitude'].notna() & df['longitude'].notna()].copy()
    
    # Perform K-means clustering
    coords = df_valid[['latitude', 'longitude']].values
    kmeans = KMeans(n_clusters=num_routes, random_state=42, n_init=10)
    df_valid['suggested_route'] = kmeans.fit_predict(coords)
    
    # Map to route letters (A, B, C, etc.)
    route_letters = [chr(65 + i) for i in range(num_routes)]  # A-Z
    df_valid['suggested_route_letter'] = df_valid['suggested_route'].apply(lambda x: route_letters[x])
    
    print(f"\n{'Route':<10} {'Count':<10} {'Trees':<10}")
    print("-" * 30)
    
    tree_col = 'Number of Trees'
    for i, letter in enumerate(route_letters):
        route_df = df_valid[df_valid['suggested_route'] == i]
        count = len(route_df)
        total_trees = route_df[tree_col].sum()
        print(f"{letter:<10} {count:<10} {total_trees:<10.0f}")
    
    print("-" * 30)
    print(f"{'TOTAL':<10} {len(df_valid):<10} {df_valid[tree_col].sum():<10.0f}")
    
    # Compare to actual routes if they exist
    if 'Route' in df_valid.columns and df_valid['Route'].notna().any():
        print("\nComparing to actual 2025 routes...")
        comparison = df_valid[['Name', 'full_address', 'Route', 'suggested_route_letter']]
        print("\nFirst 10 comparisons:")
        print(comparison.head(10).to_string())
    
    return df_valid


def main():
    """Main execution function."""
    print("="*60)
    print("Google OR-Tools Route Optimization Demo")
    print("="*60)
    
    # Load data
    df = load_data()
    
    # Analyze existing routes
    analyze_existing_routes(df)
    
    # Geocode a sample (let's start with just 20 addresses for testing)
    print("\n" + "="*60)
    print("GEOCODING SAMPLE")
    print("="*60)
    print("Starting with 20 addresses to test (1 sec per address due to rate limits)")
    print("This will take about 20-25 seconds...")
    
    df_geocoded = geocode_addresses(df, limit=20)
    
    # Save geocoded results
    output_path = 'data/2025-geocoded-sample.csv'
    df_geocoded.to_csv(output_path, index=False)
    print(f"\nGeocoded data saved to: {output_path}")
    
    # Simple clustering demo
    if df_geocoded['latitude'].notna().sum() > 5:
        df_clustered = simple_clustering_demo(df_geocoded, num_routes=5)
        
        # Save with suggested routes
        output_path = 'data/2025-with-suggested-routes.csv'
        df_clustered.to_csv(output_path, index=False)
        print(f"\nClustered data saved to: {output_path}")
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Review the geocoding results")
    print("2. Check the suggested route clustering")
    print("3. If this looks good, we can:")
    print("   - Geocode all 358 addresses (takes ~6-7 minutes)")
    print("   - Implement full OR-Tools VRP solver")
    print("   - Add constraints (tree count balance, distance optimization)")
    print("="*60)


if __name__ == '__main__':
    main()
