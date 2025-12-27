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

@bot.command(name='assist')
async def assist(ctx):
    """Display all available commands"""
    embed = discord.Embed(
        title="📋 Bot Commands",
        description="Here are all available commands for Eli's MM and Gambling bot:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="👑 Admin Commands",
        value=(
            "`$mmpanel` - Deploy the middleman ticket panel\n"
            "`$mmban [user]` - Ban a user from using MM services\n"
            "`$assist` - Show this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="👤 User Commands",
        value=(
            "`$ping` - Check bot responsiveness\n"
            "`$close` - Close current ticket (ticket channels only)\n"
            "**Request MM Button** - Click to create a ticket"
        ),
        inline=False
    )
    
    embed.set_footer(text="Use $ prefix for all commands")
    await ctx.send(embed=embed)

# -----------------------------
# RUN BOT
# -----------------------------
if __name__ == '__main__':
    # Get bot token from environment variable or use placeholder
    bot_token = os.getenv("token", "token")
    if bot_token == "token":
        print("⚠️ WARNING: Using placeholder bot token. Set token environment variable.")
    bot.run(bot_token)
