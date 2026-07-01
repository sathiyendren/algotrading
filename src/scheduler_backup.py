import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import schedule
from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger

from market_hours import is_market_open, is_trading_day
from option_chain_fixed import OptionChainFixed
from nse_scraper_enhanced import EnhancedNSEScraper

IST = ZoneInfo("Asia/Kolkata")

# Configure logging
logger.add(
    "/opt/algotrading/logs/scheduler.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

class AlgoTradingScheduler:
    """Scheduler for algo trading data collection and analysis tasks."""
    
    def __init__(self):
        self.scraper = EnhancedNSEScraper()
        self.option_chain = OptionChainFixed()
        self.running = False
        
        logger.info("🚀 Algo Trading Scheduler initialized")
    
    def collect_option_chain(self):
        """Collect option chain data during market hours."""
        try:
            if not is_market_open():
                logger.info("⏰ Market closed - skipping option chain collection")
                return
            
            logger.info("📊 Starting option chain data collection")
            result = self.option_chain.run_snapshot("NIFTY")
            
            if result:
                logger.info(f"✅ Option chain collected: {result['strikes_captured']} strikes, PCR: {result['pcr']}")
            else:
                logger.warning("⚠️ Option chain collection returned no data")
                
        except Exception as e:
            logger.error(f"❌ Option chain collection failed: {e}")
    
    def collect_banknifty_chain(self):
        """Collect BANKNIFTY option chain data."""
        try:
            if not is_market_open():
                logger.info("⏰ Market closed - skipping BANKNIFTY chain collection")
                return
            
            logger.info("📈 Starting BANKNIFTY option chain collection")
            result = self.option_chain.run_snapshot("BANKNIFTY")
            
            if result:
                logger.info(f"✅ BANKNIFTY chain collected: {result['strikes_captured']} strikes, PCR: {result['pcr']}")
            else:
                logger.warning("⚠️ BANKNIFTY chain collection returned no data")
                
        except Exception as e:
            logger.error(f"❌ BANKNIFTY chain collection failed: {e}")
    
    def market_open_routine(self):
        """Tasks to run at market open."""
        try:
            logger.info("🌅 Market open routine started")
            
            # Initialize scraper session
            self.scraper._init_session()
            logger.info("✅ Scraper session initialized for market open")
            
            # Collect initial option chains
            self.collect_option_chain()
            self.collect_banknifty_chain()
            
            logger.info("✅ Market open routine completed")
            
        except Exception as e:
            logger.error(f"❌ Market open routine failed: {e}")
    
    def market_close_routine(self):
        """Tasks to run at market close."""
        try:
            logger.info("🌇 Market close routine started")
            
            # Final option chain collection
            self.collect_option_chain()
            self.collect_banknifty_chain()
            
            # Clean up scraper session
            if hasattr(self.scraper, 'session') and self.scraper.session:
                self.scraper.session.close()
                logger.info("✅ Scraper session closed")
            
            logger.info("✅ Market close routine completed")
            
        except Exception as e:
            logger.error(f"❌ Market close routine failed: {e}")
    
    def health_check(self):
        """Periodic health check of the scheduler."""
        try:
            now = datetime.now(tz=IST)
            is_open = is_market_open()
            is_trading = is_trading_day()
            
            logger.info(f"🏥 Health check - Time: {now.strftime('%H:%M:%S')}, Market Open: {is_open}, Trading Day: {is_trading}")
            
        except Exception as e:
            logger.error(f"❌ Health check failed: {e}")
    
    def setup_schedule(self):
        """Setup the trading schedule."""
        logger.info("📅 Setting up trading schedule")
        
        # Market open routine (9:15 AM)
        schedule.every().monday.at("09:15").do(self.market_open_routine)
        schedule.every().tuesday.at("09:15").do(self.market_open_routine)
        schedule.every().wednesday.at("09:15").do(self.market_open_routine)
        schedule.every().thursday.at("09:15").do(self.market_open_routine)
        schedule.every().friday.at("09:15").do(self.market_open_routine)
        
        # Health checks (every hour)
        schedule.every().hour.do(self.health_check)
        
        logger.info("✅ Trading schedule setup completed")
    
    def run_continuous_collection(self):
        """Run continuous option chain collection every 15 minutes during market hours."""
        logger.info("🔄 Starting continuous collection mode")
        
        while self.running:
            try:
                if is_market_open():
                    logger.info("📊 Running continuous collection")
                    self.collect_option_chain()
                    self.collect_banknifty_chain()
                else:
                    logger.info("⏰ Market closed - waiting 15 minutes")
                
                # Wait 15 minutes
                for _ in range(15):  # Check every minute if still running
                    if not self.running:
                        break
                    time.sleep(60)
                    
            except KeyboardInterrupt:
                logger.info("⏹️ Continuous collection stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Continuous collection error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def start(self, mode="scheduled"):
        """Start the scheduler."""
        self.running = True
        
        if mode == "scheduled":
            logger.info("🚀 Starting scheduler in scheduled mode")
            self.setup_schedule()
            
            try:
                while self.running:
                    schedule.run_pending()
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("⏹️ Scheduler stopped by user")
                
        elif mode == "continuous":
            logger.info("🚀 Starting scheduler in continuous mode")
            self.run_continuous_collection()
        
        else:
            logger.error(f"❌ Unknown mode: {mode}")
            
        self.running = False
        logger.info("🛑 Scheduler stopped")
    
    def stop(self):
        """Stop the scheduler."""
        logger.info("⏹️ Stopping scheduler...")
        self.running = False
        
        # Clean up scraper session
        if hasattr(self.scraper, 'session') and self.scraper.session:
            self.scraper.session.close()
            logger.info("✅ Scraper session closed")


if __name__ == "__main__":
    # Test the scheduler
    scheduler = AlgoTradingScheduler()
    
    print("=== Algo Trading Scheduler Test ===")
    print(f"Current Time: {datetime.now(tz=IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"Is Market Open: {is_market_open()}")
    print(f"Is Trading Day: {is_trading_day()}")
    print()
    
    # Test individual functions
    print("=== Testing Functions ===")
    try:
        scheduler.health_check()
        print("✅ Health check completed")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print()
    print("=== Scheduler Ready ===")
    print("Usage:")
    print("  python src/scheduler.py  # Test mode")
    print("  Continuous mode: scheduler.start('continuous')")
    print("  Scheduled mode: scheduler.start('scheduled')")
    print()
    print("✅ Scheduler module test completed!")

if __name__ == '__main__':
    import sys
    import os
    
    # Add current directory to Python path for direct execution
    sys.path.insert(0, '/opt/algotrading')
    
    from scheduler import AlgoTradingScheduler
    
    # Get mode from command line argument or default to continuous
    mode = sys.argv[1] if len(sys.argv) > 1 else 'continuous'
    
    scheduler = AlgoTradingScheduler()
    scheduler.start(mode)
