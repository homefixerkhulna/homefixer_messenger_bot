
from flask import Flask, request
from utils.ai_engine import get_ai_response
from utils.sheets import save_lead
from utils.voice import speech_to_text
from config.config import VERIFY_TOKEN
from utils.greeting import greeting_message

app = Flask(__name__)

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
                if "attachments" in msg["message"]:
                    if "audio" in msg["message"]["attachments"][0]["type"]:
                        audio_url = msg["message"]["attachments"][0]["payload"]["url"]
                        user_message = speech_to_text(audio_url)
                if user_message:
                    reply = get_ai_response(user_message)
                    save_lead(sender_id, user_message)
                    send_message(sender_id, reply)
                else:
                    send_message(sender_id, greeting_message)
    return "OK", 200

def send_message(recipient_id, message_text):
    import requests
    from config.config import PAGE_ACCESS_TOKEN
    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    requests.post(url, json=payload, headers=headers)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
