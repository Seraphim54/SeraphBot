
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random
import json
import asyncio
import asyncio


# Loads the Bots Token from .env file
load_dotenv()
TOKEN = os.getenv("bot_token")

# Create a bot with a prefix for commands
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# +----------------------+
# |  LISTS, TUPLES, ETC  |
# +----------------------+
from modules.utils import alignments, races, classes, disc_colors, mention_user, msgdel, get_random_color

# +--------------+
# |  BOT EVENTS  |
# +--------------+

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")


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

# +-------------------+
# |  LOAD EXTENSIONS  |
# +-------------------+

if __name__ == "__main__":
    async def main():
        await bot.load_extension("modules.fun")
        await bot.load_extension("modules.rolls")
        await bot.load_extension("modules.admin")
        await bot.load_extension("modules.events")
        await bot.start(TOKEN)

    asyncio.run(main())
