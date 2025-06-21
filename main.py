from flask import Flask, request
import requests
from config import PAGE_ACCESS_TOKEN, VERIFY_TOKEN
from .ai_engine import get_ai_response

app = Flask(__name__)
FB_URL = 'https://graph.facebook.com/v13.0/me/messages'

@app.route('/', methods=['GET'])
def verify():
    if request.args.get('hub.mode') == 'subscribe' and request.args.get('hub.verify_token') == VERIFY_TOKEN:
        return request.args.get('hub.challenge'), 200
    return 'Unauthorized', 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get('object') == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message'].get('text')
                    if message_text:
                        reply = get_ai_response(message_text)
                        send_message(sender_id, reply)
    return 'ok', 200

def send_message(recipient_id, message_text):
    payload = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text}
    }
    auth = {'access_token': PAGE_ACCESS_TOKEN}
    requests.post(FB_URL, params=auth, json=payload)

if __name__ == '__main__':
    app.run()
