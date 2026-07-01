# Author: sathiyendren
# Email: sathiyendren@gmail.com
# Created: 2026-07-01 01:55:20
# Description: Redis-based caching system for market data and trading signals
# Project: Algo Trading System

import json
import os
from datetime import timedelta, date
from typing import Dict, Any, Optional, List

import redis
from loguru import logger
from dotenv import load_dotenv

load_dotenv("/opt/algotrading/.env")

# Redis connection
r = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

class MarketDataCache:
    def __init__(self, redis_url: str = None):
        if redis_url:
            self.r = redis.from_url(redis_url)
        else:
            self.r = r
            
        try:
            self.r.ping()
            logger.info("Redis cache initialized successfully")
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise
    
    def cache_option_chain(self, symbol: str, data: list):
        key = f"option_chain:{symbol}"
        self.r.setex(key, timedelta(minutes=5), json.dumps(data))
        logger.debug(f"Cached option chain for {symbol} — {len(data)} strikes, TTL=5min")

    def get_cached_chain(self, symbol: str) -> list | None:
        raw = self.r.get(f"option_chain:{symbol}")
        if raw:
            logger.debug(f"Cache HIT — option_chain:{symbol}")
            return json.loads(raw)
        logger.debug(f"Cache MISS — option_chain:{symbol}")
        return None
    
    def cache_participant_oi(self, data: list):
        key = f"participant_oi:{date.today()}"
        self.r.setex(key, timedelta(hours=24), json.dumps(data))
        logger.debug(f"Cached participant OI for {date.today()}")

    def get_cached_participant_oi(self) -> list | None:
        key = f"participant_oi:{date.today()}"
        raw = self.r.get(key)
        if raw:
            logger.debug("Cache HIT — participant_oi")
            return json.loads(raw)
        logger.debug("Cache MISS — participant_oi")
        return None
    
    def cache_pcr(self, symbol: str, pcr: float):
        key = f"pcr:{symbol}"
        self.r.setex(key, timedelta(minutes=5), str(pcr))
        logger.debug(f"Cached PCR for {symbol}: {pcr}")

    def get_cached_pcr(self, symbol: str) -> float | None:
        raw = self.r.get(f"pcr:{symbol}")
        return float(raw) if raw else None
    
    def cache_max_pain(self, symbol: str, strike: float):
        key = f"max_pain:{symbol}:{date.today()}"
        self.r.setex(key, timedelta(hours=1), str(strike))
        logger.debug(f"Cached max pain for {symbol}: {strike}")

    def get_cached_max_pain(self, symbol: str) -> float | None:
        key = f"max_pain:{symbol}:{date.today()}"
        raw = self.r.get(key)
        return float(raw) if raw else None
    
    def cache_market_data(self, symbol: str, data: Dict[str, Any], ttl: int = 300):
        key = f"market_data:{symbol}"
        self.r.setex(key, timedelta(seconds=ttl), json.dumps(data))
        logger.debug(f"Cached market data for {symbol}, TTL={ttl}s")

    def get_market_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        raw = self.r.get(f"market_data:{symbol}")
        if raw:
            logger.debug(f"Cache HIT — market_data:{symbol}")
            return json.loads(raw)
        logger.debug(f"Cache MISS — market_data:{symbol}")
        return None
    
    def cache_trading_signal(self, strategy: str, symbol: str, signal: Dict[str, Any], ttl: int = 60):
        key = f"signal:{strategy}:{symbol}"
        self.r.setex(key, timedelta(seconds=ttl), json.dumps(signal))
        logger.debug(f"Cached trading signal for {strategy}/{symbol}, TTL={ttl}s")

    def get_trading_signal(self, strategy: str, symbol: str) -> Optional[Dict[str, Any]]:
        raw = self.r.get(f"signal:{strategy}:{symbol}")
        if raw:
            logger.debug(f"Cache HIT — signal:{strategy}:{symbol}")
            return json.loads(raw)
        logger.debug(f"Cache MISS — signal:{strategy}:{symbol}")
        return None
    
    def invalidate(self, pattern: str):
        keys = self.r.keys(pattern)
        if keys:
            self.r.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching '{pattern}'")

    def cache_health(self) -> dict:
        try:
            self.r.ping()
            info = self.r.info("memory")
            return {
                "status": "ok",
                "used_memory_human": info["used_memory_human"],
                "connected_clients": self.r.info("clients")["connected_clients"],
            }
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            return {"status": "error", "detail": str(e)}

# Global cache instance
_cache_instance = None

def get_cache() -> MarketDataCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = MarketDataCache()
    return _cache_instance

# Export functions for direct use
cache_option_chain = get_cache().cache_option_chain
get_cached_chain = get_cache().get_cached_chain
cache_participant_oi = get_cache().cache_participant_oi
get_cached_participant_oi = get_cache().get_cached_participant_oi
cache_pcr = get_cache().cache_pcr
get_cached_pcr = get_cache().get_cached_pcr
cache_max_pain = get_cache().cache_max_pain
get_cached_max_pain = get_cache().get_cached_max_pain
invalidate = get_cache().invalidate
cache_health = get_cache().cache_health

if __name__ == '__main__':
    cache = MarketDataCache()
    health = cache.cache_health()
    print(f"Cache health: {health}")

# Convenience functions for backward compatibility
def cache_market_data(symbol: str, data: Dict[str, Any], ttl: int = 300):
    return get_cache().cache_market_data(symbol, data, ttl)

def get_market_data(symbol: str) -> Optional[Dict[str, Any]]:
    return get_cache().get_market_data(symbol)

def cache_trading_signal(strategy: str, symbol: str, signal: Dict[str, Any], ttl: int = 60):
    return get_cache().cache_trading_signal(strategy, symbol, signal, ttl)

def get_trading_signal(strategy: str, symbol: str) -> Optional[Dict[str, Any]]:
    return get_cache().get_trading_signal(strategy, symbol)
