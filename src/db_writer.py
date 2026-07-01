from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from src.db.session import SessionLocal
from src.db.models import ParticipantOI, FIIDIICash


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
        logger.info(f"Upserted {len(records)} participant OI rows")


def upsert_fii_dii_cash(records: list[dict]):
    """Insert or update FII/DII cash data."""
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


# Additional upsert functions for other tables
def upsert_option_chain_snapshot(records: list[dict]):
    """Insert option chain snapshots — no unique constraint, just insert."""
    with SessionLocal() as db:
        db.add_all([OptionChainSnapshot(**rec) for rec in records])
        db.commit()
        logger.info(f"Inserted {len(records)} option chain snapshot rows")


def upsert_market_event(event_date: str, event_type: str, description: str, source: str = 'NSE'):
    """Insert market event — skip if exists."""
    with SessionLocal() as db:
        # Check if event already exists
        existing = db.query(MarketEvent).filter(
            MarketEvent.event_date == event_date,
            MarketEvent.event_type == event_type
        ).first()
        
        if existing:
            logger.debug(f"Market event already exists: {event_type} on {event_date}")
            return
        
        # Create new event
        db_record = MarketEvent(
            event_date=event_date,
            event_type=event_type,
            description=description,
            source=source
        )
        db.add(db_record)
        db.commit()
        logger.info(f"Created market event: {event_type} on {event_date}")


def write_system_log(module: str, level: str, message: str, details: dict = None):
    """Write system log entry."""
    with SessionLocal() as db:
        db_record = SystemLog(
            module=module,
            level=level,
            message=message,
            details=details
        )
        db.add(db_record)
        db.commit()
        logger.debug(f"Created system log: {level} - {message}")


def test_connection():
    """Test database connection."""
    try:
        with SessionLocal() as db:
            db.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# Import additional models for extended functionality
from src.db.models import OptionChainSnapshot, MarketEvent, SystemLog


if __name__ == "__main__":
    # Test the database writer
    try:
        if test_connection():
            logger.info("✅ Database writer initialized successfully")
            
            # Test writing a system log
            write_system_log(
                module="db_writer",
                level="INFO",
                message="Database writer test completed"
            )
            
            logger.info("✅ Database writer tests completed")
        else:
            logger.error("❌ Database writer connection failed")
            
    except Exception as e:
        logger.error(f"❌ Database writer test failed: {e}")
