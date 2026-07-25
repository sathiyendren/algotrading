"""
Event Calendar for FII Algo Trading
Handles RBI policy dates, budget dates, and expiry dates
"""

from datetime import datetime, date
from typing import Dict, List, Optional
from .settings import EVENT_CALENDAR

class EventCalendar:
    """Manages trading-related events and dates."""
    
    def __init__(self):
        self.events = EVENT_CALENDAR
    
    def get_events_by_date(self, target_date: date) -> List[str]:
        """Get all events for a specific date."""
        events = []
        date_str = target_date.strftime('%Y-%m-%d')
        
        for event_type, event_dict in self.events.items():
            if date_str in event_dict:
                events.append(f"{event_dict[date_str]} ({event_type})")
        
        return events
    
    def get_events_by_type(self, event_type: str) -> Dict[str, str]:
        """Get all events of a specific type."""
        return self.events.get(event_type, {})
    
    def is_event_day(self, target_date: date) -> bool:
        """Check if a date has any events."""
        return len(self.get_events_by_date(target_date)) > 0
    
    def get_next_event(self, from_date: date = None) -> Optional[Dict]:
        """Get the next upcoming event."""
        if from_date is None:
            from_date = date.today()
        
        all_events = []
        for event_type, event_dict in self.events.items():
            for date_str, description in event_dict.items():
                event_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if event_date >= from_date:
                    all_events.append({
                        'date': event_date,
                        'type': event_type,
                        'description': description
                    })
        
        if not all_events:
            return None
        
        return min(all_events, key=lambda x: x['date'])
    
    def get_trading_adjustments(self, target_date: date) -> Dict:
        """Get trading adjustments for event days."""
        events = self.get_events_by_date(target_date)
        adjustments = {
            'increased_volatility': False,
            'reduced_position_size': False,
            'avoid_trading': False,
            'special_attention': False
        }
        
        for event in events:
            if 'RBI' in event or 'Budget' in event:
                adjustments['increased_volatility'] = True
                adjustments['reduced_position_size'] = True
                adjustments['special_attention'] = True
            elif 'Expiry' in event:
                adjustments['increased_volatility'] = True
                adjustments['special_attention'] = True
        
        return adjustments

# Global instance
event_calendar = EventCalendar()
