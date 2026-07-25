"""
Strategy Builder - Construct option legs from signals
Transforms trading signals into executable option strategies
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from dataclasses import dataclass
from enum import Enum

class OptionType(Enum):
    CALL = 'CE'
    PUT = 'PE'

class Action(Enum):
    BUY = 'BUY'
    SELL = 'SELL'

@dataclass
class OptionLeg:
    """Represents a single option leg in a strategy."""
    symbol: str
    strike: float
    option_type: OptionType
    action: Action
    quantity: int
    expiry: date
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

@dataclass
class OptionStrategy:
    """Represents a complete option strategy."""
    name: str
    legs: List[OptionLeg]
    max_profit: Optional[float] = None
    max_loss: Optional[float] = None
    breakeven_points: List[float] = None
    risk_reward_ratio: Optional[float] = None
    confidence_score: float = 0.0

class StrategyBuilder:
    """Builds option strategies from trading signals."""
    
    def __init__(self):
        self.min_distance_between_strikes = 50  # points
        self.max_legs_per_strategy = 4
        self.default_quantity = 25  # lot size
    
    def build_strategy_from_signal(self, signal: Dict, option_chain: List[Dict], 
                                 current_price: float, expiry: date) -> Optional[OptionStrategy]:
        """Build option strategy based on trading signal."""
        
        signal_direction = signal.get('direction', 'neutral')
        signal_strength = signal.get('strength', 0.5)
        confidence = signal.get('confidence', 0.5)
        
        if signal_direction == 'bullish':
            return self._build_bullish_strategy(option_chain, current_price, expiry, 
                                              signal_strength, confidence)
        elif signal_direction == 'bearish':
            return self._build_bearish_strategy(option_chain, current_price, expiry, 
                                              signal_strength, confidence)
        else:
            return self._build_neutral_strategy(option_chain, current_price, expiry, 
                                              signal_strength, confidence)
    
    def _build_bullish_strategy(self, option_chain: List[Dict], current_price: float, 
                              expiry: date, strength: float, confidence: float) -> OptionStrategy:
        """Build bullish option strategy."""
        
        # Find appropriate strikes
        atm_strike = self._find_atm_strike(option_chain, current_price)
        otm_call_strike = self._find_next_strike(option_chain, atm_strike, 'above')
        otm_put_strike = self._find_next_strike(option_chain, atm_strike, 'below')
        
        legs = []
        
        if strength > 0.7:  # High strength - Bull Call Spread
            # Buy ATM call
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.CALL,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            # Sell OTM call
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=otm_call_strike,
                option_type=OptionType.CALL,
                action=Action.SELL,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            strategy_name = 'Bull Call Spread'
            
        else:  # Lower strength - Simple Call Buy
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.CALL,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            strategy_name = 'Long Call'
        
        # Calculate strategy metrics
        strategy = OptionStrategy(
            name=strategy_name,
            legs=legs,
            confidence_score=confidence
        )
        
        self._calculate_strategy_metrics(strategy, option_chain)
        
        return strategy
    
    def _build_bearish_strategy(self, option_chain: List[Dict], current_price: float, 
                              expiry: date, strength: float, confidence: float) -> OptionStrategy:
        """Build bearish option strategy."""
        
        atm_strike = self._find_atm_strike(option_chain, current_price)
        otm_call_strike = self._find_next_strike(option_chain, atm_strike, 'above')
        otm_put_strike = self._find_next_strike(option_chain, atm_strike, 'below')
        
        legs = []
        
        if strength > 0.7:  # High strength - Bear Put Spread
            # Buy ATM put
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.PUT,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            # Sell OTM put
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=otm_put_strike,
                option_type=OptionType.PUT,
                action=Action.SELL,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            strategy_name = 'Bear Put Spread'
            
        else:  # Lower strength - Simple Put Buy
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.PUT,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            strategy_name = 'Long Put'
        
        strategy = OptionStrategy(
            name=strategy_name,
            legs=legs,
            confidence_score=confidence
        )
        
        self._calculate_strategy_metrics(strategy, option_chain)
        
        return strategy
    
    def _build_neutral_strategy(self, option_chain: List[Dict], current_price: float, 
                              expiry: date, strength: float, confidence: float) -> OptionStrategy:
        """Build neutral/non-directional strategy."""
        
        atm_strike = self._find_atm_strike(option_chain, current_price)
        otm_call_strike = self._find_next_strike(option_chain, atm_strike, 'above')
        otm_put_strike = self._find_next_strike(option_chain, atm_strike, 'below')
        
        legs = []
        
        if strength > 0.6:  # High strength - Iron Condor
            # Sell ATM call
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.CALL,
                action=Action.SELL,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            # Buy OTM call (protection)
            far_otm_call = self._find_next_strike(option_chain, otm_call_strike, 'above')
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=far_otm_call,
                option_type=OptionType.CALL,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            # Sell ATM put
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.PUT,
                action=Action.SELL,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            # Buy OTM put (protection)
            far_otm_put = self._find_next_strike(option_chain, otm_put_strike, 'below')
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=far_otm_put,
                option_type=OptionType.PUT,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            strategy_name = 'Iron Condor'
            
        else:  # Lower strength - Straddle
            # Buy ATM call
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.CALL,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            # Buy ATM put
            legs.append(OptionLeg(
                symbol='NIFTY',
                strike=atm_strike,
                option_type=OptionType.PUT,
                action=Action.BUY,
                quantity=self.default_quantity,
                expiry=expiry
            ))
            
            strategy_name = 'Long Straddle'
        
        strategy = OptionStrategy(
            name=strategy_name,
            legs=legs,
            confidence_score=confidence
        )
        
        self._calculate_strategy_metrics(strategy, option_chain)
        
        return strategy
    
    def _find_atm_strike(self, option_chain: List[Dict], current_price: float) -> float:
        """Find at-the-money strike."""
        
        closest_strike = None
        min_distance = float('inf')
        
        for option in option_chain:
            strike = option.get('strikePrice', 0)
            distance = abs(strike - current_price)
            
            if distance < min_distance:
                min_distance = distance
                closest_strike = strike
        
        return closest_strike or current_price
    
    def _find_next_strike(self, option_chain: List[Dict], current_strike: float, 
                         direction: str) -> float:
        """Find next strike in specified direction."""
        
        filtered_strikes = []
        
        for option in option_chain:
            strike = option.get('strikePrice', 0)
            
            if direction == 'above' and strike > current_strike:
                filtered_strikes.append(strike)
            elif direction == 'below' and strike < current_strike:
                filtered_strikes.append(strike)
        
        if not filtered_strikes:
            return current_strike
        
        if direction == 'above':
            return min(filtered_strikes)
        else:
            return max(filtered_strikes)
    
    def _calculate_strategy_metrics(self, strategy: OptionStrategy, option_chain: List[Dict]):
        """Calculate strategy metrics like max profit/loss, breakeven points."""
        
        # This is a simplified calculation - in practice, you'd need option pricing models
        total_premium = 0
        breakeven_points = []
        
        for leg in strategy.legs:
            # Find option price from chain
            option_price = self._get_option_price(option_chain, leg.strike, leg.option_type)
            
            if option_price:
                if leg.action == Action.BUY:
                    total_premium -= option_price * leg.quantity
                else:
                    total_premium += option_price * leg.quantity
                
                leg.entry_price = option_price
        
        # Set simplified metrics
        strategy.max_profit = abs(total_premium) * 0.8  # Simplified
        strategy.max_loss = abs(total_premium) * 1.2    # Simplified
        strategy.breakeven_points = breakeven_points
        
        if strategy.max_loss > 0:
            strategy.risk_reward_ratio = strategy.max_profit / strategy.max_loss
    
    def _get_option_price(self, option_chain: List[Dict], strike: float, 
                         option_type: OptionType) -> Optional[float]:
        """Get option price from option chain."""
        
        for option in option_chain:
            if option.get('strikePrice') == strike:
                if option_type == OptionType.CALL:
                    return option.get('CE', {}).get('lastPrice')
                else:
                    return option.get('PE', {}).get('lastPrice')
        
        return None
    
    def validate_strategy(self, strategy: OptionStrategy, account_balance: float, 
                         risk_per_trade: float) -> Tuple[bool, str]:
        """Validate strategy against risk parameters."""
        
        if not strategy.legs:
            return False, "No legs in strategy"
        
        if strategy.max_loss and strategy.max_loss > account_balance * risk_per_trade:
            return False, f"Max loss {strategy.max_loss} exceeds risk limit {account_balance * risk_per_trade}"
        
        if strategy.confidence_score < 0.3:
            return False, f"Low confidence score: {strategy.confidence_score}"
        
        if len(strategy.legs) > self.max_legs_per_strategy:
            return False, f"Too many legs: {len(strategy.legs)}"
        
        return True, "Strategy validated"
