import discord
from discord.ext import commands
import aiohttp

class SRD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ask")
    async def ask(self, ctx, *, question: str):
        print("ASK COMMAND FIRED:", question)
        """Ask The Sixth Wing for SRD spell or rules information."""
        await ctx.trigger_typing()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://sixth-wing-agent.onrender.com/ask",
                    json={"question": question},
                    headers={"Content-Type": "application/json"}
                ) as resp:

                    if resp.status != 200:
                        await ctx.send(
                            f"⚠️ The Sixth Wing could not retrieve an answer (HTTP {resp.status})."
                        )
                        return

                    data = await resp.json()
                    answer = data.get("response", "⚠️ No response returned from the agent.")

                    await ctx.send(
                        f"🜂 **The Sixth Wing descends in radiant light…**\n"
                        f"{answer}"
                    )


        except Exception as e:
            await ctx.send(f"⚠️ An error occurred: `{e}`")

async def setup(bot):
    await bot.add_cog(SRD(bot))
