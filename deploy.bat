@echo off
echo ============================================
echo  Deploying Yang Family Finance Bot
echo  to Google Cloud Run
echo ============================================
echo.

cd /d "%~dp0"

echo Current directory: %CD%
echo.

echo Checking gcloud installation...
where gcloud >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: gcloud not found in PATH!
    echo Please make sure Google Cloud CLI is installed.
    echo.
    pause
    exit /b 1
)

echo gcloud found. Starting deployment...
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
echo ============================================
if %ERRORLEVEL% EQU 0 (
    echo  DEPLOYMENT SUCCESSFUL!
    echo  Copy the Service URL above and share it.
) else (
    echo  DEPLOYMENT FAILED - Check errors above.
)
echo ============================================
echo.
echo Press any key to exit...
pause >nul
