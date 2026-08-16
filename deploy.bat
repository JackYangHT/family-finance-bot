@echo off
echo Deploying to Google Cloud Run...
echo.

gcloud run deploy family-finance-bot ^
  --source . ^
  --platform managed ^
  --region asia-east1 ^
  --allow-unauthenticated ^
  --set-env-vars LINE_CHANNEL_ID=2010958353,LINE_CHANNEL_SECRET=50e7e287284dfa7a0ecebf039c884b9e ^
  --set-secrets "/app/credentials.json=google-sheets-credentials:latest" ^
  --memory 512Mi ^
  --timeout 60s ^
  --port 8080

echo.
echo Deployment complete!
pause
