import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random


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

@bot.command()
async def dave(ctx):
    await ctx.send("Now, Dave. I’m afraid I can’t do that.")

import random

@bot.command()
async def deathsave(ctx):
    roll = random.randint(1, 20)

    if roll == 20:
        result = "🎉 Critical Success! You're Up with 1 HP!"
    elif roll == 1:
        result = "⚰️ Critical Fail! Death's Shadow falls upon you twice! ⚰️"
    elif roll >= 10:
        result = "✅ Success! You have gained one Success."
    else:
        result = "☠️ Fail! You are one step closer to Death."

    await ctx.send(f"You rolled a {roll}: {result}")

bot.run(TOKEN)