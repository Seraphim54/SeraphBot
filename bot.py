import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Loads the Bots Token from .env file
load_dotenv()
TOKEN = os.getenv("bot_token")

# Create a bot with a prefix for commands
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello gamer! 🎮")

bot.run(TOKEN)