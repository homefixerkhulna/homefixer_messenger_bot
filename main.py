import os
import json
import langdetect
from flask import Flask, request
import requests
from utils.sheets import save_lead
from utils.voice import speech_to_text
from config.config import VERIFY_TOKEN, PAGE_ACCESS_TOKEN
from utils.ai_engine import get_ai_response

app = Flask(__name__)

# Load root data and custom replies
with open("root_data.json", "r", encoding="utf-8") as f:
    root_json = json.load(f)

with open("custom_replies.json", "r", encoding="utf-8") as f:
    custom_replies = json.load(f).get("custom_replies", [])

# Track greeted users and processed message IDs
greeted_users = set()
processed_messages = set()

def detect_language(text):
    try:
        lang = langdetect.detect(text)
        return "bn" if lang.startswith("bn") else "en"
    except langdetect.lang_detect_exception.LangDetectException:
        return "en"

def get_greeting(lang="bn"):
    if lang == "bn":
        return (
            "Assalamualaikum. HomeFixerKhulna-te apnake swagotom! "
            "🙋Aponar ek phone-ei jekono somosshar somadhan🤗 "
            "Ami HomeFixerKhulna er ek jon sohokari. "
            "Ami apnake interior design, AC, fridge, electric, "
            "basa o office sthanantor ebong porishkar, plumbing ebong CCTV camera service songkranto jekono tothyo diye sahajjo korte pari. "
            "Bolun, apnake kibhabe sahajjo korte pari?"
        )
    else:
        return (
            "Hello! Welcome to HomeFixerKhulna! "
            "I am your digital assistant. I can help you with information about AC, Fridge, Electric, "
            "Plumbing, and CCTV Camera services. "
            "How can I assist you today?"
        )

def get_reply(user_message):
    lang = detect_language(user_message)
    msg_lower = user_message.lower()

    # 1️⃣ Intent Matching: Check for custom replies (intents).
    # Each item in custom_replies is treated as an intent category.
    for item in custom_replies:
        # 2️⃣ Keyword Matching: If keywords match, provide the specific answer for that intent.
        questions = item.get("question")
        if isinstance(questions, str):
            questions = [questions]
        for q in questions:
            if q.lower() in msg_lower:
                return item.get(f"answer_{lang}", item.get("answer_en"))

    # Check for root JSON keys (another form of intent)
    root_keys = [ "hi","tagline", "page_name", "description_bn", "description_en"]
    for key in root_keys:
        if key in msg_lower:
            if lang == "bn" and key.endswith("_bn"):
                return root_json.get(key)
            elif lang == "en" and key.endswith("_en"):
                return root_json.get(key)
            else:
                return root_json.get(key)

    # 3️⃣ AI Fallback: If no intent is matched, use the AI engine.
    ai_response = get_ai_response(user_message, lang=lang)
    if ai_response and len(ai_response.strip()) > 0:
        return ai_response

    # Default Fallback: If AI also fails, provide a default contact message.
    return (
        "Amader ekjon protinidhir sathe jogajog korun: WhatsApp: https://wa.me/8801711170639 , +8801915200299"
        if lang == "bn"
        else "Please contact our representative on WhatsApp: https://wa.me/8801711170639 , phone: +8801915200299"
    )

@app.route("/", methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route("/", methods=['POST'])
def webhook():
    data = request.json
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
            # Ignore bot echo messages
            if "message" in msg and msg["message"].get("is_echo"):
                continue

            # Skip already processed messages
            message_id = msg.get("message", {}).get("mid")
            if message_id in processed_messages:
                continue
            processed_messages.add(message_id)

            sender_id = msg.get("sender", {}).get("id")
            message = msg.get("message", {})
            user_message = message.get("text", "")

            # Handle audio attachments
            if "attachments" in message:
                attachment = message["attachments"][0]
                if attachment.get("type") == "audio":
                    audio_url = attachment.get("payload", {}).get("url")
                    if audio_url:
                        user_message = speech_to_text(audio_url)

            # Send reply
            if user_message.strip():
                reply = get_reply(user_message)
                save_lead(sender_id, user_message)
                send_message(sender_id, reply)
            else:
                # Only greet once per user
                if sender_id not in greeted_users:
                    send_message(sender_id, get_greeting("bn"))
                    greeted_users.add(sender_id)

    return "OK", 200

def send_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v13.0/me/messages"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}
    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
        print(f"Message sent to {recipient_id}: {message_text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

if __name__ == "__main__":
    from waitress import serve
    port = int(os.environ.get("PORT", 5000))
    serve(app, host="0.0.0.0", port=port)
