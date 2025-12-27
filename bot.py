import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Load all cogs from middleman folder
    try:
        await bot.load_extension('middleman.tickets')
        print('Loaded tickets extension')
    except Exception as e:
        print(f'Failed to load extension: {e}')
    
    # Sync commands only if SYNC_COMMANDS environment variable is set
    if os.getenv('SYNC_COMMANDS', '').lower() == 'true':
        try:
            synced = await bot.tree.sync()
            print(f'Synced {len(synced)} command(s)')
        except Exception as e:
            print(f'Failed to sync commands: {e}')
    else:
        print('Skipping command sync (set SYNC_COMMANDS=true to enable)')

@bot.command(name='ping')
async def ping(ctx):
    """Check if bot is responsive"""
    await ctx.send(f'Pong! Latency: {round(bot.latency * 1000)}ms')

@bot.command(name='setup_ticket')
@commands.has_permissions(administrator=True)
async def setup_ticket(ctx):
    """Setup the ticket panel (Admin only)"""
    cog = bot.get_cog('Tickets')
    if cog:
        await cog.setup_ticket_panel(ctx)
    else:
        await ctx.send('Tickets cog not loaded!')

# Run the bot
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print('Error: DISCORD_TOKEN not found in environment variables')
    else:
        bot.run(token)
