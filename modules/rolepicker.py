import discord
from discord.ext import commands
import json
import os

class RolePicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join(os.path.dirname(__file__), '../data/role_reactions.json')
        self.config = self.load_config()

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @commands.command()
    async def rolepicker(self, ctx):
        await ctx.message.delete()
        channel = self.bot.get_channel(self.config['channel_id'])
        embed = discord.Embed(
            title=self.config['embed_title'],
            description=self.config['embed_description'],
            color=discord.Color.blurple()
        )
        for role in self.config['roles']:
            embed.add_field(name=role['emoji'], value=role['description'], inline=False)
        msg = await channel.send(embed=embed)
        guild = ctx.guild
        for role in self.config['roles']:
            emoji_str = role['emoji']
            # Check for custom emoji format
            if emoji_str.startswith('<:') and emoji_str.endswith('>'):
                # Extract emoji ID
                emoji_id = int(emoji_str.split(':')[2][:-1])
                emoji_obj = discord.utils.get(guild.emojis, id=emoji_id)
                if emoji_obj:
                    await msg.add_reaction(emoji_obj)
                else:
                    await msg.add_reaction(emoji_str)  # fallback
            else:
                await msg.add_reaction(emoji_str)
        # Store message ID for tracking reactions
        self.config['last_message_id'] = msg.id
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.config.get('last_message_id'):
            return
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        emoji_match = None
        for role in self.config['roles']:
            emoji_str = role['emoji']
            # Custom emoji
            if emoji_str.startswith('<:') and emoji_str.endswith('>'):
                emoji_id = int(emoji_str.split(':')[2][:-1])
                if payload.emoji.id == emoji_id:
                    emoji_match = role
                    break
            else:
                if payload.emoji.name == emoji_str:
                    emoji_match = role
                    break
        if emoji_match:
            if emoji_match.get('admin_approval'):
                # Notify user in channel
                channel = self.bot.get_channel(self.config['channel_id'])
                user = await self.bot.fetch_user(payload.user_id)
                await channel.send(f"{user.mention}, your request for the '{emoji_match['description']}' role has been sent to the admins for approval.")
                # Post in admin channel
                admin_channel = self.bot.get_channel(self.config['admin_channel_id'])
                admin_msg = await admin_channel.send(f"User {user.mention} has requested the '{emoji_match['description']}' role. React below to approve or deny.")
                await admin_msg.add_reaction("✅")
                await admin_msg.add_reaction("❌")
                # Optionally, store pending request info for later
            else:
                role_obj = guild.get_role(emoji_match['role_id'])
                if role_obj:
                    await member.add_roles(role_obj, reason="RolePicker reaction")

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
