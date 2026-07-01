#!/usr/bin/env python3
"""
Enhanced Market Hours Detection with Holiday Support
Detects Indian stock market trading hours and holidays
"""

import datetime
import holidays
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class MarketHoursDetector:
    """Enhanced market hours detector with holiday support"""
    
    def __init__(self):
        # Indian stock market trading hours (IST)
        self.market_open = datetime.time(9, 15)  # 9:15 AM
        self.market_close = datetime.time(15, 30)  # 3:30 PM
        self.pre_open = datetime.time(9, 0)  # 9:00 AM (pre-open session)
        self.post_close = datetime.time(15, 40)  # 3:40 PM (post-close session)
        
        # Load Indian holidays
        self.indian_holidays = holidays.India()
        
        # Additional trading holidays that might not be in the library
        self.custom_holidays = {
            # Add any custom holidays here
            # Format: datetime.date(2024, 1, 26): 'Republic Day',
        }
        
        # Special trading sessions (Mahurat Trading, etc.)
        self.special_sessions = {
            # Diwali Mahurat Trading usually in evening
            # datetime.date(2024, 11, 1): {'open': datetime.time(18, 0), 'close': datetime.time(19, 30)},
        }
    
    def is_trading_day(self, date: datetime.date = None) -> bool:
        """Check if given date is a trading day (considering weekends and holidays)"""
        if date is None:
            date = datetime.date.today()
        
        # Check if it's a weekend
        if date.weekday() >= 5:  # Saturday (5) or Sunday (6)
            return False
        
        # Check if it's a holiday
        if date in self.indian_holidays:
            logger.info(f"Market closed for holiday: {self.indian_holidays.get(date)}")
            return False
        
        # Check custom holidays
        if date in self.custom_holidays:
            logger.info(f"Market closed for custom holiday: {self.custom_holidays[date]}")
            return False
        
        return True
    
    def is_market_open(self, current_time: datetime.datetime = None) -> bool:
        """Check if market is currently open for trading"""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        # Check if it's a trading day
        if not self.is_trading_day(current_time.date()):
            return False
        
        # Check if current time is within trading hours
        current_time_only = current_time.time()
        
        return self.market_open <= current_time_only <= self.market_close
    
    def is_pre_open_session(self, current_time: datetime.datetime = None) -> bool:
        """Check if it's pre-open session (9:00 AM - 9:15 AM)"""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        if not self.is_trading_day(current_time.date()):
            return False
        
        current_time_only = current_time.time()
        return self.pre_open <= current_time_only < self.market_open
    
    def is_post_close_session(self, current_time: datetime.datetime = None) -> bool:
        """Check if it's post-close session (3:30 PM - 3:40 PM)"""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        if not self.is_trading_day(current_time.date()):
            return False
        
        current_time_only = current_time.time()
        return self.market_close < current_time_only <= self.post_close
    
    def get_market_status(self, current_time: datetime.datetime = None) -> str:
        """Get current market status with detailed information"""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        date = current_time.date()
        time_only = current_time.time()
        
        # Check if it's a trading day
        if not self.is_trading_day(date):
            if date.weekday() >= 5:
                return "Weekend"
            elif date in self.indian_holidays:
                return f"Holiday: {self.indian_holidays.get(date)}"
            elif date in self.custom_holidays:
                return f"Holiday: {self.custom_holidays[date]}"
            else:
                return "Non-trading day"
        
        # Check special sessions
        if date in self.special_sessions:
            session = self.special_sessions[date]
            if session['open'] <= time_only <= session['close']:
                return "Special Trading Session"
        
        # Check regular sessions
        if time_only < self.pre_open:
            return "Pre-market (Closed)"
        elif self.pre_open <= time_only < self.market_open:
            return "Pre-open Session"
        elif self.market_open <= time_only <= self.market_close:
            return "Market Open"
        elif self.market_close < time_only <= self.post_close:
            return "Post-close Session"
        else:
            return "Post-market (Closed)"
    
    def get_next_trading_day(self, current_date: datetime.date = None) -> datetime.date:
        """Get the next trading day"""
        if current_date is None:
            current_date = datetime.date.today()
        
        next_day = current_date + datetime.timedelta(days=1)
        
        # Keep adding days until we find a trading day
        while not self.is_trading_day(next_day):
            next_day += datetime.timedelta(days=1)
        
        return next_day
    
    def get_time_until_market_open(self, current_time: datetime.datetime = None) -> Tuple[int, str]:
        """Get time until market opens (in minutes and human-readable format)"""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        # If market is open now
        if self.is_market_open(current_time):
            return 0, "Market is open"
        
        # If it's a weekend or holiday, find next trading day
        if not self.is_trading_day(current_time.date()):
            next_trading_day = self.get_next_trading_day(current_time.date())
            next_open = datetime.datetime.combine(next_trading_day, self.market_open)
            
            if current_time.tzinfo is None:
                # Assume IST if no timezone info
                current_time = current_time.replace(tzinfo=datetime.timezone.utc)
                next_open = next_open.replace(tzinfo=datetime.timezone.utc)
            
            time_until = int((next_open - current_time).total_seconds() / 60)
            
            if time_until < 60:
                return time_until, f"Market opens in {time_until} minutes"
            elif time_until < 1440:  # Less than 24 hours
                hours = time_until // 60
                return time_until, f"Market opens in {hours} hours"
            else:
                days = time_until // 1440
                return time_until, f"Market opens in {days} days"
        
        # If it's the same day but market hasn't opened yet
        today_open = datetime.datetime.combine(current_time.date(), self.market_open)
        
        if current_time < today_open:
            time_until = int((today_open - current_time).total_seconds() / 60)
            return time_until, f"Market opens in {time_until} minutes"
        
        # If market has closed for today
        next_trading_day = self.get_next_trading_day(current_time.date())
        next_open = datetime.datetime.combine(next_trading_day, self.market_open)
        time_until = int((next_open - current_time).total_seconds() / 60)
        
        if time_until < 1440:
            hours = time_until // 60
            return time_until, f"Market opens tomorrow in {hours} hours"
        else:
            days = time_until // 1440
            return time_until, f"Market opens in {days} days"
    
    def get_upcoming_holidays(self, days_ahead: int = 30) -> list:
        """Get list of upcoming holidays within specified days"""
        today = datetime.date.today()
        upcoming = []
        
        for i in range(days_ahead):
            check_date = today + datetime.timedelta(days=i)
            
            if check_date in self.indian_holidays:
                upcoming.append({
                    'date': check_date,
                    'name': self.indian_holidays.get(check_date),
                    'type': 'National Holiday'
                })
            elif check_date in self.custom_holidays:
                upcoming.append({
                    'date': check_date,
                    'name': self.custom_holidays[check_date],
                    'type': 'Custom Holiday'
                })
        
        return upcoming
    
    def add_custom_holiday(self, date: datetime.date, name: str):
        """Add a custom holiday"""
        self.custom_holidays[date] = name
        logger.info(f"Added custom holiday: {date} - {name}")
    
    def remove_custom_holiday(self, date: datetime.date):
        """Remove a custom holiday"""
        if date in self.custom_holidays:
            del self.custom_holidays[date]
            logger.info(f"Removed custom holiday: {date}")
    
    def get_trading_session_info(self, current_time: datetime.datetime = None) -> dict:
        """Get comprehensive trading session information"""
        if current_time is None:
            current_time = datetime.datetime.now()
        
        return {
            'current_time': current_time,
            'market_status': self.get_market_status(current_time),
            'is_trading_day': self.is_trading_day(current_time.date()),
            'is_market_open': self.is_market_open(current_time),
            'is_pre_open': self.is_pre_open_session(current_time),
            'is_post_close': self.is_post_close_session(current_time),
            'time_until_open': self.get_time_until_market_open(current_time),
            'next_trading_day': self.get_next_trading_day(current_time.date()),
            'upcoming_holidays': self.get_upcoming_holidays(30)[:5]  # Next 5 holidays
        }

# Global instance
market_detector = MarketHoursDetector()

# Convenience functions
def is_market_open(current_time: datetime.datetime = None) -> bool:
    """Check if market is currently open"""
    return market_detector.is_market_open(current_time)

def is_trading_day(date: datetime.date = None) -> bool:
    """Check if given date is a trading day"""
    return market_detector.is_trading_day(date)

def get_market_status(current_time: datetime.datetime = None) -> str:
    """Get current market status"""
    return market_detector.get_market_status(current_time)

def get_time_until_market_open(current_time: datetime.datetime = None) -> Tuple[int, str]:
    """Get time until market opens"""
    return market_detector.get_time_until_market_open(current_time)

if __name__ == "__main__":
    # Test the enhanced market hours detector
    detector = MarketHoursDetector()
    
    current_time = datetime.datetime.now()
    info = detector.get_trading_session_info(current_time)
    
    print("=== Enhanced Market Hours Detection ===")
    print(f"Current Time: {info['current_time']}")
    print(f"Market Status: {info['market_status']}")
    print(f"Is Trading Day: {info['is_trading_day']}")
    print(f"Is Market Open: {info['is_market_open']}")
    print(f"Time Until Open: {info['time_until_open'][1]}")
    print(f"Next Trading Day: {info['next_trading_day']}")
    
    print("\nUpcoming Holidays:")
    for holiday in info['upcoming_holidays']:
        print(f"  {holiday['date']}: {holiday['name']} ({holiday['type']})")
