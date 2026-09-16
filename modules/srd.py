import discord
from discord.ext import commands
import requests

DND_API = "https://www.dnd5eapi.co/api/spells/"

class SRD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_spell_info(self, spell_name: str):
        spell_name = spell_name.lower().replace(" ", "-")
        url = DND_API + spell_name
        r = requests.get(url)

        print("Fetching:", url, "Status:", r.status_code)

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
        await ctx.trigger_typing()

        # Try each word in the question as a spell name
        for word in question.lower().split():
            spell = self.get_spell_info(word)
            if spell:
                embed = discord.Embed(
                    title=f"{spell['name']} (Level {spell['level']} {spell['school']})",
                    description=spell['desc'],
                    color=discord.Color.blue()
                )
                embed.add_field(name="Casting Time", value=spell["casting_time"], inline=True)
                embed.add_field(name="Range", value=spell["range"], inline=True)
                embed.add_field(name="Duration", value=spell["duration"], inline=True)

                await ctx.send(embed=embed)
                return

        await ctx.send("I couldn't find a spell matching your question.")

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