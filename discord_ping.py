import requests
from datetime import datetime

# --- CONFIGURATION ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1471799990631534734/LTlPpa_bwzo2MhyM0VkEbjisgcxz0QfsxPIHIuEL9lz1wB1Us6XmY74bq0kAMT9qYywD"
MESSAGE = "Hi! Server is up. Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# ---------------------

data = {
    "content": MESSAGE
}

try:
    response = requests.post(WEBHOOK_URL, json=data)
    response.raise_for_status()
    print("Message sent successfully.")
except Exception as e:
    print(f"Error sending message: {e}")
