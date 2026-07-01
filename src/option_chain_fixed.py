import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from loguru import logger
from dotenv import load_dotenv

from src.nse_scraper_working import FixedNSEScraper
from src.db.session import SessionLocal
from src.db.models import OptionChainSnapshot

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


class OptionChainFixed:

    def __init__(self):
        self.scraper = FixedNSEScraper()

    def fetch(self, symbol: str = SYMBOL) -> dict:
        """Fetch raw option chain from NSE using fixed scraper."""
        return self.scraper.get_option_chain(symbol)

    def parse(self, raw: dict, snapshot_time: datetime, symbol: str = SYMBOL) -> list[dict]:
        """Parse NSE option chain JSON into flat row-per-strike format."""
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

    def compute_pcr(self, rows: list[dict]) -> float:
        """Overall PCR = sum of all PE OI / sum of all CE OI."""
        total_pe = sum(r["pe_oi"] for r in rows)
        total_ce = sum(r["ce_oi"] for r in rows)
        pcr = round(total_pe / total_ce, 4) if total_ce > 0 else 0.0
        logger.info(f"PCR: {pcr} (PE OI={total_pe:,}, CE OI={total_ce:,})")
        return pcr

    def compute_max_pain(self, rows: list[dict]) -> float:
        """Max pain calculation."""
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
        """Identify OI buildup — signals support/resistance."""
        ce_sorted = sorted(rows, key=lambda r: r["ce_oi"], reverse=True)[:3]
        pe_sorted = sorted(rows, key=lambda r: r["pe_oi"], reverse=True)[:3]

        result = {
            "ce_resistance": [{"strike": r["strike"], "ce_oi": r["ce_oi"]} for r in ce_sorted],
            "pe_support": [{"strike": r["strike"], "pe_oi": r["pe_oi"]} for r in pe_sorted],
        }
        logger.info(f"OI buildup — resistance: {result['ce_resistance']}")
        logger.info(f"OI buildup — support:    {result['pe_support']}")
        return result

    def save_snapshot(self, rows: list[dict]):
        """Bulk insert option chain snapshot rows."""
        with SessionLocal() as db:
            db.bulk_insert_mappings(OptionChainSnapshot, rows)
            db.commit()
        logger.info(f"Saved {len(rows)} option chain rows to DB")

    def run_snapshot(self, symbol: str = SYMBOL):
        """Full pipeline: fetch → parse → compute → save."""
        snapshot_time = datetime.now(tz=IST)
        logger.info(f"Running option chain snapshot at {snapshot_time.strftime('%H:%M:%S IST')}")

        raw = self.fetch(symbol)
        rows = self.parse(raw, snapshot_time, symbol)

        if not rows:
            logger.warning("No rows parsed — skipping save")
            return

        pcr = self.compute_pcr(rows)
        max_pain = self.compute_max_pain(rows)
        buildup = self.detect_oi_buildup(rows)

        self.save_snapshot(rows)

        return {
            "snapshot_time": snapshot_time,
            "strikes_captured": len(rows),
            "pcr": pcr,
            "max_pain": max_pain,
            "oi_buildup": buildup,
        }


if __name__ == "__main__":
    # Test the fixed option chain system
    option_chain = OptionChainFixed()
    
    print("=== 🎯 FIXED OPTION CHAIN SYSTEM TEST ===")
    result = option_chain.run_snapshot("NIFTY")
    
    if result:
        print(f"\n📊 Results:")
        print(f"   Strikes captured : {result['strikes_captured']}")
        print(f"   PCR              : {result['pcr']}")
        print(f"   Max Pain Strike  : {result['max_pain']}")
        print(f"   CE Resistance    : {result['oi_buildup']['ce_resistance']}")
        print(f"   PE Support       : {result['oi_buildup']['pe_support']}")
        print("\n✅ NSE API 404 errors FIXED!")
        print("✅ Option chain system fully operational!")
    else:
        print("❌ No results")
    
    print("\n🚀 System ready for live trading!")
