import test
import random

yesterday_data = {
    "INFY": {"EQ": {"CLOSE_PRICE": 1500.0, "PREV_CLOSE": 1490.0}},
    "TCS": {"EQ": {"CLOSE_PRICE": 3500.0, "PREV_CLOSE": 3480.0}},
    "WIPRO": {"EQ": {"CLOSE_PRICE": 400.0, "PREV_CLOSE": 395.0}},
    "ZOMATO": {"SM": {"CLOSE_PRICE": 150.0, "PREV_CLOSE": 145.0}},
}

today_data = {
    # 1. Price jump => Corporate action
    "INFY": {"EQ": {"PREV_CLOSE": 1200.0}},   # 20% drop from y_close (Dividend/Split)
    "TCS": {"EQ": {"PREV_CLOSE": 3500.0}},    # No change
    # 2. Transition EQ -> SM
    "WIPRO": {"SM": {"PREV_CLOSE": 400.0}},   
    # 3. Transition SM -> EQ
    "ZOMATO": {"EQ": {"PREV_CLOSE": 150.0}},
}

alerts = test.compare_data(yesterday_data, today_data)
test.send_discord_message(alerts, "2026-03-12", "2026-03-13")
print(alerts)
