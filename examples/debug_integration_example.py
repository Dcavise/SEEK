#!/usr/bin/env python3
"""
Example: Integrating Debug Utilities with SEEK Services

This example shows how to use the debug utilities with the AddressMatcher
and CoordinateUpdater services for performance monitoring and debugging.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.debug import timer, DebugContext, debug_dump
from src.services.address_matcher import AddressMatcher
import pandas as pd

# Set up logging to see debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@timer
def enhanced_address_matching(foia_addresses: list[str], parcel_data: pd.DataFrame) -> dict:
    """Enhanced address matching with debug utilities"""
    
    with DebugContext("address_matching_workflow"):
        matcher = AddressMatcher(confidence_threshold=0.75)
        
        # Convert parcel data to candidate format
        candidates = []
        for _, row in parcel_data.iterrows():
            candidates.append({
                'id': row['parcel_number'],
                'address': row['address']
            })
        
        # Debug dump the input data
        debug_dump({
            'foia_addresses': foia_addresses,
            'candidate_count': len(candidates),
            'sample_candidates': candidates[:3]  # First 3 for debugging
        }, 'address_matching_input')
        
        # Perform matching with individual timing
        all_matches = []
        for i, foia_addr in enumerate(foia_addresses):
            with DebugContext(f"matching_address_{i+1}"):
                matches = matcher.find_address_matches(foia_addr, candidates)
                all_matches.extend(matches)
                
                # Debug dump matches for this address
                if matches:
                    debug_dump({
                        'foia_address': foia_addr,
                        'matches_found': len(matches),
                        'best_match': matches[0] if matches else None
                    }, f'match_result_{i+1}')
        
        # Get final statistics
        stats = matcher.get_matching_stats()
        
        # Debug dump final results
        debug_dump({
            'total_matches': len(all_matches),
            'matching_stats': stats,
            'high_confidence_matches': [m for m in all_matches if m.get('confidence', 0) > 0.85]
        }, 'final_matching_results')
        
        return {
            'matches': all_matches,
            'stats': stats,
            'total_processed': len(foia_addresses)
        }


@timer
def simulate_coordinate_validation(coordinates: list[tuple[float, float]]) -> dict:
    """Simulate coordinate validation with debug utilities"""
    
    from src.services.coordinate_updater import CoordinateUpdater
    
    with DebugContext("coordinate_validation"):
        updater = CoordinateUpdater()
        
        valid_coords = []
        invalid_coords = []
        
        for i, (lat, lng) in enumerate(coordinates):
            with DebugContext(f"validating_coordinate_{i+1}"):
                is_valid = updater.is_valid_texas_coordinate(lat, lng)
                
                if is_valid:
                    valid_coords.append((lat, lng))
                else:
                    invalid_coords.append((lat, lng))
        
        # Debug dump validation results
        debug_dump({
            'total_coordinates': len(coordinates),
            'valid_count': len(valid_coords),
            'invalid_count': len(invalid_coords),
            'validity_rate': len(valid_coords) / len(coordinates) if coordinates else 0,
            'invalid_examples': invalid_coords[:5]  # First 5 invalid for debugging
        }, 'coordinate_validation_results')
        
        return {
            'valid_coordinates': valid_coords,
            'invalid_coordinates': invalid_coords,
            'validation_stats': {
                'total': len(coordinates),
                'valid': len(valid_coords),
                'invalid': len(invalid_coords),
                'validity_rate': len(valid_coords) / len(coordinates) if coordinates else 0
            }
        }


def main():
    """Main example execution"""
    print("🔧 SEEK Debug Utilities Integration Example")
    print("=" * 50)
    
    # Sample data for testing
    print("\n📊 Setting up test data...")
    parcel_data = pd.DataFrame({
        'parcel_number': ['FORT001', 'FORT002', 'FORT003'],
        'address': [
            '1261 W Green Oaks Blvd',
            '3909 Hulen St', 
            '100 Fort Worth Trl'
        ],
        'latitude': [32.7555, 32.7556, 32.7557],
        'longitude': [-97.3308, -97.3309, -97.3310]
    })
    
    foia_addresses = [
        "1261 W GREEN OAKS BLVD",
        "3909 HULEN ST",
        "6824 KIRK DR"
    ]
    
    # Test coordinates (mix of valid Texas and invalid)
    test_coordinates = [
        (32.7767, -96.7970),  # Dallas - Valid
        (29.7604, -95.3698),  # Houston - Valid
        (40.7128, -74.0060),  # New York - Invalid
        (34.0522, -118.2437), # Los Angeles - Invalid
        (29.4241, -98.4936)   # San Antonio - Valid
    ]
    
    print("\n🔍 Running enhanced address matching...")
    matching_results = enhanced_address_matching(foia_addresses, parcel_data)
    print(f"   Found {len(matching_results['matches'])} matches")
    print(f"   Matching statistics: {matching_results['stats']}")
    
    print("\n📍 Running coordinate validation...")
    validation_results = simulate_coordinate_validation(test_coordinates)
    print(f"   Valid coordinates: {validation_results['validation_stats']['valid']}/{validation_results['validation_stats']['total']}")
    print(f"   Validity rate: {validation_results['validation_stats']['validity_rate']:.1%}")
    
    print(f"\n✅ Example completed! Check the 'debug_output' directory for detailed debugging files.")
    print(f"   Debug files contain comprehensive data for performance analysis and debugging.")


if __name__ == "__main__":
    main()