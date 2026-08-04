from fastapi import FastAPI

app = FastAPI(
    title="MiraiDesk AI",
    description="AI Workplace Assistant for Japanese Companies",
    version="0.1.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to MiraiDesk AI 🚀",
        "status": "Backend Running Successfully"
    }