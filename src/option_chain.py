import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from loguru import logger
from dotenv import load_dotenv

from src.nse_scraper import NSEScraper
from src.db.session import SessionLocal
from src.db.models import OptionChainSnapshot

from cache import cache_option_chain, cache_pcr, cache_max_pain
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

    # ------------------------------------------------------------------ #
    #  Fetch + Parse                                                        #
    # ------------------------------------------------------------------ #

    def fetch(self, symbol: str = SYMBOL) -> dict:
        """Fetch raw option chain from NSE."""
        endpoint = f"/api/option-chain-indices?symbol={symbol}"
        raw = self.scraper._get(endpoint)
        return raw

    def parse(self, raw: dict, snapshot_time: datetime) -> list[dict]:
        """
        Parse NSE option chain JSON into flat row-per-strike format.
        Returns list of dicts ready for DB insert.
        """
        rows = []
        try:
            records = raw["records"]["data"]
            expiry_dates = raw["records"]["expiryDates"]
            nearest_expiry = expiry_dates[0]  # always use front-week expiry

            for entry in records:
                # Skip if not the nearest expiry
                if entry.get("expiryDate") != nearest_expiry:
                    continue

                strike = float(entry["strikePrice"])
                ce = entry.get("CE", {})
                pe = entry.get("PE", {})

                # Skip strikes with zero OI on both sides — far OTM noise
                ce_oi = int(ce.get("openInterest") or 0)
                pe_oi = int(pe.get("openInterest") or 0)
                if ce_oi == 0 and pe_oi == 0:
                    continue

                rows.append({
                    "snapshot_time": snapshot_time,
                    "symbol": symbol,
                    "expiry": datetime.strptime(nearest_expiry, "%d-%b-%Y").date(),
                    "strike": strike,
                    "ce_oi": ce_oi,
                    "ce_oi_change": int(ce.get("changeinOpenInterest") or 0),
                    "ce_ltp": float(ce.get("lastPrice") or 0),
                    "ce_iv": float(ce.get("impliedVolatility") or 0),
                    "pe_oi": pe_oi,
                    "pe_oi_change": int(pe.get("changeinOpenInterest") or 0),
                    "pe_ltp": float(pe.get("lastPrice") or 0),
                    "pe_iv": float(pe.get("impliedVolatility") or 0),
                    "pcr": round(pe_oi / ce_oi, 4) if ce_oi > 0 else None,
                })

            logger.info(
                f"Parsed {len(rows)} strikes for {symbol} "
                f"expiry={nearest_expiry} at {snapshot_time.strftime('%H:%M')}"
            )
            return rows

        except KeyError as e:
            logger.error(f"Unexpected NSE response structure — missing key: {e}")
            raise

    # ------------------------------------------------------------------ #
    #  Derived metrics                                                      #
    # ------------------------------------------------------------------ #

    def compute_pcr(self, rows: list[dict]) -> float:
        """Overall PCR = sum of all PE OI / sum of all CE OI."""
        total_pe = sum(r["pe_oi"] for r in rows)
        total_ce = sum(r["ce_oi"] for r in rows)
        pcr = round(total_pe / total_ce, 4) if total_ce > 0 else 0.0
        logger.info(f"PCR: {pcr} (PE OI={total_pe:,}, CE OI={total_ce:,})")
        return pcr

    def compute_max_pain(self, rows: list[dict]) -> float:
        """
        Max pain = strike where total option writers lose least money.
        For each strike K, sum the intrinsic value of all ITM options
        if market expires at K. The strike with minimum total payout = max pain.
        """
        strikes = sorted({r["strike"] for r in rows})

        # Build lookup: strike -> (ce_oi, pe_oi)
        oi_map = {r["strike"]: (r["ce_oi"], r["pe_oi"]) for r in rows}

        min_pain = float("inf")
        max_pain_strike = strikes[0]

        for expiry_strike in strikes:
            total_pain = 0
            for strike, (ce_oi, pe_oi) in oi_map.items():
                # CE writers lose when expiry > strike (calls finish ITM)
                if expiry_strike > strike:
                    total_pain += (expiry_strike - strike) * ce_oi
                # PE writers lose when expiry < strike (puts finish ITM)
                if expiry_strike < strike:
                    total_pain += (strike - expiry_strike) * pe_oi

            if total_pain < min_pain:
                min_pain = total_pain
                max_pain_strike = expiry_strike

        logger.info(f"Max pain strike: {max_pain_strike}")
        return max_pain_strike

    def find_atm_strike(self, rows: list[dict], spot_price: float) -> float:
        """Find the strike closest to current spot price."""
        strikes = [r["strike"] for r in rows]
        return min(strikes, key=lambda s: abs(s - spot_price))

    def detect_oi_buildup(self, rows: list[dict]) -> dict:
        """
        Identify where large OI is building — signals support/resistance.
        Returns top 3 CE strikes (resistance) and top 3 PE strikes (support).
        """
        ce_sorted = sorted(rows, key=lambda r: r["ce_oi"], reverse=True)[:3]
        pe_sorted = sorted(rows, key=lambda r: r["pe_oi"], reverse=True)[:3]

        result = {
            "ce_resistance": [{"strike": r["strike"], "ce_oi": r["ce_oi"]} for r in ce_sorted],
            "pe_support": [{"strike": r["strike"], "pe_oi": r["pe_oi"]} for r in pe_sorted],
        }
        logger.info(f"OI buildup — resistance: {result['ce_resistance']}")
        logger.info(f"OI buildup — support:    {result['pe_support']}")
        return result

    # ------------------------------------------------------------------ #
    #  DB write                                                             #
    # ------------------------------------------------------------------ #

    def save_snapshot(self, rows: list[dict]):
        """Bulk insert option chain snapshot rows."""
        with SessionLocal() as db:
            db.bulk_insert_mappings(OptionChainSnapshot, rows)
            db.commit()
        logger.info(f"Saved {len(rows)} option chain rows to DB")

    # ------------------------------------------------------------------ #
    #  Main entry point — called by scheduler                              #
    # ------------------------------------------------------------------ #

    def run_snapshot(self, symbol: str = SYMBOL):
        """Full pipeline: fetch → parse → compute → save."""
        snapshot_time = datetime.now(tz=IST)
        logger.info(f"Running option chain snapshot at {snapshot_time.strftime('%H:%M:%S IST')}")

        raw = self.fetch(symbol)
        rows = self.parse(raw, snapshot_time)

        if not rows:
            logger.warning("No rows parsed — skipping save")
            return

        pcr = self.compute_pcr(rows)
        max_pain = self.compute_max_pain(rows)
        buildup = self.detect_oi_buildup(rows)

        self.save_snapshot(rows)
n        # NEW — write to Redis cache
        cache_option_chain(symbol, rows)
        cache_pcr(symbol, pcr)
        cache_max_pain(symbol, max_pain)

        return {
            "snapshot_time": snapshot_time,
            "strikes_captured": len(rows),
            "pcr": pcr,
            "max_pain": max_pain,
            "oi_buildup": buildup,
        }


if __name__ == "__main__":
    # Test the option chain module
    try:
        from nse_scraper_enhanced import EnhancedNSEScraper
        
        scraper = EnhancedNSEScraper()
        option_chain = OptionChain(scraper)
        
        logger.info("✅ Option chain module initialized successfully")
        
        # Run a test snapshot
        result = option_chain.run_snapshot("NIFTY")
        
        if result:
            logger.info(f"📊 Snapshot completed: {result['strikes_captured']} strikes")
            logger.info(f"📈 PCR: {result['pcr']}, Max Pain: {result['max_pain']}")
            logger.info(f"🎯 OI Buildup: {result['oi_buildup']}")
        
        logger.info("✅ Option chain module test completed")
        
    except Exception as e:
        logger.error(f"❌ Option chain module test failed: {e}")
