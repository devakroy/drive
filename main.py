from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from datetime import datetime
import uvicorn
import aiohttp
import aiofiles

app = FastAPI()

# Enable CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get credentials from environment variables
VALID_USERNAME = os.getenv("APP_USERNAME")
VALID_PASSWORD = os.getenv("APP_PASSWORD")

# Telegram credentials from environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ensure credentials are set
if not VALID_USERNAME or not VALID_PASSWORD:
    raise ValueError("APP_USERNAME and APP_PASSWORD environment variables must be set")

# Keep a simple in-memory upload history for the dashboard
uploaded_files = []

class LoginRequest(BaseModel):
    username: str
    password: str

@app.post("/login")
async def login(request: LoginRequest):
    """Validate username and password"""
    
    if request.username == VALID_USERNAME and request.password == VALID_PASSWORD:
        return {
            "success": True,
            "message": "Login successful",
            "token": "your-jwt-token-here"  # You can add JWT later
        }
    else:
        return {
            "success": False,
            "message": "Invalid username or password"
        }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile):
    """Upload file to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise HTTPException(status_code=500, detail="Telegram credentials not configured")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Send to Telegram
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                telegram_url,
                data={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "caption": f"File: {file.filename}"
                },
                files={"document": (file.filename, file_content, file.content_type)}
            ) as response:
                if response.status == 200:
                    file_size = len(file_content)
                    uploaded_files.append({
                        "name": file.filename,
                        "size": file_size,
                        "status": "Uploaded",
                        "uploaded_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                    })
                    return {
                        "success": True,
                        "message": f"File '{file.filename}' uploaded to Telegram successfully"
                    }
                else:
                    raise HTTPException(status_code=400, detail="Failed to send file to Telegram")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.get("/files")
async def list_files():
    """Return upload history for the dashboard."""
    return {"files": list(reversed(uploaded_files))}

# Serve frontend files from docs/ so the same files can be used by GitHub Pages
app.mount("/", StaticFiles(directory="docs", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
