# setup_database.py - Complete Yang Family Finance Database Setup
# Run once to auto-create all Google Sheets tabs with proper structure
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file(
    ".venv/Scripts/gen-lang-client-0948238290-9a5935a59f3d.json", 
    scopes=SCOPES
)
gc = gspread.authorize(creds)

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
sh = gc.open_by_key(SPREADSHEET_ID)

print("🔧 Setting up Yang Family Finance Database...")
print("=" * 60)

# Helper function to create or get worksheet
def create_or_get_sheet(sh, title, rows=1000, cols=10, headers=None, header_color=None):
    try:
        ws = sh.worksheet(title)
        print(f"⚠️  {title} tab already exists")
        return ws
    except:
        ws = sh.add_worksheet(title=title, rows=rows, cols=cols)
        if headers:
            ws.update(range_name="A1", values=[headers])
            if header_color:
                ws.format(f"A1:{chr(64+len(headers))}1", header_color)
        print(f"✅ Created {title} tab")
        return ws

# =============================================================================
# SHEET 1: Raw_Expenses - All expense transactions
# =============================================================================
exp_headers = [
    "Timestamp", "User", "Category", "Amount (TWD)", "Vendor/Note", 
    "Payment Method", "Receipt?", "Tax Deductible?", "Raw Input (EN/TH)", "Chat Log ID"
]
exp_sheet = create_or_get_sheet(
    sh, "Raw_Expenses", rows=2000, cols=10, headers=exp_headers,
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 0, "green": 0, "blue": 0.5}}, 
                  "backgroundColor": {"red": 0.8, "green": 0.9, "blue": 1.0}}
)

# =============================================================================
# SHEET 2: Raw_Income - All income records (salary, refunds, etc.)
# =============================================================================
inc_headers = [
    "Timestamp", "Person", "Type", "Gross Amount (TWD)", "Withholding Tax (扣繳)",
    "NHI (健保費)", "Labor Ins (勞保費)", "Pension 6% (勞退自提)", 
    "Meal Allowance (伙食津貼)", "Other Deductions", "Net Pay (實發)", 
    "Tax Refund Status", "Source Document"
]
inc_sheet = create_or_get_sheet(
    sh, "Raw_Income", rows=500, cols=13, headers=inc_headers,
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 0, "green": 0, "blue": 0}}, 
                  "backgroundColor": {"red": 0.9, "green": 1.0, "blue": 0.8}}
)

# =============================================================================
# SHEET 3: Raw_Payroll_Tax - Detailed salary slip data (Taiwan tax compliance)
# =============================================================================
pay_headers = [
    "Timestamp", "Person", "Pay Period", "Gross Pay", "Withholding Tax (扣繳稅額)",
    "NHI Premium (健保費)", "Labor Insurance (勞保費)", "Employment Ins (就業保險)",
    "Pension Voluntary 6% (勞退自提)", "Meal Allowance (伙食津貼)", 
    "Other Deductions", "Net Pay (實發薪資)", "Tax Refund Status", "Slip Image URL"
]
pay_sheet = create_or_get_sheet(
    sh, "Raw_Payroll_Tax", rows=500, cols=14, headers=pay_headers,
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 0.5, "green": 0, "blue": 0.5}}, 
                  "backgroundColor": {"red": 1.0, "green": 0.9, "blue": 1.0}}
)

# =============================================================================
# SHEET 4: Chat_Logs - Raw LINE messages for audit/debugging
# =============================================================================
chat_headers = [
    "Timestamp", "LINE User ID", "User Name", "Message Type", 
    "Raw Message (EN/TH)", "AI Response", "Action Taken", "Status"
]
chat_sheet = create_or_get_sheet(
    sh, "Chat_Logs", rows=5000, cols=8, headers=chat_headers,
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 0, "green": 0, "blue": 0}}, 
                  "backgroundColor": {"red": 0.95, "green": 0.95, "blue": 0.95}}
)

# =============================================================================
# SHEET 5: Dashboard_Summary - Auto-calculated KPIs and totals
# =============================================================================
dash_sheet = create_or_get_sheet(
    sh, "Dashboard_Summary", rows=50, cols=4,
    headers=["Metric", "Value (TWD)", "Notes", "Last Updated"],
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}, 
                  "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.6}}
)

# Dashboard formulas
dashboard_data = [
    ["📊 YANG FAMILY FINANCIAL DASHBOARD", "", f"=NOW()", ""],
    ["", "", "", ""],
    ["💰 INCOME (YTD)", '=SUM(Raw_Income!D2:D)', "Total gross income", ""],
    ["🏛️ Prepaid Tax (扣繳稅額)", '=SUM(Raw_Income!E2:E)', "Withholding tax for refund", ""],
    ["🏥 NHI Premium (健保費)", '=SUM(Raw_Income!F2:F)', "Health insurance", ""],
    ["👷 Labor Insurance (勞保費)", '=SUM(Raw_Income!G2:G)', "Labor insurance", ""],
    ["📌 Pension 6% (勞退自提)", '=SUM(Raw_Income!H2:H)', "Tax-free pension contribution", ""],
    ["💵 Net Income Received", '=SUM(Raw_Income!K2:K)', "Actual take-home pay", ""],
    ["", "", "", ""],
    ["📉 EXPENSES (YTD)", '=SUM(Raw_Expenses!D2:D)', "Total expenses", ""],
    ["🏠 Family Petty Cash", '=SUMIF(Raw_Expenses!C2:C, "Family Petty Cash", Raw_Expenses!D2:D)', "Household expenses", ""],
    ["🧍 Personal Expenses", '=SUMIF(Raw_Expenses!C2:C, "Personal", Raw_Expenses!D2:D)', "Individual spending", ""],
    ["🚨 Urgent Expenses", '=SUMIF(Raw_Expenses!C2:C, "Urgent", Raw_Expenses!D2:D)', "Emergency spending", ""],
    ["🍽️ Food & Dining", '=SUMIF(Raw_Expenses!C2:C, "Food", Raw_Expenses!D2:D)', "Restaurants, groceries", ""],
    ["🚗 Transportation", '=SUMIF(Raw_Expenses!C2:C, "Transport", Raw_Expenses!D2:D)', "Fuel, transit", ""],
    ["💊 Medical", '=SUMIF(Raw_Expenses!C2:C, "Medical", Raw_Expenses!D2:D)', "Healthcare costs", ""],
    ["", "", "", ""],
    ["💎 NET SAVINGS", '=B3-B10', "Income - Expenses", "Target: 30% of income"],
    ["💎 Savings Rate", '=IF(B3>0, B18/B3, 0)', "Format as %", ""]
]
dash_sheet.update(range_name="A1:D19", values=dashboard_data)
dash_sheet.format("A1:D19", {"textFormat": {"fontSize": 11}})
dash_sheet.format("A3:A19", {"textFormat": {"bold": True}})
dash_sheet.format("B3:B19", {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}})

# =============================================================================
# SHEET 6: Monthly_Analysis - Pivot-style monthly breakdowns
# =============================================================================
monthly_sheet = create_or_get_sheet(
    sh, "Monthly_Analysis", rows=200, cols=10,
    headers=["Month", "Category", "Amount (TWD)", "Transaction Count", "Avg per Tx", "YoY Change", "Budget", "Variance", "Notes"],
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}, 
                  "backgroundColor": {"red": 0.3, "green": 0.5, "blue": 0.7}}
)

# Monthly analysis template with formulas
monthly_template = [
    ["📅 MONTHLY BREAKDOWN TEMPLATE", "", "", "", "", "", "", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["Month", "Category", "Amount", "Count", "Average", "Budget", "Variance", "Notes", ""],
    ["=TEXT(Raw_Expenses!A2:A, \"YYYY-MM\")", "=Raw_Expenses!C2:C", "=Raw_Expenses!D2:D", 
     "=COUNTA(Raw_Expenses!A2:A)", "=AVERAGE(Raw_Expenses!D2:D)", "=F3*1.1", "=E3-F3", "", ""],
    ["", "", "", "", "", "", "", "", ""],
    ["📈 TOP CATEGORIES (This Month)", "", "", "", "", "", "", "", ""],
    ["1.", '=INDEX(Raw_Expenses!C2:C, MATCH(MAX(Raw_Expenses!D2:D), Raw_Expenses!D2:D, 0))', 
     '=MAX(Raw_Expenses!D2:D)', "", "", "", "", "", ""],
    ["2.", "", "", "", "", "", "", "", ""],
    ["3.", "", "", "", "", "", "", "", ""]
]
monthly_sheet.update(range_name="A1:I11", values=monthly_template)

# =============================================================================
# SHEET 7: Tax_Summary - Taiwan tax calculation helper
# =============================================================================
tax_sheet = create_or_get_sheet(
    sh, "Tax_Summary", rows=100, cols=6,
    headers=["Tax Year", "Total Income", "Deductible Pension (6%)", "Prepaid Tax (扣繳)", 
             "Estimated Tax Due", "Refund Expected"],
    header_color={"textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}}, 
                  "backgroundColor": {"red": 0.6, "green": 0.3, "blue": 0.3}}
)

tax_template = [
    ["🏛️ TAIWAN TAX CALCULATION HELPER", "", "", "", "", ""],
    ["", "", "", "", "", ""],
    ["Year", "2026", "2027", "2028", "", ""],
    ["Total Income", '=SUMIFS(Raw_Income!D2:D, Raw_Income!A2:A, ">=2026-01-01", Raw_Income!A2:A, "<=2026-12-31")', "", "", "", ""],
    ["Deductible Pension (6%)", '=SUMIFS(Raw_Income!H2:H, Raw_Income!A2:A, ">=2026-01-01", Raw_Income!A2:A, "<=2026-12-31")', "", "", "", ""],
    ["Prepaid Tax (扣繳)", '=SUMIFS(Raw_Income!E2:E, Raw_Income!A2:A, ">=2026-01-01", Raw_Income!A2:A, "<=2026-12-31")', "", "", "", ""],
    ["Estimated Tax Rate", "5%", "", "", "", ""],
    ["Estimated Tax Due", "=B5*B7", "", "", "", ""],
    ["Refund Expected", "=B6-B8", "", "", "", ""]
]
tax_sheet.update(range_name="A1:F10", values=tax_template)

# =============================================================================
# Final formatting
# =============================================================================
print("=" * 60)
print("✅ Google Sheet database structure created successfully!")
print(f"📊 Spreadsheet: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
print("")
print("📁 SHEETS CREATED:")
print("  1. Raw_Expenses    - All expense transactions")
print("  2. Raw_Income      - Salary, refunds, income records")
print("  3. Raw_Payroll_Tax - Taiwan tax compliance data")
print("  4. Chat_Logs       - LINE message audit trail")
print("  5. Dashboard_Summary - Auto-calculated KPIs")
print("  6. Monthly_Analysis - Monthly breakdowns")
print("  7. Tax_Summary     - Taiwan tax helper")
print("")
print("🎯 NEXT STEPS:")
print("  1. Open Google Sheet and verify all 7 tabs exist")
print("  2. Delete any old/test data tabs")
print("  3. Commit app.py to GitHub for Render redeploy")
print("  4. Test in LINE: 'jack.yang 7/11 100' or 'prapa.yang เซเว่น 200'")
