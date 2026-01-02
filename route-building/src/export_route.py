#!/usr/bin/env python3
"""
Export a single route for drivers.

Generates:
1. Google Maps URL with all route locations
2. PDF form with pickup tracking sheet
"""

import sys
from pathlib import Path
import pandas as pd
from urllib.parse import quote
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import qrcode
import qrcode.constants
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


def generate_qr_code(url: str) -> Image:
    """Generate a QR code image from a URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert PIL image to ReportLab Image
    buffer = BytesIO()
    img.save(buffer, format='PNG')  # type: ignore
    buffer.seek(0)
    
    return Image(buffer, width=1.2*inch, height=1.2*inch)


def create_route_pdf(route_df: pd.DataFrame, route_name: str, output_path: str, maps_url: str):
    """
    Create a PDF pickup tracking sheet for drivers.
    
    Includes:
    - Route summary with QR code
    - Google Maps URL
    - Table with each address and fields for tracking
    """
    doc = SimpleDocTemplate(output_path, pagesize=landscape(letter),
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.25*inch, rightMargin=0.25*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    elements.append(Paragraph(f"<b>Route {route_name} - Pickup Sheet</b>", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Route summary
    total_pickups = len(route_df)
    total_trees = int(route_df['Number of Trees'].sum())
    
    summary_style = ParagraphStyle(
        'Summary',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    # Create header section with QR code and summary side by side
    if maps_url:
        qr_img = generate_qr_code(maps_url)
        
        # Create a table for header layout (QR code on left, info on right)
        header_data = [[
            qr_img,
            Paragraph(f'''
                <b>Total Pickups:</b> {total_pickups}<br/>
                <b>Total Trees:</b> {total_trees}<br/>
                <b>Driver:</b> _____________<br/>
                <br/>
                <b>Scan QR code for Google Maps directions</b>
            ''', summary_style)
        ]]
        
        header_table = Table(header_data, colWidths=[1.5*inch, 5*inch])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(Paragraph(f"<b>Total Pickups:</b> {total_pickups}", summary_style))
        elements.append(Paragraph(f"<b>Total Trees:</b> {total_trees}", summary_style))
        elements.append(Paragraph(f"<b>Driver:</b> _____________", summary_style))
        elements.append(Spacer(1, 0.2*inch))
    
    # Table header
    table_data = [[
        'Name',
        'Address',
        'Trees\nExpected',
        'Phone',
        'Gate\nCode',
        'Trees\nPicked Up',
        'Amount\nCollected',
        'Cash/\nCheck',
        'Notes'
    ]]
    
    # Add each pickup
    for idx, row in route_df.iterrows():
        name = str(row['Name'])[:20]  # Truncate long names
        address = str(row['full_address'])[:35]  # Truncate long addresses
        trees = str(int(row['Number of Trees']))
        
        # Handle missing phone/gate code (avoid 'nan')
        phone_raw = row.get('Phone Number', '')
        phone = '' if pd.isna(phone_raw) or str(phone_raw) == 'nan' else str(phone_raw)[:12]
        
        gate_raw = row.get('Gate Code (required if gated access)', '')
        gate = '' if pd.isna(gate_raw) or str(gate_raw) == 'nan' else str(gate_raw)[:8]
        
        table_data.append([
            name,
            address,
            trees,
            phone,
            gate,
            '',  # Trees picked up (blank)
            '',  # Amount collected (blank)
            '',  # Cash/Check (blank)
            ''   # Notes (blank)
        ])
    
    # Create table with wider columns for landscape
    col_widths = [1.3*inch, 2.2*inch, 0.5*inch, 0.9*inch, 0.6*inch, 0.7*inch, 0.7*inch, 0.6*inch, 1.5*inch]
    
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style the table
    table_style = TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498DB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Alternate row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ECF0F1')])
    ])
    
    table.setStyle(table_style)
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    print(f"  ✓ PDF created: {output_path}")


def export_route(route_name: str, csv_path: str, output_dir: str = None):
    """Export a single route with maps URL and PDF."""
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
    print("\nGenerating Google Maps URL and PDF...")
    maps_url = generate_google_maps_url(route_df, route_name)
    
    # Generate PDF
    pdf_file = output_path / f"Route-{route_name}-PickupSheet.pdf"
    create_route_pdf(route_df, route_name, str(pdf_file), maps_url)
    
    print(f"\n{'='*60}")
    print(f"✓ Route {route_name} exported successfully!")
    print(f"{'='*60}")
    print(f"\nFile created in: {output_dir}/")
    print(f"  - Route-{route_name}-PickupSheet.pdf")
    print(f"\nTo open the PDF:")
    print(f"  open {pdf_file}")


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
        print(f"\nFiles saved in: data/route-exports/")
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
