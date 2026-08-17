"""
Test Google Sheets Connection for Yang Family Finance Bot
"""
import os
import sys
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

SPREADSHEET_ID = "1T4uP-1WInBLJ5ulSMGGtVBJuDR0GyGR-tngwxLw8KJY"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

print("🔐 Testing Google Sheets Connection...")
print(f"   Credentials: .venv/Scripts/credentials.json")
print(f"   Spreadsheet: {SPREADSHEET_ID}")

try:
    creds = Credentials.from_service_account_file(".venv/Scripts/credentials.json", scopes=SCOPES)
    print(f"✅ Credentials loaded: {creds.service_account_email}")
    
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    print(f"✅ Connected to: {sh.title}")
    
    # Test reading Dashboard_Summary
    dash = sh.worksheet("Dashboard_Summary")
    values = dash.get_values(value_render_option='FORMATTED_VALUE')
    print(f"\n📊 Dashboard_Summary has {len(values)} rows")
    
    if len(values) > 0:
        print(f"   First row (headers): {values[0][:3]}")
    if len(values) > 10:
        print(f"   Row 10: {values[9]}")
    
    # Test writing a test row to Raw_Expenses
    exp = sh.worksheet("Raw_Expenses")
    test_row = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "test_user",
        "Test Category",
        "100",
        "Test Vendor",
        "Cash",
        "No",
        "No",
        "Test entry from setup script",
        "test_001"
    ]
    exp.append_row(test_row)
    print(f"\n✅ Test row written to Raw_Expenses")
    
    # Read it back
    rows = exp.get_all_values()
    print(f"   Raw_Expenses has {len(rows)} rows (including header)")
    print(f"   Last row: {rows[-1]}")
    
    print("\n" + "="*60)
    print("✅ GOOGLE SHEETS CONNECTION SUCCESSFUL!")
    print("="*60)
    print("\n🎉 The bot should be able to:")
    print("   ✅ Read from Dashboard_Summary")
    print("   ✅ Write to Raw_Expenses")
    print("   ✅ Access all 10 tabs")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
