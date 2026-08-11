import os
import requests
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

app = FastAPI()

# 1. Load Environment Variables from Render
LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY", "")

# 2. Get LINE Access Token
def get_channel_access_token(channel_id, channel_secret):
    url = "https://api.line.me/v2/oauth/accessToken"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials", "client_id": channel_id, "client_secret": channel_secret}
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

ACCESS_TOKEN = get_channel_access_token(LINE_CHANNEL_ID, LINE_CHANNEL_SECRET)
line_bot_api = LineBotApi(ACCESS_TOKEN) if ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 3. Setup DeepInfra (Hermes 3 Model)
di_client = OpenAI(
    api_key=DEEPINFRA_API_KEY,
    base_url="https://api.deepinfra.com/v1/openai"
)

@app.get("/")
def home():
    return {"status": "Family Finance Agent is live!"}

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    
    chat_completion = di_client.chat.completions.create(
        model="NousResearch/Hermes-3-Llama-3.1-8B",
        messages=[
            {"role": "system", "content": "You are a helpful family finance assistant for Jack and Lee. Reply briefly."},
            {"role": "user", "content": user_message}
        ]
    )
    
    ai_reply = chat_completion.choices[0].message.content
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=ai_reply))
