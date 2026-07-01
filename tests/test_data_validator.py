import pytest
from datetime import date, timedelta
from src.data_validator import (
    validate_participant_oi,
    validate_fii_dii_cash,
    validate_option_chain,
)

def good_oi_records():
    return [
        {"client_type": "FII", "long_contracts": 500000, "short_contracts": 400000, "long_value": 1000.0, "short_value": 800.0},
        {"client_type": "DII", "long_contracts": 300000, "short_contracts": 350000, "long_value": 600.0, "short_value": 700.0},
        {"client_type": "CLIENT", "long_contracts": 200000, "short_contracts": 250000, "long_value": 400.0, "short_value": 500.0},
        {"client_type": "PRO", "long_contracts": 150000, "short_contracts": 150000, "long_value": 300.0, "short_value": 300.0},
    ]

def good_cash_records():
    return [
        {"entity_type": "FII", "buy_value": 5000.0, "sell_value": 3000.0},
        {"entity_type": "DII", "buy_value": 2000.0, "sell_value": 4000.0},
    ]

def good_chain_rows(n=50):
    today = date.today()
    expiry = today + timedelta(days=3)
    return [
        {
            "strike": 24000.0 + i * 50,
            "ce_oi": 100000 + i * 1000,
            "pe_oi": 90000 + i * 900,
            "ce_oi_change": 0, "ce_ltp": 100.0, "ce_iv": 15.0,
            "pe_oi_change": 0, "pe_ltp": 80.0,  "pe_iv": 14.0,
            "expiry": expiry,
            "pcr": 0.9,
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

def test_participant_oi_missing_types():
    # Test with incomplete data (missing PRO and CLIENT)
    incomplete_records = [
        {"client_type": "FII", "long_contracts": 500000, "short_contracts": 400000, "long_value": 1000.0, "short_value": 800.0},
        {"client_type": "DII", "long_contracts": 300000, "short_contracts": 350000, "long_value": 600.0, "short_value": 700.0},
    ]
    errors = validate_participant_oi(incomplete_records)
    assert any("Missing client types" in e for e in errors)

def test_fii_dii_cash_clean():
    assert validate_fii_dii_cash(good_cash_records()) == []

def test_fii_dii_cash_zero_values():
    records = good_cash_records()
    records[0]["buy_value"] = 0
    records[0]["sell_value"] = 0
    errors = validate_fii_dii_cash(records)
    assert any("zero" in e for e in errors)

def test_option_chain_clean():
    assert validate_option_chain(good_chain_rows()) == []

def test_option_chain_too_few_strikes():
    errors = validate_option_chain(good_chain_rows(n=5))
    assert any("few strikes" in e for e in errors)

def test_option_chain_zero_ce_oi():
    rows = good_chain_rows()
    for r in rows:
        r["ce_oi"] = 0
    errors = validate_option_chain(rows)
    assert any("CE OI is zero" in e for e in errors)

def test_option_chain_bad_pcr():
    rows = good_chain_rows()
    for r in rows:
        r["pe_oi"] = r["ce_oi"] * 10
    errors = validate_option_chain(rows)
    assert any("PCR" in e for e in errors)

def test_validate_and_gate_integration():
    from src.data_validator import validate_and_gate, ValidationError
    
    # Should pass with good data
    assert validate_and_gate(good_oi_records(), "participant_oi", raise_on_error=False) == True
    
    # Should fail with bad data
    bad_records = [{"client_type": "FII", "long_contracts": -1000, "short_contracts": 0}]
    assert validate_and_gate(bad_records, "participant_oi", raise_on_error=False) == False
    
    # Should raise exception when raise_on_error=True
    with pytest.raises(ValidationError):
        validate_and_gate(bad_records, "participant_oi", raise_on_error=True)

def test_unknown_data_type():
    from src.data_validator import validate_and_gate
    
    with pytest.raises(ValueError):
        validate_and_gate([], "unknown_type")

def test_validation_performance():
    import time
    
    # Test with large dataset
    large_chain = good_chain_rows(n=200)
    
    start_time = time.time()
    errors = validate_option_chain(large_chain)
    end_time = time.time()
    
    # Should complete quickly even with 200 strikes
    assert end_time - start_time < 1.0  # Less than 1 second
    assert errors == []  # Should still be valid

def test_edge_cases():
    # Test participant OI with all zero contracts
    records = good_oi_records()
    for r in records:
        r["long_contracts"] = 0
        r["short_contracts"] = 0
    errors = validate_participant_oi(records)
    # Should flag FII/DII having zero contracts as suspicious
    assert any("suspiciously low" in e for e in errors)

def test_option_chain_stale_expiry():
    rows = good_chain_rows()
    yesterday = date.today() - timedelta(days=1)
    for r in rows:
        r["expiry"] = yesterday
    errors = validate_option_chain(rows)
    assert any("Stale expiry" in e for e in errors)
