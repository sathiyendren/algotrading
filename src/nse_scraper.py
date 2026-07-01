import time
import json
import os
from datetime import datetime, date
from pathlib import Path

import requests
from loguru import logger
from dotenv import load_dotenv

load_dotenv("/opt/algotrading/.env")

# Configure loguru — write to file + console
logger.add(
    "/opt/algotrading/logs/nse_scraper.log",
    rotation="1 day",
    retention="30 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

DATA_DIR = Path("/opt/algotrading/data")
DATA_DIR.mkdir(exist_ok=True)


class NSEScraper:

    BASE = "https://www.nseindia.com"
    SESSION_TTL = 45 * 60  # refresh cookies every 45 minutes

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(NSE_HEADERS)
        self._session_created_at = 0
        self._init_session()

    def _init_session(self):
        """Hit NSE homepage to get valid session cookies."""
        try:
            logger.info("Initializing NSE session (fetching homepage cookies)")
            resp = self.session.get(f"{self.BASE}/", timeout=15)
            resp.raise_for_status()
            self._session_created_at = time.time()
            logger.info(f"Session initialized. Cookies: {list(self.session.cookies.keys())}")
        except Exception as e:
            logger.error(f"Failed to initialize NSE session: {e}")
            raise

    def _ensure_fresh_session(self):
        """Refresh session if older than SESSION_TTL."""
        age = time.time() - self._session_created_at
        if age > self.SESSION_TTL:
            logger.info(f"Session is {age/60:.1f} min old — refreshing")
            self._init_session()

    def _get(self, endpoint: str, retries: int = 3) -> dict:
        """GET request with retry logic and raw response backup."""
        self._ensure_fresh_session()
        url = f"{self.BASE}{endpoint}"

        for attempt in range(1, retries + 1):
            try:
                logger.debug(f"GET {endpoint} (attempt {attempt})")
                resp = self.session.get(url, timeout=15)
                resp.raise_for_status()

                data = resp.json()
                self._save_raw(endpoint, data)
                return data

            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP {e.response.status_code} on {endpoint} — attempt {attempt}")
                if e.response.status_code in (401, 403):
                    # Cookie expired mid-session — force refresh
                    logger.warning("Possible cookie expiry — reinitializing session")
                    self._init_session()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on {endpoint} — attempt {attempt}")
            except Exception as e:
                logger.error(f"Unexpected error on {endpoint}: {e}")

            if attempt < retries:
                wait = 5 * attempt  # 5s, 10s backoff
                logger.info(f"Retrying in {wait}s...")
                time.sleep(wait)

        raise RuntimeError(f"All {retries} attempts failed for {endpoint}")

    def _save_raw(self, endpoint: str, data: dict):
        """Save raw JSON response to disk for debugging."""
        safe_name = endpoint.strip("/").replace("/", "_")
        filename = DATA_DIR / f"{safe_name}_{date.today()}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    # ------------------------------------------------------------------ #
    #  Public methods                                                       #
    # ------------------------------------------------------------------ #

    def get_participant_oi(self) -> list[dict]:
        """
        Fetch participant-wise OI data from NSE.
        Returns list of dicts with keys:
          client_type, long_contracts, short_contracts, long_value, short_value
        """
        raw = self._get("/api/participant-wise-trading-data")
        return self._parse_participant_oi(raw)

    def _parse_participant_oi(self, raw: dict) -> list[dict]:
        records = []

        # NSE returns a dict with keys like 'FII', 'DII', 'Client', 'Pro'
        # Structure varies slightly — handle both known formats
        try:
            data = raw.get("data", raw)  # some endpoints nest under 'data'

            for entry in data:
                client_type = (
                    entry.get("clientType") or
                    entry.get("client_type") or
                    entry.get("participant_type", "UNKNOWN")
                ).upper().strip()

                records.append({
                    "trade_date": date.today(),
                    "client_type": client_type,
                    "long_contracts": int(entry.get("futLongOI") or entry.get("long_contracts") or 0),
                    "short_contracts": int(entry.get("futShortOI") or entry.get("short_contracts") or 0),
                    "long_value": float(entry.get("futLongAmt") or entry.get("long_value") or 0),
                    "short_value": float(entry.get("futShortAmt") or entry.get("short_value") or 0),
                })

            logger.info(f"Parsed {len(records)} participant OI records")
            return records

        except Exception as e:
            logger.error(f"Failed to parse participant OI: {e} | raw keys: {list(raw.keys())}")
            raise

    def get_fii_dii_cash(self) -> list[dict]:
        """
        Fetch FII/DII cash market buy/sell data.
        Returns list of dicts with keys:
          entity_type, buy_value, sell_value
        """
        raw = self._get("/api/fiidiiTradeReact")
        return self._parse_fii_dii(raw)

    def _parse_fii_dii(self, raw: dict) -> list[dict]:
        records = []
        try:
            # NSE returns list — first entry is usually latest date
            data = raw if isinstance(raw, list) else raw.get("data", [])

            # Take only today's entry (index 0 = most recent)
            latest = data[0] if data else {}

            for entity in ("FII", "DII"):
                key = entity.lower()
                records.append({
                    "trade_date": date.today(),
                    "entity_type": entity,
                    "buy_value": float(latest.get(f"{key}BuyValue") or 0),
                    "sell_value": float(latest.get(f"{key}SellValue") or 0),
                })

            logger.info(f"Parsed FII/DII cash records: {records}")
            return records

        except Exception as e:
            logger.error(f"Failed to parse FII/DII cash: {e}")
            raise


if __name__ == "__main__":
    # Test the scraper
    try:
        scraper = NSEScraper()
        logger.info("✅ NSE scraper initialized successfully")
        
        # Test participant OI
        participant_data = scraper.get_participant_oi()
        logger.info(f"📊 Participant OI records: {len(participant_data)}")
        
        # Test FII/DII cash
        fii_dii_data = scraper.get_fii_dii_cash()
        logger.info(f"💰 FII/DII cash records: {len(fii_dii_data)}")
        
        logger.info("✅ NSE scraper tests completed")
        
    except Exception as e:
        logger.error(f"❌ NSE scraper test failed: {e}")
