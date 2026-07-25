#!/usr/bin/env python3
"""
FII Algo Trading System - Main Entry Point
Professional FII algo trading architecture with signal generation, risk management, and execution
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fii_algo.config.settings import TradingConfig
from fii_algo.data.nse_scraper import NSEDataCollector
from fii_algo.data.option_chain import OptionChainData
from fii_algo.signal.signal_engine import SignalEngine
from fii_algo.signal.fii_scorer import FIIScorer
from fii_algo.risk.risk_manager import RiskManager
from fii_algo.execution.order_executor import OrderExecutor
from fii_algo.monitoring.position_monitor import PositionMonitor
from fii_algo.alerts.telegram_bot import telegram_bot
from fii_algo.api.fastapi_server import server
from fii_algo.scheduler.scheduler import TradingScheduler

# Configure logging
logging.basicConfig(
    level=getattr(logging, TradingConfig.LOG_LEVEL),
    format=TradingConfig.LOG_FORMAT,
    handlers=[
        logging.FileHandler('fii_algo/logs/trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FIIAlgoTradingSystem:
    """Main FII algo trading system orchestrator."""
    
    def __init__(self):
        self.running = False
        self.scheduler = None
        
        # Initialize components
        self.data_collector = NSEDataCollector()
        self.option_chain = OptionChainData()
        self.fii_scorer = FIIScorer()
        self.signal_engine = SignalEngine()
        self.risk_manager = RiskManager()
        self.order_executor = OrderExecutor()
        self.position_monitor = PositionMonitor()
        
        logger.info("🚀 FII Algo Trading System initialized")
    
    async def start(self):
        """Start the trading system."""
        if self.running:
            logger.warning("System is already running")
            return
        
        logger.info("🎯 Starting FII Algo Trading System...")
        self.running = True
        
        try:
            # Start scheduler
            self.scheduler = TradingScheduler()
            await self.scheduler.start()
            
            # Start Telegram bot
            await telegram_bot.start_bot()
            
            # Start API server (in background)
            api_task = asyncio.create_task(self._start_api_server())
            
            logger.info("✅ All components started successfully")
            logger.info("📊 System is ready for trading")
            
            # Keep the system running
            await self._run_main_loop()
            
        except Exception as e:
            logger.error(f"❌ Error starting system: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the trading system."""
        if not self.running:
            return
        
        logger.info("🛑 Stopping FII Algo Trading System...")
        self.running = False
        
        try:
            # Stop scheduler
            if self.scheduler:
                await self.scheduler.stop()
            
            # Stop Telegram bot
            await telegram_bot.stop_bot()
            
            logger.info("✅ System stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")
    
    async def _start_api_server(self):
        """Start FastAPI server in background."""
        try:
            logger.info(f"🌐 Starting API server on {TradingConfig.API_HOST}:{TradingConfig.API_PORT}")
            server.run()
        except Exception as e:
            logger.error(f"❌ Error starting API server: {e}")
    
    async def _run_main_loop(self):
        """Main system loop."""
        try:
            while self.running:
                await asyncio.sleep(60)  # Check every minute
                
                # Log system status
                if datetime.now().minute % 30 == 0:  # Every 30 minutes
                    await self._log_system_status()
                
        except asyncio.CancelledError:
            logger.info("Main loop cancelled")
        except Exception as e:
            logger.error(f"❌ Error in main loop: {e}")
    
    async def _log_system_status(self):
        """Log system status."""
        try:
            active_positions = await self.position_monitor.get_active_positions_count()
            daily_pnl = await self.position_monitor.get_daily_pnl()
            
            logger.info(f"📊 System Status | Positions: {active_positions} | Daily P&L: ₹{daily_pnl:.2f}")
            
        except Exception as e:
            logger.error(f"Error logging system status: {e}")

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"📡 Received signal {signum}, initiating shutdown...")
    asyncio.create_task(system.stop())

async def main():
    """Main entry point."""
    global system
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start system
    system = FIIAlgoTradingSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("👋 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        if system.running:
            await system.stop()

if __name__ == "__main__":
    # Print startup banner
    print("""    
    ╔══════════════════════════════════════════════════════════════╗
    ║         FII Algo Trading System v1.0                        ║
    ║                                                              ║
    ║  Professional FII algo trading with:                        ║
    ║  • Real-time data collection                                ║
    ║  • Advanced signal generation                               ║
    ║  • Risk management                                          ║
    ║  • Automated execution                                      ║
    ║  • Telegram alerts                                          ║
    ║  • Web dashboard                                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run the system
    asyncio.run(main())
