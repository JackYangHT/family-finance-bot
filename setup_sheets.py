"""
Yang Family Finance Bot - Google Sheets Setup
Creates 10 tabs with formulas for complete accounting system
"""
import os
import sys
from google.oauth2.service_account import Credentials
import gspread

# =============================================================================
# 1. Connect to Google Sheets
# =============================================================================
SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
SPREADSHEET_NAME = "Yang Family Finance"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

print("🔐 Connecting to Google Sheets...")

# Try Cloud Run path first, then local
creds_paths = [
    "/app/credentials.json",
    "credentials.json",
    ".venv/Scripts/credentials.json",
    os.path.expanduser("~/.config/gcloud/credentials.json")
]

creds = None
for path in creds_paths:
    if os.path.exists(path):
        print(f"✅ Found credentials: {path}")
        creds = Credentials.from_service_account_file(path, scopes=SCOPES)
        break

if not creds:
    print("❌ No credentials found! Please check the path.")
    sys.exit(1)

try:
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    print(f"✅ Connected to: {sh.title}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\n🔧 Try sharing the sheet with the service account email:")
    print(f"   Service Account: {creds.service_account_email}")
    print(f"   Share with Editor access at: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    sys.exit(1)

# =============================================================================
# 2. Create/Reset All Tabs
# =============================================================================
print("\n📊 Setting up 10 tabs...")

# Clear existing tabs (except the first one which we'll reuse)
all_worksheets = sh.worksheets()
for ws in all_worksheets[1:]:
    try:
        sh.del_worksheet(ws)
        print(f"  Deleted: {ws.title}")
    except:
        pass

# =============================================================================
# Tab 1: Raw_Expenses
# =============================================================================
print("\n💰 Creating Raw_Expenses...")
try:
    exp_ws = sh.worksheet("Raw_Expenses")
    sh.del_worksheet(exp_ws)
except:
    pass
exp_ws = sh.add_worksheet("Raw_Expenses", 1000, 12)

exp_ws.append_row([
    "Timestamp", "User", "Category", "Amount (TWD)", "Vendor/Note", 
    "Payment Method", "Receipt?", "Tax Deductible?", "Raw Input (EN/TH/ZH)", "Chat Log ID"
])

# Format header
exp_ws.format('A1:J1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
exp_ws.freeze(1)

print("  ✅ Raw_Expenses created")

# =============================================================================
# Tab 2: Raw_Income
# =============================================================================
print("\n💵 Creating Raw_Income...")
try:
    inc_ws = sh.worksheet("Raw_Income")
    sh.del_worksheet(inc_ws)
except:
    pass
inc_ws = sh.add_worksheet("Raw_Income", 1000, 12)

inc_ws.append_row([
    "Timestamp", "Person", "Type", "Gross Amount", "Currency", "Withholding Tax", 
    "NHI", "Labor Ins", "Pension 6%", "Meal Allowance", "Net Pay", "Source Document"
])

inc_ws.format('A1:L1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.9}})
inc_ws.freeze(1)

print("  ✅ Raw_Income created")

# =============================================================================
# Tab 3: Raw_Payroll_Tax
# =============================================================================
print("\n📋 Creating Raw_Payroll_Tax...")
try:
    tax_ws = sh.worksheet("Raw_Payroll_Tax")
    sh.del_worksheet(tax_ws)
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
# Tab 4: Chat_Logs
# =============================================================================
print("\n💬 Creating Chat_Logs...")
try:
    chat_ws = sh.worksheet("Chat_Logs")
    sh.del_worksheet(chat_ws)
except:
    pass
chat_ws = sh.add_worksheet("Chat_Logs", 1000, 8)

chat_ws.append_row([
    "Timestamp", "User ID", "User Name", "Message Type", "Raw Message", 
    "AI Response", "Action", "Status"
])

chat_ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.95}})
chat_ws.freeze(1)

print("  ✅ Chat_Logs created")

# =============================================================================
# Tab 5: Pockets
# =============================================================================
print("\n🏦 Creating Pockets...")
try:
    pocket_ws = sh.worksheet("Pockets")
    sh.del_worksheet(pocket_ws)
except:
    pass
pocket_ws = sh.add_worksheet("Pockets", 10, 5)

pocket_ws.append_row(["Pocket Name", "Currency", "Balance", "Last Updated", "Notes"])
pocket_ws.append_row(["Family Petty Cash", "NTD", "=SUMIF('Raw_Expenses'!C:C, 'Pockets'!A2, 'Raw_Expenses'!D:D)*-1", "", "Monthly household expenses"])
pocket_ws.append_row(["Urgent Fund", "NTD", "=SUMIF('Raw_Expenses'!C:C, 'Pockets'!A3, 'Raw_Expenses'!D:D)*-1", "", "Emergency fund"])
pocket_ws.append_row(["Son's USD Fixed", "USD", "0", "", "Long-term savings"])
pocket_ws.append_row(["Wife's USD Fixed", "USD", "0", "", "Prapa's personal savings"])
pocket_ws.append_row(["Jack's Personal", "NTD", "=SUMIF('Raw_Expenses'!C:C, 'Pockets'!A5, 'Raw_Expenses'!D:D)*-1", "", "Jack's spending money"])

pocket_ws.format('A1:E1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.8}})
pocket_ws.freeze(1)
pocket_ws.format('C2:C6', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})

print("  ✅ Pockets created (5 pockets)")

# =============================================================================
# Tab 6: Dashboard_Summary
# =============================================================================
print("\n📊 Creating Dashboard_Summary...")
try:
    dash_ws = sh.worksheet("Dashboard_Summary")
    sh.del_worksheet(tax_ws)
except:
    pass
dash_ws = sh.add_worksheet("Dashboard_Summary", 25, 3)

# Dashboard layout
dashboard_data = [
    ["YANG FAMILY FINANCE DASHBOARD", "", "Last Updated: =NOW()"],
    ["", "", ""],
    ["💰 INCOME", "", ""],
    ["Total Income (YTD)", "=SUM('Raw_Income'!D:D)", "TWD"],
    ["Prepaid Tax", "=SUM('Raw_Payroll_Tax'!D:D)", "TWD"],
    ["Net Income", "=B4-B5", "TWD"],
    ["", "", ""],
    ["📊 EXPENSES", "", ""],
    ["Total Expenses (YTD)", "=SUM('Raw_Expenses'!D:D)", "TWD"],
    ["Family Petty Cash", "=SUMIF('Raw_Expenses'!C:C, 'Family Petty Cash', 'Raw_Expenses'!D:D)*-1", "TWD"],
    ["Personal", "=SUMIF('Raw_Expenses'!C:C, 'Personal', 'Raw_Expenses'!D:D)*-1", "TWD"],
    ["Urgent", "=SUMIF('Raw_Expenses'!C:C, 'Urgent', 'Raw_Expenses'!D:D)*-1", "TWD"],
    ["Food", "=SUMIF('Raw_Expenses'!C:C, 'Food', 'Raw_Expenses'!D:D)*-1", "TWD"],
    ["", "", ""],
    ["💰 SAVINGS", "", ""],
    ["Net Savings", "=B6-B10", "TWD"],
    ["Savings Rate", "=IF(B4>0, B16/B4, 0)", "%"],
    ["", "", ""],
    ["🏦 POCKET BALANCES", "", ""],
    ["Family Petty Cash", "=Pockets!C2", "TWD"],
    ["Urgent Fund", "=Pockets!C3", "TWD"],
    ["Son's USD", "=Pockets!C4", "USD"],
    ["Wife's USD", "=Pockets!C5", "USD"],
    ["Jack's Personal", "=Pockets!C6", "TWD"],
]

for i, row in enumerate(dashboard_data):
    if row:
        dash_ws.update(f'A{i+1}:C{i+1}', [row])

# Format
dash_ws.format('A1:C25', {'horizontalAlignment': 'LEFT'})
dash_ws.format('A1:A1', {'textFormat': {'bold': True, 'fontSize': 14}, 'horizontalAlignment': 'CENTER'})
dash_ws.format('A3:A3', {'textFormat': {'bold': True}})
dash_ws.format('A8:A8', {'textFormat': {'bold': True}})
dash_ws.format('A15:A15', {'textFormat': {'bold': True}})
dash_ws.format('A19:A19', {'textFormat': {'bold': True}})
dash_ws.format('B4:B6', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B10:B13', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B16:B17', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})
dash_ws.format('B20:B24', {'numberFormat': {'type': 'NUMBER'}, 'horizontalAlignment': 'RIGHT'})

# Set column widths
dash_ws.column_dimensions['A'] = {'pixelSize': 250}
dash_ws.column_dimensions['B'] = {'pixelSize': 150}
dash_ws.column_dimensions['C'] = {'pixelSize': 80}

print("  ✅ Dashboard_Summary created with formulas")

# =============================================================================
# Tab 7: Monthly_Analysis
# =============================================================================
print("\n📈 Creating Monthly_Analysis...")
try:
    monthly_ws = sh.worksheet("Monthly_Analysis")
    sh.del_worksheet(monthly_ws)
except:
    pass
monthly_ws = sh.add_worksheet("Monthly_Analysis", 50, 8)

monthly_ws.append_row([
    "Month", "Income", "Expenses", "Savings", "Savings Rate", 
    "Family Cash", "Personal", "Urgent"
])

monthly_ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.95}})
monthly_ws.freeze(1)

print("  ✅ Monthly_Analysis created")

# =============================================================================
# Tab 8: Tax_Summary
# =============================================================================
print("\n🇹🇼 Creating Tax_Summary (Taiwan)...")
try:
    tax_sum_ws = sh.worksheet("Tax_Summary")
    sh.del_worksheet(tax_sum_ws)
except:
    pass
tax_sum_ws = sh.add_worksheet("Tax_Summary", 30, 6)

tax_sum_ws.append_row([
    "Person", "Gross Pay", "Withholding Tax", "NHI", "Labor Ins", "Pension 6%"
])

tax_sum_ws.format('A1:F1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.85, 'blue': 0.85}})
tax_sum_ws.freeze(1)

print("  ✅ Tax_Summary created")

# =============================================================================
# Tab 9: Transfers
# =============================================================================
print("\n💸 Creating Transfers...")
try:
    transfer_ws = sh.worksheet("Transfers")
    sh.del_worksheet(transfer_ws)
except:
    pass
transfer_ws = sh.add_worksheet("Transfers", 500, 7)

transfer_ws.append_row([
    "Timestamp", "From Pocket", "To Pocket", "Amount", "Currency", "Exchange Rate", "Notes"
])

transfer_ws.format('A1:G1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'green': 0.9, 'blue': 0.95}})
transfer_ws.freeze(1)

print("  ✅ Transfers created")

# =============================================================================
# Tab 10: Exchange_Rates
# =============================================================================
print("\n💱 Creating Exchange_Rates...")
try:
    rate_ws = sh.worksheet("Exchange_Rates")
    sh.del_worksheet(rate_ws)
except:
    pass
rate_ws = sh.add_worksheet("Exchange_Rates", 500, 4)

rate_ws.append_row(["Date", "USD_NTD_Rate", "Source", "Notes"])
rate_ws.append_row(["=TODAY()", "32.5", "Taiwan Bank", "Current rate"])

rate_ws.format('A1:D1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.85, 'blue': 0.95}})
rate_ws.freeze(1)

print("  ✅ Exchange_Rates created")

# =============================================================================
# 3. Final Summary
# =============================================================================
print("\n" + "="*60)
print("✅ GOOGLE SHEETS SETUP COMPLETE!")
print("="*60)
print(f"\n📊 Spreadsheet: {sh.title}")
print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print(f"\n📋 Tabs created (10):")
print("   1. Raw_Expenses")
print("   2. Raw_Income")
print("   3. Raw_Payroll_Tax")
print("   4. Chat_Logs")
print("   5. Pockets (5 family accounts)")
print("   6. Dashboard_Summary (with formulas)")
print("   7. Monthly_Analysis")
print("   8. Tax_Summary")
print("   9. Transfers")
print("  10. Exchange_Rates")
print(f"\n👤 Service Account: {creds.service_account_email}")
print(f"   Make sure this email has Editor access to the spreadsheet!")
print("\n🎉 Ready for testing!")
