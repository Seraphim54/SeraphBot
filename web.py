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
    # Use FastAPI's loop to run the bot cleanly in the background
    # This prevents the thread loop collision that stops extensions from loading
    asyncio.create_task(bot.bot.start(bot.TOKEN))
    
    # Load all your extensions inside this same active loop context
    await bot.bot.load_extension("modules.fun")
    await bot.bot.load_extension("modules.rolls")
    await bot.bot.load_extension("modules.admin")
    await bot.bot.load_extension("modules.events")
    await bot.bot.load_extension("modules.rolepicker")
    await bot.bot.load_extension("modules.help")
    await bot.bot.load_extension("modules.srd")
    
    print("🤖 SeraphBot initialized and extensions loaded successfully!", flush=True)

## Legacy

#from fastapi import FastAPI
#import threading
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
#def start_bot():
#    bot.run_bot()
#
#@app.on_event("startup")
#async def startup_event():
#    thread = threading.Thread(target=start_bot)
#    thread.start()
