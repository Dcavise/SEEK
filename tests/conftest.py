# tests/conftest.py
import pytest
from supabase import create_client
import pandas as pd

@pytest.fixture(scope="session")
def supabase_client():
    """Shared Supabase client for tests"""
    return create_client(
        "https://mpkprmjejiojdjbkkbmn.supabase.co",
        "test-key"
    )

@pytest.fixture
def sample_parcels():
    """Sample parcel data for testing"""
    return pd.DataFrame({
        'parcel_number': ['TEST001', 'TEST002'],
        'address': ['1261 W Green Oaks Blvd', '456 Oak Ave'],
        'latitude': [29.4241, 29.4242],
        'longitude': [-98.4936, -98.4937]
    })

@pytest.fixture
def fort_worth_addresses():
    """Real Fort Worth addresses for testing"""
    return [
        "1261 W GREEN OAKS BLVD",
        "3909 HULEN ST",
        "6824 KIRK DR"
    ]