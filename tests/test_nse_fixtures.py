import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock


# ------------------------------------------------------------------ #
#  NSE API fixture responses — mimic real NSE JSON structure           #
# ------------------------------------------------------------------ #

@pytest.fixture
def nse_participant_oi_response():
    """Realistic NSE participant OI API response."""
    return [
        {
            "clientType": "FII",
            "futLongOI": 654210,
            "futShortOI": 812450,
            "futLongAmt": 13084.20,
            "futShortAmt": 16249.00,
        },
        {
            "clientType": "DII",
            "futLongOI": 982340,
            "futShortOI": 876230,
            "futLongAmt": 19646.80,
            "futShortAmt": 17524.60,
        },
        {
            "clientType": "Client",
            "futLongOI": 2845210,
            "futShortOI": 2912450,
            "futLongAmt": 56904.20,
            "futShortAmt": 58249.00,
        },
        {
            "clientType": "Pro",
            "futLongOI": 234560,
            "futShortOI": 215190,
            "futLongAmt": 4691.20,
            "futShortAmt": 4303.80,
        },
    ]


@pytest.fixture
def nse_fii_dii_cash_response():
    """Realistic NSE FII/DII cash API response."""
    return [
        {
            "date": date.today().strftime("%d-%b-%Y"),
            "fiiBuyValue": 12456.70,
            "fiiSellValue": 14230.10,
            "diiBuyValue": 8234.50,
            "diiSellValue": 6120.30,
        },
        # Older dates follow — scraper uses index 0 (latest)
        {
            "date": (date.today() - timedelta(days=1)).strftime("%d-%b-%Y"),
            "fiiBuyValue": 10000.00,
            "fiiSellValue": 11000.00,
            "diiBuyValue": 7000.00,
            "diiSellValue": 5500.00,
        },
    ]


@pytest.fixture
def nse_option_chain_response():
    """Realistic NSE option chain API response for NIFTY."""
    expiry = (date.today() + timedelta(days=3)).strftime("%d-%b-%Y")
    far_expiry = (date.today() + timedelta(days=10)).strftime("%d-%b-%Y")

    strikes = []
    base = 24000

    for i in range(40):
        strike = base + (i * 50)
        strikes.append({
            "strikePrice": strike,
            "expiryDate": expiry,
            "CE": {
                "openInterest": 100000 + i * 5000,
                "changeinOpenInterest": 2000 + i * 100,
                "lastPrice": max(0.05, 500.0 - i * 12),
                "impliedVolatility": 14.5 + i * 0.1,
            },
            "PE": {
                "openInterest": 90000 + i * 4500,
                "changeinOpenInterest": 1800 + i * 90,
                "lastPrice": max(0.05, 100.0 + i * 10),
                "impliedVolatility": 13.5 + i * 0.1,
            },
        })
        # Add far expiry strikes — parser should ignore these
        strikes.append({
            "strikePrice": strike,
            "expiryDate": far_expiry,
            "CE": {"openInterest": 5000, "changeinOpenInterest": 0,
                   "lastPrice": 10.0, "impliedVolatility": 16.0},
            "PE": {"openInterest": 4000, "changeinOpenInterest": 0,
                   "lastPrice": 8.0, "impliedVolatility": 15.0},
        })

    return {
        "records": {
            "expiryDates": [expiry, far_expiry],
            "data": strikes,
        }
    }


@pytest.fixture
def mock_scraper_old(nse_participant_oi_response, nse_fii_dii_cash_response,
                 nse_option_chain_response):
    """NSEScraper with all HTTP calls mocked out."""
    scraper = MagicMock()
    scraper._get.side_effect = lambda endpoint: {
        "/api/participant-wise-trading-data": nse_participant_oi_response,
        "/api/fiidiiTradeReact": nse_fii_dii_cash_response,
    }.get(endpoint, {})

    # Option chain endpoint has a dynamic symbol param
    def mock_get(endpoint):
        if "option-chain-indices" in endpoint:
            return nse_option_chain_response
        return {}

    scraper._get.side_effect = mock_get
    return scraper


# ------------------------------------------------------------------ #
#  Test helper functions for validating fixture data                  #
# ------------------------------------------------------------------ #

def test_participant_oi_fixture_structure(nse_participant_oi_response):
    """Verify participant OI fixture has correct structure."""
    assert isinstance(nse_participant_oi_response, list)
    assert len(nse_participant_oi_response) == 4
    
    # Check required client types
    client_types = [item["clientType"] for item in nse_participant_oi_response]
    expected_types = ["FII", "DII", "Client", "Pro"]
    assert client_types == expected_types
    
    # Check data structure for each record
    for record in nse_participant_oi_response:
        assert "clientType" in record
        assert "futLongOI" in record
        assert "futShortOI" in record
        assert "futLongAmt" in record
        assert "futShortAmt" in record
        
        # Verify data types
        assert isinstance(record["futLongOI"], int)
        assert isinstance(record["futShortOI"], int)
        assert isinstance(record["futLongAmt"], (int, float))
        assert isinstance(record["futShortAmt"], (int, float))


def test_fii_dii_cash_fixture_structure(nse_fii_dii_cash_response):
    """Verify FII/DII cash fixture has correct structure."""
    assert isinstance(nse_fii_dii_cash_response, list)
    assert len(nse_fii_dii_cash_response) >= 1
    
    # Check latest record structure
    latest = nse_fii_dii_cash_response[0]
    assert "date" in latest
    assert "fiiBuyValue" in latest
    assert "fiiSellValue" in latest
    assert "diiBuyValue" in latest
    assert "diiSellValue" in latest
    
    # Verify date format
    today_str = date.today().strftime("%d-%b-%Y")
    assert latest["date"] == today_str
    
    # Verify data types
    assert isinstance(latest["fiiBuyValue"], (int, float))
    assert isinstance(latest["fiiSellValue"], (int, float))
    assert isinstance(latest["diiBuyValue"], (int, float))
    assert isinstance(latest["diiSellValue"], (int, float))


def test_option_chain_fixture_structure(nse_option_chain_response):
    """Verify option chain fixture has correct structure."""
    assert "records" in nse_option_chain_response
    assert "expiryDates" in nse_option_chain_response["records"]
    assert "data" in nse_option_chain_response["records"]
    
    records = nse_option_chain_response["records"]
    assert isinstance(records["expiryDates"], list)
    assert len(records["expiryDates"]) >= 1
    assert isinstance(records["data"], list)
    assert len(records["data"]) > 0
    
    # Check strike data structure
    for strike in records["data"][:5]:  # Check first 5 strikes
        assert "strikePrice" in strike
        assert "expiryDate" in strike
        assert "CE" in strike
        assert "PE" in strike
        
        # Check CE data
        ce = strike["CE"]
        assert "openInterest" in ce
        assert "changeinOpenInterest" in ce
        assert "lastPrice" in ce
        assert "impliedVolatility" in ce
        
        # Check PE data
        pe = strike["PE"]
        assert "openInterest" in pe
        assert "changeinOpenInterest" in pe
        assert "lastPrice" in pe
        assert "impliedVolatility" in pe


def test_mock_scraper_fixture(mock_scraper):
    """Verify mock scraper fixture works correctly."""
    assert mock_scraper is not None
    assert hasattr(mock_scraper, '_get')
    
    # Test participant OI endpoint
    oi_data = mock_scraper._get("/api/participant-wise-trading-data")
    assert isinstance(oi_data, list)
    assert len(oi_data) == 4
    
    # Test FII/DII cash endpoint
    cash_data = mock_scraper._get("/api/fiidiiTradeReact")
    assert isinstance(cash_data, list)
    assert len(cash_data) >= 1
    
    # Test option chain endpoint
    option_data = mock_scraper._get("/api/option-chain-indices?symbol=NIFTY")
    assert "records" in option_data
    assert "data" in option_data["records"]


# ------------------------------------------------------------------ #
#  Data validation helpers                                           #
# ------------------------------------------------------------------ #

def validate_participant_oi_data(data):
    """Helper function to validate participant OI data structure."""
    required_fields = ["clientType", "futLongOI", "futShortOI", "futLongAmt", "futShortAmt"]
    required_client_types = ["FII", "DII", "Client", "Pro"]
    
    if not isinstance(data, list):
        return False, "Data should be a list"
    
    if len(data) != 4:
        return False, "Should have exactly 4 client types"
    
    client_types = [item.get("clientType") for item in data]
    if client_types != required_client_types:
        return False, f"Missing client types. Expected: {required_client_types}, Got: {client_types}"
    
    for record in data:
        for field in required_fields:
            if field not in record:
                return False, f"Missing field: {field}"
        
        # Validate numeric fields
        if not isinstance(record["futLongOI"], int) or record["futLongOI"] < 0:
            return False, "Invalid futLongOI value"
        if not isinstance(record["futShortOI"], int) or record["futShortOI"] < 0:
            return False, "Invalid futShortOI value"
    
    return True, "Valid data"


def validate_fii_dii_cash_data(data):
    """Helper function to validate FII/DII cash data structure."""
    required_fields = ["date", "fiiBuyValue", "fiiSellValue", "diiBuyValue", "diiSellValue"]
    
    if not isinstance(data, list) or len(data) == 0:
        return False, "Data should be a non-empty list"
    
    latest = data[0]
    for field in required_fields:
        if field not in latest:
            return False, f"Missing field: {field}"
    
    # Validate date format
    try:
        from datetime import datetime
        datetime.strptime(latest["date"], "%d-%b-%Y")
    except ValueError:
        return False, "Invalid date format. Expected DD-MMM-YYYY"
    
    # Validate numeric fields
    for field in ["fiiBuyValue", "fiiSellValue", "diiBuyValue", "diiSellValue"]:
        if not isinstance(latest[field], (int, float)) or latest[field] < 0:
            return False, f"Invalid {field} value"
    
    return True, "Valid data"


def validate_option_chain_data(data):
    """Helper function to validate option chain data structure."""
    if not isinstance(data, dict):
        return False, "Data should be a dictionary"
    
    if "records" not in data:
        return False, "Missing 'records' field"
    
    records = data["records"]
    if "data" not in records or not isinstance(records["data"], list):
        return False, "Missing or invalid 'data' field"
    
    if len(records["data"]) == 0:
        return False, "Data array should not be empty"
    
    # Validate strike data
    for strike in records["data"][:3]:  # Check first 3 strikes
        required_fields = ["strikePrice", "expiryDate", "CE", "PE"]
        for field in required_fields:
            if field not in strike:
                return False, f"Missing field: {field}"
        
        # Validate CE/PE data
        for option_type in ["CE", "PE"]:
            option_data = strike[option_type]
            required_option_fields = ["openInterest", "changeinOpenInterest", "lastPrice", "impliedVolatility"]
            for field in required_option_fields:
                if field not in option_data:
                    return False, f"Missing {option_type} field: {field}"
    
    return True, "Valid data"


# ------------------------------------------------------------------ #
#  Integration tests for fixtures                                      #
# ------------------------------------------------------------------ #

def test_fixture_validation_helpers():
    """Test the validation helper functions with valid data."""
    # Test participant OI validation
    valid_oi = [
        {"clientType": "FII", "futLongOI": 1000, "futShortOI": 800, "futLongAmt": 50.0, "futShortAmt": 40.0},
        {"clientType": "DII", "futLongOI": 900, "futShortOI": 700, "futLongAmt": 45.0, "futShortAmt": 35.0},
        {"clientType": "Client", "futLongOI": 2000, "futShortOI": 1800, "futLongAmt": 100.0, "futShortAmt": 90.0},
        {"clientType": "Pro", "futLongOI": 300, "futShortOI": 250, "futLongAmt": 15.0, "futShortAmt": 12.5},
    ]
    is_valid, message = validate_participant_oi_data(valid_oi)
    assert is_valid, f"Validation failed: {message}"
    
    # Test FII/DII cash validation
    valid_cash = [{
        "date": date.today().strftime("%d-%b-%Y"),
        "fiiBuyValue": 1000.0,
        "fiiSellValue": 800.0,
        "diiBuyValue": 600.0,
        "diiSellValue": 400.0,
    }]
    is_valid, message = validate_fii_dii_cash_data(valid_cash)
    assert is_valid, f"Validation failed: {message}"
    
    # Test option chain validation
    valid_options = {
        "records": {
            "data": [{
                "strikePrice": 24000,
                "expiryDate": "31-Jul-2026",
                "CE": {"openInterest": 100000, "changeinOpenInterest": 1000, "lastPrice": 150.0, "impliedVolatility": 15.0},
                "PE": {"openInterest": 90000, "changeinOpenInterest": -500, "lastPrice": 120.0, "impliedVolatility": 14.0},
            }]
        }
    }
    is_valid, message = validate_option_chain_data(valid_options)
    assert is_valid, f"Validation failed: {message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

@pytest.fixture
def mock_scraper_fixed(nse_participant_oi_response, nse_fii_dii_cash_response,
                       nse_option_chain_response):
    """Fixed NSEScraper with all HTTP calls mocked out."""
    scraper = MagicMock()
    
    def mock_get_side_effect(endpoint):
        if endpoint == "/api/participant-wise-trading-data":
            return nse_participant_oi_response
        elif endpoint == "/api/fiidiiTradeReact":
            return nse_fii_dii_cash_response
        elif "option-chain-indices" in endpoint:
            return nse_option_chain_response
        else:
            return {}
    
    scraper._get.side_effect = mock_get_side_effect
    return scraper


def test_mock_scraper_fixture_fixed(mock_scraper_fixed):
    """Verify fixed mock scraper fixture works correctly."""
    assert mock_scraper_fixed is not None
    assert hasattr(mock_scraper_fixed, '_get')
    
    # Test participant OI endpoint
    oi_data = mock_scraper_fixed._get("/api/participant-wise-trading-data")
    assert isinstance(oi_data, list)
    assert len(oi_data) == 4
    
    # Test FII/DII cash endpoint
    cash_data = mock_scraper_fixed._get("/api/fiidiiTradeReact")
    assert isinstance(cash_data, list)
    assert len(cash_data) >= 1
    
    # Test option chain endpoint
    option_data = mock_scraper_fixed._get("/api/option-chain-indices?symbol=NIFTY")
    assert "records" in option_data
    assert "data" in option_data["records"]
