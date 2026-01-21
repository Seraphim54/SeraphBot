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
            async with self._reactions_lock:
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

    def _emoji_matches(self, emoji_str, reaction_emoji):
        """
        Helper method to check if a configured emoji string matches a Discord reaction emoji.
        
        Args:
            emoji_str: The emoji string from configuration (e.g., "<:name:id>" or "❌")
            reaction_emoji: The Discord reaction emoji object
            
        Returns:
            bool: True if the emojis match, False otherwise
        """
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
        # 'add' is reserved for future differentiation between add/remove approvals.
        # Referencing it here avoids unused-parameter warnings without changing behavior.
        _ = add
        admin_channel_id = self.config.get('admin_channel_id')
        if not admin_channel_id:
            return
        admin_channel = self.bot.get_channel(admin_channel_id)
        
        # Check if admin channel is accessible
        if not admin_channel:
            print(f"Warning: Admin channel {admin_channel_id} not found or inaccessible")
            await self._notify_user(member, "Your request could not be processed. Please contact an administrator.")
            return
        
        # Get admin approval configuration
        approval_config = self.config.get('admin_approval', {})
        request_name = approval_config.get('request_name', 'role access')
        pending_msg = approval_config.get('pending_message', 'Your request is pending administrator approval.')
        approval_prompt = approval_config.get('approval_prompt', 'React below to approve or deny.')
        deny_emoji = approval_config.get('deny_emoji', '❌')
        denied_msg = approval_config.get('denied_message', 'Your request was denied by an admin.')
        approval_options = approval_config.get('approval_options', [])
        
        # Send DM to user that request is pending (with safe formatting)
        try:
            formatted_pending_msg = pending_msg.format(request_name=request_name)
        except (KeyError, ValueError):
            formatted_pending_msg = f"Your request for {request_name} is pending administrator approval."
        await self._notify_user(member, formatted_pending_msg)
        
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
            description=f"User: {member.mention}\nRequest: {request_name}\n{approval_prompt}",
            color=discord.Color.gold()
        )
        request_msg = await admin_channel.send(embed=embed)
        
        # Add reactions for all approval options plus deny (with error handling)
        for option in approval_options:
            try:
                await request_msg.add_reaction(option['emoji'])
            except (discord.HTTPException, discord.NotFound, discord.Forbidden) as e:
                print(f"Warning: Failed to add reaction {option['emoji']}: {e}")
        
        try:
            await request_msg.add_reaction(deny_emoji)
        except (discord.HTTPException, discord.NotFound, discord.Forbidden) as e:
            print(f"Warning: Failed to add deny reaction {deny_emoji}: {e}")
        
        # Build check function dynamically based on configured emojis
        def check(reaction, user):
            if reaction.message.id != request_msg.id or not user.guild_permissions.administrator:
                return False
            
            # Check deny emoji using helper method
            if self._emoji_matches(deny_emoji, reaction.emoji):
                return True
            
            # Check approval option emojis using helper method
            for option in approval_options:
                if self._emoji_matches(option['emoji'], reaction.emoji):
                    return True
            
            return False
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', check=check, timeout=3600.0)
        except asyncio.TimeoutError:
            # No admin responded within the timeout period (1 hour)
            await request_msg.edit(content="Request timed out - no admin response.")
            await self._notify_user(member, "Your request timed out. Please contact an administrator.")
            return
        
        # Remove all reactions from admin message after decision
        try:
            await request_msg.clear_reactions()
        except (discord.Forbidden, discord.HTTPException) as e:
            # Bot may lack 'Manage Messages' permission - log but continue
            print(f"Warning: Failed to clear reactions from approval message: {e}")
        
        # Check if denied
        if self._emoji_matches(deny_emoji, reaction.emoji):
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
            try:
                formatted_denied_msg = denied_msg.format(request_name=request_name)
            except (KeyError, ValueError):
                formatted_denied_msg = f"Your {request_name} request was denied by an admin."
            await self._notify_user(member, formatted_denied_msg)
            return
        
        # Find which approval option was selected and assign role
        for option in approval_options:
            if self._emoji_matches(option['emoji'], reaction.emoji):
                role = member.guild.get_role(option['role_id'])
                if not role:
                    # Role doesn't exist - notify user and admin
                    error_msg = f"Error: Role {option['role_id']} not found in server."
                    await request_msg.edit(content=error_msg)
                    await self._notify_user(member, "Your request could not be completed. Please contact an administrator.")
                    print(f"Error: Role ID {option['role_id']} not found for approval option '{option['label']}'")
                    return
                
                try:
                    await member.add_roles(role, reason=f"Admin approved {option['label']}")
                    
                    # Format and send approval messages
                    try:
                        approved_msg = option.get('approved_message', 'Your request was approved!')
                        formatted_approved_msg = approved_msg.format(label=option['label'], request_name=request_name)
                    except (KeyError, ValueError):
                        formatted_approved_msg = f"Your request for {option['label']} was approved!"
                    
                    await self._notify_user(member, formatted_approved_msg)
                    
                    try:
                        admin_confirm = option.get('admin_confirmation', 'Request approved.')
                        formatted_admin_confirm = admin_confirm.format(label=option['label'])
                    except (KeyError, ValueError):
                        formatted_admin_confirm = f"Request approved as {option['label']}."
                    
                    await request_msg.edit(content=formatted_admin_confirm)
                except discord.Forbidden:
                    # Bot lacks permissions to assign the role
                    error_msg = f"Error: Missing permissions to assign role {role.name}."
                    await request_msg.edit(content=error_msg)
                    await self._notify_user(member, "Your request could not be completed due to permission issues. Please contact an administrator.")
                    print(f"Error: Missing permissions to assign role {role.name} (ID: {role.id})")
                except discord.HTTPException as e:
                    # General Discord API error
                    error_msg = f"Error: Failed to assign role - {str(e)}"
                    await request_msg.edit(content=error_msg)
                    await self._notify_user(member, "Your request could not be completed. Please contact an administrator.")
                    print(f"Error: Failed to assign role {role.name} (ID: {role.id}): {e}")
                
                break

    async def _notify_user(self, member, message):
        try:
            await member.send(message)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
