import discord
from discord.ext import commands
from discord.ui import Button, View, Select, Modal, TextInput
from discord import app_commands
import asyncio
import os
import re
from .mm_database import MMDatabase

class TicketActionsView(View):
    """View with Claim and Close buttons for MM staff"""
    def __init__(self, mm_role_id: int, ticket_channel_id: int = None, db: MMDatabase = None):
        super().__init__(timeout=None)
        self.mm_role_id = mm_role_id
        self.ticket_channel_id = ticket_channel_id
        self.claimed_by = None
        self.db = db if db else MMDatabase()
    
    @discord.ui.button(label="Claim", style=discord.ButtonStyle.green, custom_id="persistent_ticket_claim")
    async def claim_button(self, interaction: discord.Interaction, button: Button):
        """Claim the ticket"""
        # Check if user has the MM role
        mm_role = interaction.guild.get_role(self.mm_role_id)
        if not mm_role or mm_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You don't have permission to claim tickets.",
                ephemeral=True
            )
            return
        
        if self.claimed_by:
            await interaction.response.send_message(
                f"⚠️ This ticket has already been claimed by {self.claimed_by.mention}",
                ephemeral=True
            )
            return
        
        self.claimed_by = interaction.user
        button.disabled = True
        button.label = f"Claimed by {interaction.user.display_name}"
        button.style = discord.ButtonStyle.gray
        
        await interaction.response.edit_message(view=self)
        
        # Get MM profile data
        profile = self.db.get_profile(interaction.user.id)
        rank = profile.get("rank", "Middleman")
        completed_tickets = profile.get("completed_tickets", 0)
        
        # Create professional MM profile embed
        mm_embed = discord.Embed(
            title="• MM Profile •",
            color=0x3498db  # Professional blue
        )
        
        # Add profile information with clean formatting
        profile_info = (
            f"**Username:** {interaction.user.mention} ({interaction.user.name})\n"
            f"**User ID:** {interaction.user.id}\n"
            f"**Rank:** {rank}\n"
            f"**Completed tickets:** {completed_tickets}"
        )
        
        mm_embed.add_field(name="", value=profile_info, inline=False)
        
        # Set the middleman's profile picture/gif on the right
        if interaction.user.avatar:
            mm_embed.set_thumbnail(url=interaction.user.avatar.url)
        
        # Add timestamp for professionalism
        mm_embed.timestamp = discord.utils.utcnow()
        mm_embed.set_footer(text="Eli's MM Service")
        
        # Send the profile message
        await interaction.channel.send(
            f"{interaction.user.mention} will be assisting your trade.",
            embed=mm_embed
        )
    
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, custom_id="persistent_ticket_close")
    async def close_button(self, interaction: discord.Interaction, button: Button):
        """Close the ticket"""
        # Check if user has the MM role
        mm_role = interaction.guild.get_role(self.mm_role_id)
        if not mm_role or mm_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ You don't have permission to close tickets.",
                ephemeral=True
            )
            return
        
        # If this ticket was claimed by an MM, increment their completed tickets
        if self.claimed_by and self.claimed_by == interaction.user:
            self.db.increment_tickets(interaction.user.id)
            close_message = f"🔒 Ticket is being closed by {interaction.user.mention}... (+1 completed ticket)"
        else:
            close_message = f"🔒 Ticket is being closed by {interaction.user.mention}..."
        
        await interaction.response.send_message(
            close_message,
            ephemeral=False
        )
        
        # Wait a moment then delete the channel
        await asyncio.sleep(3)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")

class TradeQuestionnaire(Modal):
    """Modal for collecting trade information"""
    def __init__(self, category: str):
        super().__init__(title=f"Trade Information - {category}")
        self.category = category
        
        # For MM2/JB/ETC category, use different questions
        if category == "mm2-jb-etc":
            self.game = TextInput(
                label="What is the game?",
                placeholder="E.g., MM2, Jailbreak, etc.",
                required=True,
                max_length=100
            )
            self.add_item(self.game)
        
        self.trade = TextInput(
            label="What is the trade?",
            placeholder="E.g., Garama (SAB) for Apple Pay",
            required=True,
            max_length=200
        )
        
        self.your_side = TextInput(
            label="What is your side" + (" of the trade?" if category == "mm2-jb-etc" else "?"),
            placeholder="E.g., Garama (SAB) or $50 Apple Pay",
            required=True,
            max_length=200
        )
        
        self.their_side = TextInput(
            label="What is their side" + (" of the trade?" if category == "mm2-jb-etc" else "?"),
            placeholder="E.g., $50 Apple Pay or Garama (SAB)",
            required=True,
            max_length=200
        )
        
        self.discord_id = TextInput(
            label="What is their discord ID? (required)" if category == "mm2-jb-etc" else "Discord ID? (required)",
            placeholder="Enter the other user's Discord ID",
            required=True,
            max_length=20
        )
        
        self.add_item(self.trade)
        self.add_item(self.your_side)
        self.add_item(self.their_side)
        self.add_item(self.discord_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle questionnaire submission"""
        # Store the responses on the modal instance
        if self.category == "mm2-jb-etc":
            self.game_value = self.game.value
        else:
            self.game_value = None
        
        self.trade_value = self.trade.value
        self.your_side_value = self.your_side.value
        self.their_side_value = self.their_side.value
        self.discord_id_value = self.discord_id.value
        
        # Defer response
        await interaction.response.defer(ephemeral=True)


class TicketPanel(View):
    def __init__(self, db: MMDatabase = None):
        super().__init__(timeout=None)
        self.db = db if db else MMDatabase()
    
    @discord.ui.select(
        placeholder="Select a category to begin",
        min_values=1,
        max_values=1,
        custom_id='ticket_category_select',
        options=[
            discord.SelectOption(
                label="SAB", 
                value="sab",
                emoji="<:sab:1462812023133044797>"
            ),
            discord.SelectOption(label="150m-500m", value="150m-500m"),
            discord.SelectOption(label="500m-1b", value="500m-1b"),
            discord.SelectOption(label="Drag / OG", value="drag-og"),
            discord.SelectOption(label="MM2, JB, ETC", value="mm2-jb-etc")
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: Select):
        """Handle category selection and show questionnaire"""
        guild = interaction.guild
        user = interaction.user
        
        # Check if user has MM ban role first
        mm_ban_role_id = int(os.getenv('MM_BAN_ROLE_ID', '1446370352757342279'))
        mm_ban_role = guild.get_role(mm_ban_role_id)
        
        if mm_ban_role and mm_ban_role in user.roles:
            await interaction.response.send_message(
                'You are currently banned from using middleman services. '
                'Please contact an administrator if you believe this is an error.',
                ephemeral=True
            )
            return
        
        selected_category = select.values[0]
        
        # Show the questionnaire modal
        modal = TradeQuestionnaire(selected_category)
        await interaction.response.send_modal(modal)
        
        # Wait for modal submission
        await modal.wait()
        
        # Create the ticket with the questionnaire data
        await self.create_ticket(
            interaction, 
            user, 
            guild, 
            selected_category,
            modal.game_value if hasattr(modal, 'game_value') else None,
            modal.trade_value,
            modal.your_side_value,
            modal.their_side_value,
            modal.discord_id_value
        )
    
    async def create_ticket(self, interaction: discord.Interaction, user: discord.Member, guild: discord.Guild, category: str, game: str, trade: str, your_side: str, their_side: str, discord_id: str):
        """Create the ticket channel after questionnaire completion"""
        
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
        
        # Try to get the other user from Discord ID
        other_user = None
        discord_id_valid = False
        try:
            other_user_id = int(discord_id.strip())
            other_user = guild.get_member(other_user_id)
            if not other_user:
                # Try to fetch if not in cache
                try:
                    other_user = await guild.fetch_member(other_user_id)
                    discord_id_valid = True
                except:
                    # Could not find user with this ID
                    discord_id_valid = False
            else:
                discord_id_valid = True
        except ValueError:
            # Invalid Discord ID format
            discord_id_valid = False
        
        # If Discord ID is invalid, send error message and return
        if not discord_id_valid:
            await interaction.followup.send(
                '**Please provide the other users full username or Discord ID.**',
                ephemeral=True
            )
            return
        
        # Sanitize username for channel name (remove invalid characters)
        # Remove non-alphanumeric chars, replace with single hyphen, strip leading/trailing hyphens
        sanitized_name = re.sub(r'[^a-zA-Z0-9]+', '-', user.name).strip('-').lower()
        
        # Fallback to user ID if sanitized name is empty
        if not sanitized_name:
            sanitized_name = str(user.id)
        
        # Determine ticket name based on category
        if category == "mm2-jb-etc":
            ticket_name = f'request-mm-{sanitized_name}'
        elif category == "sab":
            ticket_name = f'{sanitized_name}-mm150'
        elif category == "150m-500m":
            ticket_name = f'{sanitized_name}-mm500'
        elif category == "500m-1b":
            ticket_name = f'{sanitized_name}-mm1b'
        elif category == "drag-og":
            ticket_name = f'{sanitized_name}-owneronly'
        else:
            ticket_name = f'{sanitized_name}-mm'
        
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
        
        # Add the other user to the ticket if found
        if other_user:
            overwrites[other_user] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        try:
            ticket_channel = await guild.create_text_channel(
                name=ticket_name,
                category=ticket_category,
                overwrites=overwrites
            )
            
            # Role ID to ping (from environment or default)
            try:
                mm_role_id = int(os.getenv('MM_ROLE_ID', '1452247731648200816'))
            except ValueError:
                await interaction.followup.send('Error: Invalid role ID in configuration!', ephemeral=True)
                return
            
            # Create professional, eye-catching welcome embed (inspired by $mmpanel format)
            welcome_embed = discord.Embed(
                title="**Eli's MM Service**",
                color=0x3498db  # Professional blue color matching $mmpanel
            )
            
            # Add server logo using the same method as $mmban command
            if guild.icon:
                welcome_embed.set_thumbnail(url=guild.icon.url)
            
            # Header with ticket creator and other user (NO spoiler tags in embed)
            if other_user:
                header_text = f"> {user.mention} has made a middleman ticket with {other_user.mention}"
            else:
                header_text = f"> {user.mention} has made a middleman ticket with <@{discord_id}>"
            
            welcome_embed.add_field(
                name="", 
                value=header_text,
                inline=False
            )
            
            # Display the full trade prominently with blockquote formatting
            if game:
                trade_info = f"> **Trade:** {trade}\n> **Game:** {game}"
            else:
                trade_info = f"> **Trade:** {trade}"
            
            welcome_embed.add_field(
                name="", 
                value=trade_info,
                inline=False
            )
            
            # Trade sides with blockquote formatting
            trade_sides = (
                f"> **{user.display_name}'s Side:**\n> {your_side}\n> \n"
                f"> **Other User's Side:**\n> {their_side}"
            )
            
            welcome_embed.add_field(
                name="", 
                value=trade_sides,
                inline=False
            )
            
            # Footer message with better formatting
            welcome_embed.add_field(
                name="",
                value="> Welcome to Eli's MM Service! A middleman will be here very soon.",
                inline=False
            )
            
            # Add timestamp and footer for professionalism
            welcome_embed.timestamp = discord.utils.utcnow()
            welcome_embed.set_footer(text="Eli's MM Service")
            
            # Send pings (role + both users) and embed
            user_pings = f"||{user.mention}||"
            if other_user:
                user_pings += f" ||{other_user.mention}||"
            else:
                user_pings += f" ||<@{discord_id}>||"
            
            ping_message = f"<@&{mm_role_id}> {user_pings}"
            await ticket_channel.send(ping_message)
            
            # Create the view with Claim and Close buttons
            actions_view = TicketActionsView(mm_role_id, db=self.db)
            await ticket_channel.send(embed=welcome_embed, view=actions_view)
            
            # Wait 30 seconds before sending follow-up questionnaire
            await asyncio.sleep(30)
            
            # Send follow-up questionnaire to the ticket creator
            questionnaire_message = (
                "Welcome! Thank you for choosing Eli's MM Service. Answer the questions below to begin.\n\n"
                "1. what is your roblox username?\n"
                "2. are you able to join PS links? (13+)\n"
                "3. Do you understand that you will be MM Banned from this server if you fail to vouch? (Y/N)\n\n"
                "**Please answer these questions as soon as possible**"
            )
            await ticket_channel.send(questionnaire_message)
            
            await interaction.followup.send(f'Ticket created: {ticket_channel.mention}', ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f'Error creating ticket: {str(e)}', ephemeral=True)


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = MMDatabase()
    
    async def cog_load(self):
        """Add the persistent views when the cog loads"""
        self.bot.add_view(TicketPanel(db=self.db))
        # Add persistent view for ticket actions (with default MM role ID)
        try:
            mm_role_id = int(os.getenv('MM_ROLE_ID', '1452247731648200816'))
            self.bot.add_view(TicketActionsView(mm_role_id, db=self.db))
        except ValueError:
            print("Warning: Invalid MM_ROLE_ID in configuration")
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('❌ You don\'t have permission to use this command.')
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send('❌ User not found. Please mention a valid user or provide a valid user ID.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('❌ Invalid argument provided. For `$mmban`, please mention a user: `$mmban @user`')
    
    async def setup_ticket_panel(self, ctx):
        """Setup the ticket panel with category selection"""
        embed = discord.Embed(
            title="**Eli's MM Service**",
            description=(
                "To request a middleman from this server,\n"
                "select a category from the dropdown below.\n"
            ),
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="",
            value=(
                "> **How does a Middleman Work?**\n"
                "> Example: Trade is Brulee (JB) For Cashapp\n"
                "> 1. Seller gives Brulee to middleman.\n"
                "> 2. Buyer sends money to seller (after middleman receives items)\n"
                "> 3. Middleman gives Brulee to buyer (after seller confirms payment)"
            ),
            inline=False
        )
        
        embed.add_field(
            name="",
            value=(
                "> **Important**\n"
                "> • Fake tickets are not allowed. Once the trade is completed you must vouch your middleman.\n"
                "> • If you have trouble getting a user's ID **[click here to find a users ID](https://discord.com/channels/1442270020959867162/1454757054471475210)**.\n"
                "> • Make sure to read the rules before making a ticket."
            ),
            inline=False
        )
        
        view = TicketPanel()
        await ctx.send(embed=embed, view=view)
        await ctx.send('Ticket panel setup complete!', delete_after=5)
    
    @commands.command(name='mmpanel')
    @commands.has_permissions(administrator=True)
    async def mmpanel(self, ctx):
        """Send the ticket panel (Admin only)"""
        await self.setup_ticket_panel(ctx)
    
    @commands.command(name='mmban')
    @commands.has_permissions(administrator=True)
    async def mmban(self, ctx, *, member: discord.Member = None):
        """Ban a user from using middleman services (Admin only)"""
        if member is None:
            await ctx.send('❌ Please specify a user to ban. Usage: `$mmban @user` or `$mmban UserID`')
            return
        
        # Get MM ban role ID from environment or use default
        try:
            mm_ban_role_id = int(os.getenv('MM_BAN_ROLE_ID', '1446370352757342279'))
        except ValueError:
            await ctx.send('Error: Invalid MM ban role ID in configuration!')
            return
            
        mm_ban_role = ctx.guild.get_role(mm_ban_role_id)
        
        if not mm_ban_role:
            await ctx.send(f'Error: MM ban role not found! Please check role ID {mm_ban_role_id} exists in this server.')
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
            if ctx.guild.icon:
                ban_embed.set_thumbnail(url=ctx.guild.icon.url)
            
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
                title="✅ MM Ban Applied",
                description=f'{member.mention} has been banned from using middleman services.',
                color=discord.Color.orange()
            )
            confirm_embed.add_field(name="User", value=f"{member} (ID: {member.id})", inline=False)
            confirm_embed.add_field(name="DM Status", value=dm_status, inline=False)
            confirm_embed.add_field(name="Banned by", value=ctx.author.mention, inline=False)
            await ctx.send(embed=confirm_embed)
            
        except discord.Forbidden:
            await ctx.send('❌ Error: I don\'t have permission to add roles to this user. Please check my role hierarchy.')
        except Exception as e:
            await ctx.send(f'❌ Error applying MM ban: {str(e)}')
    
    def is_ticket_channel(self, channel_name: str) -> bool:
        """Check if the channel is a ticket channel"""
        return (channel_name.endswith('-mm150') or 
                channel_name.endswith('-mm500') or 
                channel_name.endswith('-mm1b') or 
                channel_name.endswith('-owneronly') or
                channel_name.startswith('request-mm-'))  # Keep backward compatibility
    
    @commands.command(name='close')
    async def close_ticket(self, ctx):
        """Close the current ticket"""
        # Check if this is a ticket channel
        if not self.is_ticket_channel(ctx.channel.name):
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
    
    @commands.command(name='mmbans')
    @commands.has_permissions(administrator=True)
    async def mmbans(self, ctx):
        """Show all users currently MM banned (Admin only)"""
        # Get MM ban role ID from environment or use default
        try:
            mm_ban_role_id = int(os.getenv('MM_BAN_ROLE_ID', '1446370352757342279'))
        except ValueError:
            await ctx.send('❌ Error: Invalid MM ban role ID in configuration!')
            return
            
        mm_ban_role = ctx.guild.get_role(mm_ban_role_id)
        
        if not mm_ban_role:
            await ctx.send(f'❌ Error: MM ban role not found! Please check role ID {mm_ban_role_id} exists in this server.')
            return
        
        # Get all members with the MM ban role
        banned_members = [member for member in ctx.guild.members if mm_ban_role in member.roles]
        
        # Create embed to display banned users
        embed = discord.Embed(
            title="🚫 MM Banned Users",
            description=f"Users currently banned from middleman services",
            color=discord.Color.red()
        )
        
        if banned_members:
            # Create a list of banned users with their info
            banned_list = []
            for i, member in enumerate(banned_members, 1):
                banned_list.append(f"{i}. {member.mention} - {member} (ID: {member.id})")
            
            # Discord embed field has a 1024 character limit, so split if needed
            banned_text = "\n".join(banned_list)
            if len(banned_text) <= 1024:
                embed.add_field(name=f"Total: {len(banned_members)} user(s)", value=banned_text, inline=False)
            else:
                # Split into multiple fields if too long
                chunks = []
                current_chunk = []
                current_length = 0
                
                for line in banned_list:
                    if current_length + len(line) + 1 > 1024:
                        chunks.append("\n".join(current_chunk))
                        current_chunk = [line]
                        current_length = len(line)
                    else:
                        current_chunk.append(line)
                        current_length += len(line) + 1
                
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                
                for i, chunk in enumerate(chunks, 1):
                    field_name = f"Banned Users (Part {i})" if len(chunks) > 1 else f"Total: {len(banned_members)} user(s)"
                    embed.add_field(name=field_name, value=chunk, inline=False)
        else:
            embed.add_field(name="No Banned Users", value="No users are currently MM banned.", inline=False)
        
        embed.set_footer(text=f"Requested by {ctx.author}")
        await ctx.send(embed=embed)
    
    @commands.command(name='add')
    async def add_to_ticket(self, ctx, member: discord.Member = None):
        """Add a user to the current ticket"""
        # Check if this is a ticket channel
        if not self.is_ticket_channel(ctx.channel.name):
            await ctx.send('❌ This command can only be used in ticket channels!')
            return
        
        if member is None:
            await ctx.send('❌ Please specify a user to add. Usage: `$add @user`')
            return
        
        # Check if user already has access
        overwrites = ctx.channel.overwrites_for(member)
        if overwrites.read_messages:
            await ctx.send(f'⚠️ {member.mention} already has access to this ticket.')
            return
        
        try:
            # Give the member permission to view and send messages in this channel
            await ctx.channel.set_permissions(
                member,
                read_messages=True,
                send_messages=True,
                reason=f'Added to ticket by {ctx.author}'
            )
            
            # Send confirmation embed
            embed = discord.Embed(
                description=f"{member.mention} has been added to the ticket!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send('❌ Error: I don\'t have permission to modify channel permissions.')
        except Exception as e:
            await ctx.send(f'❌ Error adding user to ticket: {str(e)}')
    
    @commands.command(name='findid')
    async def find_user_id(self, ctx, member: discord.Member = None):
        """Get a user's Discord ID"""
        if member is None:
            await ctx.send('❌ Please mention a user. Usage: `$findid @user`')
            return
        
        await ctx.send(f'{member.id}')
    
    @commands.command(name='setrank')
    @commands.has_permissions(administrator=True)
    async def set_rank(self, ctx, member: discord.Member, *, rank: str):
        """Set a middleman's rank - supports any text with spaces (Admin only)"""
        # Set the rank in the database
        self.db.set_rank(member.id, rank)
        
        # Send confirmation embed
        embed = discord.Embed(
            title="✅ Rank Updated",
            description=f"{member.mention}'s rank has been set to **{rank}**",
            color=0x00ff00  # Green
        )
        embed.set_footer(text=f"Updated by {ctx.author.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)
    
    @set_rank.error
    async def set_rank_error(self, ctx, error):
        """Error handler for setrank command"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('❌ Usage: `$setrank @user <rank name>`\nExample: `$setrank @User Custom Rank Name`')
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send('❌ User not found. Please mention a valid server member.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('❌ You need Administrator permission to use this command.')
    
    @commands.command(name='changetickets')
    @commands.has_permissions(administrator=True)
    async def change_tickets(self, ctx, member: discord.Member, amount: int):
        """Change a middleman's completed ticket count (Admin only)"""
        if amount < 0:
            await ctx.send('❌ Amount must be a non-negative number.')
            return
        
        # Set the completed tickets in the database
        self.db.set_completed_tickets(member.id, amount)
        
        # Send confirmation embed
        embed = discord.Embed(
            title="✅ Tickets Updated",
            description=f"{member.mention}'s completed tickets have been set to **{amount}**",
            color=0x00ff00  # Green
        )
        embed.set_footer(text=f"Updated by {ctx.author.name}")
        embed.timestamp = discord.utils.utcnow()
        
        await ctx.send(embed=embed)
    
    @change_tickets.error
    async def change_tickets_error(self, ctx, error):
        """Error handler for changetickets command"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('❌ Usage: `$changetickets @user <amount>`\nExample: `$changetickets @User 50`')
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send('❌ User not found. Please mention a valid server member.')
        elif isinstance(error, commands.BadArgument):
            await ctx.send('❌ Amount must be a valid number.')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send('❌ You need Administrator permission to use this command.')
    
    @commands.command(name='proof')
    async def proof(self, ctx, *, args: str = None):
        """Submit middleman proof with trade info and extra details
        
        Usage: $proof <trade>, <extra info>
        Example: $proof Garama for $20 Cashapp, Player let me take garama first then got paid by buyer.
        
        Attach up to 2 videos/images with the command.
        """
        if args is None:
            await ctx.send('❌ Usage: `$proof <trade>, <extra info>`\nExample: `$proof Garama for $20 Cashapp, Player let me take garama first`')
            return
        
        # Split by comma to get trade and extra info
        parts = args.split(',', 1)
        if len(parts) < 2:
            await ctx.send('❌ Please use a comma (`,`) to separate the trade from extra info.\nExample: `$proof Garama for $20 Cashapp, Player let me take garama first`')
            return
        
        trade = parts[0].strip()
        extra_info = parts[1].strip()
        
        # Check for attachments
        if not ctx.message.attachments:
            await ctx.send('❌ Please attach at least one video or image as proof.')
            return
        
        if len(ctx.message.attachments) > 2:
            await ctx.send('⚠️ Note: Only the first 2 attachments will be displayed.')
        
        # Create professional proof embed
        embed = discord.Embed(
            title="__**• Middleman Proof •**__",
            description=f"Proof submitted by {ctx.author.mention}",
            color=0x3498db  # Blue
        )
        
        # Add trade information
        embed.add_field(
            name="**Full Trade:**",
            value=trade,
            inline=False
        )
        
        # Add extra info from MM
        embed.add_field(
            name="**Extra info from MM:**",
            value=f'"{extra_info}"',
            inline=False
        )
        
        # Add timestamp and footer
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="Eli's MM Service")
        
        # Set thumbnail to user's avatar
        if ctx.guild and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        
        # Send the main embed with the first image attachment if available
        first_image = None
        for attachment in ctx.message.attachments[:2]:
            if attachment.content_type and attachment.content_type.startswith('image'):
                first_image = attachment
                break
        
        if first_image:
            embed.set_image(url=first_image.url)
        
        await ctx.send(embed=embed)
        
        # Collect all attachments by type
        video_urls = []
        image_attachments = []
        other_attachments = []
        
        for attachment in ctx.message.attachments[:2]:
            if attachment.content_type:
                if attachment.content_type.startswith('video'):
                    video_urls.append(attachment.url)
                elif attachment.content_type.startswith('image') and attachment != first_image:
                    image_attachments.append(attachment)
                else:
                    other_attachments.append(attachment)
            else:
                other_attachments.append(attachment)
        
        # Send all videos in a single message (if any)
        if video_urls:
            video_count = len(video_urls)
            video_label = "Videos" if video_count > 1 else "Video"
            video_embed = discord.Embed(
                description=f"**{video_label} ({video_count}):**",
                color=0x3498db
            )
            video_embed.set_footer(text=f"Proof videos - {video_count} of {min(len(ctx.message.attachments), 2)}")
            await ctx.send(embed=video_embed)
            # Send all video URLs together so Discord renders them all
            await ctx.send("\n".join(video_urls))
        
        # Send any additional images (not the first one already in main embed)
        for i, img_attachment in enumerate(image_attachments):
            img_embed = discord.Embed(color=0x3498db)
            img_embed.set_image(url=img_attachment.url)
            img_embed.set_footer(text=f"Proof image {i+2}")
            await ctx.send(embed=img_embed)
        
        # Send any other file types as links
        for i, other_attachment in enumerate(other_attachments):
            other_embed = discord.Embed(color=0x3498db)
            other_embed.description = f"**Attachment {i+1}:** [Click here to view]({other_attachment.url})"
            await ctx.send(embed=other_embed)

async def setup(bot):
    await bot.add_cog(Tickets(bot))
