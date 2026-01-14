from discord.ext import commands
import random
from modules.utils import alignments, classes, races, msgdel, mention_user

class Rolls(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def deathsave(self, ctx):
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

    @commands.command()
    async def random_build(self, ctx):
        await msgdel(ctx)
        rand_align = random.choice(alignments)
        rand_race = random.choice(races)
        rand_class = random.choice(classes)

        await ctx.send(f"🐉 Go forth and seek adventure, {mention_user(ctx)}, with your shiny new {rand_align} {rand_race} {rand_class}")


async def setup(bot):
    await bot.add_cog(Rolls(bot))