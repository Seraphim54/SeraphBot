from fastapi import FastAPI
import threading
import bot

app = FastAPI()

@app.get("/")
def root():
    return {"status": "SeraphBot is running"}

@app.get("/health")
def health():
    return {"ok": True}

def start_bot():
    bot.run_bot()

@app.on_event("startup")
async def startup_event():
    thread = threading.Thread(target=start_bot)
    thread.start()
