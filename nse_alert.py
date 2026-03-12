import requests
import json
import time
from fake_useragent import UserAgent
from datetime import datetime

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1471799990631534734/LTlPpa_bwzo2MhyM0VkEbjisgcxz0QfsxPIHIuEL9lz1wB1Us6XmY74bq0kAMT9qYywD"
# ---------------------

def get_nse_data():
    ua = UserAgent()
    
    # NSE requires very specific headers to prove you are a human
    headers = {
        'User-Agent': ua.random,
        'Referer': 'https://www.nseindia.com/',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

    session = requests.Session()
    session.headers.update(headers)

    try:
        print("1. Visiting Homepage to get cookies...")
        # We must visit the homepage first to get the necessary cookies
        home_resp = session.get("https://www.nseindia.com", timeout=20)
        
        if home_resp.status_code != 200:
            print(f"Failed to load homepage. Status: {home_resp.status_code}")
            return None
            
        # IMPORTANT: Wait a bit to look like a human
        print("2. Waiting 3 seconds...")
        time.sleep(3)

        print("3. Fetching Market Data...")
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20TOTAL%20MARKET"
        
        # Update headers specifically for the API call (mimicking XHR)
        session.headers.update({
            'Referer': 'https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%20TOTAL%20MARKET',
            'X-Requested-With': 'XMLHttpRequest'
        })
        
        response = session.get(url, timeout=20)
        
        if response.status_code == 200:
            return response.json()['data']
        else:
            print(f"Blocked by NSE. Status Code: {response.status_code}")
            # print(response.text) # Uncomment this if you want to see the error page HTML
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def send_discord_message(losers):
    if not losers:
        return

    message_content = f"**📉 Top 5 NIFTY TOTAL MARKET Losers**\n"
    message_content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for stock in losers:
        symbol = stock['symbol']
        # Handle cases where price might be missing or None
        price = stock.get('lastPrice', 0)
        pChange = stock.get('pChange', 0)
        
        message_content += f"🔴 **{symbol}**: ₹{price} ({pChange}%)\n"

    payload = {"content": message_content}
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print("Discord message sent!")
    except Exception as e:
        print(f"Failed to send Discord message: {e}")

def main():
    stocks = get_nse_data()
    
    if stocks:
        # Sort by pChange (ascending) to get biggest losers
        # Filter out stocks that might have pChange as None
        valid_stocks = [s for s in stocks if s.get('pChange') is not None]
        sorted_stocks = sorted(valid_stocks, key=lambda x: x['pChange'])
        
        # Get Top 5
        top_5_losers = sorted_stocks[:5]
        send_discord_message(top_5_losers)
    else:
        print("No data received from NSE.")

if __name__ == "__main__":
    main()
