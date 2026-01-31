# SeraphBot
A Discord bot built with discord.py, focused on D&D/TTRPG utilities and modular event management.

## Features
- 🎲 D&D dice rolling and character generation
- 🎭 Dynamic role picker with reaction-based assignment
- 📢 JSON-driven event announcements
- 🎮 Fun commands and utilities
- 🛡️ Admin approval system for restricted roles

## Setup

### Requirements
- Python 3.8+
- discord.py
- python-dotenv

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your bot token:
   ```
   bot_token=YOUR_BOT_TOKEN_HERE
   ```
4. Run the bot: `python bot.py`

## Commands

### 🎲 Rolls (D&D Utilities)
Commands for tabletop gaming.

- **`!deathsave`** - Roll a death saving throw
  - Rolls 1d20 with special outcomes for crits
  - Example: `!deathsave`

- **`!newstats`** - Generate D&D ability scores
  - Uses 4d6 drop lowest method
  - Guarantees minimum 72 total
  - Example: `!newstats`

- **`!random_build`** - Generate a random character concept
  - Provides random alignment, race, and class
  - Example: `!random_build`

### 🎮 Fun Commands
Lighthearted commands for entertainment.

- **`!hello`** - Get a friendly greeting
- **`!dave`** - HAL 9000 reference
- **`!mmn`** - Inside joke command
- **`!bnuuy`** - Random bunny GIF
- **`!mothman`** - Special Mothman GIF

### 🎭 Role Picker
Dynamic role management with reaction-based assignment.

#### User Commands
- **`!rolepicker`** - Post the role picker embed
  - Creates an interactive embed with role reactions
  - Users react to toggle roles on/off
  - Example: `!rolepicker`

#### Admin Commands (Requires Administrator Permission)
- **`!addrole <emoji> <@role> [admin_approval] [description]`** - Add a new role dynamically
  - `emoji`: The emoji to use (Unicode or custom)
  - `@role`: The role to assign (mention it)
  - `admin_approval`: `true` or `false` (default: false)
  - `description`: Optional description (defaults to role name)
  - Automatically updates the existing embed
  - Examples:
    - `!addrole 🎮 @Gamer false Gaming enthusiasts`
    - `!addrole <:DnD:123456> @D&D true D&D players`

- **`!removerole <role_mention_or_emoji>`** - Remove a role from the picker
  - Can use role mention or emoji to identify
  - Updates the embed automatically
  - Examples:
    - `!removerole @Gamer`
    - `!removerole 🎮`

- **`!updaterolepicker`** - Manually refresh the embed
  - Reloads config from JSON file
  - Useful after manual JSON edits
  - Example: `!updaterolepicker`

#### Configuration
Role picker settings are stored in `data/role_reactions.json`:
```json
{
  "embed_title": "Choose a reaction below to get a role!",
  "color": "brand_red",
  "embed_image": "https://...",
  "embed_footer": "Optional footer text",
  "admin_channel_id": 123456789,
  "roles": [
    {
      "emoji": "🎮",
      "role_id": 123456789,
      "description": "Gamer role",
      "admin_approval": false
    }
  ]
}
```

**Admin Approval System**: Roles marked with `"admin_approval": true` will trigger an approval workflow where admins can approve/deny requests in a designated admin channel.

### 📢 Events
JSON-driven event announcements with embeds.

- **`!event <name>`** - Post an event announcement
  - Loads configuration from `data/<name>.json`
  - Supports custom embeds with images, colors, and reactions
  - Can ping specific roles and post to specific channels
  - Example: `!event session01`

#### Event Configuration
Create a JSON file in `data/` folder (see `data/modular_event_template.json`):
```json
{
  "title": "Event Title",
  "description": "Event description",
  "color": "brand_red",
  "image_url": "https://...",
  "footer": "Footer text",
  "channel_id": 123456789,
  "role_id": 123456789,
  "reactions": ["✅", "❌", "🤔"]
}
```

**Available Colors**: Any valid `discord.Color` attribute (e.g., `brand_red`, `dark_purple`, `gold`, `blurple`)

### 🛡️ Admin Commands
Bot management commands.

- **`!shutdown`** - Gracefully shut down the bot
  - Requires bot owner permission
  - Example: `!shutdown`

## Architecture

### Project Structure
```
bot.py                    # Main bot file
modules/
  ├── fun.py              # Fun commands cog
  ├── rolls.py            # D&D rolling utilities cog
  ├── rolepicker.py       # Dynamic role picker cog
  ├── events.py           # Event announcement cog
  ├── admin.py            # Admin commands cog
  └── utils.py            # Shared utilities
data/
  ├── role_reactions.json # Role picker configuration
  └── *.json              # Event announcement files
archives/
  └── legacy_commands.archive  # Deprecated command reference
```

### Design Philosophy
- **Modular cogs**: Each feature is a separate cog for easy maintenance
- **Data-driven**: Events and roles use JSON for easy customization
- **Single bot file**: Core logic centralized in `bot.py` for simplicity
- **Fun-first**: Personality in responses, emoji-heavy, TTRPG focused

## Contributing
This is a personal learning project, but suggestions are welcome!

## License
This project is for personal use and learning purposes.
