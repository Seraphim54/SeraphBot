from fastapi import FastAPI
import asyncio
import logging
import sys
import bot

# Configure logging globally before starting anything
# This safely directs all discord.py framework events to Render's console
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI()

@app.get("/")
def root():
    return {"status": "SeraphBot is running"}

@app.get("/health")
def health():
    return {"ok": True}

@app.on_event("startup")
async def startup_event():
    # Start the bot cleanly without passing invalid arguments to .start()
    asyncio.create_task(bot.bot.start(bot.TOKEN))
    print("🚀 FastAPI startup sequence successfully initiated the Discord bot task.", flush=True)