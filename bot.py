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

alignments = ("Lawful Good", "Neutral Good", "Chatoic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil")

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
        rolls = [random.randint(1, 6) for v in range(4)]
        top_three = sorted(rolls, reverse=True)[:3]
        return sum(top_three)

    def roll_stat_block(min_total=72):
        attempts = 0

        while True:
            attempts += 1
            stats = [roll_stat() for s in range(6)]
            if sum(stats) >= min_total:
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

# -- lets play with direct embeds

@bot.command()
async def glimmerfen_event(ctx):
    channel = bot.get_channel(1406738456176099348)
    role_id = 1406739339739926538
    role_mention = f"<@&{role_id}>"
    if channel:
        embed = discord.Embed(
            title="🟣 **Shadows Over Glimmerfen Session 1** 🟣",
            description="Session 1 kicks off this week — and everything feels normal.\n*Too normal*.\nJoin us in the cozy glow of the Shadewisp Inn, where arcade contests, bard singalongs, and small-town charm set the stage. The shadows haven't started whispering yet.\n\nBut they will.\n\n 🕯️ Expect festival vibes, flickering lanterns, and your first taste of the strange.",
            
            color=discord.Color.dark_purple()  # Optional: adds a left border color
        )
        embed.set_image(url="https://files.d20.io/images/453071419/W3xZgoS3AxDljsbcoPbeDw/max.png")
        embed.set_footer(text="Saturday Nov 1, 2025 at 7 PM CST")
    
        await channel.send(content=role_mention, embed=embed)
    else:
        await ctx.send("could not find the test channel.")

# -- testing externally loaded embed from individual json

@bot.command()
async def embed(ctx, name: str):
    await msgdel(ctx)
    
    try:
        with open (f"data/{name}.json", "r") as f:
            data=json.load(f)

        # Determine color: use JSON value if present, else random

            if "color" in data and hasattr(discord.Color, data["color"]):
                color_value = getattr(discord.Color, data["color"])()
            else:
                color_value = get_random_color()
        
            embed = discord.Embed(
                title=data["title"],
                description=data["description"],
                color=color_value
            )
            if "image_url" in data and data["image_url"]:
                embed.set_image(url=data["image_url"])

            if "footer" in data and data["footer"]:
                embed.set_footer(text=data["footer"])

            await ctx.send(embed=embed)
    except FileNotFoundError:
        await ctx.send(f"No embed found for `{name}`.")
    except Exception as e:
        await ctx.send(f"Error loading embed: {e}")


bot.run(TOKEN)