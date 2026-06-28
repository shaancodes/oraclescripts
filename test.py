import csv
import io
import requests
from datetime import datetime

# --- CONFIGURATION ---
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1471799990631534734/LTlPpa_bwzo2MhyM0VkEbjisgcxz0QfsxPIHIuEL9lz1wB1Us6XmY74bq0kAMT9qYywD"

# GitHub Repo details containing the daily CSVs
REPO_OWNER = "tilak999"
REPO_NAME = "NSE-Data-bank"

# We only track specific equity series to avoid spam from expiring bonds (GS, N1, etc.)
EQUITY_SERIES = {'EQ', 'SM'}

# Threshold to flag discrepancies between yesterday's and today's price.
# E.g., a value of 0.10 means flag if today's PREV_CLOSE is off by more than 10% from yesterday's CLOSE_PRICE
PRICE_DISCREPANCY_THRESHOLD = 0.25
# ---------------------

def get_latest_two_csv_urls():
    """Fetches the latest two CSV file raw URLs from the NSE-Data-bank GitHub repo."""
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/git/trees/main?recursive=1"
    response = requests.get(api_url)
    
    if response.status_code != 200:
        print(f"Failed to fetch repo structure. Status {response.status_code}")
        return None, None, None, None
        
    tree = response.json().get('tree', [])
    
    # Filter for data/sec_bhavdata_full_ files
    csv_paths = [f['path'] for f in tree if f['path'].startswith('data/sec_bhavdata_full_') and f['path'].endswith('.csv')]
    
    parsed_files = []
    for path in csv_paths:
        # Expected format: data/sec_bhavdata_full_DDMMYYYY.csv
        filename = path.split('/')[-1]
        date_str = filename.replace('sec_bhavdata_full_', '').replace('.csv', '')
        try:
            date_obj = datetime.strptime(date_str, '%d%m%Y')
            parsed_files.append((date_obj, path))
        except ValueError:
            pass # Skip files that don't match the date format
            
    # Sort descending so the most recent dates are first
    parsed_files.sort(key=lambda x: x[0], reverse=True)
    
    if len(parsed_files) < 2:
        print("Not enough CSV files found in the repository.")
        return None, None, None, None
        
    # Get the top two newest files (today and yesterday relative to the available data)
    today_path = parsed_files[0][1]
    yesterday_path = parsed_files[1][1]
    
    base_raw_url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/"
    
    today_url = base_raw_url + today_path
    yesterday_url = base_raw_url + yesterday_path
    
    date_today = parsed_files[0][0].strftime('%Y-%m-%d')
    date_yesterday = parsed_files[1][0].strftime('%Y-%m-%d')
    
    return yesterday_url, date_yesterday, today_url, date_today

def download_and_parse_csv(url):
    """Downloads a CSV file from a URL, parses it, and returns a dictionary of records keyed by SYMBOL."""
    print(f"Downloading: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {url}. Status Code: {response.status_code}")
        return {}
        
    content = response.text
    lines = content.split('\n')
    if not lines:
        return {}
    
    # Strip spaces from header names to handle " SERIES" vs "SERIES"
    headers = [h.strip() for h in lines[0].split(',')]
    lines[0] = ','.join(headers)
    new_content = '\n'.join(lines)
    
    reader = csv.DictReader(io.StringIO(new_content))
    data = {}
    
    for row in reader:
        symbol = row.get('SYMBOL', '').strip()
        series = row.get('SERIES', '').strip()
        
        # In this updated script, we only keep EQ and SM
        if symbol and series in EQUITY_SERIES:
            if symbol not in data:
                data[symbol] = {}
            # We save the row dictionary for this specific series
            data[symbol][series] = row
            
    return data

def compare_data(yesterday_data, today_data):
    """Compares yesterday's and today's data to flag series transitions and price discrepancies."""
    alerts = []
    
    for symbol, today_series_dict in today_data.items():
        if symbol not in yesterday_data:
            # We no longer log completely new additions as requested ("also new listings into eq and deletions in equity")
            continue
            
        yesterday_series_dict = yesterday_data[symbol]
        
        today_series_set = set(today_series_dict.keys())
        yesterday_series_set = set(yesterday_series_dict.keys())
        
        added_series = today_series_set - yesterday_series_set
        removed_series = yesterday_series_set - today_series_set
        
        # Check transitions prioritizing EQ <-> SM
        if 'EQ' in removed_series and 'SM' in added_series:
            alerts.append(f"⚠️ **{symbol}**: Moved from **EQ** to **SM**.")
            removed_series.discard('EQ')
            added_series.discard('SM')
        elif 'SM' in removed_series and 'EQ' in added_series:
            alerts.append(f"✅ **{symbol}**: Moved from **SM** to **EQ**.")
            removed_series.discard('SM')
            added_series.discard('EQ')
            
        # We don't report other individual additions/deletions as per user request
        
        # Check for price discrepancies
        for series in today_series_set:
            if series in yesterday_series_dict:
                try:
                    yesterday_close = float(yesterday_series_dict[series].get('CLOSE_PRICE', 0))
                    today_prev_close = float(today_series_dict[series].get('PREV_CLOSE', 0))
                    
                    if yesterday_close > 0:
                        diff = abs(today_prev_close - yesterday_close)
                        pct_change = diff / yesterday_close
                        
                        if pct_change >= PRICE_DISCREPANCY_THRESHOLD:
                            # Potential corporate action like split, bonus, dividend, right issue
                            alerts.append(
                                f"🚨 **{symbol} ({series}) Corporate Action Alert**: "
                                f"Yesterday's Close: **₹{yesterday_close}**, "
                                f"Today's Prev Close Base: **₹{today_prev_close}** "
                                f"(*{pct_change*100:.1f}%* adj)"
                            )
                except ValueError:
                    pass
            
    return alerts

def send_discord_message(alerts, date_yesterday, date_today):
    """Sends the generated alerts to a Discord webhook."""
    if not alerts:
        print("No alerts to send.")
        return

    # Sort alerts so that Corporate action alerts are on top
    alerts.sort(key=lambda x: "Corporate Action" not in x)

    # Discord has a 2000 character limit per message, so we may need to split it
    message_chunks = []
    current_message = f"**📊 Daily Market Alerts**\nComparing: `{date_yesterday}` ➔ `{date_today}`\n\n"
    
    for alert in alerts:
        if len(current_message) + len(alert) + 2 > 1900:
            message_chunks.append(current_message)
            current_message = f"{alert}\n"
        else:
            current_message += f"{alert}\n"
            
    if current_message:
        message_chunks.append(current_message)

    for chunk in message_chunks:
        payload = {"content": chunk}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if response.status_code in [200, 204]:
                print(f"Discord chunk sent successfully! ({len(chunk)} chars)")
            else:
                print(f"Failed to send chunk. Status: {response.status_code}")
        except Exception as e:
            print(f"Error sending Discord message: {e}")

def main():
    print("Fetching the latest two CSV URLs from GitHub...")
    yesterday_url, date_yesterday, today_url, date_today = get_latest_two_csv_urls()
    
    if not yesterday_url or not today_url:
        print("Exiting as we couldn't find the necessary URLs.")
        return
        
    print(f"Data dates: {date_yesterday} -> {date_today}\n")
    
    yesterday_data = download_and_parse_csv(yesterday_url)
    today_data = download_and_parse_csv(today_url)
    
    print("\nComparing data to find alerts...")
    alerts = compare_data(yesterday_data, today_data)
    
    if alerts:
        print(f"Found {len(alerts)} alerts. Sending to Discord...")
        for alert in alerts:
            print(f" - {alert}")
        send_discord_message(alerts, date_yesterday, date_today)
    else:
        print("No changes found today.")

if __name__ == "__main__":
    main()
