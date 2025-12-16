#!/usr/bin/env python3
"""
Route optimization using Google OR-Tools Vehicle Routing Problem solver.

This script takes geocoded addresses and creates optimized pickup routes
that minimize total distance while balancing workload across routes.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Dict, Tuple, Optional
import math


def load_geocoded_data(csv_path: str = 'data/2025-geocoded-full.csv', limit: Optional[int] = None) -> pd.DataFrame:
    """Load geocoded data.
    
    Args:
        csv_path: Path to the geocoded CSV file
        limit: Optional limit on number of addresses to load (for testing)
    """
    file_path = Path(csv_path)
    if not file_path.exists():
        print(f"Error: File not found: {csv_path}")
        print("Run geocode_google.py first to geocode the addresses.")
        sys.exit(1)
    
    df = pd.read_csv(file_path)
    
    # Filter out any addresses that failed geocoding
    df_valid = df[df['latitude'].notna() & df['longitude'].notna()].copy()
    
    # Apply limit if specified (for testing)
    if limit is not None and limit > 0:
        df_valid = df_valid.head(limit)
        print(f"🧪 TEST MODE: Limited to first {len(df_valid)} addresses")
    
    print(f"Loaded {len(df_valid)} geocoded addresses from {csv_path}")
    if len(df_valid) < len(df):
        print(f"Note: {len(df) - len(df_valid)} addresses were not geocoded")
    
    return df_valid


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.
    
    Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def create_distance_matrix(df: pd.DataFrame, depot_index: int = 0) -> np.ndarray:
    """
    Create a distance matrix between all locations.
    
    Args:
        df: DataFrame with latitude and longitude columns
        depot_index: Index of the depot (starting point) - defaults to first location
        
    Returns:
        2D numpy array of distances in meters
    """
    print("\nCreating distance matrix...")
    
    n = len(df)
    distance_matrix = np.zeros((n, n))
    
    coords = list(zip(df['latitude'], df['longitude']))
    
    for i in range(n):
        for j in range(i+1, n):
            dist = haversine_distance(
                coords[i][0], coords[i][1],
                coords[j][0], coords[j][1]
            )
            distance_matrix[i][j] = dist
            distance_matrix[j][i] = dist
    
    print(f"Distance matrix created: {n}x{n}")
    return distance_matrix


def create_data_model(
    df: pd.DataFrame, 
    num_vehicles: int, 
    vehicle_capacities: List[int],
    depot_index: int = 0
) -> Dict:
    """
    Create the data model for OR-Tools.
    
    Args:
        df: DataFrame with geocoded addresses
        num_vehicles: Number of routes (vehicles) to create
        vehicle_capacities: List of tree capacities for each vehicle
        depot_index: Starting point index
        
    Returns:
        Dictionary with all data needed for the solver
    """
    print(f"\nCreating data model for {num_vehicles} routes...")
    
    distance_matrix = create_distance_matrix(df, depot_index)
    
    # Get tree counts for capacity constraints
    tree_col = 'Number of Trees'
    demands = df[tree_col].fillna(1).astype(int).tolist()
    
    data = {
        'distance_matrix': distance_matrix.astype(int).tolist(),
        'demands': demands,
        'num_vehicles': num_vehicles,
        'depot': depot_index,
        'vehicle_capacities': vehicle_capacities
    }
    
    total_trees = sum(demands)
    avg_per_route = total_trees / num_vehicles
    total_capacity = sum(vehicle_capacities)
    
    print(f"Total trees: {total_trees}")
    print(f"Total trailer capacity: {total_capacity} trees")
    print(f"Average per route: {avg_per_route:.1f} trees")
    
    if total_trees > total_capacity:
        print(f"⚠️  WARNING: Not enough capacity! Need {total_trees - total_capacity} more tree slots")
    else:
        print(f"✓ Sufficient capacity ({total_capacity - total_trees} trees spare)")
    
    return data


def print_solution(data: Dict, manager, routing, solution, df: pd.DataFrame):
    """
    Print the solution and return route assignments.
    
    Returns:
        DataFrame with route assignments
    """
    print("\n" + "="*60)
    print("OPTIMIZED ROUTES")
    print("="*60)
    
    total_distance = 0
    route_assignments = {}
    
    # Route letters (A, B, C... then AA, AB, AC... if more than 26)
    def get_route_letter(i):
        if i < 26:
            return chr(65 + i)
        else:
            return chr(65 + i // 26 - 1) + chr(65 + i % 26)
    
    for vehicle_id in range(data['num_vehicles']):
        route_letter = get_route_letter(vehicle_id)
        index = routing.Start(vehicle_id)
        route_distance = 0
        route_load = 0
        route_indices = []
        
        # Build the route
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_indices.append(node_index)
            route_load += data['demands'][node_index]
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            # Get distance from the distance matrix directly
            from_node = manager.IndexToNode(previous_index)
            to_node = manager.IndexToNode(index)
            route_distance += data['distance_matrix'][from_node][to_node]
        
        # Don't include depot in the output
        route_indices = [i for i in route_indices if i != data['depot']]
        
        # Store assignments
        for idx in route_indices:
            route_assignments[idx] = route_letter
        
        total_distance += route_distance
        
        print(f"\nRoute {route_letter}:")
        print(f"  Pickups: {len(route_indices)}")
        print(f"  Trees: {route_load}")
        print(f"  Distance: {route_distance/1609.34:.1f} miles ({route_distance/1000:.1f} km)")
        
        # Show first few addresses
        if len(route_indices) > 0:
            print(f"  Sample addresses:")
            for idx in route_indices[:3]:
                row = df.iloc[idx]
                print(f"    - {row['Name']}: {row['full_address']}")
            if len(route_indices) > 3:
                print(f"    ... and {len(route_indices) - 3} more")
    
    print(f"\n{'='*60}")
    print(f"Total distance: {total_distance/1609.34:.1f} miles ({total_distance/1000:.1f} km)")
    print(f"{'='*60}")
    
    # Add route assignments to dataframe
    df_result = df.copy()
    df_result['optimized_route'] = df_result.index.map(route_assignments)
    
    # Fill NaN (depot) with a marker so it's clear it's excluded
    # But actually, let's just drop the depot row from output since it's not a pickup
    df_result = df_result[df_result['optimized_route'].notna()].copy()
    
    return df_result


def solve_vrp(
    df: pd.DataFrame, 
    num_vehicles: int = 23, 
    time_limit_seconds: int = 30,
    trailer_capacities: List[int] = None
) -> pd.DataFrame:
    """
    Solve the Vehicle Routing Problem.
    
    Args:
        df: DataFrame with geocoded addresses
        num_vehicles: Number of routes to create (default 23, same as 2025)
        time_limit_seconds: Time limit for solver
        trailer_capacities: List of tree capacities for each vehicle/route
                           If None, uses balanced distribution
        
    Returns:
        DataFrame with route assignments
    """
    print("\n" + "="*60)
    print("GOOGLE OR-TOOLS VRP SOLVER")
    print("="*60)
    
    # If no specific capacities provided, create balanced ones
    if trailer_capacities is None:
        total_trees = df['Number of Trees'].fillna(1).sum()
        avg_capacity = int(total_trees / num_vehicles * 1.5)
        trailer_capacities = [avg_capacity] * num_vehicles
    
    # Validate capacities
    if len(trailer_capacities) != num_vehicles:
        print(f"Warning: Expected {num_vehicles} trailer capacities, got {len(trailer_capacities)}")
        # Adjust by repeating the pattern
        if len(trailer_capacities) < num_vehicles:
            trailer_capacities = (trailer_capacities * ((num_vehicles // len(trailer_capacities)) + 1))[:num_vehicles]
    
    print(f"\nTrailer configuration:")
    capacity_counts = {}
    for cap in trailer_capacities:
        capacity_counts[cap] = capacity_counts.get(cap, 0) + 1
    for cap, count in sorted(capacity_counts.items(), reverse=True):
        trailer_size = "16-foot" if cap >= 20 else "12-foot"
        print(f"  {count}x {trailer_size} trailers ({cap} tree capacity)")
    
    # Create the data model
    data = create_data_model(df, num_vehicles, trailer_capacities)
    
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'],
        data['depot']
    )
    
    # Create routing model
    routing = pywrapcp.RoutingModel(manager)
    
    # Create distance callback
    def distance_callback(from_index, to_index):
        """Return the distance between two points."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]
    
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    
    # Define cost of each arc (edge)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # Add capacity constraint (tree count based on trailer size)
    def demand_callback(from_index):
        """Return the demand (trees) at each node."""
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]
    
    demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
    
    # Use actual trailer capacities with small slack for solver flexibility
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        2,  # allow 2 trees of slack per route to help solver find solutions
        data['vehicle_capacities'],  # vehicle maximum capacities (from trailer sizes)
        True,  # start cumul to zero
        'Capacity'
    )
    
    # Add constraint to balance pickups across routes
    # This encourages distributing work evenly
    count_dimension_name = 'PickupCount'
    routing.AddConstantDimension(
        1,  # increment by 1 for each location visited
        len(data['distance_matrix']),  # max pickups per route
        True,  # start at zero
        count_dimension_name
    )
    count_dimension = routing.GetDimensionOrDie(count_dimension_name)
    
    # Add penalty for unbalanced routes - heavily penalize routes with many more pickups
    # This encourages the solver to distribute pickups more evenly
    for vehicle_id in range(data['num_vehicles']):
        count_dimension.SetSpanCostCoefficientForVehicle(100000, vehicle_id)
    
    # Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = time_limit_seconds
    
    print(f"\nSolving with time limit: {time_limit_seconds} seconds...")
    print("Using Guided Local Search metaheuristic...")
    
    # Solve
    import time
    start_time = time.time()
    if solution:
        print(f"\n✓ Solution found in {solve_time:.2f} seconds!")
        df_result = print_solution(data, manager, routing, solution, df)
        return df_result
    else:
        print(f"\n✗ No solution found after {solve_time:.2f} seconds!")
        print("Tip: Try with more routes or longer time limit")
        df_result = df.copy()
        df_result['optimized_route'] = None
        return df_result


def compare_to_actual_routes(df: pd.DataFrame):
    """Compare optimized routes to actual 2025 routes."""
    if 'Route' not in df.columns or 'optimized_route' not in df.columns:
        print("\nCannot compare - missing route data")
        return
    
    print("\n" + "="*60)
    print("COMPARISON: Optimized vs Actual 2025 Routes")
    print("="*60)
    
    # Count how many addresses stayed in the same route
    df_compare = df[df['Route'].notna() & df['optimized_route'].notna()].copy()
    same_route = (df_compare['Route'] == df_compare['optimized_route']).sum()
    total = len(df_compare)
    
    print(f"\nAddresses in same route: {same_route}/{total} ({same_route/total*100:.1f}%)")
    
    # Show route size comparison
    print(f"\n{'Route':<8} {'2025 Actual':<15} {'Optimized':<15} {'Difference':<12}")
    print("-" * 60)
    
    for route in sorted(df_compare['Route'].unique()):
        actual_count = (df_compare['Route'] == route).sum()
        optimized_count = (df_compare['optimized_route'] == route).sum()
        diff = optimized_count - actual_count
        diff_str = f"{diff:+d}" if diff != 0 else "0"
        print(f"{route:<8} {actual_count:<15} {optimized_count:<15} {diff_str:<12}")


def main():
    """Main execution function."""
    print("="*60)
    print("Route Optimization with OR-Tools VRP")
    print("="*60)
    
    # Check for test mode
    import sys
    test_mode = '--test' in sys.argv
    test_limit = None
    if test_mode:
        # Default to 13 addresses (12 pickups + 1 depot)
        test_limit = 13
        for arg in sys.argv:
            if arg.startswith('--limit='):
                try:
                    test_limit = int(arg.split('=')[1])
                except ValueError:
                    pass
    
    # Load geocoded data
    df = load_geocoded_data(limit=test_limit)
    
    # Remove any existing route assignments - we're creating fresh routes
    if 'Route' in df.columns:
        df = df.drop(columns=['Route'])
        print("Note: Existing route assignments ignored - creating fresh optimized routes")
    
    # Ask user for number of routes
    print(f"\nTotal addresses to route: {len(df)}")
    print("Suggested: 15-25 routes (depending on volunteer availability)")
    
    # Trailer configuration
    # Each trailer can do multiple routes in series (prefer 3, max 4)
    # TODO: Make these configurable via command line or config file
    if test_mode:
        # Test mode: smaller capacities to force distribution
        NUM_LARGE_TRAILERS = 2
        NUM_SMALL_TRAILERS = 0
        CAPACITY_LARGE = 7      # Smaller capacity for testing (allows some slack)
        CAPACITY_SMALL = 7
        ROUTES_PER_TRAILER = 1
    else:
        NUM_LARGE_TRAILERS = 4  # Large (16-foot) trailers
        NUM_SMALL_TRAILERS = 2  # Small (12-foot) trailers
        CAPACITY_LARGE = 24     # Trees per route for large trailer
        CAPACITY_SMALL = 16     # Trees per route for small trailer
        ROUTES_PER_TRAILER = 3  # Preferred routes per trailer (can go up to 4)
    
    # Calculate route limits
    print(f"\nTrailer inventory:")
    print(f"  {NUM_LARGE_TRAILERS}x large trailers (16-foot, {CAPACITY_LARGE} trees/route)")
    print(f"  {NUM_SMALL_TRAILERS}x small trailers (12-foot, {CAPACITY_SMALL} trees/route)")
    print(f"  Each trailer does {ROUTES_PER_TRAILER} routes in series (can do up to 4)")
    
    preferred_routes = (NUM_LARGE_TRAILERS + NUM_SMALL_TRAILERS) * ROUTES_PER_TRAILER
    max_routes = (NUM_LARGE_TRAILERS + NUM_SMALL_TRAILERS) * 4
    total_capacity_preferred = (NUM_LARGE_TRAILERS * CAPACITY_LARGE + NUM_SMALL_TRAILERS * CAPACITY_SMALL) * ROUTES_PER_TRAILER
    print(f"  Preferred total capacity: {total_capacity_preferred} trees across {preferred_routes} routes")
    
    print(f"\nPreferred routes: {preferred_routes} (3 routes per trailer)")
    print(f"Maximum routes: {max_routes} (4 routes per trailer if needed)")
    
    # In test mode, use sensible defaults
    if test_mode:
        num_routes = min(2, len(df) - 1)  # 2 routes for test, but not more than addresses
        print(f"\n🧪 TEST MODE: Using {num_routes} routes automatically")
    else:
        num_routes = None
    
    while num_routes is None:
        try:
            num_routes = int(input(f"\nHow many routes (1-{max_routes}, suggest {preferred_routes})? "))
            if num_routes < 1:
                print("Please enter a positive number")
                continue
            if num_routes > max_routes:
                print(f"Cannot use more than {max_routes} routes (4 routes per trailer limit)")
                continue
            if num_routes > len(df):
                print(f"Cannot have more routes than addresses ({len(df)})")
                continue
            if num_routes > preferred_routes:
                print(f"⚠️  Note: Using {num_routes} routes means some trailers do 4 routes instead of 3")
            break
        except ValueError:
            print("Please enter a valid number")
    
    # Create trailer capacity list
    # Distribute routes across trailers (large first, then small)
    large_routes = min(num_routes, NUM_LARGE_TRAILERS * ROUTES_PER_TRAILER)
    small_routes = max(0, num_routes - large_routes)
    
    trailer_capacities = [CAPACITY_LARGE] * large_routes + [CAPACITY_SMALL] * small_routes
    
    # Show distribution
    if num_routes <= preferred_routes:
        large_per = min(ROUTES_PER_TRAILER, (large_routes + NUM_LARGE_TRAILERS - 1) // NUM_LARGE_TRAILERS)
        small_per = min(ROUTES_PER_TRAILER, (small_routes + NUM_SMALL_TRAILERS - 1) // NUM_SMALL_TRAILERS) if small_routes > 0 else 0
        print(f"\n→ Route distribution: {large_routes} large-capacity routes, {small_routes} small-capacity routes")
        print(f"   (~{large_per} routes per large trailer, ~{small_per} routes per small trailer)")
    else:
        print(f"\n→ Route distribution: {large_routes} large-capacity routes, {small_routes} small-capacity routes")
        print(f"   ⚠️  Some trailers will do 4 routes")
    
    print(f"\n→ Creating {num_routes} optimized routes with trailer constraints...")
    
    # Solve VRP with trailer capacities
    df_optimized = solve_vrp(
        df, 
        num_vehicles=num_routes, 
        time_limit_seconds=60,  # Increased to 60 seconds for better solutions
        trailer_capacities=trailer_capacities
    )
    
    # Only proceed with comparison if we got a solution
    if df_optimized['optimized_route'].notna().any():
        # Optional: Compare to manual 2025 routes if available (skip in test mode)
        if not test_mode:
            manual_file = 'data/2025-tree_requests.csv.manual'
            if Path(manual_file).exists():
                df_manual = pd.read_csv(manual_file)
                if 'Route' in df_manual.columns:
                    # Merge manual routes back for comparison
                    df_optimized['manual_route'] = df_manual['Route']
                    print("\n" + "="*60)
                    print("COMPARISON: Optimized vs Manual 2025 Routes")
                    print("="*60)
                    print("(This is informational only - not used in optimization)")
                    # Show basic comparison
                    if 'manual_route' in df_optimized.columns:
                        same_route = (df_optimized['optimized_route'] == df_optimized['manual_route']).sum()
                        total = len(df_optimized[df_optimized['manual_route'].notna()])
                        if total > 0:
                            print(f"\nAddresses in same route: {same_route}/{total} ({same_route/total*100:.1f}%)")
            else:
                print(f"\nNote: No manual routes file found ({manual_file}) - skipping comparison")
    else:
        print("\n⚠️  No solution found - skipping comparison and statistics")
        return
    
    # Save results
    if test_mode:
        output_path = 'data/2025-test-optimized-routes.csv'
    else:
        output_path = 'data/2025-optimized-routes.csv'
    
    df_optimized.to_csv(output_path, index=False)
    print(f"\n✓ Optimized routes saved to: {output_path}")
    
    # Show a preview of the output
    print(f"\n📋 Preview of output (first 10 rows):")
    preview_cols = ['Name', 'full_address', 'Number of Trees', 'optimized_route', 'latitude', 'longitude']
    print(df_optimized[preview_cols].head(10).to_string())
    
    # Show some statistics
    print("\n" + "="*60)
    print("ROUTE STATISTICS")
    print("="*60)
    
    for route in sorted(df_optimized['optimized_route'].dropna().unique()):
        route_df = df_optimized[df_optimized['optimized_route'] == route]
        trees = route_df['Number of Trees'].sum()
        print(f"Route {route}: {len(route_df)} pickups, {trees:.0f} trees")


if __name__ == '__main__':
    main()
