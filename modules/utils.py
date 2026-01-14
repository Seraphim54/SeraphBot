import random
import discord

# Shared D&D data
alignments = (
    "Lawful Good", "Neutral Good", "Chaotic Good", "Lawful Neutral", "True Neutral", "Chaotic Neutral", "Lawful Evil", "Neutral Evil", "Chaotic Evil"
)

races = (
    "Aarakocra", "Aasimar", "Astral Elf", "Autognome", "Bugbear", "Centaur", "Changeling", "Custom Lineage", "Deep Gnome", "Dhampir", "Dragonborn", "Duergar", "Dwarf", "Eladrin", "Elf", "Fairy", "Firbolg", "Genasi", "Giff", "Githyanki", "Githzerai", "Gnome", "Goblin", "Goliath", "Grung", "Hadozee", "Half-Elf", "Half-Orc", "Halfling", "Harengon", "Hexblood", "Hobgoblin", "Human", "Kalashtar", "Kender", "Kenku", "Kobold", "Leonin", "Lizardfolk", "Locathah", "Loxodon", "Minotaur", "Orc", "Owlin", "Plasmoid", "Reborn", "Satyr", "Sea Elf", "Shadar-Kai", "Shifter", "Simic Hybrid", "Tabaxi", "Thri-kreen", "Tiefling", "Tortle", "Triton", "Vedalken", "Verdan", "Warforged", "Yuan-ti"
)

classes = (
    "Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"
)

disc_colors = (
    "default", "teal", "dark_teal", "green", "dark_green", "blue", "dark_blue", "purple", "dark_purple", "magenta", "gold", "orange", "red", "dark_red", "brand_red", "brand_green", "grey", "dark_grey", "light_grey", "navy"
)

def mention_user(ctx):
    return ctx.author.mention

async def msgdel(ctx):
    await ctx.message.delete()

def get_random_color():
    return getattr(discord.Color, random.choice(disc_colors))()
