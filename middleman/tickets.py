import discord
from discord.ext import commands
from discord.ui import Button, View
from discord import app_commands
import asyncio
import os
import re

class TicketButton(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Request MM', style=discord.ButtonStyle.primary, custom_id='request_mm_button')
    async def request_mm(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle ticket creation when button is clicked"""
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        user = interaction.user
        
        # Get the ticket category from environment or use default
        ticket_category_id = int(os.getenv('TICKET_CATEGORY_ID', '1442410056019742750'))
        ticket_category = guild.get_channel(ticket_category_id)
        
        if not ticket_category:
            await interaction.followup.send('Error: Ticket category not found!', ephemeral=True)
            return
        
        # Sanitize username for channel name (remove invalid characters)
        sanitized_name = re.sub(r'[^a-z0-9-]', '', user.name.lower().replace(' ', '-'))
        ticket_name = f'request-mm-{sanitized_name}'
        existing_ticket = discord.utils.get(guild.text_channels, name=ticket_name)
        
        if existing_ticket:
            await interaction.followup.send(f'You already have an open ticket: {existing_ticket.mention}', ephemeral=True)
            return
        
        # Create ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_name,
                category=ticket_category,
                overwrites=overwrites
            )
            
            # Role IDs to ping (from environment or defaults)
            role_id_1 = int(os.getenv('MM_ROLE_ID_1', '1442993726057087089'))
            role_id_2 = int(os.getenv('MM_ROLE_ID_2', '1446603033445142559'))
            role_ids = [role_id_1, role_id_2]
            role_mentions = ' '.join([f'<@&{role_id}>' for role_id in role_ids])
            
            # Create welcome embed
            welcome_embed = discord.Embed(
                title=f"Welcome {user.display_name} to Eli's MM and Gambling!",
                description="A middleman will be with you very shortly.",
                color=discord.Color.blue()
            )
            welcome_embed.set_footer(text=f"Ticket created for {user.name}")
            
            # Send ping and embed
            await ticket_channel.send(role_mentions)
            await ticket_channel.send(embed=welcome_embed)
            
            await interaction.followup.send(f'Ticket created: {ticket_channel.mention}', ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f'Error creating ticket: {str(e)}', ephemeral=True)


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_load(self):
        """Add the persistent view when the cog loads"""
        self.bot.add_view(TicketButton())
    
    async def setup_ticket_panel(self, ctx):
        """Setup the ticket panel with button"""
        embed = discord.Embed(
            title="🎫 Middleman Services",
            description="Click the button below to request a middleman for your trade.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="How it works:",
            value="1. Click 'Request MM' button\n2. A private ticket will be created\n3. A middleman will assist you shortly",
            inline=False
        )
        
        view = TicketButton()
        await ctx.send(embed=embed, view=view)
        await ctx.send('Ticket panel setup complete!', delete_after=5)
    
    @commands.command(name='close')
    async def close_ticket(self, ctx):
        """Close the current ticket"""
        # Check if this is a ticket channel
        if not ctx.channel.name.startswith('request-mm-'):
            await ctx.send('This command can only be used in ticket channels!')
            return
        
        embed = discord.Embed(
            title="Closing Ticket",
            description="This ticket will be deleted in 5 seconds...",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        
        await asyncio.sleep(5)
        await ctx.channel.delete()

async def setup(bot):
    await bot.add_cog(Tickets(bot))
