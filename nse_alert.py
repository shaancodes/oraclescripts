import json
import time
from datetime import datetime
from curl_cffi import requests  # <-- The Magic Upgrade

# --- CONFIGURATION ---
# PUT YOUR NEWLY REGENERATED WEBHOOK HERE!
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."
# ---------------------


def get_nse_data():
    # impersonate="chrome120" forces Python to send the exact TLS packet hello of Google Chrome
    session = requests.Session(impersonate="chrome120")

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }

    session.headers.update(headers)

    try:
        print("1. Visiting Homepage to harvest Akamai cookies...")
        home_resp = session.get("https://www.nseindia.com", timeout=15)

        if home_resp.status_code != 200:
            print(
                f"Failed to load homepage. Status: {home_resp.status_code}"
            )
            return None

        print("2. Sleeping 2.5 seconds...")
        time.sleep(2.5)

        print("3. Fetching Market Data...")
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20TOTAL%20MARKET"

        # Update headers to match an AJAX call from the table page
        session.headers.update(
            {
                "Referer": "https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%20TOTAL%20MARKET",
                "X-Requested-With": "XMLHttpRequest",
            }
        )

        response = session.get(url, timeout=15)

        if response.status_code == 200:
            return response.json().get("data", [])
        else:
            print(f"Blocked by NSE. Status Code: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


def send_discord_message(losers):
    if not losers:
        return

    message_content = "**📉 Top 5 NIFTY TOTAL MARKET Losers**\n"
    message_content += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for stock in losers:
        symbol = stock["symbol"]
        price = stock.get("lastPrice", 0)
        pChange = stock.get("pChange", 0)

        message_content += f"🔴 **{symbol}**: ₹{price} ({pChange}%)\n"

    payload = {"content": message_content}

    try:
        # Standard requests is fine for hitting Discord, just don't mix up the sessions
        import requests as std_requests

        std_requests.post(DISCORD_WEBHOOK_URL, json=payload)
        print("Discord message sent!")
    except Exception as e:
        print(f"Failed to send Discord message: {e}")


def main():
    stocks = get_nse_data()

    if stocks:
        valid_stocks = []
        for s in stocks:
            # SAFETY FIX: The first item returned in an NSE JSON array is the Index itself!
            # If we don't skip it, "NIFTY TOTAL MARKET" will show up as a loser stock.
            if (
                s.get("pChange") is not None
                and s.get("symbol") != "NIFTY TOTAL MARKET"
            ):
                valid_stocks.append(s)

        sorted_stocks = sorted(valid_stocks, key=lambda x: x["pChange"])

        top_5_losers = sorted_stocks[:5]
        send_discord_message(top_5_losers)
    else:
        print("No data received from NSE.")


if __name__ == "__main__":
    main()
