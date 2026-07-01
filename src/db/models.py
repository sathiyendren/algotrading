from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Index,
    Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


# 1. Participant OI — daily NSE participant-wise OI data
class ParticipantOI(Base):
    __tablename__ = "participant_oi"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False)
    symbol = Column(String(20), default="NIFTY")
    client_type = Column(String(30), nullable=False)  # FII, DII, CLIENT, PRO
    long_contracts = Column(BigInteger)
    short_contracts = Column(BigInteger)
    long_value = Column(Numeric(18, 2))
    short_value = Column(Numeric(18, 2))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("trade_date", "client_type", name="uq_participant_oi"),
    )


# 2. FII/DII Cash — cash market buy/sell activity
class FIIDIICash(Base):
    __tablename__ = "fii_dii_cash"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False)
    entity_type = Column(String(10), nullable=False)  # FII or DII
    buy_value = Column(Numeric(18, 2))
    sell_value = Column(Numeric(18, 2))
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("trade_date", "entity_type", name="uq_fii_dii_cash"),
    )


# 3. Option Chain Snapshots — intraday, every 5 minutes
class OptionChainSnapshot(Base):
    __tablename__ = "option_chain_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    symbol = Column(String(20), default="NIFTY")
    expiry = Column(Date, nullable=False)
    strike = Column(Numeric(10, 2), nullable=False)
    ce_oi = Column(BigInteger)
    ce_oi_change = Column(BigInteger)
    ce_ltp = Column(Numeric(10, 2))
    ce_iv = Column(Numeric(6, 2))
    pe_oi = Column(BigInteger)
    pe_oi_change = Column(BigInteger)
    pe_ltp = Column(Numeric(10, 2))
    pe_iv = Column(Numeric(6, 2))
    pcr = Column(Numeric(6, 4))

    __table_args__ = (
        Index("idx_oc_time_strike", "snapshot_time", "strike"),
    )


# 4. Signal Scores — computed daily before market open
class SignalScore(Base):
    __tablename__ = "signal_scores"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    score_date = Column(Date, nullable=False, unique=True)
    fii_oi_score = Column(Numeric(5, 2))       # 0–40
    pcr_score = Column(Numeric(5, 2))           # 0–20
    chart_score = Column(Numeric(5, 2))         # 0–20
    max_pain_score = Column(Numeric(5, 2))      # 0–10
    pro_score = Column(Numeric(5, 2))           # 0–10
    total_score = Column(Numeric(5, 2))         # 0–100
    bias = Column(String(10))                   # BULLISH, BEARISH, NEUTRAL
    raw_inputs = Column(JSONB)                  # full snapshot for audit
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


# 5. Strategy Decisions — what strategy was chosen and why
class StrategyDecision(Base):
    __tablename__ = "strategy_decisions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    decision_date = Column(Date, nullable=False, unique=True)
    strategy_name = Column(String(50))          # bull_put_spread, bear_call_spread etc.
    signal_score_id = Column(BigInteger)        # FK to signal_scores
    expiry = Column(Date)
    rationale = Column(Text)
    approved = Column(Boolean, default=False)   # manual approval gate
    approved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# 6. Orders — SEBI-compliant audit trail for every order
class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True)       # Zerodha order ID
    parent_strategy_id = Column(BigInteger)           # FK to strategy_decisions
    symbol = Column(String(20))
    instrument_token = Column(BigInteger)
    order_type = Column(String(20))                   # LIMIT, MARKET, SL
    transaction_type = Column(String(5))              # BUY, SELL
    quantity = Column(Integer)
    price = Column(Numeric(10, 2))
    trigger_price = Column(Numeric(10, 2))
    status = Column(String(20))                       # PENDING, OPEN, COMPLETE, REJECTED
    exchange_order_id = Column(String(50))
    exchange_timestamp = Column(DateTime(timezone=True))
    placed_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    raw_response = Column(JSONB)                      # full Zerodha response


# 7. Positions — tracks open and closed legs
class Position(Base):
    __tablename__ = "positions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    strategy_id = Column(BigInteger)
    symbol = Column(String(20))
    instrument_token = Column(BigInteger)
    option_type = Column(String(2))             # CE or PE
    strike = Column(Numeric(10, 2))
    expiry = Column(Date)
    quantity = Column(Integer)
    entry_price = Column(Numeric(10, 2))
    exit_price = Column(Numeric(10, 2))
    sl_price = Column(Numeric(10, 2))
    status = Column(String(10))                 # OPEN, CLOSED, SL_HIT
    opened_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True))


# 8. PnL Daily — end-of-day P&L summary
class PnLDaily(Base):
    __tablename__ = "pnl_daily"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, unique=True)
    strategy_name = Column(String(50))
    gross_pnl = Column(Numeric(12, 2))
    brokerage = Column(Numeric(10, 2))
    taxes = Column(Numeric(10, 2))
    net_pnl = Column(Numeric(12, 2))
    capital_deployed = Column(Numeric(14, 2))
    roi_percent = Column(Numeric(6, 2))
    computed_at = Column(DateTime(timezone=True), server_default=func.now())


# 9. Market Events — holidays, circuit breakers, expiry days
class MarketEvent(Base):
    __tablename__ = "market_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_date = Column(Date, nullable=False)
    event_type = Column(String(30))             # HOLIDAY, CIRCUIT_BREAKER, EXPIRY, RBI_POLICY
    description = Column(Text)
    source = Column(String(50))


# 10. System Log — scraper health, errors, alerts sent
class SystemLog(Base):
    __tablename__ = "system_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    logged_at = Column(DateTime(timezone=True), server_default=func.now())
    module = Column(String(50))                 # nse_scraper, signal_engine etc.
    level = Column(String(10))                  # INFO, WARNING, ERROR, CRITICAL
    message = Column(Text)
    details = Column(JSONB)
