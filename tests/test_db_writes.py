import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from src.db_writer import upsert_participant_oi, upsert_fii_dii_cash


@pytest.fixture
def sample_oi():
    return [
        {"trade_date": date.today(), "client_type": "FII",
         "long_contracts": 500000, "short_contracts": 400000,
         "long_value": 10000.0, "short_value": 8000.0},
        {"trade_date": date.today(), "client_type": "DII",
         "long_contracts": 300000, "short_contracts": 250000,
         "long_value": 6000.0, "short_value": 5000.0},
    ]


@pytest.fixture
def sample_cash():
    return [
        {"trade_date": date.today(), "entity_type": "FII",
         "buy_value": 12000.0, "sell_value": 10000.0},
        {"trade_date": date.today(), "entity_type": "DII",
         "buy_value": 8000.0, "sell_value": 6000.0},
    ]


# ---- Validation gate ----

def test_upsert_participant_oi_blocked_on_bad_data():
    bad_records = []  # empty — should fail validation
    with patch("src.db_writer.validate_and_gate", side_effect=Exception("bad data")):
        with patch("src.db_writer.SessionLocal") as mock_db:
            with pytest.raises(Exception):
                upsert_participant_oi(bad_records)
            # DB session should never be opened
            mock_db.assert_not_called()


def test_upsert_fii_dii_blocked_on_bad_data():
    with patch("src.db_writer.validate_and_gate", side_effect=Exception("bad")):
        with patch("src.db_writer.SessionLocal") as mock_db:
            with pytest.raises(Exception):
                upsert_fii_dii_cash([])
            mock_db.assert_not_called()


# ---- Successful write ----

def test_upsert_participant_oi_calls_db(sample_oi):
    with patch("src.db_writer.validate_and_gate", return_value=True):
        with patch("src.db_writer.SessionLocal") as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
            with patch("src.db_writer.cache_participant_oi"):
                upsert_participant_oi(sample_oi)
                mock_db.execute.assert_called()
                mock_db.commit.assert_called_once()


def test_upsert_fii_dii_calls_db(sample_cash):
    with patch("src.db_writer.validate_and_gate", return_value=True):
        with patch("src.db_writer.SessionLocal") as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
            with patch("src.db_writer.cache_participant_oi"):
                upsert_fii_dii_cash(sample_cash)
                mock_db.execute.assert_called()
                mock_db.commit.assert_called_once()


# ---- Idempotency — upsert runs twice, no duplicate rows ----

def test_upsert_is_idempotent(sample_oi):
    """Running upsert twice with same data must not raise."""
    with patch("src.db_writer.validate_and_gate", return_value=True):
        with patch("src.db_writer.SessionLocal") as mock_session_cls:
            mock_db = MagicMock()
            mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_db)
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
            with patch("src.db_writer.cache_participant_oi"):
                upsert_participant_oi(sample_oi)
                upsert_participant_oi(sample_oi)
                assert mock_db.commit.call_count == 2
