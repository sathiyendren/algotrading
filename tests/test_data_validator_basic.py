import pytest
from datetime import date, timedelta
from src.data_validator import (
    validate_participant_oi,
    validate_fii_dii_cash,
    validate_option_chain,
)

def good_oi_records():
    return [
        {client_type: FII, long_contracts: 500000, short_contracts: 400000, long_value: 1000.0, short_value: 800.0},
        {client_type: DII, long_contracts: 300000, short_contracts: 350000, long_value: 600.0, short_value: 700.0},
    ]

def good_cash_records():
    return [
        {entity_type: FII, buy_value: 5000.0, sell_value: 3000.0},
        {entity_type: DII, buy_value: 2000.0, sell_value: 4000.0},
    ]

def good_chain_rows(n=50):
    today = date.today()
    expiry = today + timedelta(days=3)
    return [
        {
            strike: 24000.0 + i * 50,
            ce_oi: 100000 + i * 1000,
            pe_oi: 90000 + i * 900,
            ce_oi_change: 0, ce_ltp: 100.0, ce_iv: 15.0,
            pe_oi_change: 0, pe_ltp: 80.0,  pe_iv: 14.0,
            expiry: expiry,
            pcr: 0.9,
        }
        for i in range(n)
    ]

def test_participant_oi_clean():
    assert validate_participant_oi(good_oi_records()) == []

def test_participant_oi_empty():
    errors = validate_participant_oi([])
    assert any(empty in e for e in errors)

def test_participant_oi_negative_contracts():
    records = good_oi_records()
    records[0][long_contracts] = -1000
    errors = validate_participant_oi(records)
    assert any(negative in e for e in errors)

def test_fii_dii_cash_clean():
    assert validate_fii_dii_cash(good_cash_records()) == []

def test_fii_dii_cash_zero_values():
    records = good_cash_records()
    records[0][buy_value] = 0
    records[0][sell_value] = 0
    errors = validate_fii_dii_cash(records)
    assert any(zero in e for e in errors)

def test_option_chain_clean():
    assert validate_option_chain(good_chain_rows()) == []

def test_option_chain_too_few_strikes():
    errors = validate_option_chain(good_chain_rows(n=5))
    assert any(few strikes in e for e in errors)
