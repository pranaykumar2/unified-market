"""
Test MoneyControl API endpoints to debug issues
"""
import httpx
import json

# API URLs
MAJOR_INDICES_URL = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=mi"
INDIAN_INDICES_URL = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=ii"
COMMODITIES_URL = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=co"
CURRENCIES_URL = "https://api.moneycontrol.com/mcapi/v1/premarket/get-global-marketdata?section=cu"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://www.moneycontrol.com/",
    "Origin": "https://www.moneycontrol.com",
    "DNT": "1",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "sec-gpc": "1"
}

def test_endpoint(url, name):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        # Remove encoding headers - let httpx handle it automatically
        test_headers = headers.copy()
        test_headers.pop('Accept-Encoding', None)
        
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get(url, headers=test_headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type')}")
            print(f"Content-Encoding: {response.headers.get('content-encoding')}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\n✅ JSON parsed successfully")
                    print(f"Keys: {list(data.keys())}")
                    if 'data' in data:
                        print(f"Data items: {len(data.get('data', []))}")
                        if data.get('data'):
                            print(f"First item keys: {list(data['data'][0].keys())}")
                            print(f"Sample: {data['data'][0].get('dispName', 'N/A')} - {data['data'][0].get('value', 'N/A')}")
                except Exception as e:
                    print(f"\n❌ JSON parse error: {e}")
                    print(f"Content bytes (first 50): {response.content[:50]}")
            else:
                print(f"\n❌ Error: {response.status_code}")
                
    except Exception as e:
        print(f"\n❌ Request failed: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("\n🧪 Testing MoneyControl API Endpoints")
    print("="*60)
    
    test_endpoint(MAJOR_INDICES_URL, "Major Indices")
    test_endpoint(INDIAN_INDICES_URL, "Indian Indices")
    test_endpoint(COMMODITIES_URL, "Commodities")
    test_endpoint(CURRENCIES_URL, "Currencies")
    
    print(f"\n{'='*60}")
    print("✅ Testing complete")
    print(f"{'='*60}\n")
