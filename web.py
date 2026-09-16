from fastapi import FastAPI
import asyncio
import bot

app = FastAPI()

@app.get("/")
def root():
    return {"status": "SeraphBot is running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    # Launches the bot cleanly using FastAPI's existing async event loop.
    # This automatically triggers the custom_setup_hook() inside bot.py.
    asyncio.create_task(bot.bot.start(bot.TOKEN))
    print("🚀 FastAPI startup sequence successfully initiated the Discord bot task.", flush=True)
