# Admin Approval Configuration

This document explains how to configure the admin approval system for the RolePicker module.

## Overview

The admin approval system allows administrators to review and approve role requests before assigning roles to users. All hardcoded values have been removed and moved to the JSON configuration file, making the system reusable across different servers and role types.

## Configuration Structure

The admin approval configuration is defined in the `admin_approval` section of your `role_reactions.json` file:

```json
{
  "admin_approval": {
    "request_name": "D&D access",
    "pending_message": "Your request for {request_name} is pending administrator approval.",
    "approval_prompt": "React below to approve as Player, Spectator, or Deny.",
    "deny_emoji": "❌",
    "denied_message": "Your {request_name} request was denied by an admin.",
    "approval_options": [
      {
        "emoji": "<:DnD:858802171193327616>",
        "role_id": 957848615173378108,
        "label": "D&D Player",
        "approved_message": "Your request for {label} was approved!",
        "admin_confirmation": "Request approved as {label}."
      }
    ]
  }
}
```

## Configuration Fields

### Top-Level Fields

- **`request_name`**: The name of what the user is requesting (e.g., "D&D access", "VIP access")
- **`pending_message`**: Message sent to user when their request is pending. Supports `{request_name}` placeholder.
- **`approval_prompt`**: Text shown to admins explaining how to approve/deny requests
- **`deny_emoji`**: The emoji admins react with to deny a request (default: ❌)
- **`denied_message`**: Message sent to user when request is denied. Supports `{request_name}` placeholder.
- **`approval_options`**: Array of approval options (different roles that can be assigned)

### Approval Option Fields

Each approval option in the `approval_options` array has:

- **`emoji`**: The emoji admins react with to approve this option (can be custom or unicode)
- **`role_id`**: The Discord role ID to assign when this option is selected
- **`label`**: Human-readable name for this option (e.g., "D&D Player", "Spectator")
- **`approved_message`**: Message sent to user when approved. Supports `{label}` and `{request_name}` placeholders.
- **`admin_confirmation`**: Message shown in admin channel after approval. Supports `{label}` placeholder.

## Message Placeholders

Messages support the following placeholders:

- `{request_name}`: Replaced with the value from `request_name` field
- `{label}`: Replaced with the label of the selected approval option

## Examples

### Example 1: D&D Server with Player and Spectator Roles

See `data/role_reactions_dnd_example.json` for a complete example using the original D&D server configuration.

### Example 2: Gaming Community with Multiple Game Access

```json
{
  "admin_approval": {
    "request_name": "game access",
    "pending_message": "Your request for {request_name} is pending review.",
    "approval_prompt": "Select the game to grant access to, or deny.",
    "deny_emoji": "🚫",
    "denied_message": "Your {request_name} request was not approved.",
    "approval_options": [
      {
        "emoji": "🎮",
        "role_id": 111111111111111111,
        "label": "Minecraft Player",
        "approved_message": "You now have access to {label}!",
        "admin_confirmation": "Granted {label} access."
      },
      {
        "emoji": "⚔️",
        "role_id": 222222222222222222,
        "label": "Valheim Player",
        "approved_message": "You now have access to {label}!",
        "admin_confirmation": "Granted {label} access."
      }
    ]
  }
}
```

## Migration from Hardcoded Values

If you were using the previous version with hardcoded values, here's how to migrate:

1. The hardcoded player role ID (957848615173378108) → now in `approval_options[0].role_id`
2. The hardcoded spectator role ID (809223517949919272) → now in `approval_options[1].role_id`
3. The hardcoded player emoji (<:DnD:858802171193327616>) → now in `approval_options[0].emoji`
4. The hardcoded spectator emoji (<:dndspec:1462113193051553799>) → now in `approval_options[1].emoji`
5. All hardcoded text ("D&D access", etc.) → now configurable in the respective message fields

## Notes

- If the `admin_approval` section is missing, the system will use safe defaults
- Custom emojis must be in the format `<:name:id>` or `<a:name:id>` for animated emojis
- Unicode emojis can be used directly (e.g., "❌", "✅")
- You can add as many approval options as you need
- All placeholders are optional; messages without placeholders will work as-is
