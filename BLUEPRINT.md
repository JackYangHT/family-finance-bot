# Yang Family Financial & Tax Agent - Project Blueprint

**📍 Local Project Folder:** `C:/Users/Jack/Documents/family finance/`  
**📂 Code Repository:** `C:/Users/Jack/Documents/family finance/family-finance-bot/`  
**🔗 GitHub:** https://github.com/JackYangHT/family-finance-bot

## 📋 Project Overview

**Project Name:** Yang Family Financial & Tax Agent (LINE Bot)  
**Version:** 2.0 (Google Cloud Run)  
**Last Updated:** 2026-08-17  
**Owner:** Jack Yang  
**GitHub:** https://github.com/JackYangHT/family-finance-bot

---

## 🎯 Project Goals

1. **24/7 Hosting:** Migrate from Render.com to Google Cloud Run (free tier, no spin-down)
2. **Multi-Currency Support:** Income in USD/NTD, expenditures in NTD only
3. **5-Pocket Architecture:** Family Petty Cash, Urgent Fund, Son's USD Fixed, Wife's USD Fixed, Jack's Personal
4. **Conversational AI:** Bot asks clarifying questions (never "Unknown")
5. **Bilingual Support:** Jack (English/Chinese), Prapa/Araya (Thai ONLY with formal address)
6. **OCR Fallback:** Prompt user if AI cannot extract amount/vendor
7. **Google Sheets Integration:** 12 tabs with auto-formulas
8. **Dual Approval Workflow:** Jack ↔ Prapa mutual approval for budget/transfer/account operations

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   LINE App      │
│   (User Chat)   │
└────────┬────────┘
         │ Webhook
         ▼
┌─────────────────────────────────────────┐
│  Google Cloud Run (asia-southeast1)     │
│  ┌─────────────────────────────────┐    │
│  │  FastAPI + Uvicorn              │    │
│  │  app.py (Webhook Handler)       │    │
│  │  approval_workflow.py           │    │
│  └─────────────┬───────────────────┘    │
└────────────────┼─────────────────────────┘
         │
         ├──────────────┬────────────────┬─────────────────┐
         ▼              ▼                ▼                 ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ DeepInfra   │ │ Google      │ │ Google      │ │ Google      │
│ AI API      │ │ Sheets      │ │ Secret      │ │ Cloud       │
│ (DeepSeek-  │ │ (12 tabs)   │ │ Manager     │ │ Logging     │
│ V3, Qwen3-  │ │             │ │             │ │             │
│ VL)         │ │             │ │             │ │             │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
```

---

## 📊 Google Sheets Structure (12 Tabs)

| Tab Name | Purpose | Key Columns |
|----------|---------|-------------|
| **Raw_Expenses** | Daily expense logging | Timestamp, User, Category, Amount, Vendor, Pocket, Language |
| **Raw_Income** | Salary & income tracking | Timestamp, Person, Gross Pay, Tax, NHI, Labor Ins, Pension, Net Pay, Currency |
| **Raw_Payroll_Tax** | Taiwan tax compliance | Gross Pay, 扣繳，健保費，勞保費，勞退自提，實發 |
| **Chat_Logs** | AI conversation audit trail | User ID, Message Type, Raw Input, AI Response, Action, Status |
| **Pockets** | 5-pocket balance tracking | Pocket Name, Currency, Balance, Last Updated |
| **Transfers** | Inter-pocket transfers | From, To, Amount, Currency, Exchange Rate, Details |
| **Exchange_Rates** | USD/NTD conversion rates | Date, USD_NTD_Rate, Source |
| **Accounts** | Bank/pocket accounts | Account Name, Type, Currency, Owner, Balance, Approval Required |
| **Budget_Limits** | Monthly budget settings | Category, Monthly Budget, Approvers, Auto-Approve Below, Current MTD, Remaining |
| **Pending_Approvals** | Dual approval queue | Request ID, Requester, Type, Details, Amount, Approver, Status |
| **Approval_History** | Audit trail for approvals | Request ID, Decision, Approved At, Comments, Execution Status |
| **Dashboard_Summary** | Auto-calculated summaries | YTD totals, Net worth, Category breakdowns (FORMATTED_VALUE) |

---

## 👥 User Configuration

### Jack Yang (jack.yang)
- **Language:** English/Chinese
- **Polite Particle:** ครับ (male)
- **Greeting:** "Hello Mr Jack, what help can I do for you today?"
- **Approval Required:** Yes (for budget/transfer/account)
- **Approver:** Prapa (Araya Yang)

### Prapa Yang (prapa.yang, อารยา หยาง)
- **Language:** Thai ONLY
- **Formal Address:** คณนายอารยา หยาง
- **Polite Particle:** ครับ (male speaker - bot)
- **Greeting:** "สวัสดีครับคณนายอารยา หยาง มีอะไรให้รับใช้วันนี้ครับ?"
- **Approval Required:** Yes (for budget/transfer/account)
- **Approver:** Jack Yang

---

## 🔧 Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Hosting** | Google Cloud Run | 24/7 webhook server (free tier: 2M requests/month) |
| **Framework** | FastAPI + Uvicorn | Python webhook server |
| **LINE SDK** | line-bot-sdk 3.9.0 | QuickReplyButton support |
| **AI Text** | DeepSeek-V3 (DeepInfra) | Cheaper, fast categorization |
| **AI Vision** | Qwen3-VL-30B-A3B-Instruct | Receipt/salary slip OCR |
| **Database** | Google Sheets | 12 tabs with auto-formulas |
| **Auth** | Google Secret Manager | credentials.json mounted as /app/credentials.json |
| **Logging** | Google Cloud Logging | Real-time debugging |

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] Credentials stored in Secret Manager as `google-sheets-credentials`
- [ ] Secret mounted at `/app/credentials.json` in Cloud Run
- [ ] Environment variables set: `LINE_CHANNEL_ID`, `LINE_CHANNEL_SECRET`, `DEEPINFRA_API_KEY`
- [ ] Google Sheets service account has Editor access
- [ ] LINE webhook URL points to Cloud Run URL

### Cloud Run Configuration
- [ ] Region: asia-southeast1 (Singapore)
- [ ] Memory: 512Mi
- [ ] Timeout: 60s
- [ ] PORT: Uses $PORT env variable
- [ ] Secret volume: `/app/credentials.json`

### LINE Console
- [ ] Webhook URL: https://family-finance-bot-68212775293.asia-southeast1.run.app/webhook
- [ ] Use webhooks: ON
- [ ] Verification: Success (200 OK)

---

## 📱 LINE Bot Features

### Main Menu
1. 💸 Expenses / รายจ่าย
2. 💰 Salary / เงินเดือน
3. 🏦 Open Account / เปิดบัญชี
4. 💸 Transfer / โอนเงิน
5. 📊 Balance / ตรวจสอบยอด
6. 📋 Budget / ตั้งงบประมาณ
7. ⚖️ Approvals / ตรวจสอบคำขออนุมัติ

### Approval Workflow
- **Jack requests** → Prapa approves via `Approve REQ...` or `อนุมัติ REQ...`
- **Prapa requests** → Jack approves via `Approve REQ...`
- **Transactions execute** ONLY after approval
- **Audit trail** logged in Approval_History tab

### Expense Logging
- **Text format:** `vendor amount` (e.g., "7/11 200")
- **AI categorization:** DeepSeek-V3 extracts category, amount, vendor
- **Image upload:** Qwen3-VL OCR for receipts/salary slips
- **Fallback:** If OCR fails, prompt user to enter manually

### Balance Query
- **Dashboard_Summary** tab with FORMATTED_VALUE
- **11 lines max** for mobile-friendly display
- **Multi-currency:** USD + NTD support

---

## 🔐 Security & Compliance

### Secrets Management
- ✅ `credentials.json` NOT in Git (blocked by GitHub secret scanning)
- ✅ Stored in Google Secret Manager
- ✅ Mounted as volume in Cloud Run
- ✅ Service account: hermes-bot@gen-lang-client-0948238290.iam.gserviceaccount.com

### Taiwan Tax Compliance
- ✅ 扣繳 (Withholding Tax)
- ✅ 勞保費 (Labor Insurance)
- ✅ 健保費 (NHI)
- ✅ 勞退自提 (Pension 6%)
- ✅ 實發 (Net Pay)

### Data Privacy
- ✅ LINE user IDs stored (not personal info)
- ✅ Chat logs in Chat_Logs tab for audit
- ✅ Approval history tracked

---

## 📈 Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **Webhook Response Time** | < 5s | ~3s |
| **AI Categorization** | < 3s | ~2s |
| **Google Sheets Write** | < 2s | ~1s |
| **Uptime** | 99.9% | 100% (Cloud Run) |
| **Monthly Requests** | < 2M (free tier) | ~10K (family usage) |

---

## 🐛 Known Issues & Limitations

| Issue | Status | Workaround |
|-------|--------|------------|
| LINE User IDs not mapped | PENDING | Use prefix `jack.yang` / `prapa.yang` in messages |
| gcloud CLI OpenSSL bug | WORKAROUND | Use Cloud Console web UI |
| Google Sheets rate limit | MONITORING | Wait 60s between bulk operations |
| Approval notifications | MANUAL | Approver must check pending approvals manually |

---

## 🎯 Future Enhancements (Backlog)

### 🎨 LINE Flex Message UI (PRIORITY: HIGH - Active Development)
1. **Approval Cards** - Interactive JSON cards with Approve/Reject buttons (replaces text commands)
2. **Financial Summary Cards** - Color-coded dashboard with YTD totals, net worth, budget utilization
3. **Receipt Confirmation Cards** - Show extracted OCR data with Confirm/Edit buttons
4. **Weekly Wrap-Up Cards** - Auto-sent Friday afternoon (English for Jack, Thai for Prapa)

### 🏦 Account Architecture (PRIORITY: HIGH - Active Development)
5. **Pre-seeded 5 Pockets** - Hardcode accounts during deployment (no dynamic creation)
6. **Replace "Open Account"** with "Account Settings" / "Request New Category"
7. **New pocket requests** → Approval Card to spouse before creation

### ⚡ Async Processing (PRIORITY: MEDIUM - Planned)
8. **Google Cloud Tasks** - Queue OCR requests to prevent LINE webhook timeouts
9. **Instant 200 OK** → "Processing..." message → Background task → Result card

### 📅 Scheduled Notifications (PRIORITY: MEDIUM - Planned)
10. **Google Cloud Scheduler** - Weekly Friday wrap-up notifications
11. **Budget alerts** - Push when category exceeds 80% of budget
12. **Monthly reports** - Auto-generate PDF summary on 1st of month

---

## 📞 Support & Contacts

| Role | Contact |
|------|---------|
| **Project Owner** | Jack Yang (wenchiyang.jack@gmail.com) |
| **GitHub** | JackYangHT |
| **LINE Channel ID** | 2010958353 |
| **Google Cloud Project** | family-accounting-505206 |
| **Cloud Run Service** | family-finance-bot |
| **Service URL** | https://family-finance-bot-68212775293.asia-southeast1.run.app |

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-08-15 | Initial Render.com deployment |
| 1.1 | 2026-08-16 | Thai language support, 10-sheet structure |
| 1.2 | 2026-08-16 | QuickReplyButton fix, deduplication, smart image classifier |
| 2.0 | 2026-08-17 | Google Cloud Run migration, dual approval system, 12 tabs |
| 2.1 | 2026-08-17 | Professional bank call center style, DeepSeek model, formal Thai for Prapa |

---

## 📚 Related Documents

- `TASKS.md` - Current task tracking (done/in progress/backlog)
- `app.py` - Main webhook handler
- `approval_workflow.py` - Dual approval system
- `setup_sheets_full.py` - Google Sheets setup script
- `Dockerfile` - Cloud Run container configuration
- `IDEA.md` - Original project roadmap

---

**Last Updated:** 2026-08-17  
**Next Review:** 2026-08-24
