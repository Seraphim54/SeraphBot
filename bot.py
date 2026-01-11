import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import random
import json


# Loads the Bots Token from .env file
load_dotenv()
TOKEN = os.getenv("bot_token")

# Create a bot with a prefix for commands
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# +----------------------+
# |  LISTS, TUPLES, ETC  |
# +----------------------+

alignments = ("Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil")

races = ("Aarakocra", "Aasimar", "Astral Elf", "Autognome", "Bugbear", "Centaur", "Changeling", "Custom Lineage", "Deep Gnome", "Dhampir", "Dragonborn", "Duergar", "Dwarf", "Eladrin", "Elf", "Fairy", "Firbolg", "Genasi", "Giff", "Githyanki", "Githzerai", "Gnome", "Goblin", "Goliath", "Grung", "Hadozee", "Half-Elf", "Half-Orc", "Halfling", "Harengon", "Hexblood", "Hobgoblin", "Human", "Kalashtar", "Kender", "Kenku", "Kobold", "Leonin", "Lizardfolk", "Locathah", "Loxodon", "Minotaur", "Orc", "Owlin", "Plasmoid", "Reborn", "Satyr", "Sea Elf", "Shadar-Kai", "Shifter", "Simic Hybrid", "Tabaxi", "Thri-kreen", "Tiefling", "Tortle", "Triton", "Vedalken", "Verdan", "Warforged", "Yuan-ti")

classes = ("Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard")

disc_colors = ("default", "teal", "dark_teal", "green", "dark_green", "blue", "dark_blue", "purple", "dark_purple", "magenta", "gold", "orange", "red", "dark_red", "brand_red", "brand_green", "grey", "dark_grey", "light_grey", "navy")

rand_color = random.choice(disc_colors)

# +--------------------+
# |  HELPER FUNCTIONS  |
# +--------------------+

def mention_user(ctx):
    return ctx.author.mention

async def msgdel(ctx):
    await ctx.message.delete()

def get_random_color():
    return getattr(discord.Color, random.choice(disc_colors))()

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
async def hello(ctx):
    await ctx.send("Hello gamer! 🎮")

@bot.command()
async def hello2(ctx):
    await ctx.message.delete()
    await ctx.send("Hello gamer! If this worked right then your command of `!hello2` should not be above me")

@bot.command()
async def colortest(ctx):
    await ctx.send(f"The color choices are {disc_colors}")

@bot.command()
async def dave(ctx):
    await ctx.send("Now, Dave. I'm afraid I can't do that.")

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

@bot.command()
async def random_build(ctx):
    await msgdel(ctx)
    rand_align = random.choice(alignments)
    rand_race = random.choice(races)
    rand_class = random.choice(classes)

    await ctx.send(f"🐉 Go forth and seek adventure, {mention_user(ctx)}, with your shiny new {rand_align} {rand_race} {rand_class}")

@bot.command()
async def mmn(ctx):
    await ctx.send("🤓 Eugene 🤓")

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

bot.run(TOKEN)
