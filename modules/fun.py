from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello gamer! 🎮")

    @commands.command()
    async def dave(self, ctx):
        await ctx.send("Now, Dave. I'm afraid I can't do that.")

    @commands.command()
    async def mmn(self, ctx):
        await ctx.send("🤓 Eugene 🤓")


def setup(bot):
    bot.add_cog(Fun(bot))
