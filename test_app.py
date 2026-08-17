"""Minimal test app for Cloud Run"""
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
@app.get("/health")
def health():
    return {"status": "healthy", "message": "Cloud Run is working!"}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
