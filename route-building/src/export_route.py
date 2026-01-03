#!/usr/bin/env python3
"""
Export a single route for drivers.

Generates:
1. Google Maps URL with all route locations
2. HTML page with pickup tracking sheet
"""

import sys
from pathlib import Path
import pandas as pd
from urllib.parse import quote
import qrcode
import qrcode.constants
import base64
from io import BytesIO


def load_routes(csv_path: str = 'data/2026-clustered-routes.csv') -> pd.DataFrame:
    """Load route assignments."""
    file_path = Path(csv_path)
    if not file_path.exists():
        print(f"Error: File not found: {csv_path}")
        print("Run cluster_routes.py first to generate routes.")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    return df


def generate_google_maps_url(route_df: pd.DataFrame, route_name: str) -> str:
    """
    Generate a Google Maps URL with all addresses as waypoints.
    
    Google Maps URL limit is ~2000 characters, so we may need to split large routes.
    """
    # Get addresses
    addresses = []
    for _, row in route_df.iterrows():
        addr = row['full_address']
        addresses.append(addr)
    
    if len(addresses) == 0:
        return ""
    
    # Build Google Maps URL
    # Format: https://www.google.com/maps/dir/address1/address2/address3/...
    base_url = "https://www.google.com/maps/dir/"
    
    # URL encode each address
    encoded_addresses = [quote(addr) for addr in addresses]
    
    # Join with slashes
    url = base_url + "/".join(encoded_addresses)
    
    # Check length and warn if too long
    if len(url) > 2000:
        print(f"  ⚠️  Warning: URL is {len(url)} characters (may be too long for some browsers)")
        print(f"     Consider splitting Route {route_name} into smaller sections")
    
    return url


def generate_qr_code_base64(url: str) -> str:
    """Generate a QR code as base64 encoded image."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')  # type: ignore
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def create_route_html(route_df: pd.DataFrame, route_name: str, output_path: str, maps_url: str):
    """
    Create an HTML pickup tracking sheet for drivers.
    
    Includes:
    - Route summary with QR code
    - Google Maps link
    - Table with each address and fields for tracking
    """
    # Route summary
    total_pickups = len(route_df)
    total_trees = int(route_df['Number of Trees'].sum())
    
    # Generate QR code as base64
    qr_code_data = generate_qr_code_base64(maps_url) if maps_url else ""
    
    # Build HTML table rows
    table_rows = []
    for idx, row in route_df.iterrows():
        name = str(row['Name'])
        address = str(row['full_address'])
        trees = str(int(row['Number of Trees']))
        
        # Handle missing values (avoid 'nan')
        phone_raw = row.get('Phone Number', '')
        phone = '' if pd.isna(phone_raw) or str(phone_raw) == 'nan' else str(phone_raw)
        
        gate_raw = row.get('Gate Code (required if gated access)', '')
        gate = '' if pd.isna(gate_raw) or str(gate_raw) == 'nan' else str(gate_raw)
        
        unit_raw = row.get('Apt. Number', '')
        unit = '' if pd.isna(unit_raw) or str(unit_raw) == 'nan' else str(unit_raw)
        
        comments_raw = row.get('Comments', '')
        comments = '' if pd.isna(comments_raw) or str(comments_raw) == 'nan' else str(comments_raw)
        
        home_raw = row.get('Will someone be home', '')
        home = '' if pd.isna(home_raw) or str(home_raw) == 'nan' else str(home_raw)
        
        table_rows.append(f"""
            <tr>
                <td>{name}</td>
                <td>{address}</td>
                <td class="text-center">{unit}</td>
                <td class="text-center">{trees}</td>
                <td>{phone}</td>
                <td class="text-center">{home}</td>
                <td>{gate}</td>
                <td>{comments}</td>
                <td class="editable"></td>
                <td class="editable"></td>
                <td class="editable"></td>
                <td class="editable"></td>
            </tr>
        """)
    
    # Create HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Route {route_name} - Pickup Sheet</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #3498DB;
        }}
        .header-left {{
            flex: 1;
        }}
        h1 {{
            color: #2C3E50;
            margin-bottom: 15px;
            font-size: 28px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .summary-item {{
            background: #ECF0F1;
            padding: 12px;
            border-radius: 5px;
        }}
        .summary-item strong {{
            display: block;
            color: #2C3E50;
            margin-bottom: 5px;
        }}
        .maps-section {{
            background: #E8F5E9;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4CAF50;
        }}
        .maps-section a {{
            color: #2E7D32;
            text-decoration: none;
            font-weight: 600;
            font-size: 16px;
        }}
        .maps-section a:hover {{
            text-decoration: underline;
        }}
        .qr-section {{
            text-align: center;
            padding: 10px;
        }}
        .qr-section img {{
            width: 180px;
            height: 180px;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            background: white;
        }}
        .qr-section p {{
            margin-top: 10px;
            font-size: 13px;
            color: #666;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #3498DB;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            font-size: 14px;
            border: 1px solid #2980B9;
        }}
        td {{
            padding: 10px 8px;
            border: 1px solid #ddd;
            font-size: 13px;
        }}
        tr:nth-child(even) {{
            background: #ECF0F1;
        }}
        tr:hover {{
            background: #D5DBDB;
        }}
        .text-center {{
            text-align: center;
        }}
        .editable {{
            background: #FFF9C4 !important;
            min-width: 80px;
        }}
        @media print {{
            body {{
                padding: 0;
                background: white;
            }}
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
            .maps-section {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>Route {route_name} - Pickup Sheet</h1>
                
                <div class="summary">
                    <div class="summary-item">
                        <strong>Total Pickups</strong>
                        <span>{total_pickups}</span>
                    </div>
                    <div class="summary-item">
                        <strong>Total Trees</strong>
                        <span>{total_trees}</span>
                    </div>
                    <div class="summary-item">
                        <strong>Driver</strong>
                        <span>_______________</span>
                    </div>
                </div>
                
                {"<div class='maps-section'><strong>🗺️ Google Maps Directions:</strong><br><a href='" + maps_url + "' target='_blank'>Open Route in Google Maps →</a></div>" if maps_url else ""}
            </div>
            
            {"<div class='qr-section'><img src='" + qr_code_data + "' alt='QR Code for Google Maps'><p>Scan for directions</p></div>" if maps_url else ""}
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Address</th>
                    <th class="text-center">Unit #</th>
                    <th class="text-center">Trees<br>Expected</th>
                    <th>Phone</th>
                    <th class="text-center">Home?<br>(Y/N)</th>
                    <th>Gate<br>Code</th>
                    <th>Comments</th>
                    <th class="text-center">Trees<br>Picked Up</th>
                    <th class="text-center">Amount<br>Collected</th>
                    <th class="text-center">Cash/<br>Check</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"  ✓ HTML created: {output_path}")


def export_route(route_name: str, csv_path: str, output_dir: str = None):
    """Export a single route with maps URL and HTML."""
    # Load data
    df = load_routes(csv_path)
    
    # Determine output directory based on year if not specified
    if output_dir is None:
        year = '2026' if '2026' in csv_path else '2025'
        output_dir = f'../website/routes/{year}'
    
    # Get route data
    route_df = df[df['optimized_route'] == route_name].copy()
    
    if len(route_df) == 0:
        print(f"❌ Route {route_name} not found")
        available = sorted(df['optimized_route'].unique())
        print(f"Available routes: {', '.join(available)}")
        return
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"EXPORTING ROUTE {route_name}")
    print(f"{'='*60}")
    print(f"Pickups: {len(route_df)}")
    print(f"Trees: {int(route_df['Number of Trees'].sum())}")
    
    # Generate Google Maps URL
    print("\nGenerating Google Maps URL and HTML...")
    maps_url = generate_google_maps_url(route_df, route_name)
    
    # Generate HTML
    html_file = output_path / f"Route-{route_name}.html"
    create_route_html(route_df, route_name, str(html_file), maps_url)
    
    print(f"\n{'='*60}")
    print(f"✓ Route {route_name} exported successfully!")
    print(f"{'='*60}")
    print(f"\nFile created in: {output_dir}/")
    print(f"  - Route-{route_name}.html")
    print(f"\nTo open the HTML:")
    print(f"  open {html_file}")


def main():
    """Main execution."""
    # Check for test mode and all flag
    test_mode = '--test' in sys.argv
    export_all = '--all' in sys.argv
    
    if test_mode:
        csv_path = 'data/2025-clustered-routes.csv'
        print("\n🧪 TEST MODE: Using 2025 dataset")
    else:
        csv_path = 'data/2026-clustered-routes.csv'
    
    # Handle --all flag to export all routes
    if export_all:
        print("="*60)
        print("EXPORTING ALL ROUTES")
        print("="*60)
        
        df = load_routes(csv_path)
        routes = sorted(df['optimized_route'].unique())
        
        print(f"\nFound {len(routes)} routes to export: {', '.join(routes)}")
        print("\nExporting...")
        
        for route_name in routes:
            export_route(route_name, csv_path)
        
        print(f"\n{'='*60}")
        print(f"✓ ALL ROUTES EXPORTED SUCCESSFULLY!")
        print(f"{'='*60}")
        year = '2026' if '2026' in csv_path else '2025'
        print(f"\nFiles saved in: ../website/routes/{year}/")
        sys.exit(0)
    
    # Get route name from command line
    if len(sys.argv) < 2 or sys.argv[1] in ['--test', '--all']:
        print("="*60)
        print("ROUTE EXPORT TOOL")
        print("="*60)
        print("\nUsage:")
        print("  uv run src/export_route.py <ROUTE_NAME>")
        print("  uv run src/export_route.py <ROUTE_NAME> --test")
        print("  uv run src/export_route.py --all")
        print("  uv run src/export_route.py --all --test")
        print("\nExample:")
        print("  uv run src/export_route.py A")
        print("  uv run src/export_route.py AA")
        print("  uv run src/export_route.py --all  # Export all routes")
        print("\n")
        
        # Show available routes
        df = load_routes(csv_path)
        routes = sorted(df['optimized_route'].unique())
        print(f"Available routes in {csv_path}:")
        print(f"  {', '.join(routes)}")
        sys.exit(1)
    
    route_name = sys.argv[1].upper()
    
    # Export the route
    export_route(route_name, csv_path)


if __name__ == '__main__':
    main()
