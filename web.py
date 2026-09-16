from fastapi import FastAPI
import asyncio
import logging  # Import Python's logging library
import sys
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
    # 1. Create a stream handler pointing straight to standard output
    render_log_handler = logging.StreamHandler(sys.stdout)
    
    # 2. Launch the bot while explicitly telling discord.py to use this handler.
    # This forces internal command errors and triggers to show up on Render.
    asyncio.create_task(
        bot.bot.start(
            bot.TOKEN, 
            log_handler=render_log_handler, 
            log_level=logging.INFO
        )
    )
    print("🚀 FastAPI startup sequence successfully initiated the Discord bot task.", flush=True)

#from fastapi import FastAPI
#import asyncio
#import bot
#
#app = FastAPI()
#
#@app.get("/")
#def root():
#    return {"status": "SeraphBot is running"}
#
#@app.get("/health")
#def health():
#    return {"ok": True}
#
#@app.on_event("startup")
#async def startup_event():
#    # Launches the bot cleanly using FastAPI's existing async event loop.
#    # This automatically triggers the custom_setup_hook() inside bot.py.
#    asyncio.create_task(bot.bot.start(bot.TOKEN))
#    print("🚀 FastAPI startup sequence successfully initiated the Discord bot task.", flush=True)