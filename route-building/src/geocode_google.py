#!/usr/bin/env python3
"""
Geocoding using Google Maps API with persistent caching.

This script geocodes addresses using the Google Maps Geocoding API
and caches results permanently to avoid re-geocoding the same addresses.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
import googlemaps
from geocode_cache import GeocodeCache


def get_google_api_key() -> str:
    """
    Get the Google Maps API key from various sources.
    
    Tries in order:
    1. Environment variable GOOGLE_MAPS_API_KEY
    2. File: geocoding-apikey.txt
    3. File: .env
    
    Returns:
        API key string
        
    Raises:
        ValueError: If API key cannot be found
    """
    # Try environment variable first
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if api_key:
        print("✓ Using API key from environment variable")
        return api_key
    
    # Try geocoding-apikey.txt
    key_file = Path('geocoding-apikey.txt')
    if key_file.exists():
        api_key = key_file.read_text().strip()
        if api_key:
            print("✓ Using API key from geocoding-apikey.txt")
            return api_key
    
    # Try .env file
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith('GOOGLE_MAPS_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                if api_key:
                    print("✓ Using API key from .env file")
                    return api_key
    
    raise ValueError(
        "Google Maps API key not found!\n"
        "Please set it in one of these ways:\n"
        "1. Environment variable: export GOOGLE_MAPS_API_KEY='your_key'\n"
        "2. Create file: geocoding-apikey.txt with your key\n"
        "3. Create .env file with: GOOGLE_MAPS_API_KEY=your_key"
    )


def geocode_address(
    address: str,
    gmaps_client: googlemaps.Client,
    cache: GeocodeCache
) -> Optional[Tuple[float, float]]:
    """
    Geocode a single address using cache-first approach.
    
    Args:
        address: Address string to geocode
        gmaps_client: Google Maps client instance
        cache: Geocode cache instance
        
    Returns:
        Tuple of (latitude, longitude) or None if geocoding failed
    """
    # Check cache first
    cached = cache.get(address)
    if cached:
        return cached
    
    # Not in cache, call Google API
    try:
        result = gmaps_client.geocode(address)  # type: ignore[attr-defined]
        if result and len(result) > 0:
            location = result[0]['geometry']['location']
            lat = location['lat']
            lng = location['lng']
            
            # Cache the result
            cache.set(address, lat, lng)
            
            return (lat, lng)
        else:
            return None
            
    except Exception as e:
        print(f"  Error geocoding '{address}': {e}")
        return None


def geocode_dataframe(
    df: pd.DataFrame,
    address_components: Optional[list] = None,
    limit: Optional[int] = None
) -> pd.DataFrame:
    """
    Geocode all addresses in a DataFrame.
    
    Args:
        df: DataFrame with address columns
        address_components: List of column names to combine for address
                          Default: ['House #', 'Street', 'City']
        limit: Limit number of addresses to geocode (for testing)
        
    Returns:
        DataFrame with added 'latitude' and 'longitude' columns
    """
    if address_components is None:
        address_components = ['House #', 'Street', 'City']
    
    print("\n" + "="*60)
    print("GEOCODING WITH GOOGLE MAPS API")
    print("="*60)
    
    # Get API key and initialize client
    api_key = get_google_api_key()
    gmaps = googlemaps.Client(key=api_key)
    
    # Create full address string
    df = df.copy()
    
    # Build address from components
    address_parts = []
    for col in address_components:
        if col in df.columns:
            address_parts.append(df[col].astype(str))
    
    # Join components with comma separator using pandas str.cat()
    if address_parts:
        df['full_address'] = address_parts[0].str.cat(address_parts[1:], sep=', ')
    else:
        df['full_address'] = ''
    
    # Add state (assuming Texas)
    df['full_address'] = df['full_address'].str.cat(others=[', TX'] * len(df))
    
    # Limit for testing if specified
    if limit:
        df_to_geocode = df.head(limit).copy()
        print(f"\nGeocoding first {limit} addresses for testing...")
    else:
        df_to_geocode = df.copy()
        print(f"\nGeocoding {len(df_to_geocode)} addresses...")
    
    # Initialize cache
    with GeocodeCache() as cache:
        latitudes = []
        longitudes = []
        api_calls = 0
        
        for count, (idx, row) in enumerate(df_to_geocode.iterrows(), 1):
            address = row['full_address']
            
            # Check if already in cache before making API call
            result = geocode_address(address, gmaps, cache)
            
            if result:
                lat, lng = result
                latitudes.append(lat)
                longitudes.append(lng)
                
                # Count API calls (cache misses)
                if cache.misses > api_calls:
                    api_calls = cache.misses
                    status = "🌐 API"
                else:
                    status = "💾 Cache"
                
                print(f"  [{count}/{len(df_to_geocode)}] {status} ✓ {row['Name']}: {address}")
            else:
                latitudes.append(None)
                longitudes.append(None)
                print(f"  [{count}/{len(df_to_geocode)}] ✗ Failed: {address}")
        
        df_to_geocode['latitude'] = latitudes
        df_to_geocode['longitude'] = longitudes
        
        # Cache saves automatically on context exit
        successful = df_to_geocode['latitude'].notna().sum()
        print(f"\n{'='*60}")
        print(f"Geocoding complete: {successful}/{len(df_to_geocode)} successful")
        print(f"API calls made: {api_calls}")
        print(f"Cache hits: {cache.hits}")
        print(f"{'='*60}")
    
    return df_to_geocode


def main():
    """Main execution - geocode addresses with test/live mode support."""
    print("="*60)
    print("Google Maps Geocoding with Persistent Cache")
    print("="*60)
    
    # Parse arguments
    test_mode = '--test' in sys.argv
    
    # Set paths based on mode
    if test_mode:
        csv_path = 'data/2025-tree_requests.csv'
        output_path = 'data/2025-geocoded-full.csv'
        print("\n🧪 TEST MODE: Using 2025 dataset")
    else:
        csv_path = 'data/2026-tree_requests.csv'
        output_path = 'data/2026-geocoded-full.csv'
    
    print(f"\nLoading data from {csv_path}...")
    
    if not Path(csv_path).exists():
        print(f"Error: File not found: {csv_path}")
        print("Run fetch_data.py first to download the data.")
        sys.exit(1)
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} requests")
    
    # Geocode all addresses
    print("\nStarting geocoding...")
    print("Note: First run will make API calls, subsequent runs use cache!")
    
    df_geocoded = geocode_dataframe(df)
    
    # Save results
    df_geocoded.to_csv(output_path, index=False)
    print(f"\n✓ Geocoded data saved to: {output_path}")
    
    # Show summary
    total = len(df_geocoded)
    successful = df_geocoded['latitude'].notna().sum()
    failed = df_geocoded['latitude'].isna().sum()
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total addresses:     {total}")
    print(f"Successfully geocoded: {successful} ({successful/total*100:.1f}%)")
    print(f"Failed:              {failed} ({failed/total*100:.1f}%)")
    print(f"{'='*60}")
    
    if failed > 0:
        print("\nAddresses that failed to geocode:")
        failed_df = df_geocoded[df_geocoded['latitude'].isna()][['Name', 'full_address']]
        print(failed_df.to_string(index=False))


if __name__ == '__main__':
    main()
