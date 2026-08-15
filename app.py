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

# Deduplication cache - track processed message IDs (last 5 minutes)
processed_messages = {}

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
            QuickReplyButton(action=MessageAction(label="💰 สลปเงนเดอน", text="Upload Salary Slip")),
            QuickReplyButton(action=MessageAction(label="🏠 ค่าใชจายครอบครัว", text="Category: Petty Cash")),
            QuickReplyButton(action=MessageAction(label="🧍 ส่วนตัว", text="Category: Personal")),
            QuickReplyButton(action=MessageAction(label="🚨 เรงด่วน", text="Category: Urgent")),
            QuickReplyButton(action=MessageAction(label="📊 ยอดคงเหลอ", text="Check Balance"))
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="💰 Salary Slip", text="Upload Salary Slip")),
            QuickReplyButton(action=MessageAction(label="🏠 Petty Cash", text="Category: Petty Cash")),
            QuickReplyButton(action=MessageAction(label="🧍 Personal", text="Category: Personal")),
            QuickReplyButton(action=MessageAction(label="🚨 Urgent", text="Category: Urgent")),
            QuickReplyButton(action=MessageAction(label="📊 Balance", text="Check Balance"))
        ])

# Polite follow-up message (Thai/English bank call center style)
def get_polite_followup(user_name="jack.yang", context="general"):
    if user_name == "prapa.yang":
        followups = {
            "expense": "🙏 ขอบคณค่ะ ทานมีรายจ่ายอ่นๆ ต้องการบันทกเพ่มเตมไหมค๊ะ? พมพขอมูลเชน 'ร้านค้า จำนวน' ไดเลยค๊ะ",
            "balance": "🙏 ขอบคณค่ะ ทานตองการทราบขอมูลเพ่มเตมดานไหนอีกไหมค๊ะ? ยินดใหบรการตลอด 24 ชั่โมงค๊ะ",
            "salary": "🙏 ขอบคณค่ะ ทานมสลิปเงนเดอนของเดอนหนาทจะอัปโหลดไหมค๊ะ? หรอมีขอสงสยตองการถามเพ่มเตมไหมค๊ะ",
            "general": "🙏 ขอบคณค่ะ ทานมีขอสงสยอ่นๆ หรอตองการบันทกรายจ่ายเพ่มเตมไหมค๊ะ? ยินดใหบรการค๊ะ"
        }
        return followups.get(context, followups["general"])
    else:
        followups = {
            "expense": "🙏 Thank you! Would you like to log more expenses or check your balance?",
            "balance": "🙏 Thank you! Would you like more details on any category or log new expenses?",
            "salary": "🙏 Thank you! Do you have more salary slips to upload or any questions?",
            "general": "🙏 Thank you! Any other questions or expenses to log today?"
        }
        return followups.get(context, followups["general"])

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
    global processed_messages  # MUST declare global to modify it!
    
    # DEDUPLICATION: Skip if already processed this message ID
    msg_id = event.message.id
    if msg_id in processed_messages:
        print(f"⚠️ Skipping duplicate text message: {msg_id}")
        return "OK"
    processed_messages[msg_id] = datetime.now()
    
    # Clean old entries (older than 5 minutes)
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(minutes=5)
    processed_messages = {k: v for k, v in processed_messages.items() if v > cutoff}
    
    text = event.message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Handle both 1-on-1 chats and group chats
    if hasattr(event.source, 'user_id') and event.source.user_id:
        # 1-on-1 chat or user in group
        user_id = event.source.user_id
    else:
        # Group chat without user context - use group ID as fallback
        user_id = event.source.group_id if hasattr(event.source, 'group_id') else "unknown"
    
    # Determine user name from prefix or auto-detect
    who_spent = "jack.yang"  # Default
    if text.startswith("jack.yang"):
        who_spent = "jack.yang"
        text = text.replace("jack.yang", "", 1).strip()
    elif text.startswith("prapa.yang"):
        who_spent = "prapa.yang"
        text = text.replace("prapa.yang", "", 1).strip()
    else:
        # Auto-detect from LINE User ID (update with real IDs when available)
        FAMILY_MEMBERS = {
            "YOUR_LINE_USER_ID": "jack.yang",  # Replace with your real LINE ID
            "LEE_LINE_USER_ID": "prapa.yang"   # Replace with Prapa's real LINE ID
        }
        who_spent = FAMILY_MEMBERS.get(user_id, "prapa.yang")  # Default to prapa for unknown users

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
                # Get ACTUAL VALUES not formulas!
                vals = dash.get_values(value_render_option='FORMATTED_VALUE')
                
                # Extract key metrics (handle empty/missing cells)
                def get_val(row_idx, col_idx=1):
                    if row_idx < len(vals) and col_idx < len(vals[row_idx]):
                        val = vals[row_idx][col_idx]
                        return val if val else "0"
                    return "0"
                
                income_ytd = get_val(2)      # Row 3 (0-indexed: 2)
                prepaid_tax = get_val(3)     # Row 4
                net_income = get_val(5)      # Row 6
                expenses_ytd = get_val(6)    # Row 7
                family_cash = get_val(7)     # Row 8
                personal_exp = get_val(8)    # Row 9
                urgent_exp = get_val(9)      # Row 10
                food_exp = get_val(10)       # Row 11
                net_savings = get_val(14)    # Row 15
                savings_rate = get_val(15)   # Row 16
                
                if who_spent == "prapa.yang":
                    # 100% Thai - Mobile-friendly concise format
                    msg = (
                        f"📊 **ยอดคงเหลอครอบครัวหยาง**\n\n"
                        f"💰 รายได้รวม: {income_ytd} บ.\n"
                        f"💵 เงินได้จริง: {net_income} บ.\n"
                        f"📊 รายจายรวม: {expenses_ytd} บ.\n"
                        f"─────────────────\n"
                        f"💰 เงินออมสทธ: {net_savings} บ.\n"
                        f"📈 อตราเงินออม: {savings_rate}%\n\n"
                        f"🏠 ค่าใชจายครอบครัว: {family_cash} บ.\n"
                        f"🧍 ค่าใชจายสวนตัว: {personal_exp} บ.\n"
                        f"🚨 ค่าใชจายเรงด่วน: {urgent_exp} บ.\n"
                        f"🍽️ อาหาร: {food_exp} บ."
                    )
                else:
                    # English version
                    msg = (
                        f"📊 **YANG FAMILY DASHBOARD**\n\n"
                        f"💰 Total Income: {income_ytd} TWD\n"
                        f"💵 Net Income: {net_income} TWD\n"
                        f"📊 Total Expenses: {expenses_ytd} TWD\n"
                        f"─────────────────\n"
                        f"💰 Net Savings: {net_savings} TWD\n"
                        f"📈 Savings Rate: {savings_rate}%\n\n"
                        f"🏠 Family Cash: {family_cash} TWD\n"
                        f"🧍 Personal: {personal_exp} TWD\n"
                        f"🚨 Urgent: {urgent_exp} TWD\n"
                        f"🍽️ Food: {food_exp} TWD"
                    )
            except Exception as e:
                if who_spent == "prapa.yang":
                    msg = f"⚠️ เกิดข้ดพลาด: {str(e)}"
                else:
                    msg = f"⚠️ Error reading dashboard: {str(e)}"
        else:
            if who_spent == "prapa.yang":
                msg = "⚠️ ฐานขอมูลไมสามารถเช่อมตอได"
            else:
                msg = "⚠️ Database connection offline."
        line_bot_api.push_message(
            user_id,
            TextSendMessage(text=msg, quick_reply=get_quick_replies(who_spent)),
            TextSendMessage(text=get_polite_followup(who_spent, "balance"))
        )
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
                reply = f"✅ บันทกแลว: {category} {amount:,} บาท - {vendor}"
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

    # Send main reply + polite follow-up (bank call center style)
    line_bot_api.push_message(
        user_id,
        TextSendMessage(text=reply, quick_reply=get_quick_replies(who_spent)),
        TextSendMessage(text=get_polite_followup(who_spent, "expense"))
    )

# =============================================================================
# 5. Vision Handler for Salary Slips (Taiwan Tax Compliance)
# =============================================================================
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    global processed_messages  # MUST declare global to modify it!
    
    # DEDUPLICATION: Skip if already processed this message ID
    msg_id = event.message.id
    if msg_id in processed_messages:
        print(f"⚠️ Skipping duplicate image message: {msg_id}")
        return "OK"
    processed_messages[msg_id] = datetime.now()
    
    # Clean old entries (older than 5 minutes)
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(minutes=5)
    processed_messages = {k: v for k, v in processed_messages.items() if v > cutoff}
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Handle both 1-on-1 chats and group chats
    if hasattr(event.source, 'user_id') and event.source.user_id:
        user_id = event.source.user_id
    else:
        user_id = event.source.group_id if hasattr(event.source, 'group_id') else "unknown"
    
    who_spent = "jack.yang"
    FAMILY_MEMBERS = {
        "YOUR_LINE_USER_ID": "jack.yang",  # Replace with your real LINE ID
        "LEE_LINE_USER_ID": "prapa.yang"   # Replace with Prapa's real LINE ID
    }
    who_spent = FAMILY_MEMBERS.get(user_id, "prapa.yang")  # Default to prapa for unknown users
    
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
                        reply = f"📄 บันทกสลปแลว: {person} รวม {gross} บาท ไดจรง {net} บาท (หกภาษ {tax} บาท)"
                    elif who_spent == "jack.yang":
                        reply = f"📄 Salary logged: {person} Gross {gross} TWD Net {net} TWD (Tax {tax} TWD)"
                    else:
                        reply = f"📄 薪资已记录：{person} 总额 {gross} 元 实发 {net} 元 (扣税 {tax} 元)"
                    
                    log_chat(user_id, who_spent, "image", "Salary Slip", f"Gross: {gross}", "Logged to Raw_Income", "success")
                    
                    # Send with polite follow-up
                    line_bot_api.push_message(
                        user_id,
                        TextSendMessage(text=reply, quick_reply=get_quick_replies(who_spent)),
                        TextSendMessage(text=get_polite_followup(who_spent, "salary"))
                    )
                else:
                    reply = "⚠️ Database offline"
                    log_chat(user_id, who_spent, "image", "Salary Slip", "", "Failed - Sheets offline", "failed")
                    line_bot_api.push_message(user_id, TextSendMessage(text=reply))
        
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
