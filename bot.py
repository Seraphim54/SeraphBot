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

# -- Choice Tuples

alignments = ("Lawful Good", "Neutral Good", "Chatoic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil")

races = ("Aarakocra", "Aasimar", "Astral Elf", "Autognome", "Bugbear", "Centaur", "Changeling", "Custom Lineage", "Deep Gnome", "Dhampir", "Dragonborn", "Duergar", "Dwarf", "Eladrin", "Elf", "Fairy", "Firbolg", "Genasi", "Giff", "Githyanki", "Githzerai", "Gnome", "Goblin", "Goliath", "Grung", "Hadozee", "Half-Elf", "Half-Orc", "Halfling", "Harengon", "Hexblood", "Hobgoblin", "Human", "Kalashtar", "Kender", "Kenku", "Kobold", "Leonin", "Lizardfolk", "Locathah", "Loxodon", "Minotaur", "Orc", "Owlin", "Plasmoid", "Reborn", "Satyr", "Sea Elf", "Shadar-Kai", "Shifter", "Simic Hybrid", "Tabaxi", "Thri-kreen", "Tiefling", "Tortle", "Triton", "Vedalken", "Verdan", "Warforged", "Yuan-ti")

classes = ("Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard")

@bot.command()
async def random_build(ctx):
    rand_align = random.choice(alignments)
    rand_race = random.choice(races)
    rand_class = random.choice(classes)

    await ctx.send(f"🐉 Go forth and seek adventure with your shiny new {rand_align} {rand_race} {rand_class}")

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

# -- lets play with embeds

@bot.command()
async def glimmerfen_event(ctx):
    channel = bot.get_channel(1406738456176099348)
    role_id = 1406739339739926538
    role_mention = f"<@&1406739339739926538>"
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

bot.run(TOKEN)


723372562255446076