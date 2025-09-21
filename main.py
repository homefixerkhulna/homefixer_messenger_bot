import json
import langdetect
from openai import OpenAI

# OpenAI client init
client = OpenAI()

# custom replies লোড করা
with open("custom_replies.json", "r", encoding="utf-8") as f:
    custom_replies = json.load(f)

# ভাষা detect
def detect_language(text):
    try:
        lang = langdetect.detect(text)
        if lang.startswith("bn"):
            return "bn"
        else:
            return "en"
    except:
        return "en"

# AI Response
def get_ai_response(user_message, lang="en"):
    if lang == "bn":
        system_prompt = (
            "আপনি একজন কাস্টমার সার্ভিস অ্যাসিস্ট্যান্ট। "
            "সব প্রশ্নের উত্তর বাংলায় দিন। সংক্ষেপে, ভদ্রভাবে ও পরিষ্কারভাবে লিখুন। "
            "HomeFixer Khulna এর সার্ভিসের সাথে সম্পর্কিত উত্তর দিন।"
        )
    else:
        system_prompt = (
            "You are a helpful customer service assistant. "
            "Always reply in English. Keep answers short, polite and clear. "
            "Focus on HomeFixer Khulna services."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # lightweight, faster
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("AI error:", e)
        return None

# Main reply ফাংশন
def get_reply(user_message):
    lang = detect_language(user_message)

    # Step 1: custom replies check
    for item in custom_replies["replies"]:
        if item["question"].lower() in user_message.lower():
            return item["answer_bn"] if lang == "bn" else item["answer_en"]

    # Step 2: AI response
    ai_response = get_ai_response(user_message, lang=lang)

    if ai_response and len(ai_response.strip()) > 5:
        return ai_response

    # Step 3: fallback default reply
    if lang == "bn":
        return "আমাদের একজন প্রতিনিধি সাথে যোগাযোগ করুন: WhatsApp: https://wa.me/8801711170639"
    else:
        return "Please contact our representative on WhatsApp: https://wa.me/8801711170639"
