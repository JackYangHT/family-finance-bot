import os
import io
import json
import base64
import requests
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage, 
    QuickReply, QuickReplyItem, MessageAction
)
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

app = FastAPI()

# 1. Environment & Auth Setup
LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY", "")
SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
except Exception as e:
    print(f"Google Sheets auth failed: {e}")
    gc = None

def get_channel_access_token(cid, secret):
    url = "https://api.line.me/v2/oauth/accessToken"
    data = {"grant_type": "client_credentials", "client_id": cid, "client_secret": secret}
    res = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return res.json().get("access_token") if res.status_code == 200 else None

ACCESS_TOKEN = get_channel_access_token(LINE_CHANNEL_ID, LINE_CHANNEL_SECRET)
line_bot_api = LineBotApi(ACCESS_TOKEN) if ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET)

di_client = OpenAI(api_key=DEEPINFRA_API_KEY, base_url="https://api.deepinfra.com/v1/openai")

# Quick Reply Button Generator
def get_quick_replies():
    return QuickReply(items=[
        QuickReplyItem(action=MessageAction(label="💰 Salary Slip", text="Upload Salary Slip")),
        QuickReplyItem(action=MessageAction(label="🏠 Petty Cash", text="Category: Petty Cash")),
        QuickReplyItem(action=MessageAction(label="🧍 Personal", text="Category: Personal")),
        QuickReplyItem(action=MessageAction(label="🚨 Urgent", text="Category: Urgent")),
        QuickReplyItem(action=MessageAction(label="📊 Balance", text="Check Balance"))
    ])

@app.get("/")
def home():
    # Auto-run database setup on first deploy
    try:
        import subprocess
        subprocess.run(["python", "setup_database.py"], check=True, capture_output=True)
    except:
        pass  # Setup already ran or will run manually
    return {"status": "Automated ERP Agent Active"}

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# 2. Text Message Handler (Interactive Buttons & Standard Expense Processing)
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = event.source.user_id
    
    # Map LINE user IDs to family members (update after first use)
    FAMILY_MEMBERS = {
        "YOUR_LINE_USER_ID": "Jack",
        "LEE_LINE_USER_ID": "Lee"
    }
    who_spent = FAMILY_MEMBERS.get(user_id, f"Unknown ({user_id})")

    # Command Router for Menu Buttons
    if text == "Upload Salary Slip":
        reply = "📄 Please upload a photo or screenshot of the salary slip now."
        line_bot_api.push_message(user_id, TextSendMessage(text=reply, quick_reply=get_quick_replies()))
        return

    if text == "Check Balance":
        if gc:
            try:
                sh = gc.open_by_key(SPREADSHEET_ID)
                dash = sh.worksheet("Dashboard_Summary")
                vals = dash.get("A1:B9")
                msg = "📊 **YANG FAMILY FINANCIAL DASHBOARD**\n\n"
                for row in vals[2:]:
                    if len(row) >= 2:
                        msg += f"• {row[0]}: TWD {row[1]}\n"
            except Exception as e:
                msg = f"⚠️ Error reading dashboard: {str(e)}"
        else:
            msg = "⚠️ Database connection offline."
        line_bot_api.push_message(user_id, TextSendMessage(text=msg, quick_reply=get_quick_replies()))
        return

    # Categorization Processing via Hermes Model
    system_prompt = """
    Categorize the expenditure message into JSON:
    {"category": "Family Petty Cash"|"Personal"|"Urgent"|"General", "amount": number, "vendor": "string"}
    Output strictly valid JSON.
    """
    try:
        chat = di_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        parsed = json.loads(chat.choices[0].message.content)
        category = parsed.get("category", "General")
        amount = parsed.get("amount", 0)
        vendor = parsed.get("vendor", "N/A")

        if gc:
            sh = gc.open_by_key(SPREADSHEET_ID)
            wks = sh.worksheet("Raw_Expenses")
            wks.append_row([timestamp, who_spent, category, amount, vendor, text])
            reply = f"✅ Logged Expense:\n• Category: {category}\n• Amount: TWD {amount}\n• Note: {vendor}\n• Spent by: {who_spent}"
        else:
            reply = f"⚠️ Config error, parsed: {category} TWD {amount}"
    except Exception as e:
        reply = f"📝 Logged input: '{text}'. Use standard format (e.g., '7/11 250')."

    line_bot_api.push_message(user_id, TextSendMessage(text=reply, quick_reply=get_quick_replies()))

# 3. Vision Handler for Salary Slips & Tax Deduction Processing
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = event.source.user_id
    
    FAMILY_MEMBERS = {
        "YOUR_LINE_USER_ID": "Jack",
        "LEE_LINE_USER_ID": "Lee"
    }
    who_spent = FAMILY_MEMBERS.get(user_id, f"Unknown ({user_id})")
    
    # Download Image from LINE
    try:
        message_content = line_bot_api.get_message_content(event.message.id)
        img_bytes = io.BytesIO()
        for chunk in message_content.iter_content():
            img_bytes.write(chunk)
        base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

        # Taiwan Tax Engine VLM Prompt
        tax_prompt = """
        Extract Taiwan Salary Slip data. Output strictly JSON with these keys:
        {
          "person": "Jack"|"Lee"|"Unknown",
          "gross_pay": number,
          "withholding_tax": number,
          "nhi_premium": number,
          "labor_insurance": number,
          "pension_voluntary_6": number,
          "meal_allowance": number,
          "other_deductions": number,
          "net_pay": number
        }
        """

        response = di_client.chat.completions.create(
            model="Qwen/Qwen2.5-VL-72B-Instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": tax_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        
        raw_json = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
        data = json.loads(raw_json)

        if gc:
            sh = gc.open_by_key(SPREADSHEET_ID)
            wks = sh.worksheet("Raw_Payroll_Tax")
            wks.append_row([
                timestamp,
                data.get("person", "Unknown"),
                data.get("gross_pay", 0),
                data.get("withholding_tax", 0),
                data.get("nhi_premium", 0),
                data.get("labor_insurance", 0),
                data.get("pension_voluntary_6", 0),
                data.get("meal_allowance", 0),
                data.get("other_deductions", 0),
                data.get("net_pay", 0),
                "Pending Refund"
            ])
            reply = (
                f"📄 **Payroll & Tax Slip Logged!**\n"
                f"• Person: {data.get('person', 'Unknown')}\n"
                f"• Gross Pay: TWD {data.get('gross_pay', 0):,}\n"
                f"• Pre-paid Tax (扣繳): TWD {data.get('withholding_tax', 0):,}\n"
                f"• Tax-Free Pension (勞退自提): TWD {data.get('pension_voluntary_6', 0):,}\n"
                f"• Net Deposit: TWD {data.get('net_pay', 0):,}\n\n"
                f"💡 Prepaid tax recorded for next May's tax refund!"
            )
        else:
            reply = "⚠️ Google Sheets not reachable."
    except Exception as e:
        reply = f"⚠️ Vision processing failed: {str(e)}"

    line_bot_api.push_message(user_id, TextSendMessage(text=reply, quick_reply=get_quick_replies()))
