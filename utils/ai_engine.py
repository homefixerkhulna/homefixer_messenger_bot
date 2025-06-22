
import requests
import json
from config.config import GEMINI_API_KEY

def get_ai_response(message):
    url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"You are a customer support agent for HomeFixerKhulna. Reply in Bangla or English as needed. User: {message}"}
                ]
            }
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "দুঃখিত, আমি আপনার বার্তাটি বুঝতে পারিনি। অনুগ্রহ করে আবার লিখুন।"
