#!/usr/bin/env python3
"""
NSE Access Fix - Enhanced authentication and session management
"""

import requests
import json
import time
import random
import re
from datetime import datetime

class EnhancedNSEAccess:
    """Enhanced NSE access with proper authentication."""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        self.csrf_token = None
        self._init_enhanced_session()
    
    def _get_random_user_agent(self):
        """Get random user agent to avoid detection."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)
    
    def _init_enhanced_session(self):
        """Initialize session with enhanced authentication."""
        user_agent = self._get_random_user_agent()
        
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        self.session.headers.update(headers)
        
        try:
            print("Establishing session with NSE...")
            response = self.session.get(self.base_url, timeout=15)
            
            if response.status_code == 200:
                print("Session established successfully")
                self._extract_csrf_token(response.text)
            else:
                print(f"Homepage access failed: {response.status_code}")
                
        except Exception as e:
            print(f"Session initialization failed: {e}")
    
    def _extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML."""
        try:
            patterns = [
                r'name="csrf_token" content="([^"]+)"',
                r'csrf_token.*?:.*?"([^"]+)"',
                r'X-CSRF-Token.*?:.*?"([^"]+)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    self.csrf_token = match.group(1)
                    print(f"CSRF token extracted: {self.csrf_token[:10]}...")
                    return
            
            print("No CSRF token found")
            
        except Exception as e:
            print(f"CSRF token extraction failed: {e}")
    
    def test_nse_access(self):
        """Test NSE access with enhanced authentication."""
        print("\nTesting Enhanced NSE Access")
        print("=" * 40)
        
        # Test homepage
        print("\n1. Testing homepage access...")
        try:
            response = self.session.get(self.base_url, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Homepage accessible")
            else:
                print(f"Homepage blocked: {response.status_code}")
        except Exception as e:
            print(f"Homepage error: {e}")
        
        # Test option chain API
        print("\n2. Testing option chain API...")
        api_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'{self.base_url}/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        if self.csrf_token:
            api_headers['X-CSRF-Token'] = self.csrf_token
        
        endpoints = [
            f"{self.api_base}/option-chain-indices?symbol=NIFTY",
            f"{self.base_url}/market-data/option-chain-indices?symbol=NIFTY"
        ]
        
        for i, endpoint in enumerate(endpoints, 1):
            print(f"   2.{i} Testing: {endpoint}")
            try:
                time.sleep(random.uniform(1, 2))
                response = self.session.get(endpoint, headers=api_headers, timeout=15)
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'records' in data:
                            records = len(data.get('records', {}).get('data', []))
                            print(f"      SUCCESS! Found {records} records")
                            return True
                        else:
                            print(f"      Unexpected structure: {list(data.keys())[:3]}")
                    except json.JSONDecodeError:
                        print(f"      Invalid JSON response")
                else:
                    print(f"      Error: {response.status_code}")
                    
            except Exception as e:
                print(f"      Request failed: {e}")
        
        return False

if __name__ == "__main__":
    print("NSE Access Fix - Enhanced Authentication Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    enhancer = EnhancedNSEAccess()
    success = enhancer.test_nse_access()
    
    if success:
        print("\nNSE Access Successfully Restored!")
    else:
        print("\nNSE Access Still Blocked")
