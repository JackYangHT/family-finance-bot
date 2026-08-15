"""
Yang Family Finance Bot - Database Setup
Creates 10-tab Google Sheets structure with multi-currency support & pockets
"""
import gspread
from google.oauth2.service_account import Credentials
import os

# Google Sheets Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# Try both possible credential paths
cred_paths = [
    "credentials.json",
    r"C:\Users\Jack\Documents\family finance\family-finance-bot\.venv\Scripts\gen-lang-client-0948238290-9a5935a59f3d.json"
]

creds = None
for path in cred_paths:
    try:
        creds = Credentials.from_service_account_file(path, scopes=SCOPES)
        print(f"✅ Using credentials: {path}")
        break
    except:
        continue

if not creds:
    print("❌ No credentials found. Please upload credentials.json")
    exit(1)

gc = gspread.authorize(creds)

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
sh = gc.open_by_key(SPREADSHEET_ID)

print("🏗️  Setting up Yang Family Finance Bank database...")

# =============================================================================
# 1. Raw_Expenses (NTD only, with pocket tracking)
# =============================================================================
try:
    ws = sh.worksheet("Raw_Expenses")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Raw_Expenses", 1000, 15)
ws.append_row([
    "Timestamp", "User", "Category", "Amount (NTD)", "Vendor/Note", 
    "Pocket", "Payment Method", "Receipt?", "Tax Deductible?", 
    "Raw Input", "LINE User ID", "AI Confidence"
])
ws.format('A1:L1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 1}})
# Freeze header row
ws.freeze(rows=1)
print("✅ Raw_Expenses tab created (with Pocket column)")

# =============================================================================
# 2. Raw_Income (Multi-currency: NTD + USD)
# =============================================================================
try:
    ws = sh.worksheet("Raw_Income")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Raw_Income", 1000, 15)
ws.append_row([
    "Timestamp", "Person", "Type", "Gross Amount", "Currency", 
    "Amount in NTD", "Exchange Rate", "Withholding Tax", "NHI", 
    "Labor Ins", "Pension 6%", "Meal Allowance", "Other Deductions", 
    "Net Pay", "Pocket", "Tax Refund Status", "Source Document"
])
ws.format('A1:Q1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 1, 'blue': 0.9}})
ws.freeze(rows=1)
print("✅ Raw_Income tab created (Multi-currency)")

# =============================================================================
# 3. Raw_Payroll_Tax (Taiwan tax compliance)
# =============================================================================
try:
    ws = sh.worksheet("Raw_Payroll_Tax")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Raw_Payroll_Tax", 1000, 15)
ws.append_row([
    "Timestamp", "Person", "Gross Pay", "Withholding Tax (扣繳)", 
    "NHI (健保費)", "Labor Ins (勞保費)", "Pension 6% (勞退自提)", 
    "Meal Allowance", "Other Deductions", "Net Pay (實發)", 
    "Tax Refund Status", "Currency", "Month/Year"
])
ws.format('A1:M1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.95}})
ws.freeze(rows=1)
print("✅ Raw_Payroll_Tax tab created")

# =============================================================================
# 4. Chat_Logs (Audit trail with AI confidence)
# =============================================================================
try:
    ws = sh.worksheet("Chat_Logs")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Chat_Logs", 1000, 10)
ws.append_row([
    "Timestamp", "LINE User ID", "User Name", "Message Type", 
    "Raw Message", "AI Response", "Action", "Status", 
    "Pocket", "AI Confidence %"
])
ws.format('A1:J1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.95, 'blue': 0.95}})
ws.freeze(rows=1)
print("✅ Chat_Logs tab created")

# =============================================================================
# 5. Pockets (The 5 family accounts)
# =============================================================================
try:
    ws = sh.worksheet("Pockets")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Pockets", 20, 8)
ws.append_row([
    "Pocket Name", "Currency", "Balance", "Type", "Owner", 
    "Last Updated", "Notes", "Auto-Replenish"
])

# Initial pocket structure (balances start at 0, user can update manually or via transfers)
pockets_data = [
    ["Family Petty Cash", "NTD", 0, "Expense", "Both", "=NOW()", "Monthly household expenses", "Yes"],
    ["Urgent Fund", "NTD", 0, "Emergency", "Both", "=NOW()", "Emergency fund (3-6 months expenses)", "No"],
    ["Son's USD Fixed", "USD", 0, "Savings", "Son", "=NOW()", "Son's long-term USD fixed deposit", "No"],
    ["Wife's USD Fixed", "USD", 0, "Savings", "Prapa", "=NOW()", "Prapa's personal USD savings", "No"],
    ["Jack's Personal", "NTD", 0, "Personal", "Jack", "=NOW()", "Jack's spending money", "Yes"]
]
ws.append_rows(pockets_data)
ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.8, 'green': 0.9, 'blue': 1}})
ws.freeze(rows=1)
print("✅ Pockets tab created (5 family accounts)")

# =============================================================================
# 6. Transfers (Money movement between pockets)
# =============================================================================
try:
    ws = sh.worksheet("Transfers")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Transfers", 500, 10)
ws.append_row([
    "Timestamp", "From Pocket", "To Pocket", "Amount", "Currency", 
    "Amount in NTD", "Exchange Rate", "Reason", "Authorized By", "Status"
])
ws.format('A1:J1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 1, 'green': 0.85, 'blue': 0.85}})
ws.freeze(rows=1)
print("✅ Transfers tab created")

# =============================================================================
# 7. Exchange_Rates (USD/NTD conversion)
# =============================================================================
try:
    ws = sh.worksheet("Exchange_Rates")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Exchange_Rates", 100, 6)
ws.append_row(["Date", "USD to NTD", "Source", "Last Updated", "Auto-Fetch", "Notes"])

# Add current rate (user can update or enable auto-fetch)
from datetime import datetime
ws.append_row([datetime.now().strftime("%Y-%m-%d"), 32.0, "Manual", "=NOW()", "No", "1 USD = 32 NTD (update as needed)"])

ws.format('A1:F1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 1, 'blue': 0.95}})
ws.freeze(rows=1)
print("✅ Exchange_Rates tab created (USD/NTD)")

# =============================================================================
# 8. Dashboard_Summary (Multi-currency net worth)
# =============================================================================
try:
    ws = sh.worksheet("Dashboard_Summary")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Dashboard_Summary", 30, 4)
ws.append_row(["Metric", "Value", "Currency", "Notes"])

dashboard_data = [
    ["=== POCKET BALANCES ===", "", "", ""],
    ["Family Petty Cash", "=Pockets!C2", "NTD", "Monthly expenses"],
    ["Urgent Fund", "=Pockets!C3", "NTD", "Emergency fund"],
    ["Son's USD Fixed", "=Pockets!C4", "USD", "Long-term savings"],
    ["Wife's USD Fixed", "=Pockets!C5", "USD", "Prapa's savings"],
    ["Jack's Personal", "=Pockets!C6", "NTD", "Personal spending"],
    ["", "", "", ""],
    ["=== TOTAL NET WORTH ===", "", "", ""],
    ["Total NTD Pockets", "=B3+B4+B7", "NTD", ""],
    ["Total USD Pockets", "=B5+B6", "USD", ""],
    ["Exchange Rate (USD→NTD)", "=Exchange_Rates!B2", "NTD", ""],
    ["TOTAL NET WORTH (NTD)", "=B10+(B11*B12)", "NTD", "All pockets combined"],
    ["", "", "", ""],
    ["=== INCOME (YTD) ===", "", "", ""],
    ["Total Income (NTD)", "=SUM(Raw_Income!F:F)", "NTD", "Converted to NTD"],
    ["Total Income (USD)", "=SUMIF(Raw_Income!E:E, \"USD\", Raw_Income!D:D)", "USD", ""],
    ["", "", "", ""],
    ["=== EXPENSES (YTD) ===", "", "", ""],
    ["Total Expenses", "=SUM(Raw_Expenses!D:D)", "NTD", "All categories"],
    ["Family Petty Cash", "=SUMIF(Raw_Expenses!F:F, \"Family Petty Cash\", Raw_Expenses!D:D)", "NTD", ""],
    ["Personal", "=SUMIF(Raw_Expenses!F:F, \"Jack's Personal\", Raw_Expenses!D:D)", "NTD", ""],
    ["Urgent", "=SUMIF(Raw_Expenses!F:F, \"Urgent Fund\", Raw_Expenses!D:D)", "NTD", ""],
    ["", "", "", ""],
    ["=== SAVINGS METRICS ===", "", "", ""],
    ["Net Savings", "=B14-B20", "NTD", "Income - Expenses"],
    ["Savings Rate", "=IF(B14>0, B25/B14, 0)", "%", "Percentage saved"]
]
ws.append_rows(dashboard_data)
ws.format('A1:D1', {'textFormat': {'bold': True}})
ws.format('A2:A27', {'fontStyle': 'bold'})
ws.freeze(rows=1)
print("✅ Dashboard_Summary tab created (Multi-currency net worth)")

# =============================================================================
# 9. Monthly_Analysis (Monthly breakdowns)
# =============================================================================
try:
    ws = sh.worksheet("Monthly_Analysis")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Monthly_Analysis", 200, 10)
ws.append_row([
    "Month", "Income (NTD)", "Income (USD)", "Expenses (NTD)", 
    "Net Savings", "Savings Rate", "Top Category", "Top Vendor", 
    "Pocket Usage", "Notes"
])
ws.format('A1:J1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 1}})
ws.freeze(rows=1)
print("✅ Monthly_Analysis tab created")

# =============================================================================
# 10. Tax_Summary (Taiwan tax calculation helper)
# =============================================================================
try:
    ws = sh.worksheet("Tax_Summary")
    sh.del_worksheet(ws)
except:
    pass

ws = sh.add_worksheet("Tax_Summary", 100, 10)
ws.append_row([
    "Tax Year", "Total Income", "Withholding Tax Paid", "Taxable Income", 
    "Tax Bracket", "Estimated Tax", "Tax Refund Due", "NHI Deductible", 
    "Labor Ins Deductible", "Notes"
])
ws.format('A1:J1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 1, 'green': 0.95, 'blue': 0.8}})
ws.freeze(rows=1)
print("✅ Tax_Summary tab created")

print("\n" + "="*60)
print("🎉 YANG FAMILY FINANCE BANK - DATABASE COMPLETE!")
print("="*60)
print("\n📊 10 Tabs Created:")
print("   1. Raw_Expenses (NTD, with Pocket tracking)")
print("   2. Raw_Income (Multi-currency: NTD + USD)")
print("   3. Raw_Payroll_Tax (Taiwan tax compliance)")
print("   4. Chat_Logs (AI audit trail)")
print("   5. Pockets (5 family accounts)")
print("   6. Transfers (Money movement)")
print("   7. Exchange_Rates (USD/NTD)")
print("   8. Dashboard_Summary (Net worth)")
print("   9. Monthly_Analysis (Monthly breakdowns)")
print("  10. Tax_Summary (Taiwan tax helper)")
print("\n🏦 5 Family Pockets:")
print("   • Family Petty Cash (NTD)")
print("   • Urgent Fund (NTD)")
print("   • Son's USD Fixed (USD)")
print("   • Wife's USD Fixed (USD)")
print("   • Jack's Personal (NTD)")
print("\n💱 Exchange Rate: 1 USD = 32 NTD (update in Exchange_Rates tab)")
print("="*60)
