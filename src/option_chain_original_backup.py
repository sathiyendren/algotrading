import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

from loguru import logger
from dotenv import load_dotenv

from nse_scraper import NSEScraper
from db.session import SessionLocal
from db.models import OptionChainSnapshot
from cache import cache_option_chain, get_cached_chain, cache_pcr, get_cached_pcr, cache_max_pain, get_cached_max_pain

load_dotenv(/opt/algotrading/.env)

logger.add(
    /opt/algotrading/logs/option_chain.log,
    rotation=1 day,
    retention=30 days,
    level=os.getenv(LOG_LEVEL, INFO),
    format={time:YYYY-MM-DD HH:mm:ss}
