import discord
from discord.ext import commands
import json
import os

class RolePicker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join(os.path.dirname(__file__), '../data/role_reactions.json')
        self.load_config()
        self._bot_removing_reactions = set()  # (user_id, message_id, emoji_str)

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
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
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
            self._bot_removing_reactions.add(key)
            await msg.remove_reaction(payload.emoji, member)
            # Start admin approval flow
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

    async def _handle_admin_approval(self, payload, member, role_entry, add=True):
        admin_channel_id = self.config.get('admin_channel_id')
        if not admin_channel_id:
            return
        admin_channel = self.bot.get_channel(admin_channel_id)
        if admin_channel is None:
            # Admin channel is misconfigured or inaccessible; notify user and exit gracefully
            await self._notify_user(
                member,
                "Your request for D&D access could not be processed because the admin approval channel "
                "is not configured correctly. Please contact a server administrator."
            )
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
        try:
            await request_msg.add_reaction(player_emoji_str)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        try:
            await request_msg.add_reaction(spectator_emoji_str)
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        try:
            await request_msg.add_reaction("❌")  # Deny
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
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
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=300)
        except asyncio.TimeoutError:
            # No admin responded in time; mark request as expired and notify user
            try:
                await request_msg.clear_reactions()
                await request_msg.edit(content="Request expired: no admin response.")
            except Exception:
                pass
            await self._notify_user(member, "Your D&D role request expired because no admin responded in time. Please try again later.")
            return
        # Remove all reactions from admin message after decision
        await request_msg.clear_reactions()
        if hasattr(reaction.emoji, 'id') and str(reaction.emoji.id) == "858802171193327616":
            # Approve as Player
            player_role_id = 957848615173378108
            role = member.guild.get_role(player_role_id)
            if role is not None:
                await member.add_roles(role, reason="Admin approved D&D Player")
                await self._notify_user(member, f"Your request for D&D Player was approved!")
                await request_msg.edit(content="Request approved as Player.")
            else:
                await request_msg.edit(content="Configuration error: Player role not found.")
                await self._notify_user(member, "There was a configuration problem assigning your D&D Player role. Please contact an admin.")
        elif hasattr(reaction.emoji, 'id') and str(reaction.emoji.id) == "1462113193051553799":
            # Approve as Spectator
            spectator_role_id = 809223517949919272
            role = member.guild.get_role(spectator_role_id)
            if role is not None:
                await member.add_roles(role, reason="Admin approved D&D Spectator")
                await self._notify_user(member, f"Your request for D&D Spectator was approved!")
                await request_msg.edit(content="Request approved as Spectator.")
            else:
                await request_msg.edit(content="Configuration error: Spectator role not found.")
                await self._notify_user(member, "There was a configuration problem assigning your D&D Spectator role. Please contact an admin.")
        else:
            await request_msg.edit(content="Request denied.")
            await self._notify_user(member, "Your D&D role request was denied by an admin.")

    async def _notify_user(self, member, message):
        try:
            await member.send(message)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
