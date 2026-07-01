"""Test configuration and fixtures"""
import pytest
import responses
from datetime import date, datetime
from zoneinfo import ZoneInfo
from unittest.mock import Mock

IST = ZoneInfo("Asia/Kolkata")

@pytest.fixture
def sample_option_chain_data():
    """Sample option chain JSON data"""
    return {
        "records": {
            "expiryDates": ["27-Jul-2023", "31-Aug-2023"],
            "data": [
                {
                    "strikePrice": "43500",
                    "expiryDate": "27-Jul-2023",
                    "CE": {"openInterest": "8000", "lastPrice": "300.50"},
                    "PE": {"openInterest": "18000", "lastPrice": "150.75"}
                },
                {
                    "strikePrice": "44000",
                    "expiryDate": "27-Jul-2023",
                    "CE": {"openInterest": "15000", "lastPrice": "250.50"},
                    "PE": {"openInterest": "12000", "lastPrice": "180.75"}
                },
                {
                    "strikePrice": "44200",
                    "expiryDate": "27-Jul-2023",
                    "CE": {"openInterest": "11000", "lastPrice": "225.30"},
                    "PE": {"openInterest": "13500", "lastPrice": "195.60"}
                }
            ]
        }
    }

@pytest.fixture
def sample_parsed_rows():
    """Sample parsed rows for option chain tests"""
    return [
        {
            "strike_price": 44000,
            "expiry_date": date(2023, 7, 27),
            "call_oi": 15000,
            "put_oi": 12000,
            "call_ltp": 250.50,
            "put_ltp": 180.75,
            "snapshot_time": datetime.now(tz=IST)
        }
    ]

@pytest.fixture
def mock_scraper():
    """Mock scraper for option chain tests"""
    scraper = Mock()
    
    def mock_get_side_effect(endpoint):
        if endpoint == "/api/participant-wise-trading-data":
            return [
                {"clientType": "FII", "futLongOI": "2500000", "futShortOI": "2400000"},
                {"clientType": "DII", "futLongOI": "1500000", "futShortOI": "1450000"},
                {"clientType": "CLIENT", "futLongOI": "800000", "futShortOI": "780000"},
                {"clientType": "PRO", "futLongOI": "600000", "futShortOI": "590000"}
            ]
        elif endpoint == "/api/fiidiiTradeReact":
            return [{"fiiBuyValue": "1250.50", "fiiSellValue": "1150.25"}]
        elif "option-chain-indices" in endpoint:
            return {"records": {"data": []}}
        else:
            return {}
    
    scraper._get.side_effect = mock_get_side_effect
    return scraper