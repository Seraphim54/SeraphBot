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
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass  # Bot lacks permissions or message already deleted
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
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=43200)  # 12 hours
        except asyncio.TimeoutError:
            await request_msg.edit(content="Request timed out after 12 hours.")
            await self._notify_user(member, "Your D&D role request timed out after 12 hours. Please request again if still needed.")
            return
        
        # Remove all reactions from admin message after decision
        try:
            await request_msg.clear_reactions()
        except (discord.Forbidden, discord.HTTPException):
            pass  # Bot may lack permissions
        
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

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def addrole(self, ctx, emoji: str, role: discord.Role, admin_approval: bool = False, *, description: str = None):
        """
        Add a new role to the rolepicker system and update the embed.
        
        Usage: !addrole <emoji> <@role> [admin_approval] [description]
        Examples:
            !addrole 🎮 @Gamer false Gaming enthusiasts
            !addrole <:custom:123456> @VIP true VIP members (requires admin approval)
        """
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        
        # Check if role already exists
        for entry in self.config['roles']:
            if entry['role_id'] == role.id:
                await ctx.send(f"❌ Role {role.mention} is already in the rolepicker!", delete_after=10)
                return
        
        # Use role name as description if not provided
        if description is None:
            description = role.name
        
        # Add new role entry
        new_entry = {
            "emoji": emoji,
            "role_id": role.id,
            "description": description,
            "admin_approval": admin_approval
        }
        self.config['roles'].append(new_entry)
        
        # Save config
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except (IOError, OSError, PermissionError) as e:
            await ctx.send(f"❌ Failed to save configuration: {e}", delete_after=10)
            return
        
        # Update the embed if it exists
        if 'message_id' in self.config and 'channel_id' in self.config:
            await self._update_rolepicker_embed(ctx)
            approval_text = " (requires admin approval)" if admin_approval else ""
            await ctx.send(f"✅ Added {emoji} {role.mention} to rolepicker{approval_text}!", delete_after=10)
        else:
            await ctx.send(f"✅ Added {emoji} {role.mention} to config. Use `!rolepicker` to post the embed.", delete_after=10)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def removerole(self, ctx, *, identifier: str):
        """
        Remove a role from the rolepicker system and update the embed.
        
        Usage: !removerole <role_mention_or_emoji>
        Examples:
            !removerole @Gamer
            !removerole 🎮
        """
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        
        # Try to find role by mention or emoji
        removed = False
        for i, entry in enumerate(self.config['roles']):
            # Check if identifier matches emoji
            if entry['emoji'] == identifier or entry['emoji'] in identifier:
                self.config['roles'].pop(i)
                removed = True
                break
            # Check if identifier is a role mention or ID
            try:
                role_id = int(identifier.strip('<@&>'))
                if entry['role_id'] == role_id:
                    self.config['roles'].pop(i)
                    removed = True
                    break
            except ValueError:
                pass
        
        if not removed:
            await ctx.send(f"❌ Could not find a role matching `{identifier}` in the rolepicker!", delete_after=10)
            return
        
        # Save config
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except (IOError, OSError, PermissionError) as e:
            await ctx.send(f"❌ Failed to save configuration: {e}", delete_after=10)
            return
        
        # Update the embed if it exists
        if 'message_id' in self.config and 'channel_id' in self.config:
            await self._update_rolepicker_embed(ctx)
            await ctx.send(f"✅ Removed role from rolepicker!", delete_after=10)
        else:
            await ctx.send(f"✅ Removed role from config.", delete_after=10)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def updaterolepicker(self, ctx):
        """
        Manually refresh the rolepicker embed with current configuration.
        Useful after editing role_reactions.json manually.
        """
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        
        if 'message_id' not in self.config or 'channel_id' not in self.config:
            await ctx.send("❌ No rolepicker message found. Use `!rolepicker` first!", delete_after=10)
            return
        
        # Reload config from file in case it was edited manually
        self.load_config()
        
        await self._update_rolepicker_embed(ctx)
        await ctx.send("✅ Rolepicker embed updated!", delete_after=10)

    async def _update_rolepicker_embed(self, ctx):
        """Update the existing rolepicker message with current config."""
        try:
            channel = self.bot.get_channel(self.config['channel_id'])
            if not channel:
                await ctx.send("❌ Rolepicker channel not found!", delete_after=10)
                return
            
            message = await channel.fetch_message(self.config['message_id'])
            if not message:
                await ctx.send("❌ Rolepicker message not found!", delete_after=10)
                return
            
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
            
            await message.edit(embed=embed)
            
            # Clear and re-add all reactions
            try:
                await message.clear_reactions()
            except (discord.Forbidden, discord.HTTPException):
                pass  # Bot may lack permissions
            
            for entry in self.config['roles']:
                try:
                    await message.add_reaction(entry['emoji'])
                except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                    # Ignore failures to add reactions (invalid emoji, missing permissions, etc.)
                    pass
        
        except (discord.NotFound, discord.HTTPException) as e:
            await ctx.send(f"❌ Failed to update rolepicker: {e}", delete_after=10)

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
