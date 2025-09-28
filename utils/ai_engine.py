import requests
import json
from config.config import GEMINI_API_KEY

def get_ai_response(message, lang='en'):
    # Load custom replies
    with open('custom_replies.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        custom_replies = data.get("custom_replies", [])

    # 🔹 Check for a custom reply
    for reply in custom_replies:
        questions = reply.get("question", [])

        # Convert to list if it's a single string
        if isinstance(questions, str):
            questions = [questions]

        for q in questions:
            if q.lower() in message.lower():
                return reply.get("answer_bn") if lang == "bn" else reply.get("answer_en")

    # 🔹 If no custom reply, fallback to Gemini API
    url = (
        "https://generativelanguage.googleapis.com/v1/models/"
        "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
    )
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"You are a customer support agent for HomeFixerKhulna. "
                                f"Reply in Bangla if the user writes in Bangla, otherwise in English. "
                                f"User: {message}"
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return (
            data.get("candidates", [])[0]
            .get("content", {})
            .get("parts", [])[0]
            .get("text", "No response")
        )
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return (
            "আমাদের একজন প্রতিনিধির সাথে যোগাযোগ করুন: WhatsApp: https://wa.me/8801711170639"
            if lang == "bn"
            else "Please contact our representative on WhatsApp: https://wa.me/8801711170639 or call 01915200299"
        )
