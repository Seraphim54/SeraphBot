import requests
from discord.ext import commands

DND_API = "https://www.dnd5eapi.co/api/spells/"

class SRD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_spell_info(self, spell_name: str):
        spell_name = spell_name.lower().replace(" ", "-")
        url = DND_API + spell_name
        r = requests.get(url)

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

        # Try to detect a spell name in the question
        words = question.lower().split()
        for w in words:
            spell = self.get_spell_info(w)
            if spell:
                response = (
                    f"**{spell['name']}** (Level {spell['level']} {spell['school']} spell)\n"
                    f"**Casting Time:** {spell['casting_time']}\n"
                    f"**Range:** {spell['range']}\n"
                    f"**Duration:** {spell['duration']}\n\n"
                    f"**Description:**\n{spell['desc']}"
                )
                await ctx.send(response)
                return

        # No spell found
        await ctx.send("I couldn't find a spell matching your question.")
