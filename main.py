from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uvicorn

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

# Ensure credentials are set
if not VALID_USERNAME or not VALID_PASSWORD:
    raise ValueError("APP_USERNAME and APP_PASSWORD environment variables must be set")

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

@app.get("/")
async def root():
    return {"message": "My Drive API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

# Serve static files (HTML, CSS, JS)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
