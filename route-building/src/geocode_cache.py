#!/usr/bin/env python3
"""
Global geocoding cache for tree recycling routes.

This module provides persistent caching of geocoded addresses that works
across all years, runs, and environments. Once an address is geocoded,
it's cached forever since addresses don't move.
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime


class GeocodeCache:
    """
    Persistent cache for geocoded addresses.
    
    The cache is stored as a JSON file and is shared across all years and runs.
    Cache keys are hashed normalized addresses to handle variations in formatting.
    """
    
    def __init__(self, cache_file: str = 'data/geocode_cache.json'):
        """
        Initialize the geocode cache.
        
        Args:
            cache_file: Path to the cache file
        """
        self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.cache = self._load_cache()
        self.hits = 0
        self.misses = 0
    
    def _load_cache(self) -> Dict:
        """Load the cache from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    print(f"Loaded geocode cache: {len(cache_data.get('addresses', {}))} addresses")
                    return cache_data
            except Exception as e:
                print(f"Warning: Could not load cache: {e}")
                return self._new_cache()
        else:
            print("Creating new geocode cache")
            return self._new_cache()
    
    def _new_cache(self) -> Dict:
        """Create a new empty cache structure."""
        return {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'addresses': {}
        }
    
    def _normalize_address(self, address: str) -> str:
        """
        Normalize an address string for consistent cache lookups.
        
        Handles variations like:
        - "123 Main St" vs "123 main street"
        - "Cedar Park, TX" vs "cedar park, texas"
        - Extra spaces, punctuation, etc.
        
        Args:
            address: Raw address string
            
        Returns:
            Normalized address string
        """
        # Convert to lowercase
        normalized = address.lower()
        
        # Standardize common abbreviations
        replacements = {
            ' street': ' st',
            ' drive': ' dr',
            ' road': ' rd',
            ' avenue': ' ave',
            ' lane': ' ln',
            ' court': ' ct',
            ' circle': ' cir',
            ' boulevard': ' blvd',
            ' place': ' pl',
            ' trail': ' trl',
            ' way': ' wy',
            ' texas': ' tx',
        }
        
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        # Remove extra spaces and punctuation
        normalized = ' '.join(normalized.split())
        normalized = normalized.replace('.', '').replace(',', '')
        
        return normalized
    
    def _get_cache_key(self, address: str) -> str:
        """
        Generate a unique cache key for an address.
        
        Uses SHA-256 hash of normalized address for consistent lookups
        regardless of formatting variations.
        
        Args:
            address: Address string
            
        Returns:
            Cache key (hash string)
        """
        normalized = self._normalize_address(address)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]
    
    def get(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Get cached coordinates for an address.
        
        Args:
            address: Address string
            
        Returns:
            Tuple of (latitude, longitude) if cached, None otherwise
        """
        cache_key = self._get_cache_key(address)
        
        if cache_key in self.cache['addresses']:
            entry = self.cache['addresses'][cache_key]
            self.hits += 1
            return (entry['latitude'], entry['longitude'])
        
        self.misses += 1
        return None
    
    def set(self, address: str, latitude: float, longitude: float) -> None:
        """
        Cache coordinates for an address.
        
        Args:
            address: Address string
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """
        cache_key = self._get_cache_key(address)
        
        self.cache['addresses'][cache_key] = {
            'address': address,  # Store original for reference
            'normalized': self._normalize_address(address),
            'latitude': latitude,
            'longitude': longitude,
            'cached_at': datetime.now().isoformat()
        }
        
        self.cache['last_updated'] = datetime.now().isoformat()
    
    def save(self) -> None:
        """Save the cache to disk."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
            print(f"\nCache saved: {len(self.cache['addresses'])} addresses")
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")
    
    def stats(self) -> Dict:
        """Get cache statistics."""
        return {
            'total_cached': len(self.cache['addresses']),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{(self.hits / (self.hits + self.misses) * 100):.1f}%" if (self.hits + self.misses) > 0 else "N/A"
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - auto-save cache."""
        self.save()
        
        # Print stats
        stats = self.stats()
        print(f"Cache stats: {stats['hits']} hits, {stats['misses']} misses, {stats['hit_rate']} hit rate")


# Convenience function for quick cache access
def get_geocode_cache() -> GeocodeCache:
    """Get the global geocode cache instance."""
    return GeocodeCache()


if __name__ == '__main__':
    # Test the cache
    print("Testing GeocodeCache...")
    
    with GeocodeCache() as cache:
        # Test address variations
        test_addresses = [
            "123 Main Street, Cedar Park, TX",
            "123 main st, cedar park, texas",
            "123 Main St., Cedar Park, TX",
        ]
        
        # Add to cache
        cache.set(test_addresses[0], 30.5050, -97.8200)
        
        # Test retrieval with variations
        for addr in test_addresses:
            result = cache.get(addr)
            print(f"Lookup '{addr}': {result}")
        
        print(f"\nCache stats: {cache.stats()}")
