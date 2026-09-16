from fastapi import FastAPI
from bot import run_bot

app = FastAPI()

@app.get("/")
def root():
    return {"status": "SeraphBot is running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    run_bot()