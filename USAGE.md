# Ticket System Usage Guide

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Bot Token**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token and configuration:
     ```
     token=your_bot_token_here
     TICKET_CATEGORY_ID=1442410056019742750
     MM_ROLE_ID_1=1442993726057087089
     MM_ROLE_ID_2=1446603033445142559
     ```

3. **Run the Bot**
   ```bash
   python bot.py
   ```

4. **Setup Ticket Panel**
   - In your Discord server, run: `$setup_ticket` or `$mmpanel`
   - This creates an embed with the "Request MM" button

## User Flow

1. User clicks "Request MM" button
2. Bot creates private channel: `request-mm-[username]`
3. Bot pings roles: <@&1442993726057087089> <@&1446603033445142559>
4. Bot sends welcome message: "Welcome [username] to Eli's MM and Gambling! A middleman will be with you very shortly."
5. Middleman assists user in the ticket
6. When complete, use `$close` to delete the ticket

## Features

- ✅ Persistent button (survives bot restarts)
- ✅ Private ticket channels
- ✅ Automatic role pings
- ✅ Welcome embed for each ticket
- ✅ Tickets created in category [1442410056019742750]
- ✅ Prevents duplicate tickets per user
- ✅ Clean ticket closure with `$close` command

## Bot Permissions Required

- Manage Channels
- Send Messages
- Embed Links
- Manage Roles (for channel permissions)
- Mention Everyone (to ping roles)
