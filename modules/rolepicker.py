import discord
from discord.ext import commands
import json
import os

# Cleaned-up, single definition RolePicker module
import discord
from discord.ext import commands
import json
import os
import asyncio

class RolePicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join(os.path.dirname(__file__), '../data/role_reactions.json')
        self.load_config()
        self._bot_removing_reactions = set()  # (user_id, message_id, emoji_str)

    def load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

    @commands.command()
    async def rolepicker(self, ctx):
        """Post the role picker embed with role descriptions."""
        await ctx.message.delete()
        # Build description listing all roles
        desc_lines = []
        for entry in self.config['roles']:
            approval = " (Admin Approval Required)" if entry.get('admin_approval') else ""
            desc_lines.append(f"{entry['emoji']} — {entry['description']}{approval}")
        description = "\n".join(desc_lines)
        embed = discord.Embed(
            title=self.config.get('embed_title', 'Pick Your Role!'),
            description=description,
            color=discord.Color.blurple()
        )
        if 'embed_image' in self.config:
            embed.set_image(url=self.config['embed_image'])
        if 'embed_footer' in self.config:
            embed.set_footer(text=self.config['embed_footer'])
        msg = await ctx.send(embed=embed)
        self.config['message_id'] = msg.id
        self.config['channel_id'] = msg.channel.id
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)
        for entry in self.config['roles']:
            await msg.add_reaction(entry['emoji'])

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if not self._is_rolepicker_message(payload):
            return
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role_entry = self._get_role_entry(payload.emoji)
        if not role_entry:
            return
        role = guild.get_role(role_entry['role_id'])
        if not role:
            return
        if role_entry.get('admin_approval'):
            await self._handle_admin_approval(payload, member, role_entry, add=True)
        else:
            if role in member.roles:
                await member.remove_roles(role, reason="RolePicker toggle off")
                await self._notify_user(member, f"The role {role.name} has been removed from you.")
            else:
                await member.add_roles(role, reason="RolePicker reaction add")
                await self._notify_user(member, f"You have been given the role: {role.name}")
        channel = self.bot.get_channel(self.config['channel_id'])
        msg = await channel.fetch_message(self.config['message_id'])
        # Track that the bot is about to remove this user's reaction so we can ignore the resulting remove event
        key = (member.id, msg.id, str(payload.emoji))
        self._bot_removing_reactions.add(key)
        await msg.remove_reaction(payload.emoji, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Prevent role removal if this was a bot-initiated reaction removal
        key = (payload.user_id, payload.message_id, str(payload.emoji))
        if key in self._bot_removing_reactions:
            self._bot_removing_reactions.remove(key)
            return
        if not self._is_rolepicker_message(payload):
            return
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role_entry = self._get_role_entry(payload.emoji)
        if not role_entry:
            return
        role = guild.get_role(role_entry['role_id'])
        if not role:
            return
        if role_entry.get('admin_approval'):
            await self._handle_admin_approval(payload, member, role_entry, add=False)
        else:
            if role in member.roles:
                await member.remove_roles(role, reason="RolePicker reaction remove")
                await self._notify_user(member, f"The role {role.name} has been removed from you.")

    def _is_rolepicker_message(self, payload):
        return (
            payload.message_id == self.config.get('message_id') and
            payload.channel_id == self.config.get('channel_id')
        )

    def _get_role_entry(self, emoji):
        for entry in self.config['roles']:
            if str(entry['emoji']) == str(emoji):
                return entry
        return None

    async def _handle_admin_approval(self, payload, member, role_entry, add=True):
        admin_channel_id = self.config.get('admin_channel_id')
        if not admin_channel_id:
            return
        admin_channel = self.bot.get_channel(admin_channel_id)
        action = "add" if add else "remove"
        embed = discord.Embed(
            title="Role Approval Needed",
            description=f"User: {member.mention}\nRole: <@&{role_entry['role_id']}>\nAction: {action}",
            color=discord.Color.gold()
        )
        request_msg = await admin_channel.send(embed=embed)
        await request_msg.add_reaction("✅")
        await request_msg.add_reaction("❌")
        def check(reaction, user):
            return (
                reaction.message.id == request_msg.id and
                str(reaction.emoji) in ["✅", "❌"] and
                user.guild_permissions.administrator
            )
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=3600, check=check)
        except asyncio.TimeoutError:
            await request_msg.edit(content="Request timed out.")
            await self._notify_user(member, "Your role request timed out.")
            return
        if str(reaction.emoji) == "✅":
            role = member.guild.get_role(role_entry['role_id'])
            if add:
                await member.add_roles(role, reason="Admin approved rolepicker")
                await self._notify_user(member, f"Your request for {role.name} was approved!")
            else:
                await member.remove_roles(role, reason="Admin approved role removal")
                await self._notify_user(member, f"Your request to remove {role.name} was approved!")
            await request_msg.edit(content="Request approved.")
        else:
            await request_msg.edit(content="Request denied.")
            await self._notify_user(member, "Your role request was denied by an admin.")

    async def _notify_user(self, member, message):
        try:
            await member.send(message)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
