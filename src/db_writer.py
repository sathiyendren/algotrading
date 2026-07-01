from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from cache import cache_participant_oi
from db.session import SessionLocal
from db.models import ParticipantOI, FIIDIICash


def upsert_participant_oi(records: list[dict]):
    """Insert or update participant OI — safe to run multiple times per day."""
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

    # NEW — cache after successful DB write
    cache_participant_oi(records)
    logger.info(f"Upserted and cached {len(records)} participant OI rows")


def upsert_fii_dii_cash(records: list[dict]):
    """Insert or update FII/DII cash data."""
    with SessionLocal() as db:
        for rec in records:
            stmt = insert(FIIDIICash).values(**rec)
            stmt = stmt.on_conflict_do_update(
                constraint="uq_fii_dii_cash",
                set_={
                    "fii_cash": stmt.excluded.fii_cash,
                    "dii_cash": stmt.excluded.dii_cash,
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
