import os
from datetime import date, datetime
from datetime import timedelta
from zoneinfo import ZoneInfo

from loguru import logger
from dotenv import load_dotenv

load_dotenv("/opt/algotrading/.env")

logger.add(
    "/opt/algotrading/logs/data_validator.log",
    rotation="1 day",
    retention="30 days",
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

IST = ZoneInfo("Asia/Kolkata")

EXPECTED_CLIENT_TYPES = {"FII", "DII", "CLIENT", "PRO"}
EXPECTED_ENTITY_TYPES = {"FII", "DII"}

# Reasonable bounds for NIFTY OI values
MIN_TOTAL_OI        = 100_000     # below this = clearly wrong
MAX_NET_OI_IMBALANCE = 500_000   # total net OI across all participants
MAX_PCR             = 5.0         # PCR above this = bad parse
MIN_PCR             = 0.1         # PCR below this = bad parse
MIN_STRIKES         = 30          # option chain must have at least 30 strikes
MAX_FII_DAILY_MOVE  = 50_000      # crores — above this = suspect


class ValidationError(Exception):
    pass


# ------------------------------------------------------------------ #
#  Participant OI Validator                                            #
# ------------------------------------------------------------------ #

def validate_participant_oi(records: list[dict]) -> list[str]:
    """
    Returns list of error strings.
    Empty list = data is clean.
    """
    errors = []

    if not records:
        errors.append("CRITICAL: participant OI returned empty list")
        return errors

    found_types = {r["client_type"].upper() for r in records}

    # Check all 4 participant types present
    missing = EXPECTED_CLIENT_TYPES - found_types
    if missing:
        errors.append(f"Missing client types: {missing}")

    for r in records:
        ctype = r["client_type"]

        # No negative OI
        if r["long_contracts"] < 0:
            errors.append(f"{ctype}: negative long_contracts ({r['long_contracts']})")
        if r["short_contracts"] < 0:
            errors.append(f"{ctype}: negative short_contracts ({r['short_contracts']})")

        # No zero OI for FII/DII — they always participate
        if ctype in ("FII", "DII"):
            total = r["long_contracts"] + r["short_contracts"]
            if total < MIN_TOTAL_OI:
                errors.append(
                    f"{ctype}: suspiciously low total OI ({total}) "
                    f"— likely scrape failure or market holiday"
                )

        # Long/short values must be positive if contracts are positive
        if r["long_contracts"] > 0 and r["long_value"] <= 0:
            errors.append(f"{ctype}: has long_contracts but zero long_value")
        if r["short_contracts"] > 0 and r["short_value"] <= 0:
            errors.append(f"{ctype}: has short_contracts but zero short_value")

    # Cross-check: sum of net OI across all participants should be near zero
    # (every long has a short counterparty in the market)
    net_sum = sum(r["long_contracts"] - r["short_contracts"] for r in records)
    if abs(net_sum) > MAX_NET_OI_IMBALANCE:
        errors.append(
            f"Net OI imbalance too large: {net_sum:,} "
            f"(threshold: ±{MAX_NET_OI_IMBALANCE:,}) — possible parse error"
        )

    if errors:
        logger.warning(f"Participant OI validation failed: {errors}")
    else:
        logger.info("Participant OI validation passed ✓")

    return errors


# ------------------------------------------------------------------ #
#  FII/DII Cash Validator                                              #
# ------------------------------------------------------------------ #

def validate_fii_dii_cash(records: list[dict]) -> list[str]:
    errors = []

    if not records:
        errors.append("CRITICAL: FII/DII cash returned empty list")
        return errors

    found_types = {r["entity_type"].upper() for r in records}
    missing = EXPECTED_ENTITY_TYPES - found_types
    if missing:
        errors.append(f"Missing entity types: {missing}")

    for r in records:
        etype = r["entity_type"]

        if r["buy_value"] < 0 or r["sell_value"] < 0:
            errors.append(f"{etype}: negative buy/sell value")

        if r["buy_value"] == 0 and r["sell_value"] == 0:
            errors.append(f"{etype}: both buy and sell are zero — likely scrape failure")

        net = abs(r["buy_value"] - r["sell_value"])
        if net > MAX_FII_DAILY_MOVE:
            errors.append(
                f"{etype}: net move {net:,.0f} crores exceeds threshold "
                f"{MAX_FII_DAILY_MOVE:,} — verify manually"
            )

    if errors:
        logger.warning(f"FII/DII cash validation failed: {errors}")
    else:
        logger.info("FII/DII cash validation passed ✓")

    return errors


# ------------------------------------------------------------------ #
#  Option Chain Validator                                              #
# ------------------------------------------------------------------ #

def validate_option_chain(rows: list[dict]) -> list[str]:
    errors = []

    if not rows:
        errors.append("CRITICAL: option chain returned empty list")
        return errors

    # Must have enough strikes
    if len(rows) < MIN_STRIKES:
        errors.append(
            f"Too few strikes: {len(rows)} "
            f"(minimum {MIN_STRIKES}) — likely partial scrape"
        )

    total_ce = sum(r["ce_oi"] for r in rows)
    total_pe = sum(r["pe_oi"] for r in rows)

    # Both sides must have OI
    if total_ce == 0:
        errors.append("Total CE OI is zero — bad parse")
    if total_pe == 0:
        errors.append("Total PE OI is zero — bad parse")

    # PCR sanity
    if total_ce > 0:
        pcr = total_pe / total_ce
        if pcr > MAX_PCR:
            errors.append(f"PCR {pcr:.2f} exceeds max {MAX_PCR} — suspect data")
        if pcr < MIN_PCR:
            errors.append(f"PCR {pcr:.2f} below min {MIN_PCR} — suspect data")

    # No negative OI
    neg_ce = [r["strike"] for r in rows if r["ce_oi"] < 0]
    neg_pe = [r["strike"] for r in rows if r["pe_oi"] < 0]
    if neg_ce:
        errors.append(f"Negative CE OI at strikes: {neg_ce[:5]}")
    if neg_pe:
        errors.append(f"Negative PE OI at strikes: {neg_pe[:5]}")

    # Expiry date must be in the future
    expiry_dates = {r["expiry"] for r in rows}
    today = date.today()
    past_expiries = [str(e) for e in expiry_dates if e < today]
    if past_expiries:
        errors.append(f"Stale expiry dates in chain: {past_expiries} — data from wrong day?")

    if errors:
        logger.warning(f"Option chain validation failed: {errors}")
    else:
        logger.info(f"Option chain validation passed ✓ ({len(rows)} strikes)")

    return errors


# ------------------------------------------------------------------ #
#  Redis Cache Integration                                            #
# ------------------------------------------------------------------ #

def validate_cached_data() -> dict:
    """Validate data cached in Redis and return comprehensive results"""
    from cache import get_cached_chain, get_cached_pcr, get_cached_max_pain, get_cached_participant_oi
    
    results = {
        'option_chain': {'status': 'not_cached', 'errors': [], 'warnings': []},
        'participant_oi': {'status': 'not_cached', 'errors': [], 'warnings': []},
        'cache_health': {'status': 'unknown', 'errors': [], 'warnings': []}
    }
    
    try:
        # Validate cached option chain
        cached_chain = get_cached_chain('NIFTY')
        if cached_chain:
            chain_errors = validate_option_chain(cached_chain)
            results['option_chain']['status'] = 'valid' if not chain_errors else 'invalid'
            results['option_chain']['errors'] = chain_errors
            results['option_chain']['data_points'] = len(cached_chain)
        else:
            results['option_chain']['warnings'].append('No cached option chain data found')
        
        # Validate cached participant OI
        cached_oi = get_cached_participant_oi()
        if cached_oi:
            oi_errors = validate_participant_oi(cached_oi)
            results['participant_oi']['status'] = 'valid' if not oi_errors else 'invalid'
            results['participant_oi']['errors'] = oi_errors
            results['participant_oi']['data_points'] = len(cached_oi)
        else:
            results['participant_oi']['warnings'].append('No cached participant OI data found')
        
        # Check cache health
        from cache import cache_health
        health = cache_health()
        if health.get('status') == 'ok':
            results['cache_health']['status'] = 'healthy'
            results['cache_health']['memory_usage'] = health.get('used_memory_human', 'Unknown')
        else:
            results['cache_health']['status'] = 'unhealthy'
            results['cache_health']['errors'].append(f'Cache health check failed: {health}')
        
        # Overall validation status
        all_valid = all(
            results[key]['status'] in ['valid', 'healthy'] 
            for key in ['option_chain', 'participant_oi', 'cache_health']
        )
        results['overall_status'] = 'valid' if all_valid else 'invalid'
        
    except Exception as e:
        logger.error(f"Cache validation error: {e}")
        results['overall_status'] = 'error'
        results['error'] = str(e)
    
    return results


# ------------------------------------------------------------------ #
#  Master validator — raises on critical errors                        #
# ------------------------------------------------------------------ #

def validate_and_gate(
    data: list[dict],
    data_type: str,
    raise_on_error: bool = True,
) -> bool:
    """
    Validate data and optionally raise if errors found.
    Returns True if clean, False if errors (when raise_on_error=False).
    """
    validators = {
        "participant_oi": validate_participant_oi,
        "fii_dii_cash":   validate_fii_dii_cash,
        "option_chain":   validate_option_chain,
    }

    if data_type not in validators:
        raise ValueError(f"Unknown data_type: {data_type}")

    errors = validators[data_type](data)

    if errors:
        msg = f"[{data_type}] Validation failed ({len(errors)} errors): {errors}"
        logger.critical(msg)
        if raise_on_error:
            raise ValidationError(msg)
        return False

    return True


# ------------------------------------------------------------------ #
#  Validation Summary and Reporting                                   #
# ------------------------------------------------------------------ #

def print_validation_summary(results: dict) -> None:
    """Print a formatted validation summary"""
    print("\n🔍 Data Validation Summary")
    print("=" * 50)
    
    for data_type, result in results.items():
        if data_type == 'overall_status':
            continue
            
        status_icon = "✅" if result['status'] in ['valid', 'healthy'] else "❌"
        print(f"\n{data_type.replace('_', ' ').title()}: {status_icon} {result['status'].upper()}")
        
        if result.get('data_points'):
            print(f"  Data points: {result['data_points']}")
        
        if result.get('memory_usage'):
            print(f"  Memory usage: {result['memory_usage']}")
        
        if result['errors']:
            print("  Errors:")
            for error in result['errors']:
                print(f"    - {error}")
        
        if result['warnings']:
            print("  Warnings:")
            for warning in result['warnings']:
                print(f"    - {warning}")
    
    overall_icon = "✅" if results.get('overall_status') == 'valid' else "❌"
    print(f"\n🎯 Overall Status: {overall_icon} {results.get('overall_status', 'unknown').upper()}")


if __name__ == "__main__":
    # Test the enhanced data validator
    logger.info("Testing Enhanced Data Validator with Redis Integration...")
    
    # Validate cached data
    results = validate_cached_data()
    print_validation_summary(results)
    
    # Test with sample data if cache is empty
    if results.get('overall_status') in ['invalid', 'error']:
        print("\n🔄 Testing with sample data...")
        
        # Sample option chain data
        sample_chain = [
            {'symbol': 'NIFTY', 'strike': 19500, 'ce_oi': 1000000, 'pe_oi': 1200000, 'expiry': date.today() + timedelta(days=7)},
            {'symbol': 'NIFTY', 'strike': 19600, 'ce_oi': 800000, 'pe_oi': 900000, 'expiry': date.today() + timedelta(days=7)},
        ]
        
        print(f"Sample option chain validation: {validate_option_chain(sample_chain)}")
    
    logger.info("Enhanced data validation test completed")
