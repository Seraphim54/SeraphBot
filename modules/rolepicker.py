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
            await msg.add_reaction(entry['emoji'])

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
        
        # Get admin approval configuration
        approval_config = self.config.get('admin_approval', {})
        request_name = approval_config.get('request_name', 'role access')
        pending_msg = approval_config.get('pending_message', 'Your request is pending administrator approval.')
        approval_prompt = approval_config.get('approval_prompt', 'React below to approve or deny.')
        deny_emoji = approval_config.get('deny_emoji', '❌')
        denied_msg = approval_config.get('denied_message', 'Your request was denied by an admin.')
        approval_options = approval_config.get('approval_options', [])
        
        # Send DM to user that request is pending
        await self._notify_user(member, pending_msg.format(request_name=request_name))
        
        # Send admin channel message
        embed = discord.Embed(
            title="Role Approval Needed",
            description=f"User: {member.mention}\nRequest: {request_name}\n{approval_prompt}",
            color=discord.Color.gold()
        )
        request_msg = await admin_channel.send(embed=embed)
        
        # Add reactions for all approval options plus deny
        for option in approval_options:
            await request_msg.add_reaction(option['emoji'])
        await request_msg.add_reaction(deny_emoji)
        
        # Build check function dynamically based on configured emojis
        def check(reaction, user):
            if reaction.message.id != request_msg.id or not user.guild_permissions.administrator:
                return False
            
            # Check deny emoji
            if str(reaction.emoji) == deny_emoji:
                return True
            
            # Check approval option emojis
            for option in approval_options:
                option_emoji = option['emoji']
                # Custom emoji: <a:name:id> or <:name:id>
                if option_emoji.startswith('<:') or option_emoji.startswith('<a:'):
                    try:
                        option_id = int(option_emoji.split(':')[2][:-1])
                        if hasattr(reaction.emoji, 'id') and reaction.emoji.id == option_id:
                            return True
                    except Exception:
                        continue
                else:
                    # Unicode emoji
                    if str(reaction.emoji) == option_emoji:
                        return True
            
            return False
        
        reaction, user = await self.bot.wait_for('reaction_add', check=check)
        
        # Remove all reactions from admin message after decision
        await request_msg.clear_reactions()
        
        # Check if denied
        if str(reaction.emoji) == deny_emoji:
            await request_msg.edit(content="Request denied.")
            await self._notify_user(member, denied_msg.format(request_name=request_name))
            return
        
        # Find which approval option was selected
        for option in approval_options:
            option_emoji = option['emoji']
            is_match = False
            
            # Custom emoji: <a:name:id> or <:name:id>
            if option_emoji.startswith('<:') or option_emoji.startswith('<a:'):
                try:
                    option_id = int(option_emoji.split(':')[2][:-1])
                    if hasattr(reaction.emoji, 'id') and reaction.emoji.id == option_id:
                        is_match = True
                except Exception:
                    continue
            else:
                # Unicode emoji
                if str(reaction.emoji) == option_emoji:
                    is_match = True
            
            if is_match:
                role = member.guild.get_role(option['role_id'])
                if role:
                    await member.add_roles(role, reason=f"Admin approved {option['label']}")
                    approved_msg = option.get('approved_message', 'Your request was approved!')
                    await self._notify_user(member, approved_msg.format(label=option['label'], request_name=request_name))
                    admin_confirm = option.get('admin_confirmation', 'Request approved.')
                    await request_msg.edit(content=admin_confirm.format(label=option['label']))
                break

    async def _notify_user(self, member, message):
        try:
            await member.send(message)
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
