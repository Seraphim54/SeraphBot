import discord
from discord.ext import commands
import json
import os
import logging
import asyncio
from modules.utils import get_random_color

class RolePicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join(os.path.dirname(__file__), '../data/role_reactions.json')
        self.load_config()
        self._bot_removing_reactions = set()  # (user_id, message_id, emoji_str)
        self._reactions_lock = asyncio.Lock()  # Protect access to _bot_removing_reactions

    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Initialize a default configuration if the file is missing
            self.config = {
                "embed_title": "Pick Your Role!",
                "roles": []
            }
            # Ensure the directory exists and create the config file
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2)
            except (IOError, OSError, PermissionError) as e:
                # If file write fails during init, log but continue with in-memory config
                logging.warning(f"Failed to create role picker configuration file: {e}")
        except json.JSONDecodeError:
            # Fall back to a safe default if the JSON is corrupted
            self.config = {
                "embed_title": "Pick Your Role!",
                "roles": []
            }

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
        
        # Determine color following the pattern from events module
        if "color" in self.config and hasattr(discord.Color, self.config["color"]):
            color_value = getattr(discord.Color, self.config["color"])()
        else:
            color_value = get_random_color()
        
        embed = discord.Embed(
            title=self.config.get('embed_title', 'Pick Your Role!'),
            description=description,
            color=color_value
        )
        if 'embed_image' in self.config:
            embed.set_image(url=self.config['embed_image'])
        if 'embed_footer' in self.config:
            embed.set_footer(text=self.config['embed_footer'])
        msg = await ctx.send(embed=embed)
        self.config['message_id'] = msg.id
        self.config['channel_id'] = msg.channel.id
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except (IOError, OSError, PermissionError) as e:
            # If file write fails, log the error but don't crash the command
            # The message was already sent, so the role picker is functional
            # but the config won't be persisted
            logging.warning(f"Failed to save role picker configuration: {e}")
        for entry in self.config['roles']:
            try:
                await msg.add_reaction(entry['emoji'])
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                # Ignore failures to add reactions (invalid emoji, missing permissions, etc.)
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return
        if not self._is_rolepicker_message(payload):
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None:
            return
        role_entry = self._get_role_entry(payload.emoji)
        if not role_entry:
            return
        role = guild.get_role(role_entry['role_id'])
        if not role:
            return
        if role_entry.get('admin_approval'):
            # Remove user's reaction immediately
            channel = self.bot.get_channel(self.config['channel_id'])
            msg = await channel.fetch_message(self.config['message_id'])
            key = (member.id, msg.id, str(payload.emoji))
            async with self._reactions_lock:
                self._bot_removing_reactions.add(key)
            await msg.remove_reaction(payload.emoji, member)
            # Start admin approval flow
            await self._handle_admin_approval(payload, member, role_entry)
        else:
            if role in member.roles:
                await member.remove_roles(role, reason="RolePicker toggle off")
                await self._notify_user(member, f"The role {role.name} has been removed from you.")
            else:
                await member.add_roles(role, reason="RolePicker reaction add")
                await self._notify_user(member, f"You have been given the role: {role.name}")
            channel = self.bot.get_channel(self.config['channel_id'])
            msg = await channel.fetch_message(self.config['message_id'])
            key = (member.id, msg.id, str(payload.emoji))
            async with self._reactions_lock:
                self._bot_removing_reactions.add(key)
            await msg.remove_reaction(payload.emoji, member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        # Prevent role removal if this was a bot-initiated reaction removal
        key = (payload.user_id, payload.message_id, str(payload.emoji))
        async with self._reactions_lock:
            if key in self._bot_removing_reactions:
                self._bot_removing_reactions.remove(key)
                return
        if not self._is_rolepicker_message(payload):
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return
        member = guild.get_member(payload.user_id)
        if member is None:
            return
        role_entry = self._get_role_entry(payload.emoji)
        if not role_entry:
            return
        role = guild.get_role(role_entry['role_id'])
        if not role:
            return
        # For admin approval roles, ignore reaction removals since users never have the role
        # (it's removed by the bot immediately on add)
        if not role_entry.get('admin_approval'):
            if role in member.roles:
                await member.remove_roles(role, reason="RolePicker reaction remove")
                await self._notify_user(member, f"The role {role.name} has been removed from you.")

    def _is_rolepicker_message(self, payload):
        return (
            payload.message_id == self.config.get('message_id') and
            payload.channel_id == self.config.get('channel_id')
        )

    def _get_role_entry(self, emoji):
        # emoji: discord.PartialEmoji or str
        for entry in self.config['roles']:
            entry_emoji = entry['emoji']
            # Custom emoji: <a:name:id> or <:name:id>
            if entry_emoji.startswith('<:') or entry_emoji.startswith('<a:'):
                # Extract ID
                try:
                    entry_id = int(entry_emoji.split(':')[2][:-1])
                except Exception:
                    continue
                if hasattr(emoji, 'id') and emoji.id == entry_id:
                    return entry
            else:
                # Unicode emoji
                if (hasattr(emoji, 'name') and emoji.name == entry_emoji) or (str(emoji) == entry_emoji):
                    return entry
        return None

    def _emoji_matches(self, emoji_str, reaction_emoji):
        """Helper to check if a configured emoji string matches a Discord reaction emoji."""
        # Custom emoji: <a:name:id> or <:name:id>
        if emoji_str.startswith('<:') or emoji_str.startswith('<a:'):
            try:
                emoji_id = int(emoji_str.split(':')[2][:-1])
                return hasattr(reaction_emoji, 'id') and reaction_emoji.id == emoji_id
            except (IndexError, ValueError):
                return False
        else:
            # Unicode emoji
            return str(reaction_emoji) == emoji_str

    async def _handle_admin_approval(self, payload, member, role_entry, add=True):
        """Handle D&D role approval flow with admin reactions."""
        _ = add  # Reserved for future use
        admin_channel_id = self.config.get('admin_channel_id')
        if not admin_channel_id:
            return
        admin_channel = self.bot.get_channel(admin_channel_id)
        if not admin_channel:
            print(f"Warning: Admin channel {admin_channel_id} not found")
            await self._notify_user(member, "Your request could not be processed. Please contact an administrator.")
            return

        # Send DM to user that request is pending
        await self._notify_user(member, "Your request for D&D access is pending administrator approval.")
        
        # Send admin channel message
        embed = discord.Embed(
            title="Role Approval Needed",
            description=f"User: {member.mention}\nRequest: D&D access\nReact below to approve as Player, Spectator, or Deny.",
            color=discord.Color.gold()
        )
        request_msg = await admin_channel.send(embed=embed)
        
        player_emoji_str = "<:DnD:858802171193327616>"
        spectator_emoji_str = "<:dndspec:1462113193051553799>"
        await request_msg.add_reaction(player_emoji_str)
        await request_msg.add_reaction(spectator_emoji_str)
        await request_msg.add_reaction("❌")  # Deny
        
        def check(reaction, user):
            return (
                reaction.message.id == request_msg.id and
                (
                    (hasattr(reaction.emoji, 'id') and str(reaction.emoji.id) == "858802171193327616") or
                    (hasattr(reaction.emoji, 'id') and str(reaction.emoji.id) == "1462113193051553799") or
                    (str(reaction.emoji) == "❌")
                ) and
                user.guild_permissions.administrator
            )
        
        reaction, user = await self.bot.wait_for('reaction_add', check=check)
        
        # Remove all reactions from admin message after decision
        await request_msg.clear_reactions()
        
        if hasattr(reaction.emoji, 'id') and str(reaction.emoji.id) == "858802171193327616":
            # Approve as Player
            player_role_id = 957848615173378108
            role = member.guild.get_role(player_role_id)
            if role:
                await member.add_roles(role, reason="Admin approved D&D Player")
                await self._notify_user(member, "Your request for D&D Player was approved!")
                await request_msg.edit(content="Request approved as Player.")
            else:
                await request_msg.edit(content="Configuration error: Player role not found.")
        elif hasattr(reaction.emoji, 'id') and str(reaction.emoji.id) == "1462113193051553799":
            # Approve as Spectator
            spectator_role_id = 809223517949919272
            role = member.guild.get_role(spectator_role_id)
            if role:
                await member.add_roles(role, reason="Admin approved D&D Spectator")
                await self._notify_user(member, "Your request for D&D Spectator was approved!")
                await request_msg.edit(content="Request approved as Spectator.")
            else:
                await request_msg.edit(content="Configuration error: Spectator role not found.")
        else:
            # Denied
            await request_msg.edit(content="Request denied.")
            await self._notify_user(member, "Your D&D role request was denied by an admin.")

    async def _notify_user(self, member, message):
        """Attempt to send a DM to the user. Silently fails if user has DMs disabled or other send errors occur."""
        try:
            await member.send(message)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            # User has DMs disabled, the message cannot be sent, or the user object is invalid
            # This is acceptable - we don't want to break the flow if DMs fail
            pass

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
