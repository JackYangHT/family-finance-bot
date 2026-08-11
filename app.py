import os
import requests
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

app = FastAPI()

# 1. Load Environment Variables from Render
LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY", "")

# 2. Google Sheets Authentication
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
try:
    # This looks for the secret credentials.json file you add in Render
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
except Exception as e:
    print("Google Sheets auth failed. Check credentials.json on Render.")
    gc = None

# 3. Get LINE Access Token
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

# 4. Setup DeepInfra (Hermes 3 Model)
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
    
    # Custom Hermes System Prompt for Jack and Lee
    system_prompt = """
    You are the Yang family finance bot serving Jack (English) and Lee (Thai). 
    Categorize the user's expense into a short summary. 
    Format: [Category]: [Amount] at [Vendor]
    Example: '7/11 250' -> 'Grocery: NT$250 at 7-Eleven'
    Example: 'Safe 1000' -> 'Safety Box Withdrawal: NT$1000'
    Keep the reply strictly to the categorization.
    """
    
    chat_completion = di_client.chat.completions.create(
        model="NousResearch/Hermes-3-Llama-3.1-8B",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    
    ai_reply = chat_completion.choices[0].message.content
    
    # 5. Write to Google Sheets
    status_msg = ai_reply
    if gc:
        try:
            # Using your specific Spreadsheet ID
            sheet = gc.open_by_key("1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY").sheet1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sheet.append_row([timestamp, user_message, ai_reply])
            status_msg = f"✅ Logged to Google Sheets:\n{ai_reply}"
        except Exception as e:
            status_msg = f"⚠️ Sheet permission error. Did you share the sheet with the bot email?\n\nAI Reply: {ai_reply}"
    else:
        status_msg = f"⚠️ credentials.json not found in Render.\n\nAI Reply: {ai_reply}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=status_msg))
