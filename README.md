# Discord Middleman Bot

A Python-based Discord bot for managing middleman services with a ticket system for secure trades.

## Features

- **Ticket System**: Users can request middleman assistance through an interactive button
- **Automated Ticket Creation**: Creates private channels for each user request
- **Role Notifications**: Automatically pings designated middleman roles
- **Command Prefix**: Uses `$` as the command prefix

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Copy `.env.example` to `.env`
   - Add your Discord bot token to `.env`:
     ```
     DISCORD_TOKEN=your_bot_token_here
     ```

3. **Run the Bot**
   ```bash
   python bot.py
   ```

## Commands

### Admin Commands
- `$setup_ticket` - Setup the ticket panel with Request MM button (Admin only)

### User Commands
- `$ping` - Check if bot is responsive
- `$close` - Close the current ticket (use in ticket channels)

## How It Works

1. Admin sets up the ticket panel using `$setup_ticket`
2. Users click the "Request MM" button on the ticket panel
3. Bot creates a private ticket channel named `request-mm-[username]`
4. Bot pings the configured middleman roles
5. Bot sends a welcome message in the ticket
6. Middlemen can assist the user in the ticket channel
7. When done, use `$close` to close and delete the ticket

## Configuration

The bot is configured with:
- Ticket Category ID: `1442410056019742750`
- Middleman Role IDs: `1442993726057087089`, `1446603033445142559`

These can be modified in `middleman/tickets.py` if needed.

## Project Structure

```
discord-middleman-bot/
├── bot.py                      # Main bot entry point
├── middleman/
│   ├── __init__.py            # Package initializer
│   └── tickets.py             # Ticket system implementation
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore file
└── README.md                 # This file
```