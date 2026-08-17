"""
Yang Family Finance Bot - Approval Workflow Module
Dual approval system: Jack ↔ Prapa must approve each other's requests
"""
from datetime import datetime
import json

def create_request(sh, requester_id, requester_name, request_type, details, amount=0, from_acc="", to_acc=""):
    """Create a new approval request"""
    try:
        pending_ws = sh.worksheet("Pending_Approvals")
        
        # Determine approver (opposite party)
        approver = "prapa.yang" if requester_name == "jack.yang" else "jack.yang"
        
        # Generate request ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        request_id = f"REQ{timestamp}"
        
        # Add to pending approvals
        pending_ws.append_row([
            request_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            requester_id,
            requester_name,
            request_type,
            details,
            amount,
            from_acc,
            to_acc,
            "PENDING",
            approver,
            "NO",
            "",
            ""
        ])
        
        print(f"✅ Created request {request_id}: {request_type} by {requester_name}, approver: {approver}")
        return request_id, approver
    
    except Exception as e:
        print(f"❌ Failed to create request: {e}")
        return None, None

def get_pending_approvals(sh, user_name):
    """Get all pending approvals for a user"""
    try:
        pending_ws = sh.worksheet("Pending_Approvals")
        rows = pending_ws.get_all_values()
        
        pending = []
        for row in rows[1:]:  # Skip header
            if len(row) >= 11 and row[10] == user_name and row[9] == "PENDING":
                pending.append({
                    "request_id": row[0],
                    "timestamp": row[1],
                    "requester": row[3],
                    "type": row[4],
                    "details": row[5],
                    "amount": row[6],
                    "from_acc": row[7],
                    "to_acc": row[8]
                })
        
        return pending
    
    except Exception as e:
        print(f"❌ Failed to get pending approvals: {e}")
        return []

def approve_request(sh, request_id, approver_name):
    """Approve a request and execute the transaction"""
    try:
        pending_ws = sh.worksheet("Pending_Approvals")
        history_ws = sh.worksheet("Approval_History")
        
        rows = pending_ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row[0] == request_id:
                # Update pending status
                pending_ws.update(f'J{i}', [[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
                pending_ws.update(f'I{i}', [['APPROVED']])
                
                # Add to history
                history_ws.append_row([
                    row[0], row[1], row[3], row[4], row[5],
                    row[6], approver_name, "APPROVED",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "EXECUTED"
                ])
                
                # Execute the transaction based on type
                execute_transaction(sh, row)
                
                return True, "APPROVED"
        
        return False, "NOT_FOUND"
    
    except Exception as e:
        print(f"❌ Failed to approve: {e}")
        return False, f"ERROR: {e}"

def reject_request(sh, request_id, approver_name, reason=""):
    """Reject a request"""
    try:
        pending_ws = sh.worksheet("Pending_Approvals")
        history_ws = sh.worksheet("Approval_History")
        
        rows = pending_ws.get_all_values()
        for i, row in enumerate(rows[1:], start=2):
            if row[0] == request_id:
                # Update pending status
                pending_ws.update(f'K{i}', [[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
                pending_ws.update(f'I{i}', [['REJECTED']])
                
                # Add to history
                history_ws.append_row([
                    row[0], row[1], row[3], row[4], row[5],
                    row[6], approver_name, "REJECTED",
                    "", reason,
                    "", "NOT_EXECUTED"
                ])
                
                return True, "REJECTED"
        
        return False, "NOT_FOUND"
    
    except Exception as e:
        print(f"❌ Failed to reject: {e}")
        return False, f"ERROR: {e}"

def execute_transaction(sh, row):
    """Execute the approved transaction"""
    try:
        request_type = row[4]
        
        if request_type == "Transfer":
            # Log to Transfers sheet
            transfer_ws = sh.worksheet("Transfers")
            transfer_ws.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                row[7],  # From Account
                row[8],  # To Account
                row[6],  # Amount
                "TWD",
                "1",  # Exchange rate (assume same currency)
                row[6],
                row[5],  # Details
                row[3]   # Requester
            ])
            print(f"✅ Executed transfer: {row[7]} → {row[8]}, Amount: {row[6]}")
        
        elif request_type == "Open Account":
            # Add to Accounts sheet
            acc_ws = sh.worksheet("Accounts")
            acc_ws.append_row([
                f"ACC{datetime.now().strftime('%Y%m%d%H%M%S')}",
                row[5],  # Account name from details
                "Pocket",
                "NTD",
                row[3],  # Requester
                "0",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Active"
            ])
            print(f"✅ Created account: {row[5]}")
        
        elif request_type == "Budget":
            # Add to Budget_Limits sheet
            budget_ws = sh.worksheet("Budget_Limits")
            budget_ws.append_row([
                row[5],  # Category
                row[6],  # Amount
                "Both",
                "0",
                "0",
                row[6],
                "Active",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ])
            print(f"✅ Created budget: {row[5]} = {row[6]}")
    
    except Exception as e:
        print(f"❌ Failed to execute transaction: {e}")

def format_approval_message(request, user_name):
    """Format approval request message for approver"""
    if user_name == "prapa.yang":
        return (
            f"⚖️ **คำขออนุมัติจากคุณแจ๊ค**\n\n"
            f"📋 ประเภท: {request['type']}\n"
            f"📝 รายละเอียด: {request['details']}\n"
            f"💰 จำนวน: {request['amount']} บาท\n"
            f"🏦 จาก: {request['from_acc']}\n"
            f"💸 ไป: {request['to_acc']}\n\n"
            f"กรุณาตรวจสอบและอนุมัติครับ"
        )
    else:
        return (
            f"⚖️ **Approval Request from Prapa**\n\n"
            f"📋 Type: {request['type']}\n"
            f"📝 Details: {request['details']}\n"
            f"💰 Amount: {request['amount']} TWD\n"
            f"🏦 From: {request['from_acc']}\n"
            f"💸 To: {request['to_acc']}\n\n"
            f"Please review and approve."
        )
