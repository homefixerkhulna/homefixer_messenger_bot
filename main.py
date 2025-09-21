import json
import os
from difflib import get_close_matches
from flask import Flask, request, jsonify
import requests

from utils.ai_engine import get_ai_response
from utils.sheets import save_lead
from utils.voice import speech_to_text
from utils.greeting import greeting_message
from config.config import VERIFY_TOKEN, PAGE_ACCESS_TOKEN

app = Flask(__name__)

# --- Load custom replies from JSON file ---
with open("custom_replies.json", "r", encoding="utf-8") as f:
    CUSTOM_REPLIES = json.load(f)


def find_custom_reply(user_message):
    user_message = user_message.lower().strip()

    # Exact match
    if user_message in CUSTOM_REPLIES:
        return CUSTOM_REPLIES[user_message]

    # Fuzzy match (similar word)
    matches = get_close_matches(user_message, CUSTOM_REPLIES.keys(), n=1, cutoff=0.7)
    if matches:
        return CUSTOM_REPLIES[matches[0]]

    return None


@app.route("/", methods=["GET"])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403


@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
            sender_id = msg["sender"]["id"]

            if "message" in msg:
                user_message = msg["message"].get("text", "")

                # Handle audio input
                if "attachments" in msg["message"]:
                    if msg["message"]["attachments"][0]["type"] == "audio":
                        audio_url = msg["message"]["attachments"][0]["payload"]["url"]
                        user_message = speech_to_text(audio_url)

                if user_message:
                    # ✅ First check custom replies
                    custom_reply = find_custom_reply(user_message)

                    if custom_reply:
                        reply = custom_reply
                    else:
                        reply = get_ai_response(user_message)

                    save_lead(sender_id, user_message)
                    send_message(sender_id, reply)
                else:
                    send_message(sender_id, greeting_message)

    return "OK", 200


def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v13.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}

    response = requests.post(url, json=payload, headers=headers, params=params)
    if response.status_code != 200:
        print("Failed to send message:", response.text)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
