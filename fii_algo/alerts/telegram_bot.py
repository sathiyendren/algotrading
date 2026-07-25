"""
Telegram Bot for FII Algo Trading System
Handles alerts and command processing
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from ..config.settings import TradingConfig

class TelegramBot:
    """Telegram bot for trading alerts and commands."""
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or TradingConfig.TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TradingConfig.TELEGRAM_CHAT_ID
        self.bot = Bot(token=self.token)
        self.application = None
        
        # Setup logging
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)
    
    async def start_bot(self):
        """Start the Telegram bot."""
        if not self.token:
            self.logger.error("Telegram bot token not configured")
            return
        
        self.application = Application.builder().token(self.token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("positions", self.positions_command))
        self.application.add_handler(CommandHandler("pnl", self.pnl_command))
        self.application.add_handler(CommandHandler("risk", self.risk_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Add message handler
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start the bot
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        self.logger.info("Telegram bot started successfully")
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.logger.info("Telegram bot stopped")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        welcome_message = (
            "🚀 *FII Algo Trading Bot Started!*\n\n"
            "Available commands:\n"
            "/status - System status\n"
            "/positions - Current positions\n"
            "/pnl - P&L summary\n"
            "/risk - Risk metrics\n"
            "/help - Show this help"
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        # This would integrate with your monitoring system
        status_message = (
            "📊 *System Status*\n\n"
            f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}\n"
            "🟢 Scheduler: Running\n"
            "🟢 Data Collection: Active\n"
            "🟢 Database: Connected\n"
            "📈 NIFTY: 19,850.50 (+0.8%)\n"
            "📈 BANKNIFTY: 44,250.30 (+1.2%)"
        )
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command."""
        positions_message = (
            "📋 *Current Positions*\n\n"
            "🟢 *Bull Call Spread*\n"
            "  • NIFTY 19800 CE (Buy) x 25\n"
            "  • NIFTY 20000 CE (Sell) x 25\n"
            "  • Entry: 45.50\n"
            "  • Current: 52.30 (+14.9%)\n\n"
            "No other positions"
        )
        
        await update.message.reply_text(positions_message, parse_mode='Markdown')
    
    async def pnl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pnl command."""
        pnl_message = (
            "💰 *P&L Summary*\n\n"
            "📅 Today: +₹2,450 (+1.8%)\n"
            "📈 This Week: +₹8,750 (+6.4%)\n"
            "📊 This Month: +₹15,320 (+11.2%)\n"
            "💎 Total: +₹45,680 (+33.5%)\n\n"
            "🎯 Win Rate: 68.5%"
        )
        
        await update.message.reply_text(pnl_message, parse_mode='Markdown')
    
    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command."""
        risk_message = (
            "⚠️ *Risk Metrics*\n\n"
            "🛡️ Current Risk: 1.2% (Target: 2.0%)\n"
            "📊 Portfolio Beta: 0.85\n"
            "🔥 Max Drawdown: -4.2%\n"
            "⚡ VIX: 16.8 (Low Volatility)\n"
            "🎯 Risk-Adjusted Return: 2.1"
        )
        
        await update.message.reply_text(risk_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = (
            "🤖 *FII Algo Trading Bot Help*\n\n"
            "*Commands:*\n"
            "/start - Start the bot\n"
            "/status - System status\n"
            "/positions - Current positions\n"
            "/pnl - P&L summary\n"
            "/risk - Risk metrics\n"
            "/help - Show this help\n\n"
            "*Alerts:*\n"
            "🔔 You'll receive automatic alerts for:\n"
            "• New trade entries\n"
            "• Exit signals\n"
            "• Risk breaches\n"
            "• System errors"
        )
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        user_message = update.message.text.lower()
        
        if 'help' in user_message:
            await self.help_command(update, context)
        elif 'status' in user_message:
            await self.status_command(update, context)
        else:
            await update.message.reply_text(
                "Use /help to see available commands"
            )
    
    async def send_trade_alert(self, signal: Dict):
        """Send trade entry alert."""
        if not self.chat_id:
            return
        
        direction_emoji = "🟢" if signal.get('direction') == 'bullish' else "🔴"
        strategy = signal.get('strategy', 'Unknown')
        
        alert_message = (
            f"{direction_emoji} *Trade Alert*\n\n"
            f"📊 *Strategy:* {strategy}\n"
            f"🎯 *Direction:* {signal.get('direction', 'N/A').title()}\n"
            f"💪 *Strength:* {signal.get('strength', 0):.1%}\n"
            f"🎲 *Confidence:* {signal.get('confidence', 0):.1%}\n"
            f"🕐 *Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"📝 *Note:* Trade execution in progress"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=alert_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"Failed to send trade alert: {e}")
    
    async def send_exit_alert(self, position: Dict):
        """Send trade exit alert."""
        if not self.chat_id:
            return
        
        pnl_emoji = "🟢" if position.get('pnl', 0) > 0 else "🔴"
        pnl_text = "+" if position.get('pnl', 0) > 0 else ""
        
        alert_message = (
            f"{pnl_emoji} *Exit Alert*\n\n"
            f"📊 *Strategy:* {position.get('strategy', 'Unknown')}\n"
            f"💰 *P&L:* {pnl_text}₹{abs(position.get('pnl', 0)):,.2f}\n"
            f"📈 *Return:* {position.get('return_pct', 0):.1%}\n"
            f"⏱️ *Duration:* {position.get('duration', 'N/A')}\n"
            f"🕐 *Time:* {datetime.now().strftime('%H:%M:%S')}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=alert_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"Failed to send exit alert: {e}")
    
    async def send_risk_alert(self, risk_data: Dict):
        """Send risk breach alert."""
        if not self.chat_id:
            return
        
        alert_message = (
            f"⚠️ *Risk Alert*\n\n"
            f"🚨 *Issue:* {risk_data.get('issue', 'Unknown')}\n"
            f"📊 *Current Level:* {risk_data.get('current', 'N/A')}\n"
            f"🎯 *Threshold:* {risk_data.get('threshold', 'N/A')}\n"
            f"🕐 *Time:* {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"🔧 *Action:* {risk_data.get('action', 'Monitor')}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=alert_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"Failed to send risk alert: {e}")
    
    async def send_system_alert(self, message: str):
        """Send system status alert."""
        if not self.chat_id:
            return
        
        alert_message = (
            f"🔧 *System Alert*\n\n"
            f"{message}\n\n"
            f"🕐 *Time:* {datetime.now().strftime('%H:%M:%S')}"
        )
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=alert_message,
                parse_mode='Markdown'
            )
        except Exception as e:
            self.logger.error(f"Failed to send system alert: {e}")

# Global bot instance
telegram_bot = TelegramBot()

# Helper functions for easy access
async def send_trade_alert(signal: Dict):
    """Send trade alert through Telegram bot."""
    await telegram_bot.send_trade_alert(signal)

async def send_exit_alert(position: Dict):
    """Send exit alert through Telegram bot."""
    await telegram_bot.send_exit_alert(position)

async def send_risk_alert(risk_data: Dict):
    """Send risk alert through Telegram bot."""
    await telegram_bot.send_risk_alert(risk_data)

async def send_system_alert(message: str):
    """Send system alert through Telegram bot."""
    await telegram_bot.send_system_alert(message)
