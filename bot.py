import discord
from discord.ext import commands
import os
import random
import json
import asyncio
from modules.utils import disc_colors

# Retrieve the token from Render environment variables
TOKEN = os.getenv("bot_token")

# Create a bot with a prefix for commands
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), help_command=None)

# +------------------------+
# |  EXTENSION SETUP HOOK  |
# +------------------------+
# This special discord.py function automatically runs inside FastAPI's 
# async loop BEFORE the bot connects, loading your commands cleanly.
async def custom_setup_hook():
    print("🤖 Starting to load bot extensions...", flush=True)
    await bot.load_extension("modules.fun")
    await bot.load_extension("modules.rolls")
    await bot.load_extension("modules.admin")
    await bot.load_extension("modules.events")
    await bot.load_extension("modules.rolepicker")
    await bot.load_extension("modules.help")
    await bot.load_extension("modules.srd")
    print("✅ All extensions successfully attached to the setup hook!", flush=True)

# Attach the setup function directly to the bot instance
bot.setup_hook = custom_setup_hook

# +--------------+
# |  BOT EVENTS  |
# +--------------+

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}", flush=True)


# +----------------+
# |  BOT COMMANDS  |
# +----------------+

@bot.command()
async def hello2(ctx):
    await ctx.message.delete()
    await ctx.send("Hello gamer! If this worked right then your command of `!hello2` should not be above me")

@bot.command()
async def colortest(ctx):
    await ctx.send(f"The color choices are {disc_colors}")
