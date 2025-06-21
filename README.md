# HomeFixerKhulna Messenger Bot (Secure)

A customer support chatbot for HomeFixerKhulna using Gemini API and Facebook Messenger.

## Secure Setup

1. All credentials are moved to `.config/config.py`
2. `.gitignore` should include `.config/config.py`
3. Deploy on Render.com with Environment Variables (RECOMMENDED)

## Deployment Steps:

1. Push this repo to GitHub
2. Create a Web Service on Render.com
3. Set Environment Variables manually instead of using `.config/config.py`:
   - VERIFY_TOKEN
   - PAGE_ACCESS_TOKEN
   - GEMINI_API_KEY
