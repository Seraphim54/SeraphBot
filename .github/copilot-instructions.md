# SeraphBot - AI Agent Instructions

## Project Overview
SeraphBot is a Discord bot built with discord.py focused on D&D/TTRPG utility commands and modular event announcements. It's a single-file bot ([bot.py](../bot.py)) with JSON-driven event management.

## Architecture

### Core Structure
- **Main File**: [bot.py](../bot.py) - All bot logic in one file (185 lines)
- **Data Storage**: `data/*.json` - Event announcement definitions
- **Archives**: `archives/legacy_comands.archive` - Retired command implementations for reference
- **Environment**: `.env` contains `bot_token` (loaded via python-dotenv)

### Key Components
1. **Static Data** (lines 20-28): D&D reference lists (alignments, races, classes, Discord colors)
2. **Helper Functions** (lines 35-41): `mention_user()`, `msgdel()`, `get_random_color()`
3. **Simple Commands** (lines 53-98): Fun/utility commands
4. **D&D Utilities** (lines 100-122): `!newstats`, `!deathsave`, `!random_build`
5. **Modular Event Loader** (lines 135-180): JSON-driven embed announcements

## Critical Patterns

### JSON Event System
The `!event <name>` command loads structured announcements from `data/{name}.json`:

```json
{
  "title": "Event Title",
  "description": "Event details",
  "color": "brand_red",           // Must match discord.Color attribute names
  "image_url": "https://...",
  "footer": "Footer text",
  "channel_id": 1234567890,       // Optional: target channel
  "role_id": 1234567890,          // Optional: role to ping
  "reactions": ["✅", "❌"]       // Auto-added reactions
}
```

**Color handling**: Colors must be valid `discord.Color` attributes (e.g., `brand_red`, `dark_purple`). If invalid/missing, falls back to `get_random_color()`.

### Command Patterns
- **Context deletion**: Use `await msgdel(ctx)` to remove user's command message (cleaner channels)
- **User mentions**: Use `mention_user(ctx)` helper for consistent @mentions
- **Stat rolling**: D&D stat generation uses 4d6-drop-lowest with minimum 72 total, tracking attempts

### Discord.py Conventions
- Bot prefix: `!` (hardcoded)
- Intents: `discord.Intents.all()` required for full functionality
- Commands use `@bot.command()` decorator pattern
- Event handlers use `@bot.event` (currently only `on_ready`)

## Development Workflow

### Running the Bot
```powershell
# From project root with .venv activated
python bot.py
```

**Requirements**: discord.py, python-dotenv (see `.venv/` for environment)

### Adding New Commands
1. Use `@bot.command()` decorator before async function
2. First parameter must be `ctx` (Context object)
3. Follow naming: lowercase, snake_case for multi-word
4. Add `await msgdel(ctx)` if command should be hidden
5. Use helpers: `mention_user(ctx)`, `get_random_color()`

### Adding Events
1. Create `data/<event-name>.json` following template in [modular_event_template.json](../data/modular_event_template.json)
2. Trigger with `!event <event-name>`
3. See [session01.json](../data/session01.json) for real example

### Archiving Commands
Move deprecated commands to `archives/legacy_commands.archive` (note: intentional typo in filename). See archived `!glimmerfen_event` and `!embed` for evolution of event system.

## Project-Specific Conventions
- **Single-file philosophy**: All bot code in one file for simplicity
- **Data-driven events**: Prefer JSON configs over hardcoded embeds (lesson from archived commands)
- **Fun factor**: Emoji-heavy responses, personality in error messages
- **D&D focus**: Commands designed for tabletop gaming Discord servers

## External Dependencies
- **Discord.py**: Bot framework, requires valid bot token in `.env`
- **Discord API**: Channel/role IDs are Discord snowflakes (18-19 digit integers)
- No database: All state is ephemeral or JSON-file based
