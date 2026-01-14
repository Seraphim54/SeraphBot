from discord.ext import commands
import random
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
    
    @commands.command()
    async def bnuuy(self, ctx):
        bunny_gifs = [
        "https://tenor.com/JBF3fq5wKL.gif",
        "https://tenor.com/view/bunny-cute-bun-rabbit-dance-gif-12204421675478327501",
        "https://tenor.com/view/bunny-eating-gif-27018618",
        "https://tenor.com/view/albert-harebrayne-bunny-rabbit-gif-10500821922776666435",
        "https://tenor.com/view/bunny-kissing-dog-bunny-dog-kissing-puppy-gif-10364923600939704626",
    ]
        gif = random.choice(bunny_gifs)
        await ctx.send(gif)

    @commands.command()
    async def mothman(self, ctx):
        mothtwerk = "https://art.ngfiles.com/images/3435000/3435336_codingcanine_thicc-mothman.gif"
        await ctx.send(mothtwerk)


async def setup(bot):
    await bot.add_cog(Fun(bot))