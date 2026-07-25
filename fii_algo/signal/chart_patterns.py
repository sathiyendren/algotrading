"""
Chart Pattern Detection Engine
Identifies Order Blocks, Fair Value Gaps, and Sweeps
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ChartPatternDetector:
    """Detects advanced chart patterns for trading signals."""
    
    def __init__(self):
        self.min_swing_points = 3
        self.fvg_threshold = 0.001  # 0.1% for fair value gaps
        self.ob_threshold = 0.002   # 0.2% for order blocks
    
    def detect_order_blocks(self, df: pd.DataFrame) -> List[Dict]:
        """Detect order blocks from price action."""
        order_blocks = []
        
        if len(df) < 10:
            return order_blocks
        
        # Find swing highs and lows
        swing_highs = self._find_swing_points(df, 'high')
        swing_lows = self._find_swing_points(df, 'low')
        
        # Bearish order blocks at swing highs
        for high_idx in swing_highs:
            if high_idx > 0:
                candle = df.iloc[high_idx]
                prev_candle = df.iloc[high_idx - 1]
                
                # Order block is the candle before the swing high
                ob_high = prev_candle['high']
                ob_low = prev_candle['low']
                ob_close = prev_candle['close']
                
                # Validate order block strength
                if self._validate_order_block(df, high_idx, ob_low, ob_high, 'bearish'):
                    order_blocks.append({
                        'type': 'bearish',
                        'index': high_idx - 1,
                        'price_high': ob_high,
                        'price_low': ob_low,
                        'close': ob_close,
                        'time': df.index[high_idx - 1],
                        'strength': self._calculate_ob_strength(df, high_idx - 1, ob_low, ob_high)
                    })
        
        # Bullish order blocks at swing lows
        for low_idx in swing_lows:
            if low_idx > 0:
                candle = df.iloc[low_idx]
                prev_candle = df.iloc[low_idx - 1]
                
                # Order block is the candle before the swing low
                ob_high = prev_candle['high']
                ob_low = prev_candle['low']
                ob_close = prev_candle['close']
                
                # Validate order block strength
                if self._validate_order_block(df, low_idx, ob_low, ob_high, 'bullish'):
                    order_blocks.append({
                        'type': 'bullish',
                        'index': low_idx - 1,
                        'price_high': ob_high,
                        'price_low': ob_low,
                        'close': ob_close,
                        'time': df.index[low_idx - 1],
                        'strength': self._calculate_ob_strength(df, low_idx - 1, ob_low, ob_high)
                    })
        
        return order_blocks
    
    def detect_fair_value_gaps(self, df: pd.DataFrame) -> List[Dict]:
        """Detect Fair Value Gaps (FVG) in price action."""
        fvgs = []
        
        if len(df) < 3:
            return fvgs
        
        for i in range(2, len(df)):
            # Check for bullish FVG (gap up)
            candle_2 = df.iloc[i-2]  # 2 candles back
            candle_1 = df.iloc[i-1]  # 1 candle back
            candle_0 = df.iloc[i]    # Current candle
            
            # Bullish FVG: top of candle_2 < bottom of candle_0
            if candle_2['high'] < candle_0['low']:
                gap_size = (candle_0['low'] - candle_2['high']) / candle_2['high']
                
                if gap_size > self.fvg_threshold:
                    fvgs.append({
                        'type': 'bullish',
                        'top': candle_2['high'],
                        'bottom': candle_0['low'],
                        'size': gap_size,
                        'start_index': i-2,
                        'end_index': i,
                        'time': df.index[i],
                        'mitigated': self._is_fvg_mitigated(df, i, candle_2['high'], candle_0['low'])
                    })
            
            # Bearish FVG: bottom of candle_2 > top of candle_0
            elif candle_2['low'] > candle_0['high']:
                gap_size = (candle_2['low'] - candle_0['high']) / candle_2['low']
                
                if gap_size > self.fvg_threshold:
                    fvgs.append({
                        'type': 'bearish',
                        'top': candle_0['high'],
                        'bottom': candle_2['low'],
                        'size': gap_size,
                        'start_index': i-2,
                        'end_index': i,
                        'time': df.index[i],
                        'mitigated': self._is_fvg_mitigated(df, i, candle_0['high'], candle_2['low'])
                    })
        
        return fvgs
    
    def detect_liquidity_sweeps(self, df: pd.DataFrame, swing_highs: List[int], 
                              swing_lows: List[int]) -> List[Dict]:
        """Detect liquidity sweeps above/below swing points."""
        sweeps = []
        
        # Detect bullish sweeps (sweep below swing low)
        for low_idx in swing_lows:
            if low_idx < len(df) - 5:  # Need candles after the swing low
                swing_low_price = df.iloc[low_idx]['low']
                
                # Look for price going below swing low then reversing
                for i in range(low_idx + 1, min(low_idx + 6, len(df))):
                    current_low = df.iloc[i]['low']
                    current_high = df.iloc[i]['high']
                    
                    # Price went below swing low
                    if current_low < swing_low_price:
                        # Check for reversal in next few candles
                        for j in range(i + 1, min(i + 4, len(df))):
                            if df.iloc[j]['high'] > swing_low_price * 1.002:  # 0.2% above swing low
                                sweeps.append({
                                    'type': 'bullish_sweep',
                                    'swing_point': low_idx,
                                    'swing_price': swing_low_price,
                                    'sweep_low': current_low,
                                    'reversal_index': j,
                                    'reversal_price': df.iloc[j]['high'],
                                    'time': df.index[j]
                                })
                                break
        
        # Detect bearish sweeps (sweep above swing high)
        for high_idx in swing_highs:
            if high_idx < len(df) - 5:
                swing_high_price = df.iloc[high_idx]['high']
                
                # Look for price going above swing high then reversing
                for i in range(high_idx + 1, min(high_idx + 6, len(df))):
                    current_high = df.iloc[i]['high']
                    current_low = df.iloc[i]['low']
                    
                    # Price went above swing high
                    if current_high > swing_high_price:
                        # Check for reversal in next few candles
                        for j in range(i + 1, min(i + 4, len(df))):
                            if df.iloc[j]['low'] < swing_high_price * 0.998:  # 0.2% below swing high
                                sweeps.append({
                                    'type': 'bearish_sweep',
                                    'swing_point': high_idx,
                                    'swing_price': swing_high_price,
                                    'sweep_high': current_high,
                                    'reversal_index': j,
                                    'reversal_price': df.iloc[j]['low'],
                                    'time': df.index[j]
                                })
                                break
        
        return sweeps
    
    def _find_swing_points(self, df: pd.DataFrame, price_col: str) -> List[int]:
        """Find swing points using fractal analysis."""
        swing_points = []
        
        for i in range(self.min_swing_points, len(df) - self.min_swing_points):
            current = df.iloc[i][price_col]
            
            # Check if it's a swing high
            is_swing_high = True
            for j in range(i - self.min_swing_points, i + self.min_swing_points + 1):
                if j != i and df.iloc[j][price_col] >= current:
                    is_swing_high = False
                    break
            
            if is_swing_high and price_col == 'high':
                swing_points.append(i)
            
            # Check if it's a swing low
            is_swing_low = True
            for j in range(i - self.min_swing_points, i + self.min_swing_points + 1):
                if j != i and df.iloc[j][price_col] <= current:
                    is_swing_low = False
                    break
            
            if is_swing_low and price_col == 'low':
                swing_points.append(i)
        
        return swing_points
    
    def _validate_order_block(self, df: pd.DataFrame, index: int, low: float, 
                            high: float, direction: str) -> bool:
        """Validate order block strength."""
        if index < 5:
            return False
        
        # Check for strong rejection
        if direction == 'bearish':
            # Price should have moved down significantly after the order block
            future_candles = df.iloc[index + 1:index + 6]
            min_future_low = future_candles['low'].min()
            return min_future_low < low * (1 - self.ob_threshold)
        else:
            # Price should have moved up significantly after the order block
            future_candles = df.iloc[index + 1:index + 6]
            max_future_high = future_candles['high'].max()
            return max_future_high > high * (1 + self.ob_threshold)
    
    def _calculate_ob_strength(self, df: pd.DataFrame, index: int, low: float, 
                             high: float) -> float:
        """Calculate order block strength based on volume and price movement."""
        if index >= len(df):
            return 0.5
        
        candle = df.iloc[index]
        
        # Base strength from volume (if available)
        volume_strength = 0.5
        if 'volume' in candle and not pd.isna(candle['volume']):
            # Normalize volume (simplified)
            avg_volume = df['volume'].rolling(20).mean().iloc[index]
            if avg_volume > 0:
                volume_strength = min(candle['volume'] / avg_volume, 2.0) / 2.0
        
        # Price range strength
        price_range = (high - low) / low
        range_strength = min(price_range * 100, 1.0)
        
        # Combine strengths
        return (volume_strength * 0.6 + range_strength * 0.4)
    
    def _is_fvg_mitigated(self, df: pd.DataFrame, start_index: int, top: float, 
                         bottom: float) -> bool:
        """Check if FVG has been mitigated."""
        if start_index >= len(df):
            return False
        
        # Check future candles to see if gap has been filled
        for i in range(start_index + 1, len(df)):
            candle = df.iloc[i]
            
            # Bullish FVG mitigated if price closes in the gap
            if bottom < top:  # Bullish FVG
                if candle['close'] >= bottom and candle['close'] <= top:
                    return True
            else:  # Bearish FVG
                if candle['close'] >= top and candle['close'] <= bottom:
                    return True
        
        return False
    
    def get_pattern_signals(self, df: pd.DataFrame) -> Dict:
        """Get all pattern signals for analysis."""
        swing_highs = self._find_swing_points(df, 'high')
        swing_lows = self._find_swing_points(df, 'low')
        
        order_blocks = self.detect_order_blocks(df)
        fvgs = self.detect_fair_value_gaps(df)
        sweeps = self.detect_liquidity_sweeps(df, swing_highs, swing_lows)
        
        return {
            'order_blocks': order_blocks,
            'fair_value_gaps': fvgs,
            'liquidity_sweeps': sweeps,
            'swing_highs': swing_highs,
            'swing_lows': swing_lows,
            'timestamp': datetime.now()
        }
