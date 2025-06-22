
import requests
import datetime

def save_lead(user_id, message):
    timestamp = datetime.datetime.now().isoformat()
    # Replace with actual Google Sheets API call
    print(f"Saving lead: {user_id}, {message}, {timestamp}")
