from discord.ext import commands
import discord
import asyncio
from datetime import datetime, timedelta, timezone
import json
import os

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config_path = os.path.join(os.path.dirname(__file__), '../data/help_config.json')
        self.load_config()

    def load_config(self):
        """Load help configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.permissions = config.get('permissions', {})
                self.settings = config.get('settings', {})
                self.commands_db = config.get('commands', {})
                self.timeout_duration = self.settings.get('timeout_duration', 300)
        except FileNotFoundError:
            print(f"Error: Help config file not found at {self.config_path}")
            # Fallback to minimal config
            self.permissions = {"minimum_role_id": None, "admin_role_ids": [], "admin_user_ids": []}
            self.settings = {"timeout_duration": 300, "dm_only": True}
            self.commands_db = {}
        except json.JSONDecodeError:
            print(f"Error: Help config JSON is invalid")
            self.permissions = {"minimum_role_id": None, "admin_role_ids": [], "admin_user_ids": []}
            self.settings = {"timeout_duration": 300, "dm_only": True}
            self.commands_db = {}

    def check_minimum_role(self, member):
        """Check if user has minimum required role."""
        minimum_role_id = self.permissions.get('minimum_role_id')
        if not minimum_role_id:
            return True  # No minimum role requirement
        
        if not member.guild:
            return False  # Must be in a guild to check roles
        
        # Check if user has the minimum role
        for role in member.roles:
            if role.id == minimum_role_id:
                return True
        return False

    def check_admin_permissions(self, member):
        """Check if user has admin permissions based on JSON config."""
        # Check if user is bot owner
        if member.id == self.bot.owner_id:
            return True
        
        # Check if user has administrator permission
        if member.guild and member.guild_permissions.administrator:
            return True
        
        # Check if user ID is in admin list
        if member.id in self.permissions.get('admin_user_ids', []):
            return True
        
        # Check if user has any of the admin roles
        admin_role_ids = self.permissions.get('admin_role_ids', [])
        if member.guild:
            for role in member.roles:
                if role.id in admin_role_ids:
                    return True
        
        return False

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Interactive help system with DM-based menu navigation."""
        # Delete the user's command message
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        
        # Reload config on each invocation to get latest changes
        self.load_config()
        
        # Check if user has minimum required role
        if not self.check_minimum_role(ctx.author):
            minimum_role_name = self.permissions.get('minimum_role_name', 'member')
            await ctx.send(
                f"{ctx.author.mention}, you need the `{minimum_role_name}` role to use bot commands!",
                delete_after=10
            )
            return
        
        # Check if user is admin
        is_admin = self.check_admin_permissions(ctx.author)
        
        # Send confirmation in channel
        confirmation = await ctx.send(f"{ctx.author.mention}, check your DMs for help! 📬")
        
        # Try to start DM conversation
        try:
            await ctx.author.send("🤖 **SeraphBot Help System Activated!**")
            await asyncio.sleep(0.5)  # Brief pause for effect
            
            # Start the help loop
            await self._help_loop(ctx.author, is_admin)
            
        except discord.Forbidden:
            # User has DMs disabled
            await confirmation.edit(content=f"{ctx.author.mention}, I couldn't DM you! Please enable DMs from server members and try again.")
        except Exception as e:
            print(f"Error in help command: {e}")
            await confirmation.edit(content=f"{ctx.author.mention}, an error occurred. Please try again later.")
        
        # Clean up confirmation message after a delay
        await asyncio.sleep(10)
        try:
            await confirmation.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def _help_loop(self, user, is_admin):
        """Main loop for the interactive help system."""
        while True:
            # Show command menu
            response = await self._show_menu(user, is_admin)
            
            if response is None:
                # Timeout occurred
                await user.send("⏰ **Help session timed out.** Use `!help` again if you need assistance!")
                return
            
            if response.lower() in ['exit', 'quit', 'cancel']:
                await user.send("👋 **May your adventures be legendary!** Use `!help` anytime you need assistance.")
                return
            
            # Try to parse the command number
            try:
                choice = int(response)
                if 1 <= choice <= len(self._get_available_commands(is_admin)):
                    # Show command details
                    continue_help = await self._show_command_details(user, choice, is_admin)
                    
                    if continue_help is None:
                        # Timeout
                        await user.send("⏰ **Help session timed out.** Use `!help` again if you need assistance!")
                        return
                    elif not continue_help:
                        # User chose to exit
                        await user.send("👋 **May your adventures be legendary!** Use `!help` anytime you need assistance.")
                        return
                    # Otherwise, loop continues to show menu again
                else:
                    await user.send(f"❌ Invalid choice! Please enter a number between 1 and {len(self._get_available_commands(is_admin))}.")
            except ValueError:
                await user.send("❌ Invalid input! Please enter a number from the menu.")

    async def _show_menu(self, user, is_admin):
        """Show the command menu and wait for user response."""
        available_commands = self._get_available_commands(is_admin)
        
        # Calculate expiration time (use timezone-aware datetime)
        expiration_time = datetime.now(timezone.utc) + timedelta(seconds=self.timeout_duration)
        expiration_timestamp = int(expiration_time.timestamp())
        
        # Build menu embed
        embed = discord.Embed(
            title="📚 Available Commands",
            description="Select a command by typing its number to learn more.\nType `exit` to end this session.",
            color=discord.Color.blue()
        )
        
        # Group commands by category
        categories = {}
        for idx, (cmd_name, cmd_info) in enumerate(available_commands, 1):
            category = cmd_info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(f"`{idx}.` **!{cmd_name}**")
        
        # Add fields for each category
        for category, commands in categories.items():
            embed.add_field(
                name=f"__{category}__",
                value="\n".join(commands),
                inline=False
            )
        
        # Add timeout info
        timeout_minutes = self.timeout_duration // 60
        embed.set_footer(text=f"⏰ This session expires in {timeout_minutes} minutes")
        
        await user.send(embed=embed)
        # Send timestamp as separate message (timestamps don't render in embed footers)
        await user.send(f"*Session closes <t:{expiration_timestamp}:R>*")
        
        # Wait for response
        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)
        
        try:
            message = await self.bot.wait_for('message', check=check, timeout=self.timeout_duration)
            return message.content.strip()
        except asyncio.TimeoutError:
            return None

    async def _show_command_details(self, user, choice, is_admin):
        """Show details for a specific command and ask if user wants more help."""
        available_commands = self._get_available_commands(is_admin)
        cmd_name, cmd_info = available_commands[choice - 1]
        
        # Build command details embed
        embed = discord.Embed(
            title=f"ℹ️ Command: !{cmd_name}",
            description=cmd_info['description'],
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Usage",
            value=f"`{cmd_info['usage']}`",
            inline=False
        )
        
        embed.add_field(
            name="Example",
            value=f"```\n{cmd_info['example']}\n```",
            inline=False
        )
        
        if cmd_info.get('requires_admin', False):
            embed.add_field(
                name="⚠️ Permission Required",
                value="Administrator",
                inline=False
            )
        
        await user.send(embed=embed)
        
        # Ask if they want more help
        await asyncio.sleep(0.5)
        timeout_minutes = self.timeout_duration // 60
        await user.send(f"**Would you like help with another command?**\nReply with `yes` to continue or `no` to end this session.\n\n⏰ *You have {timeout_minutes} minutes to respond.*")
        
        # Wait for yes/no response
        def check(m):
            return m.author == user and isinstance(m.channel, discord.DMChannel)
        
        try:
            message = await self.bot.wait_for('message', check=check, timeout=self.timeout_duration)
            response = message.content.strip().lower()
            
            if response in ['yes', 'y', 'yeah', 'yep', 'sure']:
                return True  # Continue help loop
            elif response in ['no', 'n', 'nope', 'nah']:
                return False  # Exit help loop
            else:
                await user.send("I'll take that as a 'yes'! Let's continue...")
                return True
        except asyncio.TimeoutError:
            return None  # Timeout

    def _get_available_commands(self, is_admin):
        """Get list of commands available to the user based on their permissions."""
        available = []
        for cmd_name, cmd_info in self.commands_db.items():
            # Show all commands to admins, only non-admin commands to regular users
            if is_admin or not cmd_info.get('requires_admin', False):
                available.append((cmd_name, cmd_info))
        
        # Sort by category, then by command name
        available.sort(key=lambda x: (x[1]['category'], x[0]))
        return available

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def reloadhelp(self, ctx):
        """Reload the help configuration from JSON file (admin only)."""
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException, discord.NotFound):
            pass
        
        try:
            # Reload the cog itself
            await self.bot.reload_extension("modules.help")
            await ctx.send("✅ Help cog and configuration reloaded!", delete_after=5)
        except Exception as e:
            await ctx.send(f"❌ Failed to reload help: {e}", delete_after=10)


async def setup(bot):
    await bot.add_cog(Help(bot))
