"""
Yang Family Finance Bot - LINE Flex Message Templates
Professional app-like card designs for approvals, dashboards, receipts
"""

def create_approval_card(request_id, request_type, details, amount, from_account, to_account, requester, currency="TWD"):
    """
    Create Approval Request Flex Message Card
    Shows when Jack/Prapa requests budget/transfer/account change
    """
    
    # Color coding by request type
    colors = {
        "Transfer": "#FF6B6B",  # Red
        "Budget": "#4ECDC4",    # Teal
        "New Account": "#95E1D3" # Mint
    }
    card_color = colors.get(request_type, "#556CD6")  # Blue default
    
    # Requester display name
    requester_display = "Jack" if requester == "jack.yang" else "คุณนายอารยา หยาง"
    requester_icon = "https://cdn-icons-png.flaticon.com/512/3135/3135789.png" if requester == "jack.yang" else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    
    # Format amount with currency
    if currency == "USD":
        amount_formatted = f"${amount:,.2f} USD"
    else:
        amount_formatted = f"{amount:,.0f} บาท"
    
    flex_message = {
        "type": "bubble",
        "size": "hero",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "lg",
            "contents": [
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": "⚖️ Approval Required",
                            "weight": "bold",
                            "size": "xl",
                            "color": card_color,
                            "flex": 1
                        }
                    ]
                },
                {
                    "type": "separator",
                    "color": "#CCCCCC"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "image",
                                    "url": requester_icon,
                                    "size": "sm",
                                    "aspectMode": "cover"
                                },
                                {
                                    "type": "text",
                                    "text": f"Request from: {requester_display}",
                                    "weight": "bold",
                                    "size": "md",
                                    "margin": "sm"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📋 Type:",
                                    "size": "sm",
                                    "color": "#888888",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": request_type,
                                    "size": "sm",
                                    "weight": "bold",
                                    "color": card_color,
                                    "flex": 2
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "💰 Amount:",
                                    "size": "sm",
                                    "color": "#888888",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": amount_formatted,
                                    "size": "md",
                                    "weight": "bold",
                                    "color": "#FF6B6B",
                                    "flex": 2
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "🏦 From:",
                                    "size": "sm",
                                    "color": "#888888",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": from_account,
                                    "size": "sm",
                                    "wrap": True,
                                    "flex": 2
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "💸 To:",
                                    "size": "sm",
                                    "color": "#888888",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": to_account,
                                    "size": "sm",
                                    "wrap": True,
                                    "flex": 2
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "spacing": "sm",
                            "margin": "md",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📝 Details:",
                                    "size": "sm",
                                    "color": "#888888",
                                    "flex": 1
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "xs",
                            "margin": "sm",
                            "paddingAll": "sm",
                            "backgroundColor": "#F5F5F5",
                            "cornerRadius": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": details,
                                    "size": "sm",
                                    "wrap": True,
                                    "adjustMode": "shrink-to-fit"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "✅ Approve",
                        "text": f"Approve {request_id}"
                    },
                    "style": "primary",
                    "color": "#4CAF50",
                    "height": "md"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": "❌ Reject",
                        "text": f"Reject {request_id}"
                    },
                    "style": "primary",
                    "color": "#F44336",
                    "height": "md"
                },
                {
                    "type": "text",
                    "text": "Tap Approve or Reject to process this request",
                    "size": "xs",
                    "color": "#888888",
                    "align": "center",
                    "margin": "md"
                }
            ]
        }
    }
    
    return flex_message


def create_financial_summary_card(dashboard_data, user_name):
    """
    Create Financial Dashboard Summary Card
    Shows YTD totals, net worth, budget utilization
    """
    
    if user_name == "prapa.yang":
        title = "📊 สรุปยอดรวม"
        ytd_label = "ยอดรวมตั้งแต่ต้นปี"
        net_worth_label = "มูลค่าทรัพย์สินสุทธิ"
        budget_label = "งบประมาณคงเหลือ"
    else:
        title = "📊 Financial Summary"
        ytd_label = "Year-to-Date Total"
        net_worth_label = "Net Worth"
        budget_label = "Budget Remaining"
    
    flex_message = {
        "type": "bubble",
        "size": "hero",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "lg",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "xl",
                    "color": "#556CD6"
                },
                {
                    "type": "separator",
                    "color": "#CCCCCC"
                }
                # Add dashboard data boxes here
            ]
        }
    }
    
    return flex_message


def create_receipt_confirmation_card(vendor, amount, category, user_name):
    """
    Create Receipt Confirmation Card
    Shows extracted OCR data with Confirm/Edit buttons
    """
    
    if user_name == "prapa.yang":
        title = "✅ ยืนยันรายการ"
        vendor_label = "ร้านค้า:"
        amount_label = "จำนวนเงิน:"
        category_label = "หมวดหมู่:"
        confirm_btn = "✅ ยืนยัน"
        edit_btn = "✏️ แก้ไข"
    else:
        title = "✅ Confirm Expense"
        vendor_label = "Vendor:"
        amount_label = "Amount:"
        category_label = "Category:"
        confirm_btn = "✅ Confirm"
        edit_btn = "✏️ Edit"
    
    flex_message = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "paddingAll": "lg",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "xl",
                    "color": "#4CAF50"
                },
                {
                    "type": "separator",
                    "color": "#CCCCCC"
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": vendor_label,
                            "size": "sm",
                            "color": "#888888",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": vendor,
                            "size": "sm",
                            "weight": "bold",
                            "flex": 2
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": amount_label,
                            "size": "sm",
                            "color": "#888888",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": f"{amount:,.0f} บาท",
                            "size": "md",
                            "weight": "bold",
                            "color": "#FF6B6B",
                            "flex": 2
                        }
                    ]
                },
                {
                    "type": "box",
                    "layout": "horizontal",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": category_label,
                            "size": "sm",
                            "color": "#888888",
                            "flex": 1
                        },
                        {
                            "type": "text",
                            "text": category,
                            "size": "sm",
                            "weight": "bold",
                            "flex": 2
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": confirm_btn,
                        "text": "Confirm receipt"
                    },
                    "style": "primary",
                    "color": "#4CAF50"
                },
                {
                    "type": "button",
                    "action": {
                        "type": "message",
                        "label": edit_btn,
                        "text": "Edit receipt"
                    },
                    "style": "primary",
                    "color": "#FF9800"
                }
            ]
        }
    }
    
    return flex_message
