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
from approval_workflow import (
    create_request, get_pending_approvals, approve_request, reject_request,
    format_approval_message
)
from flex_message_templates import create_approval_card, create_receipt_confirmation_card

# Global state for multi-step flows
user_flow_state = {}  # {user_id: {'flow': 'transfer', 'step': 1, 'data': {...}}}

# Print startup debug info
print("🚀 Yang Family Finance Bot starting...")
print(f"  PORT: {os.environ.get('PORT', '8080')}")
print(f"  LINE_CHANNEL_ID: {'SET' if os.environ.get('LINE_CHANNEL_ID') else 'MISSING'}")
print(f"  LINE_CHANNEL_SECRET: {'SET' if os.environ.get('LINE_CHANNEL_SECRET') else 'MISSING'}")
print(f"  DEEPINFRA_API_KEY: {'SET' if os.environ.get('DEEPINFRA_API_KEY') else 'MISSING'}")
print(f"  GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')}")

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

# Google Sheets Auth - LAZY LOADING (defer until first use)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gc = None
sh = None
sheets_initialized = False

def init_google_sheets():
    """Initialize Google Sheets connection (called on first use)"""
    global gc, sh, sheets_initialized
    
    if sheets_initialized:
        return True
    
    try:
        # Cloud Run mounts secrets as directories - need to find the actual file
        # Mount path: /app/credentials.json/google-sheets-credentials
        # Try multiple possible paths
        possible_paths = [
            "/app/credentials.json/google-sheets-credentials",  # Cloud Run volume (directory)
            "/app/credentials.json",  # Cloud Run volume (file - old style)
            "/secrets/credentials.json",  # GOOGLE_APPLICATION_CREDENTIALS env var
            "credentials.json",  # Local development
        ]
        
        creds_path = None
        for path in possible_paths:
            if os.path.exists(path):
                creds_path = path
                break
        
        if not creds_path:
            print(f"⚠️ No credentials found in any of: {possible_paths}")
            # Debug: List /app directory to see what's there
            try:
                print(f"  ℹ️  /app contents: {os.listdir('/app')}")
                if os.path.exists('/app/credentials.json'):
                    print(f"  ℹ️  /app/credentials.json exists, is_dir={os.path.isdir('/app/credentials.json')}")
                    if os.path.isdir('/app/credentials.json'):
                        print(f"  ℹ️  Contents: {os.listdir('/app/credentials.json')}")
            except Exception as list_err:
                print(f"  ⚠️  Can't list /app: {list_err}")
            return False
        
        # If it's a directory, look for the secret file inside
        if os.path.isdir(creds_path):
            # List contents to find the actual secret file
            files = os.listdir(creds_path)
            if files:
                creds_path = os.path.join(creds_path, files[0])
                print(f"  ℹ️  Found secret file: {creds_path}")
            else:
                print(f"⚠️ Secret directory {creds_path} is empty")
                return False
        
        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        sheets_initialized = True
        print(f"✅ Google Sheets connected ({creds_path})")
        return True
        
    except Exception as e:
        print(f"⚠️ Google Sheets auth failed: {e}")
        import traceback
        traceback.print_exc()
        return False

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
            QuickReplyButton(action=MessageAction(label="⚙️ ตั้งค่าบญช", text="ตังค่าบญช")),
            QuickReplyButton(action=MessageAction(label="💸 โอนเงิน", text="โอนระหวางบญช")),
            QuickReplyButton(action=MessageAction(label="📊 ยอดคงเหลอ", text="ตรวจสอบยอด")),
            QuickReplyButton(action=MessageAction(label="📋 งบประมาณ", text="ตังงบประมาณ")),
            QuickReplyButton(action=MessageAction(label="⚖️ อนุมัติรายการ", text="ตรวจสอบคำขออนุมัต")),
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="💸 Expenses", text="Expense menu")),
            QuickReplyButton(action=MessageAction(label="💰 Salary", text="Upload salary slip")),
            QuickReplyButton(action=MessageAction(label="⚙️ Account Settings", text="Account settings")),
            QuickReplyButton(action=MessageAction(label="💸 Transfer", text="Transfer between accounts")),
            QuickReplyButton(action=MessageAction(label="📊 Balance", text="Check balance")),
            QuickReplyButton(action=MessageAction(label="📋 Budget", text="Set budget")),
            QuickReplyButton(action=MessageAction(label="⚖️ Approvals", text="Check pending approvals")),
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

def get_transfer_source_menu(user_name):
    """Transfer source account Quick Reply buttons"""
    if gc:
        try:
            acc = sh.worksheet("Accounts")
            accounts = acc.get_all_values()[1:]
            
            buttons = []
            for i, row in enumerate(accounts):
                if row and row[1]:  # Has account name
                    account_name = row[1]
                    # Shorten for button label (LINE max 20 chars)
                    short_name = account_name[:18].strip()
                    if len(account_name) > 18:
                        short_name += "..."
                    buttons.append(QuickReplyButton(action=MessageAction(label=short_name, text=f"FROM:{account_name}")))
            
            if buttons:
                return QuickReply(items=buttons)
        except:
            pass
    
    # Fallback
    if user_name == "prapa.yang":
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="Family Petty Cash", text="FROM:Family Petty Cash")),
            QuickReplyButton(action=MessageAction(label="Urgent Fund", text="FROM:Urgent Fund")),
            QuickReplyButton(action=MessageAction(label="Son's USD", text="FROM:Son's USD Fixed")),
            QuickReplyButton(action=MessageAction(label="Wife's USD", text="FROM:Wife's USD Fixed")),
            QuickReplyButton(action=MessageAction(label="Jack's Personal", text="FROM:Jack's Personal")),
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="Family Petty Cash", text="FROM:Family Petty Cash")),
            QuickReplyButton(action=MessageAction(label="Urgent Fund", text="FROM:Urgent Fund")),
            QuickReplyButton(action=MessageAction(label="Son's USD", text="FROM:Son's USD Fixed")),
            QuickReplyButton(action=MessageAction(label="Wife's USD", text="FROM:Wife's USD Fixed")),
            QuickReplyButton(action=MessageAction(label="Jack's Personal", text="FROM:Jack's Personal")),
        ])

def get_transfer_dest_menu(user_name, from_account):
    """Transfer destination account Quick Reply buttons (excludes source)"""
    if gc:
        try:
            acc = sh.worksheet("Accounts")
            accounts = acc.get_all_values()[1:]
            
            buttons = []
            for i, row in enumerate(accounts):
                if row and row[1] and row[1] != from_account:  # Exclude source account
                    account_name = row[1]
                    short_name = account_name[:18].strip()
                    if len(account_name) > 18:
                        short_name += "..."
                    buttons.append(QuickReplyButton(action=MessageAction(label=short_name, text=f"TO:{account_name}")))
            
            if buttons:
                return QuickReply(items=buttons)
        except:
            pass
    
    # Fallback - exclude from_account
    all_accounts = ["Family Petty Cash", "Urgent Fund", "Son's USD Fixed", "Wife's USD Fixed", "Jack's Personal"]
    dest_accounts = [a for a in all_accounts if a != from_account]
    
    if user_name == "prapa.yang":
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label=acc[:18], text=f"TO:{acc}")) for acc in dest_accounts
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label=acc[:18], text=f"TO:{acc}")) for acc in dest_accounts
        ])

def get_purpose_menu(user_name):
    """Purpose suggestion buttons"""
    if user_name == "prapa.yang":
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🍽️ ค่าอาหาร", text="PURPOSE:ค่าอาหารครอบครัว")),
            QuickReplyButton(action=MessageAction(label="🚨 เรงดวน", text="PURPOSE:เริงดวน")),
            QuickReplyButton(action=MessageAction(label="📦 ค่าบิล", text="PURPOSE:ชาระบิล")),
            QuickReplyButton(action=MessageAction(label="🎁 ของขวญ", text="PURPOSE:ของขวญ")),
            QuickReplyButton(action=MessageAction(label="อืนๆ", text="PURPOSE:อื่นๆ")),
        ])
    else:
        return QuickReply(items=[
            QuickReplyButton(action=MessageAction(label="🍽️ Family dinner", text="PURPOSE:Family dinner")),
            QuickReplyButton(action=MessageAction(label="🚨 Emergency", text="PURPOSE:Emergency")),
            QuickReplyButton(action=MessageAction(label="📦 Bills", text="PURPOSE:Bills")),
            QuickReplyButton(action=MessageAction(label="🎁 Gift", text="PURPOSE:Gift")),
            QuickReplyButton(action=MessageAction(label="📝 Other", text="PURPOSE:Other")),
        ])

def get_polite_followup(user_name, context="general"):
    """Polite follow-up question - Bank call center style"""
    if user_name == "prapa.yang":
        followups = {
            "greeting": "มีอะไรให้อารยาช่วยวันนี้บอกได้เลยครับ",
            "expense": "มีรายจ่ายอื่นๆ ต้องการบันทึกเพิ่มเติมไหมครับ? พิมพ์ข้อมูลเช่น 'ร้านจำนวน' ได้เลยครับ",
            "balance": "ต้องการทราบข้อมูลเพิ่มเติมด้านไหนอีกไหมครับ? ยินดีให้บริการตลอด 24 ชั่วโมงครับ",
            "salary": "มีสลิปเงินเดือนของเดือนหน้าที่จะอัปโหลดไหมครับ? หรือมีข้อสงสัยต้องการถามเพิ่มเติมไหมครับ",
            "transfer": "ต้องการโอนเงินเพิ่มเติมไหมครับ? หรือมีธุรกรรมอื่นๆ ที่ให้อารยาช่วยไหมครับ",
            "budget": "ต้องการตั้งงบประมาณเพิ่มเติมไหมครับ? หรือมีคำถามเกี่ยวกับการใช้จ่ายไหมครับ",
            "approval_pending": "อารยาจะแจ้งคุณแจ๊คให้อนุมัติครับ รอการยืนยันสักครู่นะครับ",
            "approval_required": "คุณแจ๊คต้องอนุมัติก่อนดำเนินการครับ อารยาจะส่งคำขอไปให้คุณแจ๊คครับ",
            "general": "มีข้อสงสัยอื่นๆ หรือต้องการบันทึกรายจ่ายเพิ่มเติมไหมครับ? ยินดีให้บริการครับ"
        }
        return followups.get(context, followups["general"])
    else:
        followups = {
            "greeting": "How can I assist you today?",
            "expense": "Any other expenses to log? Just type 'vendor amount'!",
            "balance": "Would you like more details on any category?",
            "salary": "Do you have more salary slips to upload?",
            "transfer": "Any other transfers or transactions today?",
            "budget": "Would you like to set more budgets or check spending limits?",
            "approval_pending": "I've sent a notification to Prapa for approval. She'll be notified shortly.",
            "approval_required": "This requires Prapa's approval. I'll send her a notification now.",
            "general": "Any other questions or expenses to log today?"
        }
        return followups.get(context, followups["general"])

def handle_transfer_step(user_id, user_name, text, flow_state):
    """Handle multi-step transfer flow with buttons"""
    step = flow_state['step']
    data = flow_state.get('data', {})
    
    print(f"💸 Transfer Step {step}: {text}")
    
    # === STEP 1: Select SOURCE account (buttons: FROM:xxx) ===
    if step == 1:
        if text.startswith("FROM:"):
            from_account = text[5:]  # Remove "FROM:" prefix
            
            data['from_account'] = from_account
            
            user_flow_state[user_id] = {'flow': 'transfer', 'step': 2, 'data': data}
            
            reply = f"✅ From: {from_account}\n\nWhere to transfer to?" if user_name != "prapa.yang" else f"✅ จาก: {from_account}\n\nตองการโอนไปบัญชีไหนครับ?"
            # Show destination buttons (exclude source)
            send_bank_response(user_id, user_name, reply, "transfer", get_transfer_dest_menu(user_name, from_account))
            return
        else:
            # User typed instead of clicking - treat as account name
            data['from_account'] = text
            user_flow_state[user_id] = {'flow': 'transfer', 'step': 2, 'data': data}
            reply = f"✅ From: {text}\n\nWhere to transfer to?" if user_name != "prapa.yang" else f"✅ จาก: {text}\n\nตองการโอนไปบัญชีไหนครับ?"
            send_bank_response(user_id, user_name, reply, "transfer", get_transfer_dest_menu(user_name, text))
            return
    
    # === STEP 2: Select DESTINATION account (buttons: TO:xxx) ===
    elif step == 2:
        if text.startswith("TO:"):
            to_account = text[3:]  # Remove "TO:" prefix
            
            # Check not same as source
            if to_account == data.get('from_account'):
                reply = "⚠️ Can't transfer to the same account. Please select a different one." if user_name != "prapa.yang" else "⚠️ ไมสามารถโอนไปบัญชีเดียวกันไดครับ กรุณาเลือกบัญชีใหม่นะครับ"
                send_bank_response(user_id, user_name, reply, "transfer", get_transfer_dest_menu(user_name, data['from_account']))
                return
            
            data['to_account'] = to_account
            
            user_flow_state[user_id] = {'flow': 'transfer', 'step': 3, 'data': data}
            
            reply = f"✅ To: {to_account}\n\nWhat's this transfer for?" if user_name != "prapa.yang" else f"✅ ไป: {to_account}\n\nโอนเงินนี้เพืออะไรครับ?"
            # Show purpose suggestions
            send_bank_response(user_id, user_name, reply, "transfer", get_purpose_menu(user_name))
            return
        else:
            # User typed destination
            if text == data.get('from_account'):
                reply = "⚠️ Can't transfer to the same account. Please select a different one." if user_name != "prapa.yang" else "⚠️ ไมสามารถโอนไปบัญชีเดียวกันไดครับ"
                send_bank_response(user_id, user_name, reply, "transfer", get_transfer_dest_menu(user_name, data['from_account']))
                return
            
            data['to_account'] = text
            user_flow_state[user_id] = {'flow': 'transfer', 'step': 3, 'data': data}
            reply = f"✅ To: {text}\n\nWhat's this transfer for?" if user_name != "prapa.yang" else f"✅ ไป: {text}\n\nโอนเงินนี้เพืออะไรครับ?"
            send_bank_response(user_id, user_name, reply, "transfer", get_purpose_menu(user_name))
            return
    
    # === STEP 3: Purpose (buttons: PURPOSE:xxx or custom text) ===
    elif step == 3:
        if text.startswith("PURPOSE:"):
            purpose = text[8:]  # Remove "PURPOSE:" prefix
            data['purpose'] = purpose
        else:
            data['purpose'] = text
        
        user_flow_state[user_id] = {'flow': 'transfer', 'step': 4, 'data': data}
        
        reply = "💰 How much would you like to transfer? (just type the number)" if user_name != "prapa.yang" else "💰 ตองการโอนจำนวนเทาไหรครับ? (พิมพเฉพาะตัวเลข)"
        # No buttons - user types amount
        send_bank_response(user_id, user_name, reply, "transfer", None)
        return
    
    # === STEP 4: Amount (user types number) ===
    elif step == 4:
        try:
            amount = float(text.replace(',', ''))
            if amount <= 0:
                raise ValueError("Amount must be positive")
            
            data['amount'] = amount
            
            # CREATE APPROVAL REQUEST
            from approval_workflow import create_request
            request_id, approver = create_request(
                sh,
                user_id,
                user_name,
                'Transfer',
                data['purpose'],
                amount=data['amount'],
                from_acc=data['from_account'],
                to_acc=data['to_account']
            )
            
            del user_flow_state[user_id]
            
            reply = f"✅ Transfer request created!\n\nFrom: {data['from_account']}\nTo: {data['to_account']}\nAmount: {data['amount']:,.2f} NTD\nPurpose: {data['purpose']}\n\nRequest ID: {request_id}\nSent to: {approver}\n\nWaiting for approval..." if user_name != "prapa.yang" else f"✅ สรางคำขอโอนแลว!\n\nจาก: {data['from_account']}\nไป: {data['to_account']}\nจำนวน: {data['amount']:,.2f} บาท\nเหตผล: {data['purpose']}\n\nรหัสคำขอ: {request_id}\nสงไป: {approver}\n\nรอการอนุมัต..."
            
            send_bank_response(user_id, user_name, reply, "transfer", get_main_menu(user_name))
            
            # TODO: Send notification to approver
            
            return
            
        except ValueError:
            reply = "Hmm, that doesn't look like an amount. Could you enter just the number? (e.g., 1000)" if user_name != "prapa.yang" else "ขอโทษครับ ดูเหมือนยังไมใชจำนวนเงิน กรุณาใสเฉพาะตัวเลขครับ (เช่น 1000)"
            send_bank_response(user_id, user_name, reply, "transfer", None)
            return
    
    # Unknown step - reset
    else:
        del user_flow_state[user_id]
        reply = "⚠️ Transfer session expired. Please start over." if user_name != "prapa.yang" else "⚠️ รายการโอนหมดเวลา กรุณาเรมใหม่นะครับ"
        send_bank_response(user_id, user_name, reply, "transfer", get_main_menu(user_name))

def send_bank_response(user_id, user_name, main_text, followup_context="general", quick_reply=None):
    """Send professional two-message bank response"""
    try:
        # Message 1: Main response (no Quick Reply)
        msg1 = TextSendMessage(text=main_text)
        
        # Message 2: Polite follow-up + Quick Reply (LINE shows QR on last message)
        msg2 = TextSendMessage(
            text=get_polite_followup(user_name, followup_context),
            quick_reply=quick_reply or get_main_menu(user_name)
        )
        
        line_bot_api.push_message(user_id, [msg1, msg2])
        return True
    except Exception as e:
        print(f"⚠️ Send failed: {e}")
        # Fallback: send text only
        line_bot_api.push_message(user_id, TextSendMessage(text=main_text))
        return False


def send_approval_card(user_id, request_id, request_type, details, amount, from_account, to_account, requester):
    """Send Approval Request Flex Message Card"""
    try:
        # Create the Flex Message bubble
        flex_bubble = create_approval_card(
            request_id=request_id,
            request_type=request_type,
            details=details,
            amount=amount,
            from_account=from_account,
            to_account=to_account,
            requester=requester
        )
        
        # Send as Flex Message
        line_bot_api.push_message(
            user_id,
            FlexMessage(
                alt_text=f"Approval Request: {request_type} - {amount}",
                contents=flex_bubble
            )
        )
        return True
    except Exception as e:
        print(f"⚠️ Failed to send approval card: {e}")
        # Fallback to text
        fallback_text = format_approval_message(request_id, request_type, details, amount, from_account, to_account, requester)
        line_bot_api.push_message(user_id, TextSendMessage(text=fallback_text))
        return False


def send_receipt_card(user_id, vendor, amount, category, user_name):
    """Send Receipt Confirmation Flex Message Card"""
    try:
        flex_bubble = create_receipt_confirmation_card(vendor, amount, category, user_name)
        
        line_bot_api.push_message(
            user_id,
            FlexMessage(
                alt_text=f"Confirm expense: {vendor} {amount}",
                contents=flex_bubble
            )
        )
        return True
    except Exception as e:
        print(f"⚠️ Failed to send receipt card: {e}")
        # Fallback to text
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
    
    # Ensure Google Sheets is initialized
    init_google_sheets()
    
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
    
    # === CHECK ACTIVE FLOW STATE FIRST ===
    if user_id in user_flow_state:
        flow = user_flow_state[user_id]
        print(f"🔄 Continuing flow: {flow['flow']} step {flow['step']}")
        
        if flow['flow'] == 'transfer':
            return handle_transfer_step(user_id, user_name, text, flow)
    
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
    
    # === CHECK PENDING APPROVALS ===
    if text == "Check pending approvals" or text == "ตรวจสอบคำขออนุมัต":
        if gc:
            pending = get_pending_approvals(sh, user_name)
            
            if not pending:
                if user_name == "prapa.yang":
                    reply = "✅ ไมมีคำขออนุมัติคงคางครับ - รายการทั้งหมดไดรับอนุมัติแลวครับ"
                else:
                    reply = "✅ No pending approvals - all requests have been processed."
                send_bank_response(user_id, user_name, reply, "general", get_main_menu(user_name))
            else:
                # Send each approval as a Flex Card
                for req in pending[:5]:  # Show first 5
                    send_approval_card(
                        user_id=user_id,
                        request_id=req["request_id"],
                        request_type=req["type"],
                        details=req["details"],
                        amount=float(req["amount"]) if req["amount"] else 0,
                        from_account=req["from_acc"],
                        to_account=req["to_acc"],
                        requester=req["requester"]
                    )
                
                # Send follow-up with instructions
                if user_name == "prapa.yang":
                    followup = f"📋 มี {len(pending)} คำขออนุมัติรอการตรวจสอบ\n\nแตะปุ่ม ✅ Approve หรือ ❌ Reject ในบัตรด้านล่างเพื่อดำเนินการครับ"
                else:
                    followup = f"📋 {len(pending)} approval(s) pending\n\nTap ✅ Approve or ❌ Reject on the cards above to process."
                
                send_bank_response(user_id, user_name, followup, "general", get_main_menu(user_name))
        else:
            reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานข้อมูลไม่สามารถเชื่อมต่อได้"
            send_bank_response(user_id, user_name, reply, "general")
        return
    
    # === APPROVE/REJECT REQUESTS ===
    if text.lower().startswith("approve") or text.lower().startswith("อนุมัต"):
        req_id = text.split()[-1] if len(text.split()) > 1 else None
        if req_id and gc:
            success, status = approve_request(sh, req_id, user_name)
            if success:
                if user_name == "prapa.yang":
                    reply = f"✅ อนุมัตคำขอ {req_id} เรยรอยครับ - ทำรายการแลว!"
                else:
                    reply = f"✅ Request {req_id} approved - transaction executed!"
            else:
                reply = f"⚠️ Failed to approve {req_id}" if user_name != "prapa.yang" else f"⚠️ ไมสามารถอนุมัตได"
        else:
            reply = "Please specify request ID. Example: 'Approve REQ20260817...'" if user_name != "prapa.yang" else "กรุณาระบุรหัสคำขอ เช่น 'อนุมัต REQ20260817...'"
        send_bank_response(user_id, user_name, reply, "general")
        return
    
    if text.lower().startswith("reject") or text.lower().startswith("ปฏเสธ"):
        req_id = text.split()[-1] if len(text.split()) > 1 else None
        if req_id and gc:
            success, status = reject_request(sh, req_id, user_name, "Rejected by approver")
            if success:
                if user_name == "prapa.yang":
                    reply = f"❌ ปฏเสธคำขอ {req_id} เรยรอยครับ"
                else:
                    reply = f"❌ Request {req_id} rejected."
            else:
                reply = f"⚠️ Failed to reject {req_id}" if user_name != "prapa.yang" else f"⚠️ ไมสามารถปฏเสธได"
        else:
            reply = "Please specify request ID. Example: 'Reject REQ20260817...'" if user_name != "prapa.yang" else "กรุณาระบุรหัสคำขอ เช่น 'ปฏเสธ REQ20260817...'"
        send_bank_response(user_id, user_name, reply, "general")
        return
    
    # === SET BUDGET (Requires Approval) ===
    if text == "Set budget" or text == "ตังงบประมาณ":
        if user_name == "prapa.yang":
            reply = (
                "📋 **ตังงบประมาณ**\n\n"
                "อารยาชวยบอกขอมูลครับ:\n"
                "1. หมวดหมู่? (Family/Personal/Urgent/Food/Transport)\n"
                "2. จำนวนเงินตอเดือน?\n"
                "3. หมายเหตุ (ถาม)\n\n"
                "⚠️ คุณแจ๊คตองอนุมัตกอนใชงานครับ"
            )
        else:
            reply = (
                "📋 **Set Budget**\n\n"
                "Please provide:\n"
                "1. Category? (Family/Personal/Urgent/Food/Transport)\n"
                "2. Monthly amount?\n"
                "3. Notes (optional)\n\n"
                "⚠️ This requires Prapa's approval before activation."
            )
        send_bank_response(user_id, user_name, reply, "budget")
        return
    
    # === ACCOUNT SETTINGS (Replaced Open Account) ===
    if text == "Account settings" or text == "ตังค่าบญช":
        if gc:
            try:
                acc = sh.worksheet("Accounts")
                accounts = acc.get_all_values()[1:6]  # Show first 5 pre-seeded pockets
                
                if user_name == "prapa.yang":
                    acc_list = "\n".join([f"{i+1}. {row[1]} ({row[3]}) - {row[8]}" for i, row in enumerate(accounts) if row])
                    reply = (
                        f"⚙️ **ตังค่าบญช**\n\n"
                        f"📋 **5 บญชทตังคาไว**:\n\n{acc_list}\n\n"
                        f"⚠️ บญชทงหมดตองการอนุมัตจากทงสองฝาย\n\n"
                        f"ตองการ:\n"
                        f"1. พมพ 'ขอเปดบญชใหม' เพ่อรองขอ\n"
                        f"2. พมพ 'โอนเงิน' เพ่อโอนระหวางบญช"
                    )
                else:
                    acc_list = "\n".join([f"{i+1}. {row[1]} ({row[3]}) - {row[8]}" for i, row in enumerate(accounts) if row])
                    reply = (
                        f"⚙️ **Account Settings**\n\n"
                        f"📋 **5 Pre-Configured Accounts**:\n\n{acc_list}\n\n"
                        f"⚠️ All accounts require dual approval\n\n"
                        f"To:\n"
                        f"1. Type 'Request new account' to propose new account\n"
                        f"2. Type 'Transfer' to transfer between accounts"
                    )
                
                send_bank_response(user_id, user_name, reply, "general", get_main_menu(user_name))
            except Exception as e:
                reply = f"⚠️ Error: {e}" if user_name != "prapa.yang" else f"⚠️ ผดพลาด: {e}"
                send_bank_response(user_id, user_name, reply, "general")
        else:
            reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานขอมูลไมสามารถเช่อมตอได"
            send_bank_response(user_id, user_name, reply, "general")
        return
    
    # === REQUEST NEW ACCOUNT (Requires Approval) ===
    if text == "Request new account" or text.startswith("ขอเปดบญชใหม"):
        if user_name == "prapa.yang":
            reply = (
                "🏦 **รองขอเปดบญชใหม**\n\n"
                "อารยาชวยบอกขอมูลครับ:\n"
                "1. ชื่อบญชทตองการ?\n"
                "2. ประเภทบญช? (กระเป๋า/ธนาคาร)\n"
                "3. เงินเรมตนเทาไร?\n"
                "4. เปดเพออะไรครับ?\n\n"
                "⚠️ คุณแจ๊คตองอนุมัตกอนเปดบญชครับ"
            )
        else:
            reply = (
                "🏦 **Request New Account**\n\n"
                "Please provide:\n"
                "1. Account name?\n"
                "2. Account type? (Pocket/Bank)\n"
                "3. Initial deposit?\n"
                "4. Purpose?\n\n"
                "⚠️ This requires Prapa's approval before creation."
            )
        send_bank_response(user_id, user_name, reply, "general")
        return
    
    # === TRANSFER BETWEEN ACCOUNTS (BUTTON FLOW) ===
    if text == "Transfer between accounts" or text == "โอนระหวางบญช":
        if gc:
            try:
                acc = sh.worksheet("Accounts")
                accounts = acc.get_all_values()[1:]  # Skip header
                
                if user_name == "prapa.yang":
                    acc_list = "\n".join([f"{i+1}. {row[1]} ({row[3]})" for i, row in enumerate(accounts) if row])
                    reply = f"📋 **บญชทมี**:\n\n{acc_list}\n\nเลอกบญชทตองการโอนครับ\n⚠️ คณแจ๊คตองอนมตกอนโอนครับ"
                else:
                    acc_list = "\n".join([f"{i+1}. {row[1]} ({row[3]})" for i, row in enumerate(accounts) if row])
                    reply = f"📋 **Available Accounts**:\n\n{acc_list}\n\nSelect account to transfer from.\n⚠️ This requires Prapa's approval."
                
                # Set flow state for step 1
                user_flow_state[user_id] = {'flow': 'transfer', 'step': 1, 'data': {}}
                
                # Send with account selection buttons
                send_bank_response(user_id, user_name, reply, "transfer", get_transfer_source_menu(user_name))
            except Exception as e:
                reply = f"⚠️ Error: {e}" if user_name != "prapa.yang" else f"⚠️ ผิดพลาด: {e}"
                send_bank_response(user_id, user_name, reply, "transfer")
        else:
            reply = "⚠️ Database offline" if user_name != "prapa.yang" else "⚠️ ฐานขอมูลไมสามารถเชื่อมตอได"
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
    
    # Ensure Google Sheets is initialized
    init_google_sheets()
    
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
    """Health check endpoint"""
    return {"status": "Yang Family Finance Agent Active", "version": "3.0-preseed"}

@app.get("/health")
def health():
    """Detailed health check - Cloud Run startup verification"""
    try:
        sheets_ok = init_google_sheets()
    except:
        sheets_ok = False
    
    ai_ok = di_client is not None
    line_ok = line_bot_api is not None
    
    status = "healthy" if all([sheets_ok, ai_ok, line_ok]) else "degraded"
    
    return {
        "status": status,
        "version": "3.0-preseed",
        "sheets": "connected" if sheets_ok else "disconnected",
        "ai": "connected" if ai_ok else "disconnected",
        "line": "connected" if line_ok else "disconnected"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Starting Yang Family Finance Bot on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
