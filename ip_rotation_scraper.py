#!/usr/bin/env python3
"""
NSE IP Rotation Scraper - Bypass IP blacklisting with rotating proxies
"""

import requests
import json
import time
import random
from datetime import datetime
from urllib.parse import urljoin
import threading
from queue import Queue

class IPRotationNSEScraper:
    """NSE scraper with IP rotation to bypass blacklisting."""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.api_base = "https://www.nseindia.com/api"
        self.current_proxy_index = 0
        self.proxy_failures = {}
        self.session_cache = {}
        self._setup_proxy_rotation()
    
    def _setup_proxy_rotation(self):
        """Setup rotating proxy list."""
        print("🔄 Setting up IP rotation proxies...")
        
        # Free proxy services (Indian IPs preferred)
        self.proxies = [
            # Method 1: Public Indian proxies
            {
                'http': 'http://103.152.112.162:8080',
                'https': 'http://103.152.112.162:8080'
            },
            {
                'http': 'http://139.59.76.215:3128',
                'https': 'http://139.59.76.215:3128'
            },
            {
                'http': 'http://164.52.7.222:8080',
                'https': 'http://164.52.7.222:8080'
            },
            # Method 2: Different ports for same IP
            {
                'http': 'http://13.234.124.176:8080',
                'https': 'http://13.234.124.176:8080'
            },
            {
                'http': 'http://13.234.124.176:8888',
                'https': 'http://13.234.124.176:8888'
            },
            # Method 3: No proxy (direct connection with rotation)
            None
        ]
        
        print(f"✅ Configured {len(self.proxies)} proxy endpoints")
        
        # Test proxy connectivity
        self._test_proxy_connectivity()
    
    def _test_proxy_connectivity(self):
        """Test which proxies are working."""
        print("🧪 Testing proxy connectivity...")
        
        working_proxies = []
        test_url = "https://httpbin.org/ip"
        
        for i, proxy in enumerate(self.proxies):
            try:
                session = requests.Session()
                session.timeout = 10
                
                if proxy:
                    session.proxies.update(proxy)
                    proxy_desc = f"Proxy {i+1}"
                else:
                    proxy_desc = "Direct connection"
                
                response = session.get(test_url, timeout=5)
                
                if response.status_code == 200:
                    ip_info = response.json()
                    print(f"   ✅ {proxy_desc}: {ip_info.get('origin', 'Unknown')}")
                    working_proxies.append(proxy)
                else:
                    print(f"   ❌ {proxy_desc}: Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ Proxy {i+1}: Error - {str(e)[:30]}...")
        
        if working_proxies:
            self.proxies = working_proxies
            print(f"\n✅ {len(self.proxies)} working proxies available")
        else:
            print("\n⚠️ No working proxies - will use direct connection with rotation")
            self.proxies = [None]
    
    def _get_next_proxy(self):
        """Get next proxy in rotation."""
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _create_session_with_proxy(self, proxy):
        """Create session with specific proxy."""
        session = requests.Session()
        
        # Rotate user agents
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,en-IN;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        session.headers.update(headers)
        
        if proxy:
            session.proxies.update(proxy)
        
        session.timeout = 15
        return session
    
    def _initialize_session_with_proxy(self, proxy):
        """Initialize NSE session with specific proxy."""
        session = self._create_session_with_proxy(proxy)
        
        try:
            # Visit homepage first for session cookies
            response = session.get(self.base_url, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ Session established with proxy")
                return session
            else:
                print(f"   ⚠️ Homepage failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Session failed: {str(e)[:30]}...")
            return None
    
    def get_option_chain_with_rotation(self, symbol='NIFTY', max_attempts=3):
        """Get option chain with IP rotation."""
        print(f"\n📊 Fetching {symbol} option chain with IP rotation...")
        
        for attempt in range(max_attempts):
            proxy = self._get_next_proxy()
            
            if proxy:
                proxy_ip = list(proxy.values())[0].split('://')[1].split(':')[0]
                print(f"   🔄 Attempt {attempt + 1}: Using proxy {proxy_ip}")
            else:
                print(f"   🔄 Attempt {attempt + 1}: Using direct connection")
            
            # Initialize session with current proxy
            session = self._initialize_session_with_proxy(proxy)
            
            if not session:
                continue
            
            # Try to get option chain data
            success = self._fetch_option_chain_data(session, symbol)
            
            if success:
                return True
            
            # Wait before next attempt
            if attempt < max_attempts - 1:
                time.sleep(random.uniform(2, 5))
        
        print(f"   ❌ All {max_attempts} attempts failed")
        return False
    
    def _fetch_option_chain_data(self, session, symbol):
        """Fetch option chain data with given session."""
        endpoints = [
            f"{self.api_base}/option-chain-indices?symbol={symbol}",
            f"{self.base_url}/market-data/option-chain-indices?symbol={symbol}"
        ]
        
        api_headers = {
            'Accept': 'application/json, text/plain, */*',
            'Referer': self.base_url + '/',
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        for endpoint in endpoints:
            try:
                response = session.get(endpoint, headers=api_headers, timeout=15)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'records' in data and 'data' in data['records']:
                            records = data['records']['data']
                            if records and len(records) > 0:
                                print(f"   🎉 SUCCESS! Found {len(records)} option contracts")
                                self._display_sample_data(records[:3])
                                return True
                    except json.JSONDecodeError:
                        continue
                        
                elif response.status_code == 403:
                    print(f"      ⚠️ Forbidden with this proxy")
                    continue
                    
            except Exception as e:
                continue
        
        return False
    
    def _display_sample_data(self, records):
        """Display sample option chain data."""
        print("   📋 Sample data:")
        for i, record in enumerate(records, 1):
            strike = record.get('strikePrice', 'N/A')
            pe_oi = record.get('PE', {}).get('openInterest', 'N/A')
            ce_oi = record.get('CE', {}).get('openInterest', 'N/A')
            print(f"      {i}. Strike: {strike}, PE OI: {pe_oi}, CE OI: {ce_oi}")
    
    def test_ip_rotation(self):
        """Test IP rotation for NSE access."""
        print("\n🧪 Testing IP Rotation for NSE Access")
        print("=" * 50)
        
        success = self.get_option_chain_with_rotation('NIFTY')
        
        if success:
            print("\n🎉 IP ROTATION SUCCESSFUL!")
            print("✅ Real NSE data collection is now working!")
            return True
        else:
            print("\n⚠️ IP rotation blocked - exploring alternatives...")
            self._explore_alternatives()
            return False
    
    def _explore_alternatives(self):
        """Explore alternative access methods."""
        print("\n🔄 Exploring alternative access methods...")
        
        alternatives = [
            "1. Cloud function rotation (AWS Lambda)",
            "2. Residential proxy services (Bright Data)",
            "3. VPN with Indian IP rotation",
            "4. Paid data feeds (Alpha Vantage)",
            "5. Continue with enhanced mock data"
        ]
        
        for alt in alternatives:
            print(f"   • {alt}")

if __name__ == "__main__":
    print("🚀 NSE IP Rotation Scraper Test")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    scraper = IPRotationNSEScraper()
    success = scraper.test_ip_rotation()
    
    if not success:
        print("\n💡 Recommendation: Implement paid data feeds for reliable access")
