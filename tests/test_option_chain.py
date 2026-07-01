import pytest
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import MagicMock, patch

from src.option_chain import OptionChain

IST = ZoneInfo("Asia/Kolkata")


@pytest.fixture
def oc(mock_scraper):
    return OptionChain(mock_scraper)


@pytest.fixture
def parsed_rows(oc, sample_option_chain_data):
    snapshot_time = datetime.now(tz=IST)
    return oc.parse(sample_option_chain_data, snapshot_time)


@pytest.fixture
def sample_parsed_rows():
    """Simple parsed rows for computational tests"""
    return [
        {
            "strike": 19500.0,
            "expiry": "2024-01-25",
            "ce_oi": 1000,
            "pe_oi": 1500,
            "snapshot_time": datetime.now(tz=IST)
        },
        {
            "strike": 19600.0,
            "expiry": "2024-01-25",
            "ce_oi": 800,
            "pe_oi": 1200,
            "snapshot_time": datetime.now(tz=IST)
        }
    ]


# ---- Parsing ----

def test_parse_filters_to_nearest_expiry(parsed_rows, sample_option_chain_data):
    # Fixture has 2 expiries — parser should keep only nearest
    expiries = {r["expiry"] for r in parsed_rows}
    assert len(expiries) == 1


def test_parse_excludes_zero_oi_strikes(oc, sample_option_chain_data):
    # Add a zero-OI strike to response
    sample_option_chain_data["records"]["data"].append({
        "strikePrice": 99999,
        "expiryDate": sample_option_chain_data["records"]["expiryDates"][0],
        "CE": {"openInterest": 0, "changeinOpenInterest": 0,
               "lastPrice": 0, "impliedVolatility": 0},
        "PE": {"openInterest": 0, "changeinOpenInterest": 0,
               "lastPrice": 0, "impliedVolatility": 0},
    })
    snapshot_time = datetime.now(tz=IST)
    rows = oc.parse(sample_option_chain_data, snapshot_time)
    strikes = [r["strike"] for r in rows]
    assert 99999 not in strikes


def test_parse_snapshot_time_recorded(parsed_rows):
    for r in parsed_rows:
        assert r["snapshot_time"] is not None


# ---- PCR calculation ----

def test_pcr_is_positive(oc, parsed_rows):
    pcr = oc.compute_pcr(parsed_rows)
    assert pcr > 0


def test_pcr_formula(oc, sample_parsed_rows):
    rows = sample_parsed_rows
    pcr = oc.compute_pcr(rows)
    # total PE=2700, total CE=1800 → PCR = 2700/1800 = 1.5
    assert pcr == round(2700 / 1800, 4)


def test_pcr_handles_zero_ce_oi(oc):
    rows = [{"ce_oi": 0, "pe_oi": 100}]
    pcr = oc.compute_pcr(rows)
    assert pcr == 0.0  # no division by zero crash


# ---- Max pain ----

def test_max_pain_returns_a_strike(oc, parsed_rows):
    strikes = {r["strike"] for r in parsed_rows}
    max_pain = oc.compute_max_pain(parsed_rows)
    assert max_pain in strikes


def test_max_pain_simple_case(oc):
    # Construct a simple case where max pain is obvious
    # All OI concentrated at strike 100
    rows = [
        {"strike": 100.0, "ce_oi": 10000, "pe_oi": 10000},
        {"strike": 200.0, "ce_oi": 100,   "pe_oi": 100},
        {"strike": 50.0,  "ce_oi": 100,   "pe_oi": 100},
    ]
    result = oc.compute_max_pain(rows)
    assert result == 100.0


# ---- OI buildup detection ----

def test_oi_buildup_returns_top_3(oc, parsed_rows):
    buildup = oc.detect_oi_buildup(parsed_rows)
    assert len(buildup["ce_resistance"]) == 3
    assert len(buildup["pe_support"]) == 3


def test_oi_buildup_sorted_descending(oc, parsed_rows):
    buildup = oc.detect_oi_buildup(parsed_rows)
    ce_ois = [r["ce_oi"] for r in buildup["ce_resistance"]]
    assert ce_ois == sorted(ce_ois, reverse=True)
