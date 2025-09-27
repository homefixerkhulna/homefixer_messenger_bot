
import requests
import json
from config.config import GEMINI_API_KEY

def get_ai_response(message, lang='en'):
    # Load custom replies
    with open('custom_replies.json', 'r', encoding='utf-8') as f:
        custom_replies = json.load(f)['custom_replies']

    # Check for a custom reply
    for reply in custom_replies:
        if reply['question'].lower() in message.lower():
            return reply['answer_bn'] if lang == 'bn' else reply['answer_en']

    # If no custom reply, use Gemini API
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
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return (
            "আমাদের একজন প্রতিনিধি সাথে যোগাযোগ করুন: WhatsApp: https://wa.me/8801711170639"
            if lang == "bn"
            else "Please contact our representative on WhatsApp: https://wa.me/8801711170639 call 01915200299"
        )
