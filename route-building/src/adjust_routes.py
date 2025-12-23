#!/usr/bin/env python3
"""
Interactive tool for manually adjusting route assignments.

Provides menu-driven interface for:
1. Moving customers between routes
2. Identifying problem routes (too large or too small)
"""

import sys
import string
from pathlib import Path
import pandas as pd
from typing import Optional


def load_routes(csv_path: str = 'data/2025-clustered-routes.csv') -> pd.DataFrame:
    """Load route assignments."""
    file_path = Path(csv_path)
    if not file_path.exists():
        print(f"Error: File not found: {csv_path}")
        print("Run cluster_routes.py first to generate routes.")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} addresses from {csv_path}")
    return df


def find_customer(df: pd.DataFrame, search_name: str) -> Optional[pd.DataFrame]:
    """
    Find customer(s) by name (case-insensitive partial match).
    
    Returns:
        DataFrame with matching rows, or None if no matches
    """
    matches = df[df['Name'].str.contains(search_name, case=False, na=False)]
    return matches if len(matches) > 0 else None


def move_customer(df: pd.DataFrame, csv_path: str):
    """Interactive flow to move a customer to a different route."""
    print("\n" + "="*60)
    print("MOVE CUSTOMER TO DIFFERENT ROUTE")
    print("="*60)
    
    # Get customer name
    search_name = input("\nEnter customer name (or part of name): ").strip()
    if not search_name:
        print("Cancelled.")
        return df
    
    # Find matching customers
    matches = find_customer(df, search_name)
    
    if matches is None:
        print(f"\n❌ No customers found matching '{search_name}'")
        return df
    
    # Show matches
    if len(matches) > 1:
        print(f"\nFound {len(matches)} matches:")
        for idx, row in matches.iterrows():
            print(f"  [{idx}] {row['Name']} - Route {row['optimized_route']} - {row['full_address']}")
        
        try:
            selected_idx = int(input("\nEnter the number in brackets to select: ").strip())
            if selected_idx not in matches.index:
                print("Invalid selection.")
                return df
        except (ValueError, KeyboardInterrupt):
            print("\nCancelled.")
            return df
    else:
        selected_idx = matches.index[0]
        row = matches.iloc[0]
        print(f"\nFound: {row['Name']} - Route {row['optimized_route']}")
        print(f"Address: {row['full_address']}")
        print(f"Trees: {int(row['Number of Trees'])}")
    
    # Get new route
    current_route = df.loc[selected_idx, 'optimized_route']
    new_route = input(f"\nEnter new route (currently: {current_route}): ").strip().upper()
    
    if not new_route:
        print("Cancelled.")
        return df
    
    # Confirm
    confirm = input(f"\nMove {df.loc[selected_idx, 'Name']} from Route {current_route} to Route {new_route}? (y/n): ").strip().lower()
    
    if confirm == 'y':
        df.loc[selected_idx, 'optimized_route'] = new_route
        df.to_csv(csv_path, index=False)
        print(f"\n✓ Customer moved to Route {new_route}")
        print(f"✓ Changes saved to {csv_path}")
    else:
        print("Cancelled.")
    
    return df


def show_problem_routes(df: pd.DataFrame):
    """Show routes that are too large or too small."""
    print("\n" + "="*60)
    print("PROBLEM ROUTES")
    print("="*60)
    
    # Calculate route statistics
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
    
    stats_df = pd.DataFrame(route_stats)
    
    # Find problems
    too_large = stats_df[stats_df['trees'] > 24]
    too_small = stats_df[stats_df['trees'] < 10]
    
    # Display
    if len(too_large) > 0:
        print("\n🔴 Routes with MORE than 24 trees:")
        print("-" * 60)
        for _, row in too_large.iterrows():
            print(f"  Route {row['route']}: {row['pickups']} pickups, {row['trees']} trees (OVER by {row['trees'] - 24})")
    else:
        print("\n✓ No routes over 24 trees")
    
    if len(too_small) > 0:
        print("\n🟡 Routes with LESS than 10 trees:")
        print("-" * 60)
        for _, row in too_small.iterrows():
            print(f"  Route {row['route']}: {row['pickups']} pickups, {row['trees']} trees")
    else:
        print("\n✓ No routes under 10 trees")
    
    # Show all route stats
    print("\n" + "="*60)
    print("ALL ROUTES")
    print("="*60)
    for _, row in stats_df.iterrows():
        status = ""
        if row['trees'] > 24:
            status = " 🔴"
        elif row['trees'] < 10:
            status = " 🟡"
        print(f"Route {row['route']}: {row['pickups']:3d} pickups, {row['trees']:3d} trees{status}")


def merge_routes(df: pd.DataFrame, csv_path: str):
    """Merge two routes into one new route."""
    print("\n" + "="*60)
    print("MERGE TWO ROUTES")
    print("="*60)
    
    # Show current routes
    routes = sorted(df['optimized_route'].unique())
    print(f"\nAvailable routes: {', '.join(routes)}")
    
    # Get first route
    route1 = input("\nEnter first route to merge: ").strip().upper()
    if route1 not in routes:
        print(f"❌ Route {route1} not found")
        return df
    
    # Get second route
    route2 = input("Enter second route to merge: ").strip().upper()
    if route2 not in routes:
        print(f"❌ Route {route2} not found")
        return df
    
    if route1 == route2:
        print("❌ Cannot merge a route with itself")
        return df
    
    # Show route details
    route1_df = df[df['optimized_route'] == route1]
    route2_df = df[df['optimized_route'] == route2]
    
    trees1 = int(route1_df['Number of Trees'].sum())
    trees2 = int(route2_df['Number of Trees'].sum())
    total_trees = trees1 + trees2
    
    print(f"\nRoute {route1}: {len(route1_df)} pickups, {trees1} trees")
    print(f"Route {route2}: {len(route2_df)} pickups, {trees2} trees")
    print(f"Combined: {len(route1_df) + len(route2_df)} pickups, {total_trees} trees")
    
    if total_trees > 24:
        print(f"⚠️  Warning: Combined route would have {total_trees} trees (over 24 tree capacity)")
    
    # Get new route name
    new_route = input(f"\nEnter new route name (default: {route1}): ").strip().upper()
    if not new_route:
        new_route = route1
    
    # Confirm
    confirm = input(f"\nMerge Route {route1} and Route {route2} into Route {new_route}? (y/n): ").strip().lower()
    
    if confirm == 'y':
        df.loc[df['optimized_route'] == route1, 'optimized_route'] = new_route
        df.loc[df['optimized_route'] == route2, 'optimized_route'] = new_route
        df.to_csv(csv_path, index=False)
        print(f"\n✓ Routes merged into Route {new_route}")
        print(f"✓ Changes saved to {csv_path}")
    else:
        print("Cancelled.")
    
    return df


def split_route(df: pd.DataFrame, csv_path: str):
    """Move selected customers from a route into a brand new route."""
    print("\n" + "="*60)
    print("SPLIT A ROUTE / START NEW ROUTE")
    print("="*60)

    routes = sorted(df['optimized_route'].unique())
    print(f"\nAvailable routes: {', '.join(routes)}")

    route_to_split = input("\nEnter the route you want to split: ").strip().upper()
    if route_to_split not in routes:
        print(f"❌ Route {route_to_split} not found")
        return df

    route_df = df[df['optimized_route'] == route_to_split]
    if len(route_df) == 0:
        print(f"❌ Route {route_to_split} has no customers")
        return df

    print(f"\nRoute {route_to_split} contains {len(route_df)} pickups:")
    for idx, row in route_df.iterrows():
        trees = int(row['Number of Trees'])
        print(f"  [{idx}] {row['Name']} - {row['full_address']} ({trees} trees)")

    selection = input("\nEnter the numbers in brackets to move (comma-separated): ").strip()
    if not selection:
        print("Cancelled.")
        return df

    try:
        selected_indices = {int(idx.strip()) for idx in selection.split(',') if idx.strip()}
    except ValueError:
        print("❌ Invalid selection format. Use comma-separated numbers, e.g. 12,15,20")
        return df

    route_indices = set(route_df.index.tolist())
    if not selected_indices.issubset(route_indices):
        print("❌ One or more selected numbers are not part of that route")
        return df

    selected_df = df.loc[list(selected_indices)]
    selected_trees = int(selected_df['Number of Trees'].sum())

    # Suggest a new route letter that is not used yet
    suggestion = next((letter for letter in string.ascii_uppercase if letter not in routes), None)
    prompt = "Enter new route letter/name"
    if suggestion:
        prompt += f" (suggested: {suggestion})"
    prompt += ": "

    new_route = input(f"\n{prompt}").strip().upper()
    if not new_route:
        if suggestion:
            new_route = suggestion
            print(f"Using suggested route {suggestion}")
        else:
            print("❌ No route entered")
            return df

    if new_route in routes:
        confirm_existing = input(f"Route {new_route} already exists. Continue anyway? (y/n): ").strip().lower()
        if confirm_existing != 'y':
            print("Cancelled.")
            return df

    print("\nThe following customers will move to the new route:")
    for _, row in selected_df.iterrows():
        trees = int(row['Number of Trees'])
        print(f"  {row['Name']} - {row['full_address']} ({trees} trees)")
    print(f"Total trees moving: {selected_trees}")

    confirm = input(f"\nCreate Route {new_route} by moving these customers from Route {route_to_split}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return df

    df.loc[list(selected_indices), 'optimized_route'] = new_route
    df.to_csv(csv_path, index=False)

    print(f"\n✓ Created Route {new_route} with {len(selected_df)} pickups ({selected_trees} trees)")
    print(f"✓ Updated Route {route_to_split} now has {len(route_df) - len(selected_df)} pickups")
    print(f"✓ Changes saved to {csv_path}")

    return df


def regenerate_map(test_mode: bool = False):
    """Regenerate the map by calling generate_map.py."""
    import subprocess
    
    print("\n" + "="*60)
    print("REGENERATE MAP")
    print("="*60)
    
    if test_mode:
        cmd = ['uv', 'run', 'src/generate_map.py', '--test']
    else:
        cmd = ['uv', 'run', 'src/generate_map.py']
    
    print("\nGenerating map...")
    try:
        result = subprocess.run(cmd, cwd=Path.cwd(), capture_output=False)
        if result.returncode == 0:
            print("\n✓ Map regenerated successfully")
        else:
            print(f"\n❌ Map generation failed with exit code {result.returncode}")
    except Exception as e:
        print(f"\n❌ Error running generate_map.py: {e}")


def show_menu():
    """Display main menu."""
    print("\n" + "="*60)
    print("ROUTE ADJUSTMENT TOOL")
    print("="*60)
    print("\n1. Move a customer to a different route")
    print("2. Split an existing route into a new route")
    print("3. Merge two routes into one")
    print("4. Show problem routes (>24 or <10 trees)")
    print("5. Regenerate map")
    print("6. Quit")
    print()


def main():
    """Main interactive loop."""
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    if test_mode:
        csv_path = 'data/2025-test-clustered-routes.csv'
        print("\n🧪 TEST MODE: Using test data")
    else:
        csv_path = 'data/2025-clustered-routes.csv'
    
    # Load routes
    df = load_routes(csv_path)
    
    # Interactive menu loop
    while True:
        show_menu()
        
        try:
            choice = input("Enter your choice (1-6): ").strip()

            if choice == '1':
                df = move_customer(df, csv_path)
            elif choice == '2':
                df = split_route(df, csv_path)
            elif choice == '3':
                df = merge_routes(df, csv_path)
            elif choice == '4':
                show_problem_routes(df)
            elif choice == '5':
                regenerate_map(test_mode)
            elif choice == '6':
                print("\nGoodbye!")
                break
            else:
                print("\n❌ Invalid choice. Please enter 1-6.")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == '__main__':
    main()
