from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()  # Only the bot owner can use this command
    async def shutdown(self, ctx):
        await ctx.send("Shutting down gracefully...")
        await self.bot.close()


async def setup(bot):
    await bot.add_cog(Admin(bot))