"""
Yang Family Finance Bot - Add Approval Workflow Tabs
"""
import os
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

print("🔐 Connecting to Google Sheets...")

creds = Credentials.from_service_account_file(".venv/Scripts/credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SPREADSHEET_ID)
print(f"✅ Connected to: {sh.title}")

# =============================================================================
# Tab: Pending_Approvals (NEW - Dual Approval System)
# =============================================================================
print("\n⚖️ Creating Pending_Approvals...")
try:
    sh.del_worksheet(sh.worksheet("Pending_Approvals"))
except:
    pass
pending_ws = sh.add_worksheet("Pending_Approvals", 500, 10)

pending_ws.append_row([
    "Request ID", "Timestamp", "Requester ID", "Requester Name", "Request Type",
    "Details", "Amount", "From Account", "To Account", "Status",
    "Approver Required", "Approver Notified", "Approved At", "Rejected At"
])

pending_ws.format('A1:N1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.95, 'green': 0.85, 'blue': 0.85}})
pending_ws.freeze(1)

# Add sample pending request
pending_ws.append_row([
    "REQ001", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "jack.yang", "Jack", "Transfer",
    "Transfer from Family Petty Cash to Personal", "5000", "Family Petty Cash", "Jack's Personal",
    "PENDING", "prapa.yang", "NO", "", ""
])

print("  ✅ Pending_Approvals created")

# =============================================================================
# Tab: Budget_Limits (NEW - Family Budget Settings)
# =============================================================================
print("\n📋 Creating Budget_Limits...")
try:
    sh.del_worksheet(sh.worksheet("Budget_Limits"))
except:
    pass
budget_ws = sh.add_worksheet("Budget_Limits", 50, 8)

budget_ws.append_row([
    "Category", "Monthly Budget (TWD)", "Approvers", "Auto-Approve Below",
    "Current MTD", "Remaining", "Status", "Last Updated"
])

# Pre-populate budget categories
budget_data = [
    ["Family Petty Cash", "50000", "Both", "5000", "=SUMIF('Raw_Expenses'!D:D, A2, 'Raw_Expenses'!E:E)*-1", "=B2-E2", "Active", "=NOW()"],
    ["Personal", "15000", "Self", "3000", "=SUMIF('Raw_Expenses'!D:D, A3, 'Raw_Expenses'!E:E)*-1", "=B3-E3", "Active", "=NOW()"],
    ["Urgent", "20000", "Both", "10000", "=SUMIF('Raw_Expenses'!D:D, A4, 'Raw_Expenses'!E:E)*-1", "=B4-E4", "Active", "=NOW()"],
    ["Food", "20000", "Self", "5000", "=SUMIF('Raw_Expenses'!D:D, A5, 'Raw_Expenses'!E:E)*-1", "=B5-E5", "Active", "=NOW()"],
    ["Transport", "5000", "Self", "1000", "=SUMIF('Raw_Expenses'!D:D, A6, 'Raw_Expenses'!E:E)*-1", "=B6-E6", "Active", "=NOW()"],
]

for i, row in enumerate(budget_data):
    budget_ws.append_row(row)

budget_ws.format('A1:H1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.95, 'blue': 0.85}})
budget_ws.freeze(1)
budget_ws.format('B2:B6', {'numberFormat': {'type': 'NUMBER'}})
budget_ws.format('E2:H6', {'numberFormat': {'type': 'NUMBER'}})

print("  ✅ Budget_Limits created (5 categories)")

# =============================================================================
# Tab: Approval_History (NEW - Audit Trail)
# =============================================================================
print("\n📜 Creating Approval_History...")
try:
    sh.del_worksheet(sh.worksheet("Approval_History"))
except:
    pass
history_ws = sh.add_worksheet("Approval_History", 1000, 12)

history_ws.append_row([
    "Request ID", "Timestamp", "Requester", "Request Type", "Details",
    "Amount", "Approver", "Decision", "Approved At", "Comments",
    "Executed At", "Execution Status"
])

history_ws.format('A1:L1', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.85, 'blue': 0.9, 'green': 0.9}})
history_ws.freeze(1)

print("  ✅ Approval_History created")

# =============================================================================
# Update Accounts Tab - Add Approval Required Column
# =============================================================================
print("\n🏦 Updating Accounts tab...")
try:
    acc_ws = sh.worksheet("Accounts")
    # Add column if not exists
    headers = acc_ws.row_values(1)
    if "Approval Required" not in headers:
        acc_ws.update('I1', [['Approval Required']])
        acc_ws.update('I2:I8', [['Both'], ['Both'], ['Self'], ['Self'], ['Self'], ['Both'], ['Both']])
    print("  ✅ Accounts updated")
except Exception as e:
    print(f"  ⚠️ Accounts update skipped: {e}")

# =============================================================================
# Final Summary
# =============================================================================
print("\n" + "="*60)
print("✅ APPROVAL WORKFLOW SETUP COMPLETE!")
print("="*60)
print(f"\n📊 New tabs created:")
print("   1. Pending_Approvals (dual approval queue)")
print("   2. Budget_Limits (family budget settings)")
print("   3. Approval_History (audit trail)")
print(f"\n🔐 Approval Rules:")
print("   - Jack's requests → Prapa must approve")
print("   - Prapa's requests → Jack must approve")
print("   - Budget over limit → Both must approve")
print("   - New accounts → Both must approve")
print("   - Transfers → Opposite party must approve")
print("\n🎉 Dual approval system ready!")
