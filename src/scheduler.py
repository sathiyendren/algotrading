#!/usr/bin/env python3
"""
Enhanced Algo Trading Scheduler with Holiday Support
Continuous option chain data collection with intelligent scheduling
"""

import time
import logging
import datetime
import os
import sys
from typing import Optional, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from market_hours_enhanced import market_detector, is_market_open, get_market_status, get_time_until_market_open
from nse_scraper_working import FixedNSEScraper
from option_chain_fixed import OptionChainFixed
from db_writer import upsert_option_chain_snapshot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class AlgoTradingScheduler:
    """Enhanced scheduler with holiday-aware market hours detection"""
    
    def __init__(self):
        self.scraper = FixedNSEScraper()
        self.option_chain = OptionChainFixed()
        self.running = True
        self.collection_stats = {
            'total_collections': 0,
            'successful_collections': 0,
            'failed_collections': 0,
            'last_collection': None,
            'last_success': None,
            'last_failure': None,
            'consecutive_failures': 0
        }
        
        logger.info("🚀 Enhanced Algo Trading Scheduler initialized with holiday support")
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check with holiday information"""
        current_time = datetime.datetime.now()
        market_info = market_detector.get_trading_session_info(current_time)
        
        return {
            'timestamp': current_time,
            'status': 'healthy' if self.running else 'stopped',
            'market_status': market_info['market_status'],
            'is_trading_day': market_info['is_trading_day'],
            'is_market_open': market_info['is_market_open'],
            'time_until_open': market_info['time_until_open'],
            'next_trading_day': market_info['next_trading_day'],
            'collection_stats': self.collection_stats.copy(),
            'upcoming_holidays': market_info['upcoming_holidays'][:3]
        }
    
    def collect_nifty_chain(self) -> bool:
        """Collect NIFTY option chain data"""
        try:
            logger.info("🔍 Collecting NIFTY option chain...")
            
            # Get option chain data
            data = self.scraper.get_option_chain('NIFTY')
            if not data:
                logger.warning("⚠️ No NIFTY data received")
                return False
            
            # Process analytics
            snapshot_time = datetime.datetime.now()
            rows = self.option_chain.parse(data, snapshot_time, 'NIFTY')
            
            if not rows:
                logger.warning("⚠️ No NIFTY data parsed")
                return False
            
            # Save to database
            success = upsert_option_chain_snapshot(rows)
            
            if success:
                pcr = self.option_chain.compute_pcr(rows)
                logger.info(f"✅ NIFTY chain collected: {len(rows)} strikes, PCR: {pcr:.4f}")
                return True
            else:
                logger.error("❌ Failed to save NIFTY chain to database")
                return False
                
        except Exception as e:
            logger.error(f"❌ NIFTY chain collection failed: {str(e)}")
            return False
    
    def collect_banknifty_chain(self) -> bool:
        """Collect BANKNIFTY option chain data"""
        try:
            logger.info("🔍 Collecting BANKNIFTY option chain...")
            
            # Get option chain data
            data = self.scraper.get_option_chain('BANKNIFTY')
            if not data:
                logger.warning("⚠️ No BANKNIFTY data received")
                return False
            
            # Process analytics
            snapshot_time = datetime.datetime.now()
            rows = self.option_chain.parse(data, snapshot_time, 'BANKNIFTY')
            
            if not rows:
                logger.warning("⚠️ No BANKNIFTY data parsed")
                return False
            
            # Save to database
            success = upsert_option_chain_snapshot(rows)
            
            if success:
                pcr = self.option_chain.compute_pcr(rows)
                logger.info(f"✅ BANKNIFTY chain collected: {len(rows)} strikes, PCR: {pcr:.4f}")
                return True
            else:
                logger.error("❌ Failed to save BANKNIFTY chain to database")
                return False
                
        except Exception as e:
            logger.error(f"❌ BANKNIFTY chain collection failed: {str(e)}")
            return False
    
    def collect_both_chains(self) -> bool:
        """Collect both NIFTY and BANKNIFTY option chains"""
        nifty_success = self.collect_nifty_chain()
        banknifty_success = self.collect_banknifty_chain()
        
        return nifty_success or banknifty_success  # Success if at least one works
    
    def update_stats(self, success: bool):
        """Update collection statistics"""
        self.collection_stats['total_collections'] += 1
        self.collection_stats['last_collection'] = datetime.datetime.now()
        
        if success:
            self.collection_stats['successful_collections'] += 1
            self.collection_stats['last_success'] = datetime.datetime.now()
            self.collection_stats['consecutive_failures'] = 0
        else:
            self.collection_stats['failed_collections'] += 1
            self.collection_stats['last_failure'] = datetime.datetime.now()
            self.collection_stats['consecutive_failures'] += 1
    
    def run_continuous_collection(self):
        """Run continuous data collection with holiday-aware scheduling"""
        logger.info("🔄 Starting continuous option chain collection with holiday support")
        
        while self.running:
            try:
                current_time = datetime.datetime.now()
                market_status = get_market_status(current_time)
                
                # Log current status
                logger.info(f"🏥 Health check - Time: {current_time.strftime('%H:%M:%S')}, Market Status: {market_status}")
                
                if is_market_open(current_time):
                    # Market is open - collect data
                    logger.info("📈 Market is open - collecting option chain data")
                    
                    success = self.collect_both_chains()
                    self.update_stats(success)
                    
                    if success:
                        # Wait 30 seconds between collections during market hours
                        sleep_time = 30
                        logger.info(f"⏰ Waiting {sleep_time} seconds until next collection")
                    else:
                        # Wait 60 seconds after failure
                        sleep_time = 60
                        logger.warning(f"⚠️ Collection failed, waiting {sleep_time} seconds before retry")
                        
                        # Check for consecutive failures
                        if self.collection_stats['consecutive_failures'] >= 5:
                            logger.error(f"🚨 {self.collection_stats['consecutive_failures']} consecutive failures - extending wait time")
                            sleep_time = 300  # 5 minutes
                    
                else:
                    # Market is closed - check why and wait appropriately
                    time_until_open, message = get_time_until_market_open(current_time)
                    
                    if "Weekend" in market_status or "Holiday" in market_status:
                        logger.info(f"🏖️ {market_status} - {message}")
                        
                        # For weekends and holidays, wait longer
                        if time_until_open > 1440:  # More than a day
                            sleep_time = 3600  # Check every hour
                        else:
                            sleep_time = 900  # Check every 15 minutes
                    else:
                        logger.info(f"⏰ Market closed - {message}")
                        
                        # For regular market closure, check every 15 minutes
                        sleep_time = 900
                    
                    logger.info(f"💤 Sleeping for {sleep_time} seconds ({sleep_time//60} minutes)")
                    
                    # Log upcoming holidays periodically
                    if current_time.minute % 30 == 0:  # Every 30 minutes
                        upcoming = market_detector.get_upcoming_holidays(7)
                        if upcoming:
                            logger.info("📅 Upcoming holidays:")
                            for holiday in upcoming[:3]:
                                logger.info(f"   {holiday['date']}: {holiday['name']}")
                
                # Sleep until next check
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("🛑 Received keyboard interrupt - stopping scheduler")
                break
            except Exception as e:
                logger.error(f"💥 Unexpected error in main loop: {str(e)}")
                logger.info("⏰ Waiting 60 seconds before continuing")
                time.sleep(60)
        
        logger.info("🏁 Scheduler stopped")
    
    def print_status(self):
        """Print current scheduler status"""
        health = self.health_check()
        
        print("\n" + "="*60)
        print("🚀 ENHANCED ALGO TRADING SCHEDULER STATUS")
        print("="*60)
        print(f"📅 Current Time: {health['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Market Status: {health['market_status']}")
        print(f"🏪 Is Trading Day: {'Yes' if health['is_trading_day'] else 'No'}")
        print(f"📈 Is Market Open: {'Yes' if health['is_market_open'] else 'No'}")
        print(f"⏰ Time Until Open: {health['time_until_open'][1]}")
        print(f"📆 Next Trading Day: {health['next_trading_day']}")
        
        print("\n📈 Collection Statistics:")
        print(f"   Total Collections: {health['collection_stats']['total_collections']}")
        print(f"   Successful: {health['collection_stats']['successful_collections']}")
        print(f"   Failed: {health['collection_stats']['failed_collections']}")
        success_rate = (health['collection_stats']['successful_collections'] / max(1, health['collection_stats']['total_collections']) * 100)
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if health['upcoming_holidays']:
            print("\n📅 Upcoming Holidays:")
            for holiday in health['upcoming_holidays']:
                print(f"   {holiday['date']}: {holiday['name']}")
        
        print("="*60)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Algo Trading Scheduler with Holiday Support')
    parser.add_argument('command', choices=['continuous', 'status', 'health', 'test'], 
                       help='Command to run')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    scheduler = AlgoTradingScheduler()
    
    if args.command == 'continuous':
        scheduler.run_continuous_collection()
    elif args.command == 'status':
        scheduler.print_status()
    elif args.command == 'health':
        health = scheduler.health_check()
        print(f"Status: {health['status']}")
        print(f"Market: {health['market_status']}")
        print(f"Trading Day: {health['is_trading_day']}")
        print(f"Market Open: {health['is_market_open']}")
    elif args.command == 'test':
        # Test market hours detection
        current_time = datetime.datetime.now()
        print(f"Current Time: {current_time}")
        print(f"Market Status: {get_market_status(current_time)}")
        print(f"Is Trading Day: {market_detector.is_trading_day(current_time.date())}")
        print(f"Is Market Open: {is_market_open(current_time)}")
        
        # Test upcoming holidays
        upcoming = market_detector.get_upcoming_holidays(30)
        print(f"\nUpcoming Holidays (next 30 days): {len(upcoming)}")
        for holiday in upcoming[:5]:
            print(f"  {holiday['date']}: {holiday['name']} ({holiday['type']})")

if __name__ == "__main__":
    main()
