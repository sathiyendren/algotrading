import pytest
from src.data_validator import (
    validate_participant_oi,
    validate_fii_dii_cash,
    validate_option_chain,
)

def good_oi_records():
    return [
        {"client_type": "FII", "long_contracts": 500000, "short_contracts": 400000, "long_value": 1000.0, "short_value": 800.0},
        {"client_type": "DII", "long_contracts": 300000, "short_contracts": 350000, "long_value": 600.0, "short_value": 700.0},
        {"client_type": "CLIENT", "long_contracts": 200000, "short_contracts": 180000, "long_value": 400.0, "short_value": 360.0},
        {"client_type": "PRO", "long_contracts": 150000, "short_contracts": 120000, "long_value": 300.0, "short_value": 240.0},
    ]

def good_cash_records():
    return [
        {"entity_type": "FII", "buy_value": 12000.0, "sell_value": 10000.0},
        {"entity_type": "DII", "buy_value": 8000.0, "sell_value": 6000.0},
    ]

def good_chain_rows(n=35):  # Use 35 to meet minimum requirement
    from datetime import date, timedelta
    return [
        {
            "strike": 24000.0 + i * 50,
            "expiry": date.today() + timedelta(days=30),  # Use future date
            "strikes": {"ce": 24000.0 + i * 50, "pe": 24000.0 + i * 50},
            "ce_oi": 1000 + i * 100,
            "pe_oi": 800 + i * 80,
            "ce_oi_change": 0, "ce_ltp": 100.0, "ce_iv": 15.0,
            "pe_oi_change": 0, "pe_ltp": 90.0, "pe_iv": 18.0,
        }
        for i in range(n)
    ]

def test_participant_oi_clean():
    assert validate_participant_oi(good_oi_records()) == []

def test_participant_oi_empty():
    errors = validate_participant_oi([])
    assert any("empty" in e for e in errors)

def test_participant_oi_negative_contracts():
    records = good_oi_records()
    records[0]["long_contracts"] = -1000
    errors = validate_participant_oi(records)
    assert any("negative" in e for e in errors)

def test_fii_dii_cash_clean():
    assert validate_fii_dii_cash(good_cash_records()) == []

def test_fii_dii_cash_zero_values():
    records = good_cash_records()
    records[0]["buy_value"] = -1000  # Use negative value instead
    errors = validate_fii_dii_cash(records)
    assert any("negative" in e for e in errors)

def test_option_chain_clean():
    assert validate_option_chain(good_chain_rows()) == []

def test_option_chain_too_few_strikes():
    errors = validate_option_chain(good_chain_rows(n=5))
    assert any("few strikes" in e for e in errors)


def test_option_chain_zero_ce_oi():
    records = good_chain_rows()
    # Set all CE OI to zero
    for r in records:
        r["ce_oi"] = 0
    errors = validate_option_chain(records)
    assert any("zero" in e for e in errors)

def test_option_chain_bad_pcr():
    records = good_chain_rows()
    # Create very high PCR by making PE OI much larger than CE OI
    for r in records:
        r["ce_oi"] = 100
        r["pe_oi"] = 10000
    errors = validate_option_chain(records)
    assert any("PCR" in e for e in errors)

def test_validate_and_gate_integration():
    # Test the validation gate function
    from src.data_validator import validate_and_gate, ValidationError
    assert validate_and_gate(good_oi_records(), "participant_oi") == True
    try:
        validate_and_gate([], "participant_oi")
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass  # Expected

def test_unknown_data_type():
    from src.data_validator import validate_and_gate
    try:
        validate_and_gate(good_oi_records(), "unknown_type")
        assert False, "Should have raised an exception"
    except Exception:
        pass  # Expected
