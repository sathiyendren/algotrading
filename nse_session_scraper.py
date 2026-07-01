#!/usr/bin/env python3
"""
NSE Session-Aware Scraper - Proper cookie management for NSE access
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from urllib.parse import urljoin

class NSESessionScraper:
    """NSE scraper with proper session cookie management."""
    
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        self.session_created = None
        self.session_duration = timedelta(minutes=45)  # Refresh every 45 minutes
        self._initialize_session()
    
    def _initialize_session(self):
        """Initialize session with proper NSE cookies."""
        print("🍪 Initializing NSE session...")
        
        # Set proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        
        self.session.headers.update(headers)
        
        # CRITICAL: Visit homepage first to get session cookies
        try:
            print("🌐 Visiting NSE homepage for session cookies...")
            response = self.session.get(self.base_url, timeout=15)
            
            if response.status_code == 200:
                self.session_created = datetime.now()
                print(f"✅ Session established at {self.session_created.strftime('%H:%M:%S')}")
                print(f"🍪 Cookies received: {len(self.session.cookies)} cookies")
                
                # Print cookie names for debugging
                for cookie in self.session.cookies:
                    print(f"   - {cookie.name}: {cookie.value[:20]}...")
                    
                self._extract_csrf_token(response.text)
                return True
            else:
                print(f"❌ Homepage access failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Session initialization failed: {e}")
            return False
    
    def _extract_csrf_token(self, html_content):
        """Extract CSRF token from homepage HTML."""
        try:
            patterns = [
                r'name="csrf_token" content="([^"]+)"',
                r'csrf_token.*?:.*?"([^"]+)"',
                r'"csrfToken":"([^"]+)"',
                r'window\.__csrf__\s*=\s*["\']([^"\']+)["\']'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content, re.IGNORECASE)
                if match:
                    csrf_token = match.group(1)
                    self.session.headers.update({'X-CSRF-Token': csrf_token})
                    print(f"🔐 CSRF token set: {csrf_token[:10]}...")
                    return
            
            print("⚠️ No CSRF token found - may not be required for all endpoints")
            
        except Exception as e:
            print(f"⚠️ CSRF token extraction failed: {e}")
    
    def _is_session_valid(self):
        """Check if session is still valid (not expired)."""
        if not self.session_created:
            return False
        
        elapsed = datetime.now() - self.session_created
        return elapsed < self.session_duration
    
    def _refresh_session_if_needed(self):
        """Refresh session if it's expired or invalid."""
        if not self._is_session_valid():
            print("🔄 Session expired, refreshing...")
            self.session.cookies.clear()
            return self._initialize_session()
        return True
    
    def _get_api_headers(self):
        """Get headers for API requests."""
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Referer': self.base_url + '/',
            'X-Requested-With': 'XMLHttpRequest',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
    
    def get_option_chain(self, symbol='NIFTY'):
        """Get option chain data with proper session management."""
        # Refresh session if needed
        if not self._refresh_session_if_needed():
            return None
        
        print(f"📊 Fetching {symbol} option chain...")
        
        # Updated NSE endpoints for 2024
        endpoints = [
            f"{self.api_base}/option-chain-indices?symbol={symbol}",
            f"{self.base_url}/market-data/option-chain-indices?symbol={symbol}",
            f"{self.api_base}/market-data/option-chain-indices?symbol={symbol}"
        ]
        
        api_headers = self._get_api_headers()
        
        for i, endpoint in enumerate(endpoints, 1):
            try:
                print(f"   📍 Trying endpoint {i}: {endpoint}")
                
                response = self.session.get(endpoint, headers=api_headers, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        
                        # Check for valid option chain data
                        if 'records' in data and 'data' in data['records']:
                            records = data['records']['data']
                            if records and len(records) > 0:
                                print(f"   ✅ SUCCESS! Found {len(records)} option contracts")
                                return data
                            else:
                                print(f"   ⚠️ Empty data received")
                        else:
                            print(f"   ⚠️ Unexpected structure: {list(data.keys())[:3]}")
                            
                    except json.JSONDecodeError:
                        print(f"   ⚠️ Invalid JSON response")
                        
                elif response.status_code == 403:
                    print(f"   ❌ Forbidden - session may be invalid")
                    # Try to refresh session and retry once
                    if i == 1:  # Only retry on first attempt
                        print("   🔄 Attempting session refresh...")
                        if self._initialize_session():
                            continue  # Retry with fresh session
                            
                elif response.status_code == 404:
                    print(f"   ❌ Not found - endpoint may have changed")
                    
                else:
                    print(f"   ❌ Error: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
        
        return None
    
    def test_session_access(self):
        """Test NSE access with proper session management."""
        print("\n🧪 Testing NSE Session Access")
        print("=" * 50)
        
        # Test option chain
        data = self.get_option_chain('NIFTY')
        
        if data:
            print("\n🎉 NSE ACCESS SUCCESSFUL!")
            print("📊 Sample data structure:")
            
            if 'records' in data and 'data' in data['records']:
                records = data['records']['data'][:3]  # First 3 records
                for i, record in enumerate(records, 1):
                    strike = record.get('strikePrice', 'N/A')
                    pe_oi = record.get('PE', {}).get('openInterest', 'N/A')
                    ce_oi = record.get('CE', {}).get('openInterest', 'N/A')
                    print(f"   {i}. Strike: {strike}, PE OI: {pe_oi}, CE OI: {ce_oi}")
            
            return True
        else:
            print("\n❌ NSE access failed - using mock data fallback")
            return False

if __name__ == "__main__":
    print("🚀 NSE Session-Aware Scraper Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    scraper = NSESessionScraper()
    success = scraper.test_session_access()
    
    if success:
        print("\n✅ Real NSE data collection is now working!")
    else:
        print("\n⚠️ Still blocked - will use enhanced mock data")
