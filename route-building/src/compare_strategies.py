#!/usr/bin/env python3
"""
Compare results from different optimization strategies.
"""

import sys
from pathlib import Path
import pandas as pd
import re

def main():
    results_dir = Path('data')
    pattern = '2025-optimized-routes-*.csv'
    
    print("="*80)
    print("OPTIMIZATION STRATEGY COMPARISON")
    print("="*80)
    
    results = []
    
    # Find all strategy result files
    result_files = list(results_dir.glob(pattern))
    
    if not result_files:
        print("\nNo strategy result files found!")
        print(f"Looking for: {results_dir}/{pattern}")
        return
    
    print(f"\nFound {len(result_files)} result files:\n")
    
    for file_path in sorted(result_files):
        # Extract strategy name from filename
        match = re.search(r'routes-(\w+)\.csv', file_path.name)
        strategy = match.group(1) if match else 'unknown'
        
        # Load the data
        df = pd.read_csv(file_path)
        
        # Calculate statistics
        num_addresses = len(df)
        num_routes = df['optimized_route'].nunique()
        total_trees = df['Number of Trees'].sum()
        
        # Calculate route statistics
        route_stats = df.groupby('optimized_route').agg({
            'Name': 'count',
            'Number of Trees': 'sum'
        }).rename(columns={'Name': 'pickups', 'Number of Trees': 'trees'})
        
        avg_pickups = route_stats['pickups'].mean()
        std_pickups = route_stats['pickups'].std()
        avg_trees = route_stats['trees'].mean()
        std_trees = route_stats['trees'].std()
        
        results.append({
            'strategy': strategy,
            'file': file_path.name,
            'addresses': num_addresses,
            'routes': num_routes,
            'total_trees': int(total_trees),
            'avg_pickups': f"{avg_pickups:.1f}",
            'std_pickups': f"{std_pickups:.1f}",
            'avg_trees': f"{avg_trees:.1f}",
            'std_trees': f"{std_trees:.1f}"
        })
    
    # Print results table
    print(f"{'Strategy':<15} {'Routes':<8} {'Addresses':<10} {'Avg Pickups/Route':<20} {'Avg Trees/Route':<20}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['strategy']:<15} {r['routes']:<8} {r['addresses']:<10} "
              f"{r['avg_pickups']:>6} ± {r['std_pickups']:<6}   "
              f"{r['avg_trees']:>6} ± {r['std_trees']:<6}")
    
    # Check logs for timing information
    print("\n" + "="*80)
    print("TIMING INFORMATION (from logs)")
    print("="*80 + "\n")
    
    logs_dir = Path('logs')
    for result in results:
        strategy = result['strategy']
        log_file = logs_dir / f"strategy-{strategy}.log"
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                content = f.read()
                
                # Look for solve time
                match = re.search(r'Solution found in ([\d.]+) seconds', content)
                if match:
                    solve_time = float(match.group(1))
                    print(f"{strategy:<15} {solve_time:>8.2f} seconds ({solve_time/60:>6.2f} minutes)")
                else:
                    # Check if it failed
                    if 'No solution found' in content:
                        match = re.search(r'No solution found after ([\d.]+) seconds', content)
                        if match:
                            solve_time = float(match.group(1))
                            print(f"{strategy:<15} {solve_time:>8.2f} seconds (NO SOLUTION)")
                        else:
                            print(f"{strategy:<15} NO SOLUTION (time unknown)")
                    else:
                        print(f"{strategy:<15} (still running or incomplete)")
        else:
            print(f"{strategy:<15} (no log file found)")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80 + "\n")
    
    print("Choose the strategy with:")
    print("  1. Lowest standard deviation in pickups/route (more balanced)")
    print("  2. Reasonable solve time (< 30 minutes preferred)")
    print("  3. All routes filled (addresses = expected based on route count)")
    print("\nThen generate the map and review the routes visually.")

if __name__ == '__main__':
    main()
