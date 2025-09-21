import json
import os
import langdetect
from openai import OpenAI
from flask import Flask, request
import requests

from utils.sheets import save_lead
from utils.voice import speech_to_text
from utils.greeting import greeting_message
from config.config import VERIFY_TOKEN, PAGE_ACCESS_TOKEN

app = Flask(__name__)

# OpenAI client init
# Make sure to set the OPENAI_API_KEY environment variable
client = OpenAI()

# Load custom replies from JSON file
with open("custom_replies.json", "r", encoding="utf-8") as f:
    custom_replies = json.load(f)

def detect_language(text):
    """Detects if the text is primarily Bengali or English."""
    try:
        lang = langdetect.detect(text)
        return "bn" if lang.startswith("bn") else "en"
    except langdetect.lang_detect_exception.LangDetectException:
        return "en"

def get_ai_response(user_message, lang="en"):
    """Generates a response using the OpenAI API based on the detected language."""
    system_prompt = (
        "আপনি একজন কাস্টমার সার্ভিস অ্যাসিস্ট্যান্ট। সব প্রশ্নের উত্তর বাংলায় দিন। "
        "সংক্ষেপে, ভদ্রভাবে ও পরিষ্কারভাবে লিখুন। HomeFixer Khulna এর সার্ভিসের সাথে সম্পর্কিত উত্তর দিন।"
    ) if lang == "bn" else (
        "You are a helpful customer service assistant. Always reply in English. "
        "Keep answers short, polite and clear. Focus on HomeFixer Khulna services."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI error: {e}")
        return None

def get_reply(user_message):
    """Determines the final reply by checking custom replies, then AI, then a fallback."""
    lang = detect_language(user_message)

    # Step 1: Check for a keyword-based custom reply
    for item in custom_replies.get("replies", []):
        if item.get("question", "").lower() in user_message.lower():
            return item.get(f"answer_{lang}", item.get("answer_en"))

    # Step 2: Try to get a response from the AI
    ai_response = get_ai_response(user_message, lang=lang)
    if ai_response and len(ai_response.strip()) > 5:
        return ai_response

    # Step 3: Fallback to a default message
    return (
        "আমাদের একজন প্রতিনিধি সাথে যোগাযোগ করুন: WhatsApp: https://wa.me/8801711170639"
        if lang == "bn"
        else "Please contact our representative on WhatsApp: https://wa.me/8801711170639"
    )

@app.route("/", methods=["GET"])
def verify():
    """Verifies the webhook subscription."""
    if (request.args.get("hub.mode") == "subscribe" and
            request.args.get("hub.verify_token") == VERIFY_TOKEN):
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route("/", methods=["POST"])
def webhook():
    """Handles incoming messages from Facebook Messenger."""
    data = request.json
    for entry in data.get("entry", []):
        for msg in entry.get("messaging", []):
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

            if user_message:
                reply = get_reply(user_message)
                save_lead(sender_id, user_message)
                send_message(sender_id, reply)
            else:
                send_message(sender_id, greeting_message)

    return "OK", 200

def send_message(recipient_id, message_text):
    """Sends a message to a user via the Facebook Messenger API."""
    url = "https://graph.facebook.com/v13.0/me/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    headers = {"Content-Type": "application/json"}
    params = {"access_token": PAGE_ACCESS_TOKEN}

    try:
        response = requests.post(url, json=payload, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Failed to send message: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
