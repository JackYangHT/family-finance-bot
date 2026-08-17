"""
Yang Family Finance Bot - Complete Google Sheets Setup
Creates 12 tabs with full banking system structure
"""
import os
import sys
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

print("🔐 Connecting to Google Sheets...")

# Find credentials
creds_paths = [
    "/app/credentials.json",
    "credentials.json",
    ".venv/Scripts/credentials.json"
]

creds = None
for path in creds_paths:
    if os.path.exists(path):
        print(f"✅ Found credentials: {path}")
        creds = Credentials.from_service_account_file(path, scopes=SCOPES)
        break

if not creds:
    print("❌ No credentials found!")
    sys.exit(1)

try:
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    print(f"✅ Connected to: {sh.title}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# =============================================================================
# Clear Existing Tabs (keep first one)
# =============================================================================
print("\n🗑️ Clearing old tabs...")
all_worksheets = sh.worksheets()
for ws in all_worksheets[1:]:
    try:
        sh.del_worksheet(ws)
    except:
        pass

# =============================================================================
# Tab 1: Raw_Expenses
# =============================================================================
print("\n💰 Creating Raw_Expenses...")
try:
    sh.del_worksheet(sh.worksheet("Raw_Expenses"))
except:
    pass
exp_ws = sh.add_worksheet("Raw_Expenses", 1000, 12)

exp_ws.append_row([
    "Timestamp", "User", "User Name", "Category", "Amount (TWD)", "Vendor/Note",
    "Payment Method", "Receipt?", "Pocket/Account", "Raw Input", "Language", "Chat Log ID"
])
exp_ws.format('A1:L1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
exp_ws.freeze(1)
print("  ✅ Raw_Expenses created")

# =============================================================================
# Tab 2: Raw_Income
# =============================================================================
print("\n💵 Creating Raw_Income...")
try:
    sh.del_worksheet(sh.worksheet("Raw_Income"))
except:
    pass
inc_ws = sh.add_worksheet("Raw_Income", 1000, 14)

inc_ws.append_row([
    "Timestamp", "User", "Person", "Type", "Gross Amount", "Currency",
    "Withholding Tax", "NHI", "Labor Ins", "Pension 6%", "Meal Allowance",
    "Net Pay", "Source Document", "Language"
])
inc_ws.format('A1:N1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.9}})
inc_ws.freeze(1)
print("  ✅ Raw_Income created")

# =============================================================================
# Tab 3: Raw_Payroll_Tax (Taiwan Tax Compliance)
# =============================================================================
print("\n📋 Creating Raw_Payroll_Tax...")
try:
    sh.del_worksheet(sh.worksheet("Raw_Payroll_Tax"))
except:
    pass
tax_ws = sh.add_worksheet("Raw_Payroll_Tax", 1000, 14)

tax_ws.append_row([
    "Timestamp", "Person", "Gross Pay", "Withholding Tax (扣繳)", "NHI (健保費)",
    "Labor Ins (勞保費)", "Employment Ins", "Pension Voluntary 6% (勞退自提)",
    "Meal Allowance", "Other Deductions", "Net Pay (實發)", "Tax Refund Status", "Source"
])
tax_ws.format('A1:M1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.9, 'blue': 0.9}})
tax_ws.freeze(1)
print("  ✅ Raw_Payroll_Tax created")

# =============================================================================
# Tab 4: Accounts (NEW - All Family Accounts)
# =============================================================================
print("\n🏦 Creating Accounts...")
try:
    sh.del_worksheet(sh.worksheet("Accounts"))
except:
    pass
acc_ws = sh.add_worksheet("Accounts", 20, 8)

acc_ws.append_row([
    "Account ID", "Account Name", "Type", "Currency", "Owner",
    "Current Balance", "Last Updated", "Status"
])

# Pre-populate 5 pockets + 2 bank accounts
accounts_data = [
    ["ACC001", "Family Petty Cash", "Pocket", "NTD", "Family", "=SUMIF('Raw_Expenses'!I:I, 'Accounts'!B2, 'Raw_Expenses'!E:E)*-1", "=NOW()", "Active"],
    ["ACC002", "Urgent Fund", "Pocket", "NTD", "Family", "=SUMIF('Raw_Expenses'!I:I, 'Accounts'!B3, 'Raw_Expenses'!E:E)*-1", "=NOW()", "Active"],
    ["ACC003", "Son's USD Fixed", "Pocket", "USD", "Son", "0", "=NOW()", "Active"],
    ["ACC004", "Wife's USD Fixed", "Pocket", "USD", "Prapa", "0", "=NOW()", "Active"],
    ["ACC005", "Jack's Personal", "Pocket", "NTD", "Jack", "=SUMIF('Raw_Expenses'!I:I, 'Accounts'!B6, 'Raw_Expenses'!E:E)*-1", "=NOW()", "Active"],
    ["ACC006", "Taiwan Bank Salary", "Bank", "NTD", "Jack", "0", "=NOW()", "Active"],
    ["ACC007", "USD Offshore Account", "Bank", "USD", "Jack", "0", "=NOW()", "Active"],
]

for i, row in enumerate(accounts_data):
    acc_ws.append_row(row)

acc_ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.8}})
acc_ws.freeze(1)
acc_ws.format('F2:F8', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
print("  ✅ Accounts created (7 accounts)")

# =============================================================================
# Tab 5: Transfers (NEW - Money Movement)
# =============================================================================
print("\n💸 Creating Transfers...")
try:
    sh.del_worksheet(sh.worksheet("Transfers"))
except:
    pass
trans_ws = sh.add_worksheet("Transfers", 500, 9)

trans_ws.append_row([
    "Timestamp", "From Account", "To Account", "Amount", "Currency",
    "Exchange Rate", "Amount After FX", "Purpose", "User"
])

trans_ws.format('A1:I1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.9, 'blue': 0.95}})
trans_ws.freeze(1)
print("  ✅ Transfers created")

# =============================================================================
# Tab 6: Exchange_Rates
# =============================================================================
print("\n💱 Creating Exchange_Rates...")
try:
    sh.del_worksheet(sh.worksheet("Exchange_Rates"))
except:
    pass
rate_ws = sh.add_worksheet("Exchange_Rates", 500, 5)

rate_ws.append_row(["Date", "USD_NTD", "Source", "Last Updated", "Notes"])
rate_ws.append_row(["=TODAY()", "32.5", "Taiwan Bank", "=NOW()", "Current rate"])

rate_ws.format('A1:E1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.85, 'blue': 0.95}})
rate_ws.freeze(1)
print("  ✅ Exchange_Rates created")

# =============================================================================
# Tab 7: Dashboard_Summary
# =============================================================================
print("\n📊 Creating Dashboard_Summary...")
try:
    sh.del_worksheet(sh.worksheet("Dashboard_Summary"))
except:
    pass
dash_ws = sh.add_worksheet("Dashboard_Summary", 30, 4)

dashboard_data = [
    ["YANG FAMILY FINANCE DASHBOARD", "", "", "=NOW()"],
    ["", "", "", ""],
    ["💰 INCOME SUMMARY", "", "", ""],
    ["Total Income (YTD)", "=SUM('Raw_Income'!E:E)", "TWD", ""],
    ["Prepaid Tax", "=SUM('Raw_Payroll_Tax'!C:C)", "TWD", ""],
    ["Net Income", "=B4-B5", "TWD", ""],
    ["", "", "", ""],
    ["📊 EXPENSE SUMMARY", "", "", ""],
    ["Total Expenses (YTD)", "=SUM('Raw_Expenses'!E:E)", "TWD", ""],
    ["Family Petty Cash", "=SUMIF('Raw_Expenses'!I:I, 'Family Petty Cash', 'Raw_Expenses'!E:E)*-1", "TWD", ""],
    ["Personal", "=SUMIF('Raw_Expenses'!I:I, 'Personal', 'Raw_Expenses'!E:E)*-1", "TWD", ""],
    ["Urgent", "=SUMIF('Raw_Expenses'!I:I, 'Urgent', 'Raw_Expenses'!E:E)*-1", "TWD", ""],
    ["Food", "=SUMIF('Raw_Expenses'!D:D, 'Food', 'Raw_Expenses'!E:E)*-1", "TWD", ""],
    ["", "", "", ""],
    ["💰 SAVINGS", "", "", ""],
    ["Net Savings", "=B6-B10", "TWD", ""],
    ["Savings Rate", "=IF(B4>0, B16/B4, 0)", "%", ""],
    ["", "", "", ""],
    ["🏦 ACCOUNT BALANCES", "", "", ""],
    ["Family Petty Cash", "=Accounts!F2", "TWD", "Pocket"],
    ["Urgent Fund", "=Accounts!F3", "TWD", "Pocket"],
    ["Son's USD", "=Accounts!F4", "USD", "Pocket"],
    ["Wife's USD", "=Accounts!F5", "USD", "Pocket"],
    ["Jack's Personal", "=Accounts!F6", "TWD", "Pocket"],
    ["Taiwan Bank", "=Accounts!F7", "TWD", "Bank"],
    ["USD Offshore", "=Accounts!F8", "USD", "Bank"],
    ["", "", "", ""],
    ["NET WORTH (NTD)", "=B20+B23+B26+(B21+B24)*Exchange_Rates!B2", "TWD", "Total"],
]

for i, row in enumerate(dashboard_data):
    if row:
        dash_ws.update(f'A{i+1}:D{i+1}', [row])

dash_ws.format('A1:D30', {'horizontalAlignment': 'LEFT'})
dash_ws.format('A1:A1', {'textFormat': {'bold': True, 'fontSize': 14}, 'horizontalAlignment': 'CENTER'})
dash_ws.format('A3:A3', {'textFormat': {'bold': True}})
dash_ws.format('A8:A8', {'textFormat': {'bold': True}})
dash_ws.format('A15:A15', {'textFormat': {'bold': True}})
dash_ws.format('A19:A19', {'textFormat': {'bold': True}})
dash_ws.format('A28:A28', {'textFormat': {'bold': True, 'fontSize': 12}})
dash_ws.format('B4:B6', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B10:B13', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B16:B17', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B20:B27', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B28:B28', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT', 'textFormat': {'bold': True}})

dash_ws.column_dimensions['A'] = {'pixelSize': 200}
dash_ws.column_dimensions['B'] = {'pixelSize': 150}
dash_ws.column_dimensions['C'] = {'pixelSize': 80}
dash_ws.column_dimensions['D'] = {'pixelSize': 100}

print("  ✅ Dashboard_Summary created with formulas")

# =============================================================================
# Tab 8: Chat_Logs
# =============================================================================
print("\n💬 Creating Chat_Logs...")
try:
    sh.del_worksheet(sh.worksheet("Chat_Logs"))
except:
    pass
chat_ws = sh.add_worksheet("Chat_Logs", 1000, 9)

chat_ws.append_row([
    "Timestamp", "User ID", "User Name", "Language", "Message Type",
    "Raw Message", "AI Response", "Action", "Status"
])
chat_ws.format('A1:I1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.95}})
chat_ws.freeze(1)
print("  ✅ Chat_Logs created")

# =============================================================================
# Tab 9: Monthly_Analysis
# =============================================================================
print("\n📈 Creating Monthly_Analysis...")
try:
    sh.del_worksheet(sh.worksheet("Monthly_Analysis"))
except:
    pass
monthly_ws = sh.add_worksheet("Monthly_Analysis", 50, 10)

monthly_ws.append_row([
    "Month", "Income", "Expenses", "Savings", "Savings Rate",
    "Family Cash", "Personal", "Urgent", "Food", "Transfer Out"
])
monthly_ws.format('A1:J1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.95}})
monthly_ws.freeze(1)
print("  ✅ Monthly_Analysis created")

# =============================================================================
# Tab 10: Tax_Summary (Taiwan)
# =============================================================================
print("\n🇹🇼 Creating Tax_Summary...")
try:
    sh.del_worksheet(sh.worksheet("Tax_Summary"))
except:
    pass
tax_sum_ws = sh.add_worksheet("Tax_Summary", 30, 8)

tax_sum_ws.append_row([
    "Person", "Gross Pay", "Withholding Tax", "NHI", "Labor Ins",
    "Pension 6%", "Total Deductions", "Net Pay"
])
tax_sum_ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.85, 'blue': 0.85}})
tax_sum_ws.freeze(1)
print("  ✅ Tax_Summary created")

# =============================================================================
# Tab 11: Budget_Planning (NEW)
# =============================================================================
print("\n📋 Creating Budget_Planning...")
try:
    sh.del_worksheet(sh.worksheet("Budget_Planning"))
except:
    pass
budget_ws = sh.add_worksheet("Budget_Planning", 50, 7)

budget_ws.append_row([
    "Category", "Monthly Budget", "Actual (MTD)", "Remaining", "Usage %",
    "Status", "Notes"
])
budget_ws.format('A1:G1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.9, 'blue': 0.95}})
budget_ws.freeze(1)
print("  ✅ Budget_Planning created")

# =============================================================================
# Tab 12: AI_Conversations (NEW - Account Opening, Transfer Requests)
# =============================================================================
print("\n🤖 Creating AI_Conversations...")
try:
    sh.del_worksheet(sh.worksheet("AI_Conversations"))
except:
    pass
ai_ws = sh.add_worksheet("AI_Conversations", 500, 8)

ai_ws.append_row([
    "Timestamp", "User ID", "User Name", "Request Type", "Conversation",
    "Extracted Data", "Status", "Completed At"
])
ai_ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.85, 'blue': 0.9}})
ai_ws.freeze(1)
print("  ✅ AI_Conversations created")

# =============================================================================
# Final Summary
# =============================================================================
print("\n" + "="*60)
print("✅ GOOGLE SHEETS SETUP COMPLETE!")
print("="*60)
print(f"\n📊 Spreadsheet: {sh.title}")
print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print(f"\n📋 Tabs created (12):")
print("   1. Raw_Expenses")
print("   2. Raw_Income")
print("   3. Raw_Payroll_Tax")
print("   4. Accounts (7 family accounts)")
print("   5. Transfers")
print("   6. Exchange_Rates")
print("   7. Dashboard_Summary (with formulas)")
print("   8. Chat_Logs")
print("   9. Monthly_Analysis")
print("  10. Tax_Summary")
print("  11. Budget_Planning")
print("  12. AI_Conversations")
print(f"\n👤 Service Account: {creds.service_account_email}")
print(f"   Make sure this email has Editor access!")
print("\n🎉 Ready for banking system!")
