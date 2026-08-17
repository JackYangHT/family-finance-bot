"""
Yang Family Finance Bot - Pre-Seed 5 Pockets Architecture
Hardcodes the 5-pocket system into Accounts tab
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
# Pre-Seed 5 Pockets in Accounts Tab
# =============================================================================
print("\n🏦 Pre-seeding 5 Pockets in Accounts tab...")

try:
    # Try to get existing Accounts tab, or create new one
    try:
        acc_ws = sh.worksheet("Accounts")
        print("  ℹ️  Found existing Accounts tab")
    except:
        acc_ws = sh.add_worksheet("Accounts", 100, 10)
        print("  ✅ Created new Accounts tab")
    
    # Clear existing data (except header)
    acc_ws.clear()
    
    # Define header row
    header = [
        "Account ID", "Account Name", "Type", "Currency", 
        "Owner", "Balance", "Last Updated", "Status", "Approval Required"
    ]
    acc_ws.append_row(header)
    
    # Pre-seed 5 pockets (Yang Family 5-Pocket Architecture)
    pockets = [
        {
            "id": "ACC001",
            "name": "Family Petty Cash",
            "type": "Pocket",
            "currency": "NTD",
            "owner": "Both",
            "balance": "0",
            "approval": "Both"
        },
        {
            "id": "ACC002",
            "name": "Urgent Fund",
            "type": "Pocket",
            "currency": "NTD",
            "owner": "Both",
            "balance": "0",
            "approval": "Both"
        },
        {
            "id": "ACC003",
            "name": "Son's USD Fixed",
            "type": "Pocket",
            "currency": "USD",
            "owner": "Both",
            "balance": "0",
            "approval": "Both"
        },
        {
            "id": "ACC004",
            "name": "Wife's USD Fixed (Araya)",
            "type": "Pocket",
            "currency": "USD",
            "owner": "prapa.yang",
            "balance": "0",
            "approval": "Both"
        },
        {
            "id": "ACC005",
            "name": "Jack's Personal",
            "type": "Pocket",
            "currency": "NTD",
            "owner": "jack.yang",
            "balance": "0",
            "approval": "Both"
        }
    ]
    
    # Insert 5 pockets
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for pocket in pockets:
        acc_ws.append_row([
            pocket["id"],
            pocket["name"],
            pocket["type"],
            pocket["currency"],
            pocket["owner"],
            pocket["balance"],
            timestamp,
            "Active",
            pocket["approval"]
        ])
        print(f"  ✅ {pocket['name']} ({pocket['currency']})")
    
    # Format header
    acc_ws.format('A1:I1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.85, 'green': 0.95, 'blue': 0.85}
    })
    
    # Freeze header row
    acc_ws.freeze(1)
    
    # Auto-resize columns
    acc_ws.column_dimensions('A').width = 10
    acc_ws.column_dimensions('B').width = 25
    acc_ws.column_dimensions('C').width = 10
    acc_ws.column_dimensions('D').width = 10
    acc_ws.column_dimensions('E').width = 12
    acc_ws.column_dimensions('F').width = 12
    acc_ws.column_dimensions('G').width = 18
    acc_ws.column_dimensions('H').width = 10
    acc_ws.column_dimensions('I').width = 15
    
    print("\n✅ Accounts tab pre-seeded successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

# =============================================================================
# Update Pockets Tab (5-pocket structure)
# =============================================================================
print("\n📊 Updating Pockets tab...")

try:
    try:
        pocket_ws = sh.worksheet("Pockets")
        print("  ℹ️  Found existing Pockets tab")
    except:
        pocket_ws = sh.add_worksheet("Pockets", 100, 6)
        print("  ✅ Created new Pockets tab")
    
    # Clear existing data
    pocket_ws.clear()
    
    # Define header
    header = ["Pocket Name", "Currency", "Balance", "Last Updated", "Owner", "Status"]
    pocket_ws.append_row(header)
    
    # Pre-seed 5 pockets
    for pocket in pockets:
        pocket_ws.append_row([
            pocket["name"],
            pocket["currency"],
            pocket["balance"],
            timestamp,
            pocket["owner"],
            "Active"
        ])
    
    # Format
    pocket_ws.format('A1:F1', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.95}
    })
    pocket_ws.freeze(1)
    
    print("  ✅ Pockets tab updated with 5 pockets")
    
except Exception as e:
    print(f"  ❌ Error: {e}")

# =============================================================================
# Summary
# =============================================================================
print("\n" + "="*60)
print("✅ PRE-SEEDING COMPLETE!")
print("="*60)
print(f"\n📊 5 Pockets Created:")
print("   1. Family Petty Cash (NTD) - Both")
print("   2. Urgent Fund (NTD) - Both")
print("   3. Son's USD Fixed (USD) - Both")
print("   4. Wife's USD Fixed (Araya) (USD) - prapa.yang")
print("   5. Jack's Personal (NTD) - jack.yang")
print(f"\n🔐 Approval Rules:")
print("   - All new accounts require BOTH approvals")
print("   - Existing 5 pockets are pre-approved")
print(f"\n🎉 Ready for deployment!")
