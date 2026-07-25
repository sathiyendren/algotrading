"""
FastAPI Server for FII Algo Trading System
REST API for dashboard and external integrations
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, date
import asyncio
import uvicorn

from ..config.settings import TradingConfig
from ..signal.signal_engine import SignalEngine
from ..risk.risk_manager import RiskManager
from ..execution.order_executor import OrderExecutor
from ..monitoring.position_monitor import PositionMonitor

class FastAPIServer:
    """FastAPI server for FII algo trading system."""
    
    def __init__(self):
        self.app = FastAPI(
            title="FII Algo Trading API",
            description="REST API for FII algo trading system",
            version="1.0.0"
        )
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Initialize components
        self.signal_engine = SignalEngine()
        self.risk_manager = RiskManager()
        self.order_executor = OrderExecutor()
        self.position_monitor = PositionMonitor()
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "FII Algo Trading API",
                "version": "1.0.0",
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/health")
        async def health_check():
            """System health check."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "signal_engine": "running",
                    "risk_manager": "running",
                    "order_executor": "running",
                    "position_monitor": "running"
                }
            }
        
        @self.app.get("/status")
        async def get_status():
            """Get system status."""
            return {
                "market_status": "open" if self._is_market_open() else "closed",
                "active_positions": await self.position_monitor.get_active_positions_count(),
                "daily_pnl": await self.position_monitor.get_daily_pnl(),
                "last_signal": await self.signal_engine.get_last_signal(),
                "risk_level": await self.risk_manager.get_current_risk_level(),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/signals")
        async def get_signals(limit: int = 10):
            """Get recent trading signals."""
            signals = await self.signal_engine.get_recent_signals(limit)
            return {
                "signals": signals,
                "count": len(signals),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/signals/generate")
        async def generate_signal(background_tasks: BackgroundTasks):
            """Generate new trading signal."""
            try:
                # Generate signal in background
                background_tasks.add_task(self._generate_and_process_signal)
                return {
                    "message": "Signal generation started",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/positions")
        async def get_positions():
            """Get current positions."""
            positions = await self.position_monitor.get_all_positions()
            return {
                "positions": positions,
                "count": len(positions),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/positions/{position_id}")
        async def get_position(position_id: str):
            """Get specific position details."""
            position = await self.position_monitor.get_position(position_id)
            if not position:
                raise HTTPException(status_code=404, detail="Position not found")
            return position
        
        @self.app.post("/positions/{position_id}/close")
        async def close_position(position_id: str, background_tasks: BackgroundTasks):
            """Close a position."""
            try:
                background_tasks.add_task(self._close_position, position_id)
                return {
                    "message": f"Position {position_id} closure initiated",
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/pnl")
        async def get_pnl():
            """Get P&L information."""
            pnl_data = await self.position_monitor.get_pnl_summary()
            return {
                **pnl_data,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/risk")
        async def get_risk_metrics():
            """Get risk metrics."""
            risk_metrics = await self.risk_manager.get_risk_metrics()
            return {
                **risk_metrics,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/market-data")
        async def get_market_data():
            """Get current market data."""
            # This would integrate with your data collection modules
            return {
                "nifty": {
                    "price": 19850.50,
                    "change": 158.90,
                    "change_percent": 0.81
                },
                "banknifty": {
                    "price": 44250.30,
                    "change": 523.70,
                    "change_percent": 1.20
                },
                "vix": 16.8,
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.get("/performance")
        async def get_performance():
            """Get performance metrics."""
            performance = await self.position_monitor.get_performance_metrics()
            return {
                **performance,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _generate_and_process_signal(self):
        """Generate and process trading signal."""
        try:
            # Generate signal
            signal = await self.signal_engine.generate_signal()
            
            if signal:
                # Risk check
                risk_check = await self.risk_manager.evaluate_signal(signal)
                
                if risk_check['approved']:
                    # Execute strategy
                    strategy = await self.order_executor.build_strategy(signal)
                    
                    if strategy:
                        # Place orders
                        orders = await self.order_executor.place_orders(strategy)
                        
                        # Send alert
                        from ..alerts.telegram_bot import send_trade_alert
                        await send_trade_alert({
                            **signal,
                            'strategy': strategy.name,
                            'orders': orders
                        })
                else:
                    # Log rejection
                    print(f"Signal rejected by risk manager: {risk_check['reason']}")
        
        except Exception as e:
            print(f"Error in signal generation: {e}")
    
    async def _close_position(self, position_id: str):
        """Close position in background."""
        try:
            # Get position
            position = await self.position_monitor.get_position(position_id)
            
            if position:
                # Close orders
                result = await self.order_executor.close_position(position)
                
                # Send alert
                from ..alerts.telegram_bot import send_exit_alert
                await send_exit_alert({
                    'position_id': position_id,
                    'pnl': result.get('pnl', 0),
                    'return_pct': result.get('return_pct', 0),
                    'duration': result.get('duration', 'Unknown')
                })
        
        except Exception as e:
            print(f"Error closing position {position_id}: {e}")
    
    def _is_market_open(self) -> bool:
        """Check if market is open."""
        now = datetime.now().time()
        return TradingConfig.MARKET_OPEN <= now <= TradingConfig.MARKET_CLOSE
    
    def run(self, host: str = None, port: int = None):
        """Run the FastAPI server."""
        host = host or TradingConfig.API_HOST
        port = port or TradingConfig.API_PORT
        
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level="info" if TradingConfig.API_DEBUG else "warning"
        )

# Create global server instance
server = FastAPIServer()

# Expose the FastAPI app for deployment
app = server.app

if __name__ == "__main__":
    server.run()
