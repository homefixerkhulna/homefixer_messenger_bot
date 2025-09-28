
import requests
import json
from config.config import OPENAI_API_KEY

# Print the start and end of the API key to verify it's loaded
print(f"Loaded OPENAI_API_KEY: {OPENAI_API_KEY[:5]}...{OPENAI_API_KEY[-4:] if len(OPENAI_API_KEY) > 9 else ''}")

def get_ai_response(message, lang='en'):
    # Load custom replies
    with open('custom_replies.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        custom_replies = data.get("custom_replies", [])

    # 🔹 Check for a custom reply
    for reply in custom_replies:
        questions = reply.get("question", [])
        if isinstance(questions, str):
            questions = [questions]
        for q in questions:
            if q.lower() in message.lower():
                return reply.get("answer_bn") if lang == "bn" else reply.get("answer_en")

    # 🔹 If no custom reply, fallback to OpenAI API
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a customer support agent for HomeFixerKhulna. Reply in Bangla if the user writes in Bangla, otherwise in English."
            },
            {
                "role": "user",
                "content": message
            }
        ]
    }

    try:
        print("Attempting to call OpenAI API...")
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        print("OpenAI API call successful.")
        return data['choices'][0]['message']['content'].strip()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during OpenAI API call: {e}")
        if e.response is not None:
            print(f"Error Response Status Code: {e.response.status_code}")
            print(f"Error Response Body: {e.response.text}")
        return (
            "আমাদের একজন প্রতিনিধির সাথে যোগাযোগ করুন: WhatsApp: https://wa.me/8801711170639"
            if lang == "bn"
            else "Please contact our representative on WhatsApp: https://wa.me/8801711170639 or call 01915200299"
        )
