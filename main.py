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

# Load custom replies
with open("custom_replies.json", "r", encoding="utf-8") as f:
    custom_replies = json.load(f)

# Keep track of users already greeted
greeted_users = set()
# Keep track of processed message IDs to avoid duplicates
processed_messages = set()

def detect_language(text):
    """Detect Bengali or English"""
    try:
        lang = langdetect.detect(text)
        return "bn" if lang.startswith("bn") else "en"
    except langdetect.lang_detect_exception.LangDetectException:
        return "en"

def get_greeting(lang="bn"):
    if lang == "bn":
        return (
            "আসসালামু আলাইকুম। HomeFixerKhulna-তে আপনাকে স্বাগতম! "
            "🙋আপনার এক ফোনেই যেকোনো সমস্যার সমাধান🤗 "
            "আমি HomeFixerKhulna এর এক জন সহকারী। আমি আপনাকে ইন্টেরিয়রডিজাইন, এসি, ফ্রিজ, ইলেকট্রিক, "
            "বাসা ও অফিস স্থানান্তর এবং পরিস্কার, "
            "প্লাম্বিং এবং সিসিটিভি ক্যামেরা সার্ভিস সংক্রান্ত যেকোনো তথ্য দিয়ে সাহায্য করতে পারি। "
            "বলুন, আপনাকে কীভাবে সাহায্য করতে পারি?"
        )
    else:
        return (
            "Hello! Welcome to HomeFixerKhulna! "
            "I am your digital assistant. I can help you with information about AC, Fridge, Electric, "
            "Plumbing, and CCTV Camera services. "
            "How can I assist you today?"
        )

def get_reply(user_message):
    """Custom reply -> AI -> fallback"""
    lang = detect_language(user_message)

    # 1️⃣ Custom replies
    for item in custom_replies.get("custom_replies", []):
        q = item.get("question", [])
        if isinstance(q, str):
            q = [q]  # একটাও যদি string হয়, list বানিয়ে নিলাম
        for keyword in q:
            if keyword.lower() in user_message.lower():
                return item.get(f"answer_{lang}", item.get("answer_en"))

    # 2️⃣ AI response
    ai_response = get_ai_response(user_message, lang=lang)
    if ai_response and len(ai_response.strip()) > 5:
        return ai_response

    # 3️⃣ Fallback
    return (
        "আমাদের একজন প্রতিনিধি সাথে যোগাযোগ করুন: WhatsApp: https://wa.me/8801711170639 , +8801915200299"
        if lang == "bn"
        else "Please contact our representative on WhatsApp: https://wa.me/8801711170639 , phone: +8801915200299"
    )

@app.route("/", methods=["GET"])
def verify():
    """Webhook verification"""
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route("/", methods=["POST"])
def webhook():
    """Handle incoming messages"""
    data = request.json
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
            # Ignore messages sent by the bot itself
            if "message" in msg and msg["message"].get("is_echo"):
                continue

            message_id = msg["message"].get("mid") if "message" in msg else None
            sender_id = msg.get("sender", {}).get("id")
            message = msg.get("message", {})
            user_message = message.get("text", "")

            # 🚫 Prevent duplicate responses
            if message_id and message_id in processed_messages:
                print(f"Duplicate message skipped: {message_id}")
                continue
            if message_id:
                processed_messages.add(message_id)

            # Handle audio attachments
            if "attachments" in message:
                attachment = message["attachments"][0]
                if attachment.get("type") == "audio":
                    audio_url = attachment.get("payload", {}).get("url")
                    if audio_url:
                        user_message = speech_to_text(audio_url)

            # Reply logic
            if user_message:
                reply = get_reply(user_message)
                save_lead(sender_id, user_message)
                send_message(sender_id, reply)
            else:
                # Only greet once per user
                if sender_id not in greeted_users:
                    lang = "bn"
                    send_message(sender_id, get_greeting(lang))
                    greeted_users.add(sender_id)

    return "OK", 200

def send_message(recipient_id, message_text):
    """Send message via Facebook Messenger API"""
    url = f"https://graph.facebook.com/v13.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
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
