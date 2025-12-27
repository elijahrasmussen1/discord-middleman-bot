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
        
        # Check if user has MM ban role
        mm_ban_role_id = int(os.getenv('MM_BAN_ROLE_ID', '1446370352757342279'))
        mm_ban_role = guild.get_role(mm_ban_role_id)
        
        if mm_ban_role and mm_ban_role in user.roles:
            await interaction.followup.send(
                'You are currently banned from using middleman services. '
                'Please contact an administrator if you believe this is an error.',
                ephemeral=True
            )
            return
        
        # Get the ticket category from environment or use default
        try:
            ticket_category_id = int(os.getenv('TICKET_CATEGORY_ID', '1442410056019742750'))
        except ValueError:
            await interaction.followup.send('Error: Invalid ticket category ID in configuration!', ephemeral=True)
            return
            
        ticket_category = guild.get_channel(ticket_category_id)
        
        if not ticket_category:
            await interaction.followup.send('Error: Ticket category not found!', ephemeral=True)
            return
        
        # Sanitize username for channel name (remove invalid characters)
        # Remove non-alphanumeric chars, replace with single hyphen, strip leading/trailing hyphens
        sanitized_name = re.sub(r'[^a-zA-Z0-9]+', '-', user.name).strip('-').lower()
        
        # Fallback to user ID if sanitized name is empty
        if not sanitized_name:
            sanitized_name = str(user.id)
        
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
            try:
                role_id_1 = int(os.getenv('MM_ROLE_ID_1', '1442993726057087089'))
                role_id_2 = int(os.getenv('MM_ROLE_ID_2', '1446603033445142559'))
            except ValueError:
                await interaction.followup.send('Error: Invalid role IDs in configuration!', ephemeral=True)
                return
                
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
    
    @commands.command(name='mmpanel')
    @commands.has_permissions(administrator=True)
    async def mmpanel(self, ctx):
        """Send the ticket panel (Admin only)"""
        await self.setup_ticket_panel(ctx)
    
    @commands.command(name='mmban')
    @commands.has_permissions(administrator=True)
    async def mmban(self, ctx, member: discord.Member):
        """Ban a user from using middleman services (Admin only)"""
        # Get MM ban role ID from environment or use default
        mm_ban_role_id = int(os.getenv('MM_BAN_ROLE_ID', '1446370352757342279'))
        mm_ban_role = ctx.guild.get_role(mm_ban_role_id)
        
        if not mm_ban_role:
            await ctx.send('Error: MM ban role not found! Please check role ID configuration.')
            return
        
        # Check if user already has the role
        if mm_ban_role in member.roles:
            await ctx.send(f'{member.mention} is already MM banned.')
            return
        
        try:
            # Add the MM ban role to the user
            await member.add_roles(mm_ban_role, reason=f'MM banned by {ctx.author}')
            
            # Create professional ban embed to send to user
            ban_embed = discord.Embed(
                title="🚫 Middleman Services Ban",
                description="You have been MM banned in **Eli's MM and Gambling!**",
                color=discord.Color.red()
            )
            ban_embed.add_field(
                name="What does this mean?",
                value="You will no longer be able to use our middleman services.",
                inline=False
            )
            ban_embed.add_field(
                name="Questions?",
                value="If you believe this is an error, please contact an administrator.",
                inline=False
            )
            ban_embed.set_footer(text="Eli's MM and Gambling")
            ban_embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            
            # Try to DM the user
            try:
                await member.send(embed=ban_embed)
                dm_status = "✅ DM sent successfully"
            except discord.Forbidden:
                dm_status = "⚠️ Could not DM user (DMs disabled)"
            except Exception as e:
                dm_status = f"⚠️ Could not DM user: {str(e)}"
            
            # Confirm in channel
            confirm_embed = discord.Embed(
                title="MM Ban Applied",
                description=f'{member.mention} has been banned from using middleman services.',
                color=discord.Color.orange()
            )
            confirm_embed.add_field(name="Status", value=dm_status, inline=False)
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            await ctx.send('Error: I don\'t have permission to add roles to this user.')
        except Exception as e:
            await ctx.send(f'Error applying MM ban: {str(e)}')
    
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
