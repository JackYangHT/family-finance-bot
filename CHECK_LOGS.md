# 🔍 Cloud Run Logs - Yang Family Finance Bot

**Open this URL in your browser:**
```
https://console.cloud.google.com/logs/query;query=resource.type%3D"cloud_run_revision"%20AND%20resource.labels.service_name%3D"family-finance-bot"%20AND%20severity%3E%3DDEFAULT?project=family-accounting-505206&advancedFilter=resource.type%3D%22cloud_run_revision%22%0Aresource.labels.service_name%3D%22family-finance-bot%22%0Aseverity%3E%3DDEFAULT
```

## What to Look For:

### ✅ If Webhook is Working:
```
🔔 WEBHOOK CALLED - Signature: YES, Body length: 523 bytes
📥 Processing webhook body: {"destination":"U...","events":[{"type":"message",...
✅ Handler processed successfully
```

### ❌ If Webhook NOT Called:
- No logs appear when you send LINE messages
- This means LINE isn't sending webhooks to Cloud Run

### ⚠️ If Errors:
```
⚠️ Webhook handler error (returning 200 anyway): [error message]
[traceback]
```

## Steps:

1. **Open the URL above** in your browser
2. **Send a test message** in LINE: `jack.yang test123`
3. **Watch for new logs** appearing in real-time
4. **Copy the log output** and paste it here

## Alternative - Direct Log Query:

If the URL doesn't work, manually:
1. Go to: https://console.cloud.google.com/logs
2. Select project: `family-accounting-505206`
3. In the query box, paste:
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="family-finance-bot"
   severity>=DEFAULT
   ```
4. Click "Run Query"
5. Send a LINE message and watch for new logs
