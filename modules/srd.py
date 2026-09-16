import discord
from discord.ext import commands
import requests

DND_API = "https://www.dnd5eapi.co/api/spells/"

class SRD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_spell_info(self, spell_name: str):
        # Format input (e.g., "Magic Missile" -> "magic-missile")
        spell_slug = spell_name.lower().strip().replace(" ", "-")
        url = DND_API + spell_slug
        
        print(f"Fetching API URL: {url}", flush=True)
        r = requests.get(url)
        print(f"API Response Status: {r.status_code}", flush=True)

        if r.status_code != 200:
            return None

        data = r.json()
        return {
            "name": data.get("name"),
            "level": data.get("level"),
            "school": data.get("school", {}).get("name"),
            "casting_time": data.get("casting_time"),
            "range": data.get("range"),
            "duration": data.get("duration"),
            "desc": "\n".join(data.get("desc", []))
        }

    @commands.command(name="ask")
    async def ask(self, ctx, *, question: str):
        # Corrected modern async context manager syntax for discord.py v2.0+
        async with ctx.typing():
            print(f"User asked for spell: '{question}'", flush=True)

            # Look up the entire user input directly as a single spell name
            spell = self.get_spell_info(question)
            
            if spell:
                embed = discord.Embed(
                    title=f"{spell['name']} (Level {spell['level']} {spell['school']})",
                    description=spell['desc'][:2000],  # Keeps it safe under Discord's 2048 limit
                    color=discord.Color.blue()
                )
                embed.add_field(name="Casting Time", value=spell["casting_time"], inline=True)
                embed.add_field(name="Range", value=spell["range"], inline=True)
                embed.add_field(name="Duration", value=spell["duration"], inline=True)

                await ctx.send(embed=embed)
                return

            await ctx.send(f"I couldn't find a spell matching '{question}'. Make sure you typed the exact name.")

    @commands.command(name="testembed")
    async def testembed(self, ctx):
        embed = discord.Embed(
            title="Embed Test",
            description="If you see this, embeds are working and SRD.py is loaded.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SRD(bot))
