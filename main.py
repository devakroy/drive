from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import traceback
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
        
        form = aiohttp.FormData()

        form.add_field("chat_id", TELEGRAM_CHAT_ID)

        form.add_field(
            "caption",
            f"File: {file.filename}"
        )

        form.add_field(
            "document",
            file_content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )

        async with aiohttp.ClientSession() as session:
            async with session.post(
                telegram_url,
                data=form
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
                    error = await response.text()
                    raise HTTPException(
                        status_code=400,
                        detail=f"Telegram error: {error}"
                    )
    
    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()
        print("Exception type:", type(e))
        print("Exception repr:", repr(e))

        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {repr(e)}"
        )

@app.get("/files")
async def list_files():
    """Return upload history for the dashboard."""
    return {"files": list(reversed(uploaded_files))}

# Serve frontend files from docs/ so the same files can be used by GitHub Pages
app.mount("/", StaticFiles(directory="docs", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
