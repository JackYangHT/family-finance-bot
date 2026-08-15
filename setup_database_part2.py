"""
Yang Family Finance Bot - Database Setup Part 2
Creates remaining tabs after rate limit reset
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

# Google Sheets Auth
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(r"C:\Users\Jack\Documents\family finance\family-finance-bot\.venv\Scripts\gen-lang-client-0948238290-9a5935a59f3d.json", scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
sh = gc.open_by_key(SPREADSHEET_ID)

print("⏳ Waiting 5 seconds for rate limit reset...")
time.sleep(5)

# =============================================================================
# 8. Dashboard_Summary (Multi-currency net worth)
# =============================================================================
try:
    ws = sh.worksheet("Dashboard_Summary")
    sh.del_worksheet(ws)
    time.sleep(2)
except:
    pass

ws = sh.add_worksheet("Dashboard_Summary", 30, 4)
ws.append_row(["Metric", "Value", "Currency", "Notes"])
time.sleep(2)

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
ws.freeze(rows=1)
print("✅ Dashboard_Summary tab created (Multi-currency net worth)")

time.sleep(3)

# =============================================================================
# 9. Monthly_Analysis (Monthly breakdowns)
# =============================================================================
try:
    ws = sh.worksheet("Monthly_Analysis")
    sh.del_worksheet(ws)
    time.sleep(2)
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

time.sleep(3)

# =============================================================================
# 10. Tax_Summary (Taiwan tax calculation helper)
# =============================================================================
try:
    ws = sh.worksheet("Tax_Summary")
    sh.del_worksheet(ws)
    time.sleep(2)
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
