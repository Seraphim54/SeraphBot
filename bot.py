
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

@bot.command()
async def newstats(ctx):
    def roll_stat():
        rolls = [random.randint(1, 6) for _ in range(4)]
        top_three = sorted(rolls, reverse=True)[:3]
        return sum(top_three)

    def roll_stat_block(min_total=72, max_attempts=100000):
        attempts = 0
        stats = None

        while attempts < max_attempts:
            attempts += 1
            stats = [roll_stat() for s in range(6)]
            if sum(stats) >= min_total:
                return stats, attempts

        # If we reach here, we failed to hit min_total within max_attempts.
        # Log this so it can be investigated, but still return the last stats.
        print(
            f"[newstats] Warning: failed to reach min_total={min_total} "
            f"within max_attempts={max_attempts}. Returning last roll after {attempts} attempts."
        )
        return stats, attempts
    stats, tries = roll_stat_block()
    await ctx.send(f"Rolled in {tries} attempt(s): `{stats}` (Total: {sum(stats)})")

@bot.command()
async def bnuuy(ctx):
    bunny_gifs = [
        "https://tenor.com/JBF3fq5wKL.gif",
        "https://tenor.com/view/bunny-cute-bun-rabbit-dance-gif-12204421675478327501",
        "https://tenor.com/view/bunny-eating-gif-27018618",
        "https://tenor.com/view/albert-harebrayne-bunny-rabbit-gif-10500821922776666435",
        "https://tenor.com/view/bunny-kissing-dog-bunny-dog-kissing-puppy-gif-10364923600939704626",
    ]
    gif = random.choice(bunny_gifs)
    await ctx.send(gif)

@bot.command()
async def mothman(ctx):
    mothtwerk = "https://art.ngfiles.com/images/3435000/3435336_codingcanine_thicc-mothman.gif"
    await ctx.send(mothtwerk)


# -- Modular Event Loader

@bot.command()
async def event(ctx, name: str):
    await msgdel(ctx)

    try:
        with open(f"data/{name}.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Get channel and role
        channel_id = data.get("channel_id")
        role_id = data.get("role_id")
        channel = bot.get_channel(channel_id) if channel_id else ctx.channel
        role_mention = f"<@&{role_id}>" if role_id else ""

        # Determine color
        if "color" in data and hasattr(discord.Color, data["color"]):
            color_value = getattr(discord.Color, data["color"])()
        else:
            color_value = get_random_color()

        # Build embed
        embed = discord.Embed(
            title=data.get("title", ""),
            description=data.get("description", ""),
            color=color_value
        )

        if "image_url" in data and data["image_url"]:
            embed.set_image(url=data["image_url"])
        if "footer" in data and data["footer"]:
            embed.set_footer(text=data["footer"])

        # Send message
        message = await channel.send(content=role_mention, embed=embed)

        # Add reactions
        for emoji in data.get("reactions", []):
            try:
                await message.add_reaction(emoji)
            except Exception as e:
                print(f"Failed to add reaction {emoji}: {e}")

    except Exception as e:
        # Log the detailed error server-side, but send a generic message to users
        print(f"Error loading event '{name}': {e}")
        await ctx.send(f"Could not load event '{name}'. Please check that the event file exists and is properly formatted.")


# +-------------------+
# |  LOAD EXTENSIONS  |
# +-------------------+

if __name__ == "__main__":
    async def main():
        await bot.load_extension("modules.fun")
        await bot.load_extension("modules.rolls")
        await bot.start(TOKEN)

    asyncio.run(main())
