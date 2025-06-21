import requests
import json
from config.config import GEMINI_API_KEY

def get_ai_response(message):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=" + GEMINI_API_KEY
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{"text": f"You are a customer support assistant for HomeFixerKhulna. Reply in Bangla or English as needed. User: {message}"}]
        }]
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    try:
        reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return reply
    except:
        return "দুঃখিত, আমি আপনার বার্তাটি বুঝতে পারিনি। অনুগ্রহ করে আবার লিখুন।"
