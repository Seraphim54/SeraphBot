from discord.ext import commands
from modules.rolls import Rolls
from modules.utils import get_random_color, msgdel, disc_colors
import discord
import json

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def event(self, ctx, name: str):
        await msgdel(ctx)

        try:
            with open(f"data/{name}.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # Get channel and role
            channel_id = data.get("channel_id")
            role_id = data.get("role_id")
            channel = self.bot.get_channel(channel_id) if channel_id else ctx.channel
            role_mention = f"<@&{role_id}>" if role_id else ""

            # Determine color
            if "color" in data and hasattr(discord.Color, data["color"]):
                color_value = getattr(discord.Color, data["color"])()
            else:
                color_value = get_random_color()

            # Build embed
            embed = discord.Embed(
                title=data.get("title", ""),
                description=data.get("description", ""),
                color=color_value
            )

            if "image_url" in data and data["image_url"]:
                embed.set_image(url=data["image_url"])
            if "footer" in data and data["footer"]:
                embed.set_footer(text=data["footer"])

            # Send message
            message = await channel.send(content=role_mention, embed=embed)

            # Add reactions
            for emoji in data.get("reactions", []):
                try:
                    await message.add_reaction(emoji)
                except Exception as e:
                    print(f"Failed to add reaction {emoji}: {e}")

        except Exception as e:
            # Log the detailed error server-side, but send a generic message to users
            print(f"Error loading event '{name}': {e}")
            await ctx.send(f"Could not load event '{name}'. Please check that the event file exists and is properly formatted.")

async def setup(bot):
    await bot.add_cog(Events(bot))