"""
Yang Family Financial & Tax Agent - LINE Bot
Professional Bank Call Center Style
- Jack (jack.yang): English/Chinese
- Prapa (prapa.yang, อารยา หยาง): Thai ONLY with formal address
- Models: DeepSeek-V3 (text, cheaper), Qwen3-VL (vision)
- Features: Expenditure, Income, Open Account, Transfer, Balance
"""
import os
import io
import json
import base64
import requests
from datetime import datetime
from fastapi import FastAPI, Request
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
LINE_CHANNEL_ID = os.environ.get("LINE_CHANNEL_ID", "2010958353")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
DEEPINFRA_API_KEY = os.environ.get("DEEPINFRA_API_KEY", "")
SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"

# User tracking - REAL LINE USER IDs (update these!)
FAMILY_MEMBERS = {
    # "YOUR_ACTUAL_LINE_USER_ID_HERE": "jack.yang",
    # "PRAPA_ACTUAL_LINE_USER_ID_HERE": "prapa.yang",
}

# Deduplication cache
processed_messages = {}

# Google Sheets Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gc = None
sh = None

try:
    creds_path = "/app/credentials.json" if os.path.exists("/app/credentials.json") else "credentials.json"
    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    print(f"✅ Google Sheets connected ({creds_path})")
except Exception as e:
    print(f"⚠️ Google Sheets auth failed: {e}")

# LINE Auth
def get_channel_access_token(cid, secret):
    url = "https://api.line.me/v2/oauth/accessToken"
    data = {"grant_type": "client_credentials", "client_id": cid, "client_secret": secret}
    res = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return res.json().get("access_token") if res.status_code == 200 else None

ACCESS_TOKEN = get_channel_access_token(LINE_CHANNEL_ID, LINE_CHANNEL_SECRET)
line_bot_api = LineBotApi(ACCESS_TOKEN) if ACCESS_TOKEN else None
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# AI Clients
# DeepSeek-V3 for text (cheaper, fast)
# Qwen3-VL for vision (receipts, salary slips)
di_client = OpenAI(api_key=DEEPINFRA_API_KEY, base_url="https://api.deepinfra.com/v1/openai") if DEEPINFRA_API_KEY else None

# =============================================================================
# 2. Helper Functions - Professional Bank Call Center Style
# =============================================================================

def get_user_name(user_id, default="jack.yang"):
    """Determine user name from LINE ID or prefix"""
    # Check FAMILY_MEMBERS dict
    if user_id in FAMILY_MEMBERS:
        return FAMILY_MEMBERS[user_id]
    return default

def get_greeting(user_name):
    """Professional bank call center greeting"""
    if user_name == "prapa.yang":
        return "สวัสดีครับคณนายอารยา หยาง มีอะไรให้รับใช้วันนี้ครับ?"
    else:
        return "Hello Mr Jack, what help can I do for you today?"

def get_main_menu(user_name):
    """Main menu Quick Reply buttons - Bank style"""
    if user_name == "prapa.yang":
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="💸 รายจ่าย", text="เมนูรายจ่าย")),
            QuickReplyButton(action=MessageAction(label="💰 เงินเดือน", text="อัปโหลดสลิป")),
            QuickReplyButton(action=MessageAction(label="🏦 เปดบญช", text="เปดบญชใหม")),
            QuickReplyButton(action=MessageAction(label="💸 โอนเงิน", text="โอนระหวางบญช")),
            QuickReplyButton(action=MessageAction(label="📊 ยอดคงเหลอ", text="ตรวจสอบยอด")),
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="💸 Expenses", text="Expense menu")),
            QuickReplyButton(action=MessageAction(label="💰 Salary", text="Upload salary slip")),
            QuickReplyButton(action=MessageAction(label="🏦 Open Account", text="Open new account")),
            QuickReplyButton(action=MessageAction(label="💸 Transfer", text="Transfer between accounts")),
            QuickReplyButton(action=MessageAction(label="📊 Balance", text="Check balance")),
        ])

def get_expense_menu(user_name):
    """Expense category Quick Reply buttons"""
    if user_name == "prapa.yang":
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🏠 ค่าใชจายครอบครัว", text="Category: Family Petty Cash")),
            QuickReplyButton(action=MessageAction(label="🧍 ส่วนตัว", text="Category: Personal")),
            QuickReplyButton(action=MessageAction(label="🚨 เรงด่วน", text="Category: Urgent")),
            QuickReplyButton(action=MessageAction(label="🍽️ อาหาร", text="Category: Food")),
            QuickReplyButton(action=MessageAction(label="🚗 คมนาคม", text="Category: Transport")),
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🏠 Family Petty Cash", text="Category: Family Petty Cash")),
            QuickReplyButton(action=MessageAction(label="🧍 Personal", text="Category: Personal")),
            QuickReplyButton(action=MessageAction(label="🚨 Urgent", text="Category: Urgent")),
            QuickReplyButton(action=MessageAction(label="🍽️ Food", text="Category: Food")),
            QuickReplyButton(action=MessageAction(label="🚗 Transport", text="Category: Transport")),
        ])

def get_polite_followup(user_name, context="general"):
    """Polite follow-up question - Bank call center style"""
    if user_name == "prapa.yang":
        followups = {
            "greeting": "มีอะไรให้อารยาชวยวันนี้บอกไดเลยครับ",
            "expense": "มีรายจ่ายอ่นๆ ตองการบันทกเพ่มเตมไหมครับ? พมพขอมูลเชน 'รานครำานวน' ไดเลยครับ",
            "balance": "ตองการทราบขอมูลเพ่มเตมดานไหนอีกไหมครับ? ยินดใหบรการตลอด 24 ชั่โมงครับ",
            "salary": "มสลิปเงนเดอนของเดอนหนาทจะอัปโหลดไหมครับ? หรอมีขอสงสยตองการถามเพ่มเตมไหมครับ",
            "transfer": "ตองการโอนเงินเพ่มเตมไหมครับ? หรอมีธุระกรรมอ่นๆ ทให้อารยาชวยไหมครับ",
            "general": "มีขอสงสยอ่นๆ หรอตองการบันทกรายจ่ายเพ่มเตมไหมครับ? ยินดใหบรการครับ"
        }
        return followups.get(context, followups["general"])
    else:
        followups = {
            "greeting": "How can I assist you today?",
            "expense": "Any other expenses to log? Just type 'vendor amount'!",
            "balance": "Would you like more details on any category?",
            "salary": "Do you have more salary slips to upload?",
            "transfer": "Any other transfers or transactions today?",
            "general": "Any other questions or expenses to log today?"
        }
        return followups.get(context, followups["general"])

def send_bank_response(user_id, user_name, main_text, followup_context="general", quick_reply=None):
    """Send professional two-message bank response"""
    try:
        # Message 1: Main response + Quick Reply
        msg1 = TextSendMessage(
            text=main_text,
            quick_reply=quick_reply or get_main_menu(user_name)
        )
        
        # Message 2: Polite follow-up (no buttons)
        msg2 = TextSendMessage(text=get_polite_followup(user_name, followup_context))
        
        line_bot_api.push_message(user_id, [msg1, msg2])
        return True
    except Exception as e:
        print(f"⚠️ Send failed: {e}")
        # Fallback: send text only
        line_bot_api.push_message(user_id, TextSendMessage(text=main_text))
        return False

# =============================================================================
# 3. Webhook Handler
# =============================================================================
@app.post("/webhook")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    
    print(f"🔔 Webhook: Signature={'YES' if signature else 'NO'}, Body={len(body)} bytes")
    
    try:
        if not signature:
            print("ℹ️ LINE verification (no signature)")
            return {"status": "OK"}
        
        handler.handle(body.decode("utf-8"), signature)
        print("✅ Handler processed")
    except InvalidSignatureError:
        print(f"⚠️ Invalid signature")
    except Exception as e:
        print(f"⚠️ Handler error: {e}")
        import traceback
        traceback.print_exc()
    
    return {"status": "OK"}

# =============================================================================
# 4. Text Message Handler
# =============================================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    global processed_messages
    
    msg_id = event.message.id
    if msg_id in processed_messages:
        print(f"⚠️ Duplicate: {msg_id}")
        return
    processed_messages[msg_id] = datetime.now()
    
    # Clean old entries
    from datetime import timedelta
    cutoff = datetime.now() - timedelta(minutes=5)
    processed_messages = {k: v for k, v in processed_messages.items() if v > cutoff}
    
    text = event.message.text.strip()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get user ID
    if hasattr(event.source, 'user_id') and event.source.user_id:
        user_id = event.source.user_id
    else:
        user_id = event.source.group_id if hasattr(event.source, 'group_id') else "unknown"
    
    # Determine user name
    user_name = get_user_name(user_id, "jack.yang")
    
    # Check for prefix override
    if text.startswith("jack.yang"):
        user_name = "jack.yang"
        text = text.replace("jack.yang", "", 1).strip()
    elif text.startswith("prapa.yang"):
        user_name = "prapa.yang"
        text = text.replace("prapa.yang", "", 1).strip()
    
    print(f"📝 User: {user_name} ({user_id[:10]}...), Text: {text[:50]}")
    
    # === GREETING / MAIN MENU ===
    if text.lower() in ["hello", "hi", "สวัสดี", "menu", "เมน"]:
        greeting = get_greeting(user_name)
        send_bank_response(user_id, user_name, greeting, "greeting", get_main_menu(user_name))
        return
    
    # === EXPENSE MENU ===
    if text == "Expense menu" or text == "เมนูรายจ่าย":
        reply = "📋 Please select expense category:" if user_name != "prapa.yang" else "📋 กรุณาเลอกหมวดหมู่รายจ่าย:"
        send_bank_response(user_id, user_name, reply, "expense", get_expense_menu(user_name))
        return
    
    # === UPLOAD SALARY SLIP ===
    if text == "Upload salary slip" or text == "อัปโหลดสลิป":
        reply = "📄 Please upload a photo or screenshot of the salary slip now." if user_name != "prapa.yang" else "📄 กรุณาอัปโหลดรูปสลิปเงินเดอนตอนนี้"
        send_bank_response(user_id, user_name, reply, "salary", get_main_menu(user_name))
        return
    
    # === CHECK BALANCE ===
    if text == "Check balance" or text == "ตรวจสอบยอด":
        if gc:
            try:
                dash = sh.worksheet("Dashboard_Summary")
                vals = dash.get_values(value_render_option='FORMATTED_VALUE')
                
                def get_val(row_idx):
                    if row_idx < len(vals) and len(vals[row_idx]) > 1:
                        return vals[row_idx][1] if vals[row_idx][1] else "0"
                    return "0"
                
                if user_name == "prapa.yang":
                    msg = (
                        f"📊 **ยอดคงเหลอครอบครัวหยาง**\n\n"
                        f"💰 รายไดรวม: {get_val(2)} บ.\n"
                        f"💵 เงินไดจริง: {get_val(5)} บ.\n"
                        f"📊 รายจายรวม: {get_val(6)} บ.\n"
                        f"─────────────────\n"
                        f"💰 เงินออมสทธ: {get_val(14)} บ.\n"
                        f"🏠 ค่าใชจายครอบครัว: {get_val(7)} บ.\n"
                        f"🧍 ค่าใชจายสวนตัว: {get_val(8)} บ.\n"
                        f"🚨 ค่าใชจายเรงด่วน: {get_val(9)} บ."
                    )
                else:
                    msg = (
                        f"📊 **YANG FAMILY DASHBOARD**\n\n"
                        f"💰 Total Income: {get_val(2)} TWD\n"
                        f"💵 Net Income: {get_val(5)} TWD\n"
                        f"📊 Total Expenses: {get_val(6)} TWD\n"
                        f"─────────────────\n"
                        f"💰 Net Savings: {get_val(14)} TWD\n"
                        f"🏠 Family Cash: {get_val(7)} TWD\n"
                        f"🧍 Personal: {get_val(8)} TWD\n"
                        f"🚨 Urgent: {get_val(9)} TWD"
                    )
                
                send_bank_response(user_id, user_name, msg, "balance", get_main_menu(user_name))
            except Exception as e:
                reply = f"⚠️ Error: {e}" if user_name != "prapa.yang" else f"⚠️ ผดพลาด: {e}"
                send_bank_response(user_id, user_name, reply, "balance")
        else:
            reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานขอมูลไมสามารถเช่อมตอได"
            send_bank_response(user_id, user_name, reply, "balance")
        return
    
    # === OPEN NEW ACCOUNT ===
    if text == "Open new account" or text == "เปดบญชใหม":
        if user_name == "prapa.yang":
            reply = (
                "🏦 **เปดบญชใหม**\n\n"
                "อารยาชวยถามขอมูลเพ่มเตมครับ:\n"
                "1. ชื่อบญชทตองการ?\n"
                "2. ประเภทบญช? (กระเป๋า/ธนาคาร)\n"
                "3. เงินเรมตนเทาไร?\n"
                "4. เปดเพออะไรครับ?"
            )
        else:
            reply = (
                "🏦 **Open New Account**\n\n"
                "I'll help you open a new account. Please tell me:\n"
                "1. Account name?\n"
                "2. Account type? (Pocket/Bank)\n"
                "3. Initial deposit?\n"
                "4. Purpose?"
            )
        send_bank_response(user_id, user_name, reply, "general")
        return
    
    # === TRANSFER BETWEEN ACCOUNTS ===
    if text == "Transfer between accounts" or text == "โอนระหวางบญช":
        if gc:
            try:
                acc = sh.worksheet("Accounts")
                accounts = acc.get_all_values()[1:]  # Skip header
                
                if user_name == "prapa.yang":
                    acc_list = "\n".join([f"{i+1}. {row[1]} ({row[3]})" for i, row in enumerate(accounts) if row])
                    reply = f"📋 **บญชทมี**:\n\n{acc_list}\n\nเลอกบญชทตองการโอนครับ"
                else:
                    acc_list = "\n".join([f"{i+1}. {row[1]} ({row[3]})" for i, row in enumerate(accounts) if row])
                    reply = f"📋 **Available Accounts**:\n\n{acc_list}\n\nSelect account to transfer from."
                
                send_bank_response(user_id, user_name, reply, "transfer")
            except Exception as e:
                reply = f"⚠️ Error: {e}" if user_name != "prapa.yang" else f"⚠️ ผดพลาด: {e}"
                send_bank_response(user_id, user_name, reply, "transfer")
        else:
            reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานขอมูลไมสามารถเช่อมตอได"
            send_bank_response(user_id, user_name, reply, "transfer")
        return
    
    # === EXPENSE LOGGING (AI Categorization) ===
    # Use DeepSeek-V3 for text categorization (cheaper)
    if di_client and gc:
        try:
            system_prompt = """
            Categorize the expenditure message into JSON. Support English, Thai, Chinese.
            Output strictly valid JSON:
            {"category": "Family Petty Cash"|"Personal"|"Urgent"|"Food"|"Transport"|"Medical"|"General", "amount": number, "vendor": "string"}
            """
            
            chat = di_client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",  # Cheaper model
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.1
            )
            
            parsed = json.loads(chat.choices[0].message.content)
            category = parsed.get("category", "General")
            amount = parsed.get("amount", 0)
            vendor = parsed.get("vendor", "N/A")
            
            # Log to Raw_Expenses
            exp_sheet = sh.worksheet("Raw_Expenses")
            exp_sheet.append_row([
                timestamp, user_id, user_name, category, amount, vendor,
                "LINE", "No", category, text, "th" if user_name == "prapa.yang" else "en", msg_id
            ])
            
            # Confirmation
            if user_name == "prapa.yang":
                reply = f"✅ บันทกแลวครับ: {category} {amount:,} บาท - {vendor}"
            else:
                reply = f"✅ Logged: {category} {amount:,} TWD - {vendor}"
            
            send_bank_response(user_id, user_name, reply, "expense", get_expense_menu(user_name))
            return
            
        except Exception as e:
            print(f"⚠️ AI categorization failed: {e}")
    
    # === FALLBACK: Unrecognized Input ===
    greeting = get_greeting(user_name)
    send_bank_response(user_id, user_name, f"{greeting}\n\nYou said: {text}", "greeting", get_main_menu(user_name))

# =============================================================================
# 5. Image Handler (Salary Slips & Receipts)
# =============================================================================
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    global processed_messages
    
    msg_id = event.message.id
    if msg_id in processed_messages:
        return
    processed_messages[msg_id] = datetime.now()
    
    # Get user
    if hasattr(event.source, 'user_id') and event.source.user_id:
        user_id = event.source.user_id
    else:
        user_id = event.source.group_id if hasattr(event.source, 'group_id') else "unknown"
    
    user_name = get_user_name(user_id, "jack.yang")
    
    # Download image from LINE
    message_content = line_bot_api.get_message_content(msg_id)
    img_data = message_content.content
    
    if not di_client:
        reply = "⚠️ AI service offline" if user_name != "prapa.yang" else "⚠️ บรการ AI ไมสามารถใชงานได"
        send_bank_response(user_id, user_name, reply, "general")
        return
    
    # Use Qwen3-VL for vision
    try:
        # Encode image to base64
        img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # First: Classify image type (SALARY or RECEIPT)
        classifier_prompt = """
        Classify this image: Is it a SALARY SLIP/PAYSTUB or an EXPENSE RECEIPT?
        Reply with ONE word: SALARY or RECEIPT
        """
        
        classifier = di_client.chat.completions.create(
            model="Qwen/Qwen3-VL-30B-A3B-Instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": classifier_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                ]
            }]
        )
        
        img_type = classifier.choices[0].message.content.strip().upper()
        print(f"🖼️ Image classified as: {img_type}")
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # ROUTE 1: SALARY SLIP
        if "SALARY" in img_type:
            if gc:
                extract_prompt = """
                Extract from this Taiwan salary slip:
                - person: Employee name
                - gross_pay: Total salary (number)
                - tax: Withholding tax (扣繳) (number)
                - nhi: NHI (健保費) (number)
                - labor_ins: Labor Insurance (勞保費) (number)
                - pension: Pension 6% (勞退自提) (number)
                - net_pay: Net pay (實發) (number)
                
                Output JSON only.
                """
                
                extractor = di_client.chat.completions.create(
                    model="Qwen/Qwen3-VL-30B-A3B-Instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extract_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    }]
                )
                
                data = json.loads(extractor.choices[0].message.content)
                person = data.get("person", "Unknown")
                gross = data.get("gross_pay", 0)
                tax = data.get("tax", 0)
                net = data.get("net_pay", 0)
                
                # Log to Raw_Income
                inc_sheet = sh.worksheet("Raw_Income")
                inc_sheet.append_row([
                    timestamp, user_id, person, "Salary", gross, "NTD",
                    tax, data.get("nhi", 0), data.get("labor_ins", 0),
                    data.get("pension", 0), 0, net, "Image OCR",
                    "th" if user_name == "prapa.yang" else "en"
                ])
                
                # Confirmation
                if user_name == "prapa.yang":
                    reply = f"📄 บันทกสลปแลวครับ! {person} รวม {gross:,} บาท ไดจริง {net:,} บาท"
                else:
                    reply = f"📄 Salary logged: {person} Gross {gross:,} TWD Net {net:,} TWD"
                
                send_bank_response(user_id, user_name, reply, "salary", get_main_menu(user_name))
            else:
                reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานขอมูลไมสามารถเช่อมตอได"
                send_bank_response(user_id, user_name, reply, "salary")
        
        # ROUTE 2: EXPENSE RECEIPT
        else:
            if gc:
                extract_prompt = """
                Extract from this receipt:
                - amount: Total amount (number)
                - vendor: Store/restaurant name
                - category: Food|Transport|Medical|General
                
                Output JSON only.
                """
                
                extractor = di_client.chat.completions.create(
                    model="Qwen/Qwen3-VL-30B-A3B-Instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extract_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}
                        ]
                    }]
                )
                
                data = json.loads(extractor.choices[0].message.content)
                amount = data.get("amount", 0)
                vendor = data.get("vendor", "Unknown")
                category = data.get("category", "General")
                
                # Log to Raw_Expenses
                exp_sheet = sh.worksheet("Raw_Expenses")
                exp_sheet.append_row([
                    timestamp, user_id, user_name, category, amount, vendor,
                    "LINE", "Yes", category, "Image OCR",
                    "th" if user_name == "prapa.yang" else "en", msg_id
                ])
                
                # Confirmation
                if user_name == "prapa.yang":
                    reply = f"✅ บันทกแลวครับ: {category} {amount:,} บาท - {vendor}"
                else:
                    reply = f"✅ Logged: {category} {amount:,} TWD - {vendor}"
                
                send_bank_response(user_id, user_name, reply, "expense", get_expense_menu(user_name))
            else:
                reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานขอมูลไมสามารถเช่อมตอได"
                send_bank_response(user_id, user_name, reply, "expense")
    
    except Exception as e:
        print(f"⚠️ Image processing failed: {e}")
        reply = "⚠️ Could not read image. Please try again or enter manually." if user_name != "prapa.yang" else "⚠️ ไมสามารถอานรูปได กรุณาลองใหมหรอพมพขอมูลดวยตนเองครับ"
        send_bank_response(user_id, user_name, reply, "general")

# =============================================================================
# 6. Server Entry Point
# =============================================================================
@app.get("/")
def root():
    return {"status": "Yang Family Finance Agent Active", "sheets": "12 tabs configured"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
