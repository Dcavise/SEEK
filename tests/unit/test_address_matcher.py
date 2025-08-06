# tests/unit/test_address_matcher.py
def test_address_matching(sample_parcels, fort_worth_addresses):
    from src.services.address_matcher import match_addresses
    
    results = match_addresses(fort_worth_addresses, sample_parcels)
    assert len(results) > 0
    assert results[0]['confidence'] > 0.8