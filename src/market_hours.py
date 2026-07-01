from datetime import time
from zoneinfo import ZoneInfo
from datetime import datetime

IST = ZoneInfo("Asia/Kolkata")

MARKET_OPEN  = time(9, 15)
MARKET_CLOSE = time(15, 30)
WEEKDAYS = {0, 1, 2, 3, 4}  # Mon=0 ... Fri=4


def is_market_open() -> bool:
    now = datetime.now(tz=IST)
    if now.weekday() not in WEEKDAYS:
        return False
    current_time = now.time()
    return MARKET_OPEN <= current_time <= MARKET_CLOSE


def is_trading_day() -> bool:
    return datetime.now(tz=IST).weekday() in WEEKDAYS


if __name__ == "__main__":
    # Test the simplified market hours module
    now = datetime.now(tz=IST)
    print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"Market Open: {MARKET_OPEN}")
    print(f"Market Close: {MARKET_CLOSE}")
    print(f"Is Trading Day: {is_trading_day()}")
    print(f"Is Market Open: {is_market_open()}")
    print("✅ Simplified market hours module working!")
