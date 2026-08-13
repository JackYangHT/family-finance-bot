# setup_database.py - Run once locally to auto-create Google Sheets structure
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
sh = gc.open_by_key(SPREADSHEET_ID)

print("🔧 Setting up Yang Family Finance Database...")

# 1. Create Raw_Expenses Tab
try:
    exp_sheet = sh.worksheet("Raw_Expenses")
    print("⚠️ Raw_Expenses tab already exists")
except:
    exp_sheet = sh.add_worksheet(title="Raw_Expenses", rows="1000", cols="10")
    exp_headers = [["Timestamp", "User", "Category", "Amount (TWD)", "Vendor/Note", "Raw Input"]]
    exp_sheet.update(range_name="A1:F1", values=exp_headers)
    exp_sheet.format("A1:F1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.8, "green": 0.9, "blue": 1.0}})
    print("✅ Created Raw_Expenses tab")

# 2. Create Raw_Payroll_Tax Tab (Taiwan Tax & Labor Compliance)
try:
    pay_sheet = sh.worksheet("Raw_Payroll_Tax")
    print("⚠️ Raw_Payroll_Tax tab already exists")
except:
    pay_sheet = sh.add_worksheet(title="Raw_Payroll_Tax", rows="500", cols="12")
    pay_headers = [[
        "Timestamp", "Person", "Gross Pay", "Withholding Tax (扣繳)", 
        "NHI (健保費)", "Labor Ins (勞保費)", "Pension 6% (勞退自提)", 
        "Meal Allowance (伙食津貼)", "Other Deductions", "Net Pay (實發)", "Tax Refund Status"
    ]]
    pay_sheet.update(range_name="A1:K1", values=pay_headers)
    pay_sheet.format("A1:K1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.9, "green": 1.0, "blue": 0.8}})
    print("✅ Created Raw_Payroll_Tax tab")

# 3. Create Automated Dashboard Summary Tab
try:
    sum_sheet = sh.worksheet("Dashboard_Summary")
    print("⚠️ Dashboard_Summary tab already exists")
except:
    sum_sheet = sh.add_worksheet(title="Dashboard_Summary", rows="100", cols="10")
    summary_structure = [
        ["YANG FAMILY FINANCIAL DASHBOARD", ""],
        ["Metric", "Value (TWD)"],
        ["Total Income (YTD)", "=SUM(Raw_Payroll_Tax!C2:C)"],
        ["Total Prepaid Tax / Refundable (扣繳稅額)", "=SUM(Raw_Payroll_Tax!D2:D)"],
        ["Total Tax-Free Pension (勞退自提)", "=SUM(Raw_Payroll_Tax!G2:G)"],
        ["Total Expenses (YTD)", "=SUM(Raw_Expenses!D2:D)"],
        ["Petty Cash Expenses", '=SUMIF(Raw_Expenses!C2:C, "Family Petty Cash", Raw_Expenses!D2:D)'],
        ["Personal Expenses", '=SUMIF(Raw_Expenses!C2:C, "Personal", Raw_Expenses!D2:D)'],
        ["Urgent Expenses", '=SUMIF(Raw_Expenses!C2:C, "Urgent", Raw_Expenses!D2:D)']
    ]
    sum_sheet.update(range_name="A1:B9", values=summary_structure)
    sum_sheet.format("A1:B2", {"textFormat": {"bold": True}})
    print("✅ Created Dashboard_Summary tab with auto-formulas")

print("\n✅ Google Sheet database structure programmatically initialized!")
print(f"📊 Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
