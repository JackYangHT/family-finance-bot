"""
Yang Family Financial & Tax Agent - LINE Bot
Supports: jack.yang (English), prapa.yang (Thai)
Database: 7-sheet Google Sheets structure for proper accounting
"""
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
    QuickReply, QuickReplyButton, MessageAction
)
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials

app = FastAPI()

# =============================================================================
# 1. Environment & Auth Setup
# =============================================================================
LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID", "")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY", "")
SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"

# Google Sheets Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
try:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    print("✅ Google Sheets connected")
except Exception as e:
    print(f"⚠️ Google Sheets auth failed: {e}")
    gc = None
    sh = None

# LINE Auth
def get_channel_access_token(cid, secret):
    url = "https://api.line.me/v2/oauth/accessToken"
    data = {"grant_type": "client_credentials", "client_id": cid, "client_secret": secret}
    res = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return res.json().get("access_token") if res.status_code == 200 else None

ACCESS_TOKEN = get_channel_access_token(LINE_CHANNEL_ID, LINE_CHANNEL_SECRET)
line_bot_api = LineBotApi(ACCESS_TOKEN) if ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# DeepInfra AI Client
di_client = OpenAI(api_key=DEEPINFRA_API_KEY, base_url="https://api.deepinfra.com/v1/openai")

# =============================================================================
# 2. Helper Functions
# =============================================================================

# Bilingual Quick Reply Buttons
def get_quick_replies(user_name="jack.yang"):
    if user_name == "prapa.yang":
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="💰 สลิปเงินเดือน", text="Upload Salary Slip")),
            QuickReplyButton(action=MessageAction(label="🏠 ค่าใช้จ่ายครอบครัว", text="Category: Petty Cash")),
            QuickReplyButton(action=MessageAction(label="🧍 ส่วนตัว", text="Category: Personal")),
            QuickReplyButton(action=MessageAction(label="🚨 เร่งด่วน", text="Category: Urgent")),
            QuickReplyButton(action=MessageAction(label="📊 ยอดคงเหลือ", text="Check Balance"))
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="💰 Salary Slip", text="Upload Salary Slip")),
            QuickReplyButton(action=MessageAction(label="🏠 Petty Cash", text="Category: Petty Cash")),
            QuickReplyButton(action=MessageAction(label="🧍 Personal", text="Category: Personal")),
            QuickReplyButton(action=MessageAction(label="🚨 Urgent", text="Category: Urgent")),
            QuickReplyButton(action=MessageAction(label="📊 Balance", text="Check Balance"))
        ])

# Log chat message to Chat_Logs sheet
def log_chat(user_id, user_name, msg_type, raw_msg, ai_response, action, status):
    if gc:
        try:
            chat_sheet = sh.worksheet("Chat_Logs")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            chat_sheet.append_row([timestamp, user_id, user_name, msg_type, raw_msg, ai_response, action, status])
        except Exception as e:
            print(f"⚠️ Chat log failed: {e}")

# =============================================================================
# 3. Health Check & Database Setup
# =============================================================================
@app.get("/")
def home():
    try:
        import subprocess
        subprocess.run(["python", "setup_database.py"], check=True, capture_output=True)
    except:
        pass
    return {"status": "Yang Family Finance Agent Active", "sheets": "7 tabs configured"}

@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return "OK"

# =============================================================================
# 4. Text Message Handler (Expenses & Commands)
# =============================================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Handle both 1-on-1 chats and group chats
    if hasattr(event.source, 'user_id') and event.source.user_id:
        # 1-on-1 chat or user in group
        user_id = event.source.user_id
    else:
        # Group chat without user context - use group ID as fallback
        user_id = event.source.group_id if hasattr(event.source, 'group_id') else "unknown"
    
    # Determine user name from prefix or fallback
    who_spent = "jack.yang"  # Default
    if text.startswith("jack.yang"):
        who_spent = "jack.yang"
        text = text.replace("jack.yang", "", 1).strip()
    elif text.startswith("prapa.yang"):
        who_spent = "prapa.yang"
        text = text.replace("prapa.yang", "", 1).strip()
    else:
        # Try to map LINE user IDs to names (update with real IDs)
        FAMILY_MEMBERS = {
            "YOUR_LINE_USER_ID": "jack.yang",
            "LEE_LINE_USER_ID": "prapa.yang"
        }
        who_spent = FAMILY_MEMBERS.get(user_id, "jack.yang")

    # Command: Upload Salary Slip
    if text == "Upload Salary Slip":
        reply = "📄 Please upload a photo or screenshot of the salary slip now."
        if who_spent == "prapa.yang":
            reply = "📄 กรุณาอัปโหลดรูปสลิปเงินเดือนตอนนี้"
        line_bot_api.push_message(user_id, TextSendMessage(text=reply, quick_reply=get_quick_replies(who_spent)))
        log_chat(user_id, who_spent, "text", text, "", "Awaiting salary slip", "success")
        return

    # Command: Check Balance
    if text == "Check Balance":
        if gc:
            try:
                dash = sh.worksheet("Dashboard_Summary")
                vals = dash.get("A1:B19")
                if who_spent == "prapa.yang":
                    msg = "📊 **ยอดคงเหลือครอบครัวหยาง**\n\n"
                    for row in vals[2:]:
                        if len(row) >= 2 and row[0]:
                            msg += f"• {row[0]}: {row[1]} บาท\n"
                else:
                    msg = "📊 **YANG FAMILY FINANCIAL DASHBOARD**\n\n"
                    for row in vals[2:]:
                        if len(row) >= 2 and row[0]:
                            msg += f"• {row[0]}: TWD {row[1]}\n"
            except Exception as e:
                msg = f"⚠️ Error reading dashboard: {str(e)}"
        else:
            msg = "⚠️ Database connection offline."
        line_bot_api.push_message(user_id, TextSendMessage(text=msg, quick_reply=get_quick_replies(who_spent)))
        log_chat(user_id, who_spent, "text", text, "Dashboard summary", "Balance check", "success")
        return

    # Categorization Processing (Supports English, Thai, Chinese)
    system_prompt = """
    Categorize the expenditure message into JSON. Support English, Thai, and Chinese input.
    
    Output strictly valid JSON:
    {"category": "Family Petty Cash"|"Personal"|"Urgent"|"Food"|"Transport"|"Medical"|"General", "amount": number, "vendor": "string"}
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
            # Log to Raw_Expenses sheet
            exp_sheet = sh.worksheet("Raw_Expenses")
            exp_sheet.append_row([
                timestamp,      # Timestamp
                who_spent,      # User
                category,       # Category
                amount,         # Amount (TWD)
                vendor,         # Vendor/Note
                "LINE",         # Payment Method
                "No",           # Receipt?
                "No",           # Tax Deductible?
                text,           # Raw Input (EN/TH/ZH)
                event.source.user_id if hasattr(event.source, 'user_id') else "group"  # Chat Log ID
            ])
            
            # Concise trilingual reply - result only
            if who_spent == "prapa.yang":
                reply = f"✅ บันทึกแล้ว: {category} {amount:,} บาท - {vendor}"
            elif who_spent == "jack.yang":
                reply = f"✅ Logged: {category} TWD {amount:,} - {vendor}"
            else:
                reply = f"✅ 已记录：{category} {amount:,} 元 - {vendor}"
        else:
            reply = "⚠️ Database offline"
        
        log_chat(user_id, who_spent, "text", text, f"{category} {amount}", "Logged to Raw_Expenses", "success")
        
    except Exception as e:
        reply = f"📝 {text}"
        log_chat(user_id, who_spent, "text", text, "", f"Parse error: {e}", "partial")

    line_bot_api.push_message(user_id, TextSendMessage(text=reply, quick_reply=get_quick_replies(who_spent)))

# =============================================================================
# 5. Vision Handler for Salary Slips (Taiwan Tax Compliance)
# =============================================================================
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Handle both 1-on-1 chats and group chats
    if hasattr(event.source, 'user_id') and event.source.user_id:
        user_id = event.source.user_id
    else:
        user_id = event.source.group_id if hasattr(event.source, 'group_id') else "unknown"
    
    who_spent = "jack.yang"
    FAMILY_MEMBERS = {
        "YOUR_LINE_USER_ID": "jack.yang",
        "LEE_LINE_USER_ID": "prapa.yang"
    }
    who_spent = FAMILY_MEMBERS.get(user_id, "jack.yang")
    
    # Download Image from LINE
    try:
        message_content = line_bot_api.get_message_content(event.message.id)
        img_bytes = io.BytesIO()
        for chunk in message_content.iter_content():
            img_bytes.write(chunk)
        base64_image = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

        # Smart Image Classifier - First determine if it's a salary slip or expense receipt
        classifier_prompt = """
        Analyze this image. Is it a SALARY SLIP/PAYROLL document or an EXPENSE RECEIPT?
        
        SALARY SLIP indicators: employee name, gross pay, withholding tax, NHI, pension, net pay, pay period
        EXPENSE RECEIPT indicators: store name, items, total amount, date, receipt number
        
        Reply with ONLY one word: "SALARY" or "RECEIPT"
        """
        
        classifier = di_client.chat.completions.create(
            model="Qwen/Qwen3-VL-30B-A3B-Instruct",  # MUST use vision model for images!
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": classifier_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }]
        )
        
        image_type = classifier.choices[0].message.content.strip().upper()
        
        # ROUTE 1: It's a SALARY SLIP - Extract Taiwan tax data
        if "SALARY" in image_type:
            tax_prompt = """
            Extract Taiwan Salary Slip data. Output strictly JSON with these keys:
            {
              "person": "Jack"|"Lee"|"Unknown",
              "pay_period": "YYYY-MM",
              "gross_pay": number,
              "withholding_tax": number,
              "nhi_premium": number,
              "labor_insurance": number,
              "employment_insurance": number,
              "pension_voluntary_6": number,
              "meal_allowance": number,
              "other_deductions": number,
              "net_pay": number
            }
            """

            response = di_client.chat.completions.create(
                model="Qwen/Qwen3-VL-30B-A3B-Instruct",
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
            
            # VALIDATION: Skip if all zeros or invalid
            if data.get("gross_pay", 0) == 0 and data.get("net_pay", 0) == 0:
                reply = "⚠️ ไม่สามารถอ่านสลิปได้ กรุณาถ่ายภาพใหม่"
                log_chat(user_id, who_spent, "image", "Salary Slip (invalid)", "", "Rejected - invalid data", "failed")
            else:
                if gc:
                    # Log to Raw_Income sheet
                    inc_sheet = sh.worksheet("Raw_Income")
                    inc_sheet.append_row([
                        timestamp,                      # Timestamp
                        data.get("person", "Unknown"),  # Person
                        "Salary",                       # Type
                        data.get("gross_pay", 0),       # Gross Amount
                        data.get("withholding_tax", 0), # Withholding Tax
                        data.get("nhi_premium", 0),     # NHI
                        data.get("labor_insurance", 0), # Labor Ins
                        data.get("pension_voluntary_6", 0), # Pension 6%
                        data.get("meal_allowance", 0),  # Meal Allowance
                        data.get("other_deductions", 0),# Other Deductions
                        data.get("net_pay", 0),         # Net Pay
                        "Pending Refund",               # Tax Refund Status
                        f"LINE:{event.message.id}"      # Source Document
                    ])
                    
                    # Concise trilingual reply
                    person = data.get("person", "Unknown")
                    gross = f"{data.get('gross_pay', 0):,}"
                    net = f"{data.get('net_pay', 0):,}"
                    tax = f"{data.get('withholding_tax', 0):,}"
                    
                    if who_spent == "prapa.yang":
                        reply = f"📄 บันทึกสลิปแล้ว: {person} รวม {gross} บาท ได้จริง {net} บาท (หักภาษี {tax} บาท)"
                    elif who_spent == "jack.yang":
                        reply = f"📄 Salary logged: {person} Gross {gross} TWD Net {net} TWD (Tax {tax} TWD)"
                    else:
                        reply = f"📄 薪资已记录：{person} 总额 {gross} 元 实发 {net} 元 (扣税 {tax} 元)"
                    
                    log_chat(user_id, who_spent, "image", "Salary Slip", f"Gross: {gross}", "Logged to Raw_Income", "success")
                else:
                    reply = "⚠️ Database offline"
                    log_chat(user_id, who_spent, "image", "Salary Slip", "", "Failed - Sheets offline", "failed")
        
        # ROUTE 2: It's an EXPENSE RECEIPT - Extract amount and vendor
        else:
            expense_prompt = """
            Extract expense receipt data. Output strictly JSON:
            {
              "vendor": "store name",
              "amount": number,
              "items": ["item1", "item2"]
            }
            """
            
            response = di_client.chat.completions.create(
                model="Qwen/Qwen3-VL-30B-A3B-Instruct",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": expense_prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )
            
            raw_json = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
            data = json.loads(raw_json)
            
            amount = data.get("amount", 0)
            vendor = data.get("vendor", "Unknown")
            items = ", ".join(data.get("items", []))
            
            if amount > 0:
                if gc:
                    # Log to Raw_Expenses sheet
                    exp_sheet = sh.worksheet("Raw_Expenses")
                    exp_sheet.append_row([
                        timestamp,
                        who_spent,
                        "Food",  # Default category for receipt images
                        amount,
                        f"{vendor} - {items}",
                        "LINE",
                        "Yes",  # Has receipt
                        "No",   # Not tax deductible
                        f"Receipt image: {vendor}",
                        event.source.user_id if hasattr(event.source, 'user_id') else "group"
                    ])
                    
                    # Concise trilingual reply
                    if who_spent == "prapa.yang":
                        reply = f"✅ บันทึกใบเสร็จแล้ว: {vendor} {amount:,} บาท"
                    elif who_spent == "jack.yang":
                        reply = f"✅ Receipt logged: {vendor} TWD {amount:,}"
                    else:
                        reply = f"✅ 收据已记录：{vendor} {amount:,} 元"
                    
                    log_chat(user_id, who_spent, "image", f"Receipt: {vendor}", f"{amount} TWD", "Logged to Raw_Expenses", "success")
                else:
                    reply = "⚠️ Database offline"
            else:
                reply = "📷 ไม่สามารถอ่านจำนวนเงน กรุณาพิมพ์เอง: 'ร้านค้า จำนวน'"
                log_chat(user_id, who_spent, "image", f"Receipt: {vendor}", "", "Failed - no amount", "partial")
        
    except Exception as e:
        reply = f"⚠️ Image processing failed: {str(e)}"
        log_chat(user_id, who_spent, "image", "Unknown", "", f"Error: {e}", "failed")

    # Send ONLY ONE reply (no duplicates)
    line_bot_api.push_message(user_id, TextSendMessage(text=reply, quick_reply=get_quick_replies(who_spent)))

# =============================================================================
# 6. Server Entry Point
# =============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
