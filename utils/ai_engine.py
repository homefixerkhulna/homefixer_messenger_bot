
import requests
import json
from config.config import GEMINI_API_KEY

def get_ai_response(message):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    prompt = f"You are a customer support assistant for HomeFixerKhulna. Reply in Bangla or English as needed. User: {message}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "দুঃখিত, আমি আপনার বার্তাটি বুঝতে পারিনি। অনুগ্রহ করে আবার লিখুন।"
