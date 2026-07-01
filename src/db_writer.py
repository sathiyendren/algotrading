from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from src.data_validator import validate_and_gate, ValidationError
# from src.notifier import alert   # for Telegram alerts
from src.cache import cache_participant_oi
from src.db.session import SessionLocal
from src.db.models import ParticipantOI, FIIDIICash


def upsert_participant_oi(records: list[dict]):
    """Insert or update participant OI — safe to run multiple times per day."""
    # Validate first — raises ValidationError if data is bad
    try:
        validate_and_gate(records, "participant_oi")
    except ValidationError as e:
        alert(f"⚠️ Participant OI validation FAILED — DB write skipped\n{e}")
        return  # do not write bad data

    with SessionLocal() as db:
        for rec in records:
            stmt = insert(ParticipantOI).values(**rec)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_participant_oi",
                set_={
                    "long_contracts": stmt.excluded.long_contracts,
                    "short_contracts": stmt.excluded.short_contracts,
                    "long_value": stmt.excluded.long_value,
                    "short_value": stmt.excluded.short_value,
                    "scraped_at": stmt.excluded.scraped_at,
                },
            )
            db.execute(stmt)
        db.commit()

    # Cache after successful DB write
    cache_participant_oi(records)
    logger.info(f"Upserted and cached {len(records)} participant OI rows")


def upsert_fii_dii_cash(records: list[dict]):
    """Insert or update FII/DII cash data."""
    try:
        validate_and_gate(records, "fii_dii_cash")
    except ValidationError as e:
        alert(f"⚠️ FII/DII cash validation FAILED — DB write skipped\n{e}")
        return

    with SessionLocal() as db:
        for rec in records:
            stmt = insert(FIIDIICash).values(**rec)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_fii_dii_cash",
                set_={
                    "buy_value": stmt.excluded.buy_value,
                    "sell_value": stmt.excluded.sell_value,
                    "scraped_at": stmt.excluded.scraped_at,
                },
            )
            db.execute(stmt)
        db.commit()
        logger.info(f"Upserted {len(records)} FII/DII cash rows")


def test_connection():
    """Test database connection."""
    with SessionLocal() as db:
        try:
            db.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
