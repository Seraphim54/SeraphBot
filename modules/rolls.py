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

    @commands.command()
    async def newstats(self, ctx):
        def roll_stat():
            rolls = [random.randint(1, 6) for _ in range(4)]
            top_three = sorted(rolls, reverse=True)[:3]
            return sum(top_three)

        async def roll_stat_block(min_total=72, max_attempts=100000):
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
        stats, tries = await roll_stat_block()
        await ctx.send(f"Rolled in {tries} attempt(s): `{stats}` (Total: {sum(stats)})")



async def setup(bot):
    await bot.add_cog(Rolls(bot))