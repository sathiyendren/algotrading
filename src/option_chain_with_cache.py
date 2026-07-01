import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
import json

from loguru import logger
from dotenv import load_dotenv

from nse_scraper import NSEScraper
from db.session import SessionLocal
from db.models import OptionChainSnapshot
from cache import cache_option_chain, get_cached_chain, cache_pcr, cache_max_pain

load_dotenv("/opt/algotrading/.env")

logger.add(
    "/opt/algotrading/logs/option_chain.log",
    rotation="1 day",
    retention="30 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

IST = ZoneInfo("Asia/Kolkata")
SYMBOL = "NIFTY"


class OptionChain:

    def __init__(self, scraper: NSEScraper):
        self.scraper = scraper

    def fetch(self, symbol: str = SYMBOL) -> dict:
        """Fetch raw option chain from NSE."""
        endpoint = f"/api/option-chain-indices?symbol={symbol}"
        raw = self.scraper._get(endpoint)
        return raw

    def parse(self, raw: dict, snapshot_time: datetime) -> list[dict]:
        """Parse NSE option chain JSON into flat row-per-strike format."""
        rows = []
        try:
            records = raw["records"]["data"]
            expiry_dates = raw["records"]["expiryDates"]
            nearest_expiry = expiry_dates[0]

            for record in records:
                strike = record["strikePrice"]
                
                ce_data = record.get("CE", {})
                ce_oi = ce_data.get("openInterest", 0) or 0
                ce_volume = ce_data.get("totalTradedVolume", 0) or 0
                ce_iv = ce_data.get("impliedVolatility", 0) or 0
                ce_ltp = ce_data.get("lastPrice", 0) or 0
                
                pe_data = record.get("PE", {})
                pe_oi = pe_data.get("openInterest", 0) or 0
                pe_volume = pe_data.get("totalTradedVolume", 0) or 0
                pe_iv = pe_data.get("impliedVolatility", 0) or 0
                pe_ltp = pe_data.get("lastPrice", 0) or 0

                if ce_oi > 0 or pe_oi > 0:
                    rows.append({
                        "symbol": symbol,
                        "strike": strike,
                        "expiry": nearest_expiry,
                        "snapshot_time": snapshot_time,
                        "ce_oi": ce_oi,
                        "ce_volume": ce_volume,
                        "ce_iv": ce_iv,
                        "ce_ltp": ce_ltp,
                        "pe_oi": pe_oi,
                        "pe_volume": pe_volume,
                        "pe_iv": pe_iv,
                        "pe_ltp": pe_ltp,
                        "pcr": round(pe_oi / ce_oi, 4) if ce_oi > 0 else None,
                    })

            msg = "Parsed {} strikes for {} expiry={}".format(len(rows), symbol, nearest_expiry)
            logger.info(msg)
            return rows

        except KeyError as e:
            logger.error(f"Unexpected NSE response structure — missing key: {e}")
            raise

    def compute_pcr(self, rows: list[dict]) -> float:
        """Overall PCR = sum of all PE OI / sum of all CE OI."""
        total_pe = sum(r["pe_oi"] for r in rows)
        total_ce = sum(r["ce_oi"] for r in rows)
        pcr = round(total_pe / total_ce, 4) if total_ce > 0 else 0.0
        msg = "PCR: {} (PE OI={}, CE OI={})".format(pcr, total_pe, total_ce)
        logger.info(msg)
        return pcr

    def compute_max_pain(self, rows: list[dict]) -> float:
        """Max pain = strike where total option writers lose least money."""
        strikes = sorted({r["strike"] for r in rows})
        oi_map = {r["strike"]: (r["ce_oi"], r["pe_oi"]) for r in rows}

        min_pain = float("inf")
        max_pain_strike = strikes[0]

        for expiry_strike in strikes:
            total_pain = 0
            for strike, (ce_oi, pe_oi) in oi_map.items():
                if expiry_strike > strike:
                    total_pain += (expiry_strike - strike) * ce_oi
                if expiry_strike < strike:
                    total_pain += (strike - expiry_strike) * pe_oi

            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = expiry_strike

        logger.info(f"Max pain strike: {max_pain_strike}")
        return max_pain_strike

    def detect_oi_buildup(self, rows: list[dict]) -> dict:
        """Identify where large OI is building — signals support/resistance."""
        ce_sorted = sorted(rows, key=lambda r: r["ce_oi"], reverse=True)[:3]
        pe_sorted = sorted(rows, key=lambda r: r["pe_oi"], reverse=True)[:3]

        result = {
            "ce_resistance": [{"strike": r["strike"], "ce_oi": r["ce_oi"]} for r in ce_sorted],
            "pe_support": [{"strike": r["strike"], "pe_oi": r["pe_oi"]} for r in pe_sorted],
        }
        return result

    def save_snapshot(self, rows: list[dict]):
        """Save parsed option chain to database."""
        db = SessionLocal()
        try:
            db.bulk_insert_mappings(OptionChainSnapshot, rows)
            db.commit()
            logger.info(f"Saved {len(rows)} strikes to database")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save to database: {e}")
            raise
        finally:
            db.close()

    def cache_snapshot_data(self, symbol: str, rows: list[dict], pcr: float, max_pain: float, buildup: dict):
        """Cache option chain data and derived metrics to Redis."""
        try:
            # Cache the raw option chain data
            cache_option_chain(symbol, rows)
            logger.debug(f"Cached option chain for {symbol} with {len(rows)} strikes")
            
            # Cache derived metrics
            cache_pcr(symbol, pcr)
            logger.debug(f"Cached PCR for {symbol}: {pcr}")
            
            cache_max_pain(symbol, max_pain)
            logger.debug(f"Cached max pain for {symbol}: {max_pain}")
            
            logger.info(f"Successfully cached all data for {symbol}")
            
        except Exception as e:
            logger.warning(f"Failed to cache snapshot data: {e}")

    def run_snapshot(self, symbol: str = SYMBOL, use_cache: bool = False):
        """Full pipeline: fetch → parse → compute → save → cache."""
        snapshot_time = datetime.now(tz=IST)
        time_str = snapshot_time.strftime('%H:%M:%S IST')
        logger.info(f"Running option chain snapshot at {time_str}")

        # Fetch fresh data
        logger.info(f"Fetching option chain data for {symbol}")
        raw = self.fetch(symbol)
        rows = self.parse(raw, snapshot_time)

        if not rows:
            logger.warning("No rows parsed — skipping save and cache")
            return

        # Compute derived metrics
        pcr = self.compute_pcr(rows)
        max_pain = self.compute_max_pain(rows)
        buildup = self.detect_oi_buildup(rows)

        # Save to database
        self.save_snapshot(rows)

        # Cache the results
        self.cache_snapshot_data(symbol, rows, pcr, max_pain, buildup)

        return {
            "snapshot_time": snapshot_time,
            "strikes_captured": len(rows),
            "pcr": pcr,
            "max_pain": max_pain,
            "oi_buildup": buildup,
            "from_cache": False
        }


if __name__ == "__main__":
    # Test the option chain module with cache integration
    try:
        from nse_scraper_enhanced import EnhancedNSEScraper
        
        scraper = EnhancedNSEScraper()
        option_chain = OptionChain(scraper)
        
        logger.info("Option chain module with cache initialized")
        
        # Run snapshot with caching
        result = option_chain.run_snapshot("NIFTY")
        
        if result:
            logger.info(f"Snapshot completed: {result['strikes_captured']} strikes")
            logger.info(f"PCR: {result['pcr']}, Max Pain: {result['max_pain']}")
        
        logger.info("Option chain cache integration test completed")
        
    except Exception as e:
        logger.error(f"Option chain module test failed: {e}")
