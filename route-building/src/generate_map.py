#!/usr/bin/env python3
"""
Generate an interactive HTML map showing optimized routes.

This script creates a Folium map with color-coded routes and markers for each pickup location.
"""

import sys
from pathlib import Path
import pandas as pd
import folium
from typing import Optional
import re


def load_optimized_routes(csv_path: str = 'data/2026-optimized-routes.csv') -> pd.DataFrame:
    """Load optimized routes data."""
    file_path = Path(csv_path)
    if not file_path.exists():
        print(f"Error: File not found: {csv_path}")
        print("Run optimize_routes.py first to generate optimized routes.")
        sys.exit(1)
    
    df = pd.read_csv(file_path)
    
    # Filter out any addresses without routes or coordinates
    df_valid = df[
        df['optimized_route'].notna() & 
        df['latitude'].notna() & 
        df['longitude'].notna()
    ].copy()
    
    print(f"Loaded {len(df_valid)} addresses with routes from {csv_path}")
    return df_valid


def create_route_map(df: pd.DataFrame, output_path: str = '../website/routes/2026/2026-routes-map.html'):
    """
    Create an interactive Folium map with all routes.
    
    Args:
        df: DataFrame with optimized routes and coordinates
        output_path: Path to save the HTML map file
    """
    print("\nCreating route map...")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Calculate map center (average of all coordinates)
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    # Create the base map
    route_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles='OpenStreetMap'
    )
    
    # Color palette for routes (using distinct colors)
    colors = [
        'red', 'blue', 'green', 'purple', 'orange', 'darkred',
        'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
        'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen',
        'gray', 'black', 'lightgray', 'brown', 'olive', 'lime',
        'gold', 'cyan'
    ]
    
    # Get unique routes sorted
    routes = sorted(df['optimized_route'].unique())
    print(f"Found {len(routes)} routes: {', '.join(routes)}")
    
    # Create a feature group for each route
    route_groups = {}
    for idx, route in enumerate(routes):
        route_color = colors[idx % len(colors)]
        route_groups[route] = {
            'color': route_color,
            'group': folium.FeatureGroup(name=f'Route {route}')
        }
    
    # Add markers for each address
    for _, row in df.iterrows():
        route = row['optimized_route']
        route_info = route_groups[route]
        
        # Escape HTML and JavaScript special characters to prevent errors
        import html
        def escape_for_js(text):
            """Escape text for safe use in JavaScript strings."""
            if pd.isna(text):
                return ''
            text = str(text)
            # HTML escape first
            text = html.escape(text)
            # Then escape backticks and other JS-breaking characters
            text = text.replace('`', '\\`').replace('${', '\\${')
            return text
        
        name = escape_for_js(row['Name'])
        address = escape_for_js(row['full_address'])
        phone = escape_for_js(row.get('Phone Number', ''))
        gate_code = escape_for_js(row.get('Gate Code (required if gated access)', ''))
        
        # Create popup with address details
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; min-width: 200px;">
            <b>Route {route}</b><br>
            <b>{name}</b><br>
            {address}<br>
            Trees: {int(row['Number of Trees'])}<br>
            {f"Phone: {phone}<br>" if phone else ""}
            {f"Gate Code: {gate_code}<br>" if gate_code else ""}
        </div>
        """
        
        # Add marker to route group
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{name} - Route {route}",
            color=route_info['color'],
            fillColor=route_info['color'],
            fillOpacity=0.7,
            weight=2
        ).add_to(route_info['group'])
    
    # Add all route groups to map
    for route_info in route_groups.values():
        route_info['group'].add_to(route_map)
    
    # Add layer control to toggle routes on/off
    folium.LayerControl(collapsed=False).add_to(route_map)
    
    # Add a title using Folium's HTML element
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 400px; height: 60px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px; opacity: 0.9;">
        <b>Christmas Tree Pickup Routes - 2025</b><br>
        Click markers for details. Use layer control to toggle routes.
    </div>
    '''
    # Use the MacroElement API to add custom HTML
    from branca.element import Element
    route_map.get_root().add_child(Element(title_html))
    
    # Save the map
    route_map.save(output_path)
    
    # Post-process the HTML to use local resources
    print("  Converting to use local resources...")
    convert_to_local_resources(output_path)
    
    print(f"\n✓ Map saved to: {output_path}")
    
    # Print route summary
    print("\n" + "="*60)
    print("ROUTE SUMMARY")
    print("="*60)
    for route in routes:
        route_df = df[df['optimized_route'] == route]
        trees = route_df['Number of Trees'].sum()
        color = route_groups[route]['color']
        print(f"Route {route} ({color}): {len(route_df)} pickups, {int(trees)} trees")


def convert_to_local_resources(html_path: str):
    """Convert HTML to use local CSS/JS resources instead of CDN."""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Replace CDN links with local paths (using ../ since files are in year subfolders)
    replacements = {
        'https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js': '../lib/js/leaflet.js',
        'https://code.jquery.com/jquery-3.7.1.min.js': '../lib/js/jquery.min.js',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js': '../lib/js/bootstrap.bundle.min.js',
        'https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js': '../lib/js/leaflet.awesome-markers.js',
        'https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css': '../lib/css/leaflet.css',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css': '../lib/css/bootstrap.min.css',
        'https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css': '',  # Remove, not needed
        'https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css': '../lib/css/fontawesome.min.css',
        'https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css': '../lib/css/leaflet.awesome-markers.css',
        'https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css': '',  # Remove, not critical
    }
    
    for cdn_url, local_path in replacements.items():
        if local_path:
            # For script tags
            html = html.replace(f'<script src="{cdn_url}">', f'<script src="{local_path}">')
            # For link tags
            html = html.replace(f'<link rel="stylesheet" href="{cdn_url}"/>', f'<link rel="stylesheet" href="{local_path}"/>')
        else:
            # Remove the line entirely
            html = re.sub(f'.*{re.escape(cdn_url)}.*\n', '', html)
    
    # Write back
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)


def main():
    """Main execution function."""
    print("="*60)
    print("Route Map Generator")
    print("="*60)
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    if test_mode:
        # Try clustered first, fall back to optimized
        if Path('data/2025-clustered-routes.csv').exists():
            input_path = 'data/2025-clustered-routes.csv'
        else:
            input_path = 'data/2025-optimized-routes.csv'
        output_path = '../website/routes/2025/2025-routes-map.html'
        print("\n🧪 TEST MODE: Using 2025 dataset")
    else:
        # Try clustered first, fall back to optimized
        if Path('data/2026-clustered-routes.csv').exists():
            input_path = 'data/2026-clustered-routes.csv'
        else:
            input_path = 'data/2026-optimized-routes.csv'
        output_path = '../website/routes/2026/2026-routes-map.html'
    
    # Load routes
    df = load_optimized_routes(input_path)
    
    if len(df) == 0:
        print("Error: No valid routes found in the data")
        sys.exit(1)
    
    # Create map
    create_route_map(df, output_path)


if __name__ == '__main__':
    main()
