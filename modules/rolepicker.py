import discord
from discord.ext import commands
import json
import os


# RolePicker Cog: Handles role assignment via emoji reactions, including admin approval flow

class RolePicker(commands.Cog):
    def __init__(self, bot):

        # Initialize with bot instance and load config from JSON

        self.bot = bot
        self.config_path = os.path.join(os.path.dirname(__file__), '../data/role_reactions.json')
        self.config = self.load_config()

    def load_config(self):

        # Load the role/reaction configuration from JSON file

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @commands.command()
    async def rolepicker(self, ctx):

        # Command to post the role picker embed in the designated channel

        await ctx.message.delete()
        channel = self.bot.get_channel(self.config['channel_id'])
        embed = discord.Embed(
            title=self.config['embed_title'],
            description=self.config['embed_description'],
            color=discord.Color.blurple()
        )

        # Add each role/emoji as a field in the embed

        for role in self.config['roles']:
            embed.add_field(name=role['emoji'], value=role['description'], inline=False)
        msg = await channel.send(embed=embed)
        guild = ctx.guild

        # Add reactions for each role (supports custom and unicode emoji)

        for role in self.config['roles']:
            emoji_str = role['emoji']
            if emoji_str.startswith('<:') and emoji_str.endswith('>'):
                emoji_id = int(emoji_str.split(':')[2][:-1])
                emoji_obj = discord.utils.get(guild.emojis, id=emoji_id)
                if emoji_obj:
                    await msg.add_reaction(emoji_obj)
                else:
                    await msg.add_reaction(emoji_str)
            else:
                await msg.add_reaction(emoji_str)

        # Store the message ID for reaction tracking
        self.config['last_message_id'] = msg.id
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Handles all reaction adds for both role assignment and admin approval
        # First, check if this is a rolepicker embed reaction

        if payload.message_id == self.config.get('last_message_id'):
            if payload.user_id == self.bot.user.id:
                return  # Ignore bot's own reactions
            guild = self.bot.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            channel = self.bot.get_channel(self.config['channel_id'])
            user = await self.bot.fetch_user(payload.user_id)
            emoji_match = None
            # Match the emoji to a configured role
            for role in self.config['roles']:
                emoji_str = role['emoji']
                if emoji_str.startswith('<:') and emoji_str.endswith('>'):
                    emoji_id = int(emoji_str.split(':')[2][:-1])
                    if payload.emoji.id == emoji_id:
                        emoji_match = role
                        break
                else:
                    if payload.emoji.name == emoji_str:
                        emoji_match = role
                        break
            if not emoji_match:
                return
            role_obj = guild.get_role(emoji_match['role_id'])

            # Remove user's reaction after processing (keeps only bot's reaction)

            message = await channel.fetch_message(payload.message_id)
            try:
                await message.remove_reaction(payload.emoji, member)
            except Exception:
                pass

            # If admin approval is required, notify user and post to admin channel

            if emoji_match.get('admin_approval'):
                await channel.send(f"{user.mention}, your request for the '{emoji_match['description']}' role has been sent to the admins for approval.")
                try:
                    await user.send(f"Your request for the '{emoji_match['description']}' role is pending admin approval.")
                except Exception:
                    pass
                admin_channel = self.bot.get_channel(self.config['admin_channel_id'])
                admin_msg = await admin_channel.send(f"@here User {user.mention} has requested the '{emoji_match['description']}' role. React below to approve or deny. (User ID: {user.id}, Role ID: {emoji_match['role_id']})")
                await admin_msg.add_reaction("✅")
                await admin_msg.add_reaction("❌")

                # Store pending request info for tracking

                if not hasattr(self, 'pending_requests'):
                    self.pending_requests = {}
                self.pending_requests[admin_msg.id] = {
                    'user_id': user.id,
                    'role_id': emoji_match['role_id'],
                    'role_desc': emoji_match['description']
                }
                return
            
            # Toggle role assignment: remove if user already has, add if not

            if role_obj in member.roles:
                await member.remove_roles(role_obj, reason="RolePicker toggle off")
                try:
                    await user.send(f"The '{emoji_match['description']}' role has been removed from your account.")
                except Exception:
                    pass
            else:
                await member.add_roles(role_obj, reason="RolePicker reaction")
                try:
                    await user.send(f"You have been granted the '{emoji_match['description']}' role!")
                except Exception:
                    pass

        # Next, check if this is an admin approval/denial reaction in the admin channel

        if hasattr(self, 'pending_requests') and payload.channel_id == self.config.get('admin_channel_id'):
            if payload.message_id in self.pending_requests:

                # Only allow users with manage_roles to approve/deny

                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                if not member.guild_permissions.manage_roles:
                    return
                request = self.pending_requests[payload.message_id]
                user = await self.bot.fetch_user(request['user_id'])
                role_obj = guild.get_role(request['role_id'])
                channel = self.bot.get_channel(self.config['channel_id'])
                admin_channel = self.bot.get_channel(self.config['admin_channel_id'])
                admin_msg = await admin_channel.fetch_message(payload.message_id)

                # Remove all reactions to lock the message after decision

                try:
                    await admin_msg.clear_reactions()
                except Exception:
                    pass

                # Approve: assign role, DM user, announce in admin channel

                if str(payload.emoji) == '✅':
                    if role_obj:
                        member_to_edit = guild.get_member(request['user_id'])
                        if member_to_edit:
                            await member_to_edit.add_roles(role_obj, reason="Admin approved role request")
                    await admin_channel.send(f"{member.mention} approved the '{request['role_desc']}' role request for {user.mention}.")
                    try:
                        await user.send(f"Your request for the '{request['role_desc']}' role was approved by an admin.")
                    except Exception:
                        pass

                # Deny: DM user, announce in admin channel

                elif str(payload.emoji) == '❌':
                    await admin_channel.send(f"{member.mention} denied the '{request['role_desc']}' role request for {user.mention}.")
                    try:
                        await user.send(f"Your request for the '{request['role_desc']}' role was denied by an admin.")
                    except Exception:
                        pass

                # Remove from pending requests

                del self.pending_requests[payload.message_id]
                role_obj = guild.get_role(request['role_id'])
                channel = self.bot.get_channel(self.config['channel_id'])
                admin_channel = self.bot.get_channel(self.config['admin_channel_id'])
                admin_msg = await admin_channel.fetch_message(payload.message_id)

                # Remove all reactions to lock the message

                try:
                    await admin_msg.clear_reactions()
                except Exception:
                    pass
                # Approve
                if str(payload.emoji) == '✅':
                    if role_obj:
                        member_to_edit = guild.get_member(request['user_id'])
                        if member_to_edit:
                            await member_to_edit.add_roles(role_obj, reason="Admin approved role request")
                    await admin_channel.send(f"{member.mention} approved the '{request['role_desc']}' role request for {user.mention}.")
                    try:
                        await user.send(f"Your request for the '{request['role_desc']}' role was approved by an admin.")
                    except Exception:
                        pass
                # Deny
                elif str(payload.emoji) == '❌':
                    await admin_channel.send(f"{member.mention} denied the '{request['role_desc']}' role request for {user.mention}.")
                    try:
                        await user.send(f"Your request for the '{request['role_desc']}' role was denied by an admin.")
                    except Exception:
                        pass

                # Remove from pending

                del self.pending_requests[payload.message_id]

        # Toggle role assignment

        if role_obj in member.roles:
            await member.remove_roles(role_obj, reason="RolePicker toggle off")
            try:
                await user.send(f"The '{emoji_match['description']}' role has been removed from your account.")
            except Exception:
                pass
        else:
            await member.add_roles(role_obj, reason="RolePicker reaction")
            try:
                await user.send(f"You have been granted the '{emoji_match['description']}' role!")
            except Exception:
                pass

async def setup(bot):
    await bot.add_cog(RolePicker(bot))
