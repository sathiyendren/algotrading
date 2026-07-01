"""NSE scraper tests"""
import pytest
from unittest.mock import Mock, patch
from datetime import date
from src.nse_scraper import NSEScraper

@pytest.fixture
def scraper():
    # Mock the session initialization to avoid HTTP calls
    with patch.object(NSEScraper, '_init_session'):
        scraper = NSEScraper()
        # Mock the session object
        scraper.session = Mock()
        return scraper

def test_parse_participant_oi_all_4_types(scraper):
    # Test data with correct field names for NSE API
    test_data = {
        "data": [
            {"clientType": "FII", "futLongOI": "2500000", "futShortOI": "2400000", "futLongAmt": "125000.0", "futShortAmt": "120000.0"},
            {"clientType": "DII", "futLongOI": "1500000", "futShortOI": "1450000", "futLongAmt": "75000.0", "futShortAmt": "72500.0"},
            {"clientType": "CLIENT", "futLongOI": "800000", "futShortOI": "780000", "futLongAmt": "40000.0", "futShortAmt": "39000.0"},
            {"clientType": "PRO", "futLongOI": "600000", "futShortOI": "590000", "futLongAmt": "30000.0", "futShortAmt": "29500.0"},
        ]
    }
    result = scraper._parse_participant_oi(test_data)
    assert len(result) == 4
    client_types = {r["client_type"] for r in result}
    assert client_types == {"FII", "DII", "CLIENT", "PRO"}

def test_parse_participant_oi_values(scraper):
    test_data = {
        "data": [
            {"clientType": "FII", "futLongOI": "1000000", "futShortOI": "900000", "futLongAmt": "50000.0", "futShortAmt": "45000.0"},
        ]
    }
    result = scraper._parse_participant_oi(test_data)
    assert len(result) == 1
    assert result[0]["client_type"] == "FII"
    assert result[0]["long_contracts"] == 1000000
    assert result[0]["short_contracts"] == 900000
    assert result[0]["long_value"] == 50000.0
    assert result[0]["short_value"] == 45000.0

def test_parse_fii_dii_returns_2_records(scraper):
    # Test data with correct field names for NSE FII/DII API
    test_data = {
        "data": [
            {"fiiBuyValue": "1250.50", "fiiSellValue": "1150.25", "diiBuyValue": "850.75", "diiSellValue": "900.50"},
        ]
    }
    result = scraper._parse_fii_dii(test_data)
    assert len(result) == 2
    entity_types = {r["entity_type"] for r in result}
    assert entity_types == {"FII", "DII"}
    fii_data = next(r for r in result if r["entity_type"] == "FII")
    assert fii_data["buy_value"] == 1250.50
    assert fii_data["sell_value"] == 1150.25

def test_parse_fii_dii_handles_empty_response(scraper):
    # When data is empty, should still return 2 records with zero values
    test_data = {"data": []}
    result = scraper._parse_fii_dii(test_data)
    assert len(result) == 2  # Always returns FII and DII records
    assert all(r["buy_value"] == 0.0 for r in result)
    assert all(r["sell_value"] == 0.0 for r in result)