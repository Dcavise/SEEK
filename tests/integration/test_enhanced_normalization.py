#!/usr/bin/env python3
"""
Quick test of enhanced address normalization for Task 2.1
Tests the improved matching rate with Fort Worth FOIA data
"""

import pandas as pd
from foia_address_matcher import FOIAAddressMatcher
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_normalization():
    """Test enhanced normalization with limited dataset for speed"""
    
    print("🎯 TASK 2.1: Enhanced Address Normalization Test")
    print("=" * 60)
    print("Testing improved match rate: Target 26% → 80%+")
    print()
    
    # Initialize matcher
    matcher = FOIAAddressMatcher()
    
    # Load limited parcel data for faster testing (first 5000 Tarrant County parcels)
    logger.info("Loading limited parcel data for testing...")
    parcel_df = matcher.load_parcel_data(limit=5000, county_name='Tarrant')
    
    if parcel_df.empty:
        print("❌ Could not load parcel data")
        return False
    
    print(f"✅ Loaded {len(parcel_df)} parcel records for testing")
    
    # Load Fort Worth FOIA data
    try:
        foia_df = pd.read_csv('fort-worth-foia-test.csv')
        print(f"✅ Loaded {len(foia_df)} FOIA records")
    except FileNotFoundError:
        print("❌ Fort Worth FOIA test file not found")
        return False
    
    # Test a sample of FOIA records
    sample_size = min(20, len(foia_df))  # Test first 20 records
    foia_sample = foia_df.head(sample_size)
    
    print(f"\n🧪 Testing enhanced normalization on {sample_size} FOIA records...")
    
    # Run matching with enhanced normalization
    results = matcher.process_foia_batch(foia_sample)
    
    # Generate summary
    summary = matcher.generate_match_summary(results)
    
    print("\n" + "="*60)
    print("🎯 ENHANCED NORMALIZATION RESULTS")
    print("="*60)
    print(f"Total Records Processed: {summary['total_records']}")
    print(f"Successfully Matched: {summary['matched_records']} ({summary['match_rate']:.1f}%)")
    print(f"Unmatched Records: {summary['unmatched_records']}")
    print(f"Manual Review Required: {summary['manual_review_required']}")
    print(f"Average Confidence Score: {summary['average_confidence']}%")
    
    print(f"\n📊 Match Rate Improvement:")
    old_rate = 26.0  # Previous rate
    new_rate = summary['match_rate']
    improvement = new_rate - old_rate
    improvement_pct = (improvement / old_rate) * 100 if old_rate > 0 else 0
    
    print(f"Previous Rate: {old_rate:.1f}%")
    print(f"New Rate:      {new_rate:.1f}%")
    print(f"Improvement:   {improvement:+.1f}% ({improvement_pct:+.1f}% relative)")
    
    # Show tier breakdown
    print(f"\n📋 Tier Breakdown:")
    for tier, count in summary['tier_breakdown'].items():
        print(f"  {tier}: {count} records")
    
    # Show successful matches with normalization examples
    print(f"\n✅ Sample Successful Matches:")
    successful_matches = [r for r in results if r.matched_parcel_id][:5]
    for i, match in enumerate(successful_matches):
        normalized_original = matcher.normalize_address(match.original_address)
        normalized_matched = matcher.normalize_address(match.matched_address) if match.matched_address else ""
        
        print(f"\n  {i+1}. FOIA Record: {match.foia_record_id}")
        print(f"     Original:    {match.original_address}")
        print(f"     Normalized:  {normalized_original}")
        print(f"     Matched:     {match.matched_address}")
        print(f"     Match Norm:  {normalized_matched}")
        print(f"     Confidence:  {match.confidence_score:.1f}% ({match.match_tier})")
    
    # Success criteria
    target_rate = 80.0
    success = new_rate >= target_rate
    
    print(f"\n🏆 TASK 2.1 ASSESSMENT:")
    if success:
        print(f"🎉 SUCCESS: Match rate {new_rate:.1f}% ≥ target {target_rate}%")
        print("✅ Enhanced address normalization working effectively")
    else:
        print(f"⚠️  PARTIAL: Match rate {new_rate:.1f}% < target {target_rate}%")
        print("📝 May need additional normalization enhancements")
    
    return success

if __name__ == "__main__":
    success = test_enhanced_normalization()
    exit(0 if success else 1)