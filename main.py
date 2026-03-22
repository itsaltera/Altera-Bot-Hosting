import discord
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime
import asyncio
import random
import re
import time
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

# Colors: {"Button Name": (ROLE_ID, "Emoji")}
COLORS_CONFIG = {
    "ʀᴇᴅ": (1469015814513496208, "❤️"),
    "ʙʟᴜᴇ": (1469019581723967569, "💙"),
    "ɢʀᴇᴇɴ": (1469019618864795914, "💚"),
    "ʏᴇʟʟᴏᴡ": (1469019664758608053, "💛"),
    "ᴘᴜʀᴘʟᴇ": (1469019698099261674, "💜"),
    "ᴘɪɴᴋ": (1469019767217193186, "🩷"),
    "ᴏʀᴀɴɢᴇ": (1469019637521060087, "🧡"),
    "ᴡʜɪᴛᴇ": (1469019779787391129, "🤍"),
    "ɢʀᴇʏ": (1469019854500663562, "🩶"),
    "ʙʟᴀᴄᴋ": (1469019880626852040, "🖤"),
}

PRONOUNS_CONFIG = {
    "ʜᴇ/ʜɪᴍ": (1469310805915861053, "🟦"),
    "sʜᴇ/ʜᴇʀ": (1469310873171394743, "🟪"),
    "sʜᴇ/ᴛʜᴇʏ": (1469310927861190708, "🟨"),
    "ʜᴇ/ᴛʜᴇʏ": (1469311190072033411, "🟩"),
    "ᴛʜᴇʏ/ᴛʜᴇᴍ": (1469310980810080451, "🟧"),
}

NOTIFICATIONS_CONFIG = {
    "ꜰʀᴇᴇ ɢᴀᴍᴇs": (1469357093374136466, "🎮"),
    "ᴍᴏᴠɪᴇ ɴɪɢʜᴛ": (1469357135962837238, "🎬"),
    "ɢɪᴠᴇᴀᴡᴀʏs": (1469583833824231608, "🎁"),
}

LOG_CHANNELS = {
    "chat": 1481292315422359632,
    "voice": 1481292400058962153,
    "nickname": 1481292472565891153,
    "channels": 1481292524692701254,
    "moderator": 1481292573531181075
}

ROLE_OWNER_ID = 1474380754187325510
ROLE_OWNER_WIFE_ID = 1474383754524098767
ROLE_STAFF_ID = 1474381713516793987
ROLE_MEMBER_ID = 1474381401192403018

# --- CHANNELS ---
WELCOME_CHANNEL_ID = 1469687284021596222
LEAVE_CHANNEL_ID = 1469687426648772913
RULES_CHANNEL_ID = 1468952515218243596
ANNOUNCEMENTS_CHANNEL_ID = 1468952538668597280
GENERAL_CHANNEL_ID = 1468952581417205986
TICKET_CHANNEL_ID = 1469693180428550178
PRONOUNS_CHANNEL_ID = 1468952807355842803
COLORS_CHANNEL_ID = 1468952774698864827
NOTIFICATIONS_CHANNEL_ID = 1468952791962615970
MEDIA_CHANNEL_ID = 1468952612295413760

TICKET_LOGS_CATEGORY_ID = 1475519132098101443
TICKET_CATEGORY_ID = 1474387376024457399
# --- BOT LOGIC ---

intents = discord.Intents.default()
intents.members = True 
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def create_log_embed(title, description, color=0xD40000):
    embed = discord.Embed(
        title=f"─── {title} ───",
        description=description,
        color=color,
        # Folosim discord.utils.utcnow() care este compatibil cu noile reguli Python
        timestamp=discord.utils.utcnow() 
    )
    embed.set_footer(text="Λ L T E R Λ sʏsᴛᴇᴍ ʟᴏɢs")
    return embed

def parse_duration(duration_str):
    time_dict = {"m": 60, "h": 3600, "d": 86400}
    match = re.match(r"(\d+)([mhd])", duration_str.lower())
    if match:
        amount, unit = match.groups()
        return int(amount) * time_dict[unit]
    return None

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="CLOSE TICKET", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        logs_category = discord.utils.get(guild.categories, id=TICKET_LOGS_CATEGORY_ID)
        
        # Sync permissions with the logs category (where only Owner/Wife see)
        await interaction.channel.edit(category=logs_category, name=f"closed-{interaction.channel.name}")
        
        # Remove user permissions so they can't see the archived ticket
        await interaction.channel.set_permissions(interaction.user, overwrite=None)
        
        await interaction.response.send_message("─── **ᴛɪᴄᴋᴇᴛ ᴄʟᴏsᴇᴅ ᴀɴᴅ ᴀʀᴄʜɪᴠᴇᴅ** ───")
        self.stop()

class TicketModal(discord.ui.Modal):
    def __init__(self, category):
        super().__init__(title=f"📝 ᴅᴇᴛᴀɪʟs: {category}")
        self.category = category
        
        self.explanation = discord.ui.TextInput(
            label="ᴇxᴘʟᴀɴᴀᴛɪᴏɴ",
            style=discord.TextStyle.paragraph,
            placeholder="Please describe your issue in detail...",
            required=True,
            min_length=10
        )
        self.add_item(self.explanation)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        active_category = discord.utils.get(guild.categories, id=TICKET_CATEGORY_ID)
        
        # Create channel
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=active_category
        )

        # Set Permissions: Deny everyone, allow Owner, Wife, Staff, and the User
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.get_role(ROLE_OWNER_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(ROLE_OWNER_WIFE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(ROLE_STAFF_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        await ticket_channel.edit(overwrites=overwrites)

        embed = discord.Embed(
            title="────────── Λ L T E R Λ ──────────",
            description=(
                f"**ɴᴇᴡ sᴜᴘᴘᴏʀᴛ ᴛɪᴄᴋᴇᴛ**\n\n"
                f"👤 **ᴜsᴇʀ:** {interaction.user.mention}\n"
                f"📂 **ᴄᴀᴛᴇɢᴏʀʏ:** `{self.category}`\n"
                f"📝 **ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ:**\n{self.explanation.value}\n"
                f"**ɴᴏᴛᴇ:** sᴛᴀꜰꜰ ᴡɪʟʟ ᴀssɪsᴛ ʏᴏᴜ sʜᴏʀᴛʟʏ."
            ),
            color=0xD40000
        )
        embed.set_footer(text="─────────── Λ L T E R Λ   S Y S T E M ───────────")
        
        await ticket_channel.send(content=f"{interaction.user.mention} | <@&{ROLE_STAFF_ID}>", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ ᴛɪᴄᴋᴇᴛ ᴄʀᴇᴀᴛᴇᴅ: {ticket_channel.mention}", ephemeral=True)

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="ʀᴇᴘᴏʀᴛ ᴀ ᴍᴇᴍʙᴇʀ", emoji="👤", description="Report a member for bad behavior."),
            discord.SelectOption(label="ʀᴇᴘᴏʀᴛ ᴀ sᴛᴀꜰꜰ", emoji="🛡️", description="Issues with a staff member."),
            discord.SelectOption(label="ǫᴜᴇsᴛɪᴏɴ", emoji="❓", description="General questions or inquiries."),
        ]
        super().__init__(placeholder="sᴇʟᴇᴄᴛ ᴀ ᴄᴀᴛᴇɢᴏʀʏ...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TicketModal(self.values[0]))

class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(TicketDropdown())

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Create ticket", style=discord.ButtonStyle.secondary, emoji="📩", custom_id="ticket_init")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "✨ **sᴇʟᴇᴄᴛ ᴛʜᴇ ʀɪɢʜᴛ ᴄᴀᴛᴇɢᴏʀʏ:**", 
            view=TicketDropdownView(), 
            ephemeral=True
        )

class GiveawayView(discord.ui.View):
    def __init__(self, prize, winners_count, end_timestamp, host_mention, description):
        super().__init__(timeout=None)
        self.prize = prize
        self.winners_count = winners_count
        self.end_timestamp = end_timestamp
        self.host_mention = host_mention
        self.desc_text = description
        self.participants = []

    async def update_embed(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"🎁 GIVEAWAY: {self.prize}",
            description=(
                f"{self.desc_text}\n\n"
                f"⌛ **Ends:** <t:{self.end_timestamp}:R>\n"
                f"👤 **Hosted by:** {self.host_mention}\n"
                f"🎟️ **Entries:** **{len(self.participants)}**\n"
                f"🏆 **Winners:** **{self.winners_count}**"
            ),
            color=0xD40000
        )
        embed.set_footer(text="Click the button below to participate!")
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="Giveaway", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="join_btn")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user not in self.participants:
            self.participants.append(interaction.user)
            await interaction.response.send_message("✅ You've successfully entered!", ephemeral=True)
            await self.update_embed(interaction)
        else:
            view = LeaveView(self, interaction.user)
            await interaction.response.send_message("You are already entered! Do you want to leave the giveaway?", view=view, ephemeral=True)

class LeaveView(discord.ui.View):
    def __init__(self, main_view, user):
        super().__init__(timeout=20)
        self.main_view = main_view
        self.user = user

    @discord.ui.button(label="Wanna leave?", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user in self.main_view.participants:
            self.main_view.participants.remove(self.user)
            await interaction.response.edit_message(content="❌ You have left the giveaway.", view=None)
            await self.main_view.update_embed(interaction)
        else:
            await interaction.response.edit_message(content="You are no longer in the list.", view=None)

class GiveawayModal(discord.ui.Modal, title="🎁 Create a Giveaway"):
    prize = discord.ui.TextInput(label="Prize", placeholder="Ex: Nitro Basic")
    duration = discord.ui.TextInput(label="Duration (m, h, d)", placeholder="Ex: 10m")
    winners = discord.ui.TextInput(label="Number of Winners", default="1")
    description = discord.ui.TextInput(label="Description", style=discord.TextStyle.paragraph, required=False)

    async def on_submit(self, interaction: discord.Interaction):
        seconds = parse_duration(self.duration.value)
        if seconds is None:
            return await interaction.response.send_message("❌ Invalid time format!", ephemeral=True)
        
        winner_count = int(self.winners.value)
        end_time = int(time.time() + seconds)
        
        embed = discord.Embed(
            title=f"🎁 GIVEAWAY: {self.prize.value}",
            description=(
                f"{self.description.value}\n\n"
                f"⌛ **Ends:** <t:{end_time}:R>\n"
                f"👤 **Hosted by:** {interaction.user.mention}\n"
                f"🎟️ **Entries:** **0**\n"
                f"🏆 **Winners:** **{winner_count}**"
            ),
            color=0xD40000
        )
        embed.set_footer(text="Click the button below to participate!")

        view = GiveawayView(self.prize.value, winner_count, end_time, interaction.user.mention, self.description.value)
        await interaction.response.send_message("Giveaway started!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)

        await asyncio.sleep(seconds)
        await msg.edit(view=None)

        if not view.participants:
            return await interaction.channel.send(f"❌ No one participated in the giveaway for **{self.prize.value}**.")

        winners_list = random.sample(view.participants, min(len(view.participants), winner_count))
        
        # --- Logic for formatting multiple winners ---
        mentions = [w.mention for w in winners_list]
        if len(mentions) == 1:
            winners_text = mentions[0]
        elif len(mentions) == 2:
            winners_text = f"{mentions[0]} and {mentions[1]}"
        else:
            winners_text = ", ".join(mentions[:-1]) + f" and {mentions[-1]}"

        win_embed = discord.Embed(
            title="🎉 GIVEAWAY WINNER(S) 🎉",
            description=f"Congratulations {winners_text}!\nYou won: **{self.prize.value}**",
            color=0x00FF00
        )
        if len(winners_list) == 1:
            win_embed.set_thumbnail(url=winners_list[0].display_avatar.url)
            
        await interaction.channel.send(content=f"Congratulations {winners_text}!", embed=win_embed)

class BaseRoleView(View):
    def __init__(self, config_dict, all_role_ids, category_name):
        super().__init__(timeout=None)
        self.config = config_dict
        self.all_role_ids = all_role_ids
        self.category_name = category_name
        self._setup_buttons()

    def _setup_buttons(self):
        for label, (role_id, emoji) in self.config.items():
            button = Button(
                label=f"┃{label}",
                style=discord.ButtonStyle.secondary,
                emoji=emoji,
                custom_id=f"role_{role_id}"
            )
            button.callback = self.create_callback(role_id)
            self.add_item(button)

    def create_callback(self, role_id):
        async def callback(interaction: discord.Interaction):
            role = interaction.guild.get_role(role_id)
            if not role:
                return await interaction.response.send_message("Error: Role does not exist!", ephemeral=True)

            to_remove = [interaction.guild.get_role(rid) for rid in self.all_role_ids if rid != role_id]
            existing_roles = [r for r in to_remove if r and r in interaction.user.roles]
            
            if existing_roles:
                await interaction.user.remove_roles(*existing_roles)

            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                msg = f"Removed the **{role.name}** {self.category_name}!"
            else:
                await interaction.user.add_roles(role)
                msg = f"You now have the **{role.name}** {self.category_name}!"
            
            await interaction.response.send_message(msg, ephemeral=True)
        return callback

class MultiRoleView(View):
    def __init__(self, config_dict):
        super().__init__(timeout=None)
        self.config = config_dict
        self._setup_buttons()

    def _setup_buttons(self):
        for label, (role_id, emoji) in self.config.items():
            button = Button(
                label=f"┃{label}",
                style=discord.ButtonStyle.secondary,
                emoji=emoji,
                custom_id=f"multi_role_{role_id}"
            )
            button.callback = self.create_callback(role_id)
            self.add_item(button)

    def create_callback(self, role_id):
        async def callback(interaction: discord.Interaction):
            role = interaction.guild.get_role(role_id)
            if not role:
                return await interaction.response.send_message("Error: Role does not exist!", ephemeral=True)

            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                msg = f"Disabled notifications for **{role.name}**!"
            else:
                await interaction.user.add_roles(role)
                msg = f"You are now subscribed to **{role.name}**!"
            
            await interaction.response.send_message(msg, ephemeral=True)
        return callback

@bot.tree.command(name="gcreate", description="Start a new giveaway")
async def gcreate(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("You don't have permission to create giveaways!", ephemeral=True)
    await interaction.response.send_modal(GiveawayModal())

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(ROLE_MEMBER_ID)
    if role:
        try:
            await member.add_roles(role)
        except discord.Forbidden:
            print(f"Nu am permisiuni să dau rolul membrului {member.name}")
        except Exception as e:
            print(f"Eroare la adăugarea rolului: {e}")

    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        human_count = len([m for m in member.guild.members if not m.bot])
        embed = discord.Embed(
            title="───── Λ L T E R Λ ─────",
            description=(
                f"**ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ sᴇʀᴠᴇʀ, {member.mention}! ✨**\n"
                f"ᴡᴇ’ʀᴇ ʜʏᴘᴇᴅ ᴛᴏ ʜᴀᴠᴇ ʏᴏᴜ ʜᴇʀᴇ!\nᴛᴏ ɢᴇᴛ sᴛᴀʀᴛᴇᴅ:\n\n"
                f"📍 ᴄʜᴇᴄᴋ ᴏᴜᴛ <#{RULES_CHANNEL_ID}> sᴏ\nᴡᴇ ᴄᴀɴ ᴋᴇᴇᴘ ᴛʜɪɴɢs ᴄʜɪʟʟ.\n"
                f"🎭 ʜᴇᴀᴅ ᴏᴠᴇʀ ᴛᴏ\n<#{PRONOUNS_CHANNEL_ID}>\n<#{COLORS_CHANNEL_ID}>\n<#{NOTIFICATIONS_CHANNEL_ID}>\nᴛᴏ ᴄᴜsᴛᴏᴍɪᴢᴇ ʏᴏᴜʀ ᴘʀᴏꜰɪʟᴇ.\n"
                f"📸 **ɪᴍᴘᴏʀᴛᴀɴᴛ:** ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ\nsʜᴀʀᴇ ᴘʜᴏᴛᴏs ᴏʀ ᴍᴇᴍᴇs,"
                f"ᴘʟᴇᴀsᴇ\nᴘᴏsᴛ ᴛʜᴇᴍ ɪɴ <#{MEDIA_CHANNEL_ID}> ᴛᴏ\nᴋᴇᴇᴘ ᴛʜᴇ ᴍᴀɪɴ ᴄʜᴀᴛ ᴄʟᴇᴀɴ!\n"
                f"👋 sᴛᴀʀᴛ ᴛᴀʟᴋɪɴɢ ɪɴ\n<#{GENERAL_CHANNEL_ID}>\n\n"
                f"ᴊᴜᴍᴘ ɪɴ ᴀɴᴅ sᴛᴀʀᴛ ᴄʜᴀᴛᴛɪɴɢ!"
            ),
            color=0xD40000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url="https://i.pinimg.com/originals/ea/d5/41/ead541982d28e6f89edd38dbe1a9d107.gif")
        embed.set_footer(text=f"ᴍᴇᴍʙᴇʀ ᴄᴏᴜɴᴛ: {human_count} ┃ Λ L T E R Λ")
        await channel.send(content=member.mention, embed=embed)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")
    
    # Adaugă vizualizarea de ticket pentru a fi permanentă
    bot.add_view(TicketView())
    
    # Restul vizualizărilor tale...
    colors_ids = [val[0] for val in COLORS_CONFIG.values()]
    pronouns_ids = [val[0] for val in PRONOUNS_CONFIG.values()]
    bot.add_view(BaseRoleView(COLORS_CONFIG, colors_ids, "color"))
    bot.add_view(BaseRoleView(PRONOUNS_CONFIG, pronouns_ids, "pronouns"))
    bot.add_view(MultiRoleView(NOTIFICATIONS_CONFIG))

@bot.command()
async def send_colors(ctx):
    embed = discord.Embed(
        title="────────── Λ L T E R Λ ──────────",
        description="**S E L E C T   C O L O R S**\n\nᴘɪᴄᴋ ʏᴏᴜʀ ꜰᴀᴠᴏʀɪᴛᴇ ᴄᴏʟᴏʀ ᴏʀ ᴛʜᴇ ᴏɴᴇ ᴛʜᴀᴛ\nʀᴇᴘʀᴇsᴇɴᴛ ʏᴏᴜ ʙᴇsᴛ ᴛᴏ ᴘᴇʀsᴏɴᴀʟɪᴢᴇ ʏᴏᴜʀ\nᴘʀᴏꜰɪʟᴇ.",
        color=0xD40000
    )
    all_ids = [val[0] for val in COLORS_CONFIG.values()]
    lines = [f"{emoji} <@&{rid}>" for rid, emoji in COLORS_CONFIG.values()]
    mid = (len(lines) + 1) // 2
    embed.add_field(name="✨ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏʟᴏʀs", value="\n".join(lines[:mid]), inline=True)
    embed.add_field(name="⠀", value="\n".join(lines[mid:]), inline=True)
    embed.set_footer(text="─────────── Λ L T E R Λ   S Y S T E M ───────────")
    await ctx.send(embed=embed, view=BaseRoleView(COLORS_CONFIG, all_ids, "color"))

@bot.command()
async def send_pronounce(ctx):
    embed = discord.Embed(
        title="────────── Λ L T E R Λ ──────────",
        description="**S E L E C T   P R O N O U N S**\n\nsᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴘʀᴏɴᴏᴜɴs ʙᴇʟᴏᴡ ᴛᴏ ᴘᴇʀsᴏɴᴀʟɪᴢᴇ\nʏᴏᴜʀ ᴘʀᴏꜰɪʟᴇ ᴀɴᴅ ʟᴇᴛ ᴜs ᴋɴᴏᴡ ʜᴏᴡ ᴛᴏ ᴀᴅᴅʀᴇss\nʏᴏᴜ.",
        color=0xD40000
    )
    all_ids = [val[0] for val in PRONOUNS_CONFIG.values()]
    lines = [f"{emoji} <@&{rid}>" for rid, emoji in PRONOUNS_CONFIG.values()]
    embed.add_field(name="✨ ᴀᴠᴀɪʟᴀʙʟᴇ ᴘʀᴏɴᴏᴜɴs", value="\n".join(lines), inline=True)
    embed.set_footer(text="─────────── Λ L T E R Λ   S Y S T E M ───────────")
    await ctx.send(embed=embed, view=BaseRoleView(PRONOUNS_CONFIG, all_ids, "pronouns"))

@bot.command()
async def send_notifications(ctx):
    new_description = (
        "**S E L E C T   N O T I F I C A T I O N S**\n\n"
        "sᴛᴀʏ ᴜᴘᴅᴀᴛᴇᴅ ᴡɪᴛʜ ᴇᴠᴇʀʏᴛʜɪɴɢ ʜᴀᴘᴘᴇɴɪɴɢ ɪɴ ᴏᴜʀ\n"
        "ᴄᴏᴍᴍᴜɴɪᴛʏ! sᴇʟᴇᴄᴛ ᴛʜᴇ ʀᴏʟᴇs ʙᴇʟᴏᴡ ᴛᴏ ʙᴇ ɴᴏᴛɪꜰɪᴇᴅ\n"
        "ᴡʜᴇɴ ꜰʀᴇᴇ ɢᴀᴍᴇs ᴀʀᴇ ᴀᴠᴀɪʟᴀʙʟᴇ ᴏɴ sᴛᴇᴀᴍ ᴏʀ ᴇᴘɪᴄ,\n"
        "ᴡʜᴇɴ ᴡᴇ ʜᴏsᴛ ᴍᴏᴠɪᴇ ɴɪɢʜᴛs ᴏʀ sᴛᴀʀᴛ ɢɪᴠᴇᴀᴡᴀʏs."
    )
    embed = discord.Embed(
        title="────────── Λ L T E R Λ ──────────",
        description=new_description,
        color=0xD40000
    )
    lines = [f"{emoji} <@&{rid}>" for rid, emoji in NOTIFICATIONS_CONFIG.values()]
    embed.add_field(name="✨ sᴜʙsᴄʀɪʙᴇ ᴛᴏ", value="\n".join(lines), inline=True)
    embed.set_footer(text="─────────── Λ L T E R Λ   S Y S T E M ───────────")
    await ctx.send(embed=embed, view=MultiRoleView(NOTIFICATIONS_CONFIG))

@bot.command()
async def setup_tickets(ctx):
    embed = discord.Embed(
        title="────────── Λ L T E R Λ ──────────",
        description=(
            "### sᴜᴘᴘᴏʀᴛ ᴛɪᴄᴋᴇᴛs\n\n"
            "ᴛᴏ ᴄʀᴇᴀᴛᴇ ᴀ ᴛɪᴄᴋᴇᴛ ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ.\n\n"
            "‼️ **ᴡᴀʀɴɪɴɢ: ᴛʀᴏʟʟ ᴛɪᴄᴋᴇᴛs ᴄᴀᴜsᴇ sᴀɴᴄᴛɪᴏɴs** ‼️"
        ),
        color=0xD40000
    )
    embed.set_footer(text="────────── Λ L T E R Λ   S Y S T E M ──────────")
    await ctx.send(embed=embed, view=TicketView())

# --- 1. CHAT LOGS (Update) ---
@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    channel = bot.get_channel(LOG_CHANNELS["chat"])
    
    executor = "Self"
    # Așteptăm puțin pentru ca Discord să genereze log-ul
    await asyncio.sleep(0.5) 
    async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=1):
        if entry.target and entry.target.id == message.author.id:
            executor = entry.user.mention
            break

    # Verificăm dacă există poze/fișiere
    files = "\n".join([f"📎 {a.url}" for a in message.attachments])
    
    desc = (f"🗑️ **Message deleted in** {message.channel.mention}\n"
            f"👤 **Author:** {message.author.mention}\n"
            f"🛠️ **Deleted by:** {executor}\n"
            f"💬 **Content:** {message.content or '*(No text)*'}\n"
            f"{files if files else ''}")
    await channel.send(embed=create_log_embed("ᴍᴇssᴀɢᴇ ᴅᴇʟᴇᴛᴇᴅ", desc))

# --- 2. VOICE LOGS (Fixed) ---
@bot.event
async def on_voice_state_update(member, before, after):
    # Verificăm dacă este un canal de log configurat
    log_channel = bot.get_channel(LOG_CHANNELS["voice"])
    if not log_channel:
        return

    # 1. User Joined a channel
    if not before.channel and after.channel:
        desc = f"📥 {member.mention} **joined** {after.channel.mention}"
        await log_channel.send(embed=create_log_embed("VOICE JOIN", desc, color=0x2ecc71))

    # 2. User Left a channel
    elif before.channel and not after.channel:
        desc = f"📤 {member.mention} **left** {before.channel.mention}"
        await log_channel.send(embed=create_log_embed("VOICE LEAVE", desc, color=0xe74c3c))

    # 3. User Switched channels (Moved)
    elif before.channel and after.channel and before.channel != after.channel:
        desc = f"🔄 {member.mention} **switched** from {before.channel.mention} to {after.channel.mention}"
        await log_channel.send(embed=create_log_embed("VOICE MOVE", desc, color=0xf1c40f))

# --- 3. MEMBER UPDATE (Timeout Fix) ---
@bot.event
async def on_member_update(before, after):
    channel_mod = bot.get_channel(LOG_CHANNELS["moderator"])
    channel_nick = bot.get_channel(LOG_CHANNELS["nickname"])
    
    # Timeout check (independent de roluri)
    if before.timed_out_until != after.timed_out_until:
        await asyncio.sleep(1) # Timeout logs durează puțin până apar
        executor = "Self or unknown"
        reason = "No reason provided"
        async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=1):
            if entry.target and entry.target.id == after.id:
                executor = entry.user.mention
                reason = entry.reason or "No reason provided"
                break
        
        if after.timed_out_until:
            desc = f"⏳ {after.mention} **timed out** by {executor}\n📝 **Reason:** {reason}\n📅 **Until:** <t:{int(after.timed_out_until.timestamp())}:f>"
            await channel_mod.send(embed=create_log_embed("ᴍᴇᴍʙᴇʀ ᴛɪᴍᴇᴏᴜᴛ", desc, color=0xe67e22))
        else:
            desc = f"🔓 {after.mention} **timeout removed** by {executor}"
            await channel_mod.send(embed=create_log_embed("ᴛɪᴍᴇᴏᴜᴛ ʀᴇᴍᴏᴠᴇᴅ", desc, color=0x2ecc71))
            
    # Nickname Change
    if before.nick != after.nick:
        executor = "Self"
        async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=1):
            if entry.target.id == after.id:
                executor = entry.user.mention
                break
        desc = (f"👤 **Member:** {after.mention}\n"
                f"🛠️ **Changed by:** {executor}\n"
                f"❌ **Old Nick:** {before.nick}\n"
                f"✅ **New Nick:** {after.nick}")
        await channel_nick.send(embed=create_log_embed("ɴɪᴄᴋɴᴀᴍᴇ ᴄʜᴀɴɢᴇ", desc))

    # Roles Change
    if before.roles != after.roles:
        executor = "Self"
        async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=1):
            if entry.target.id == after.id:
                executor = entry.user.mention
                break
        
        added = [r.mention for r in after.roles if r not in before.roles]
        removed = [r.mention for r in before.roles if r not in after.roles]
        
        desc = f"👤 **Member:** {after.mention}\n🛠️ **Updated by:** {executor}\n"
        if added: desc += f"✅ **Roles Added:** {', '.join(added)}\n"
        if removed: desc += f"❌ **Roles Removed:** {', '.join(removed)}"
        await channel_mod.send(embed=create_log_embed("ʀᴏʟᴇs ᴜᴘᴅᴀᴛᴇᴅ", desc, color=0x9b59b6))

# --- 4. CHANNEL LOGS ---
@bot.event
async def on_guild_channel_create(channel):
    log_ch = bot.get_channel(LOG_CHANNELS["channels"])
    executor = "Unknown"
    async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
        executor = entry.user.mention
        break
    await log_ch.send(embed=create_log_embed("ᴄʜᴀɴɴᴇʟ ᴄʀᴇᴀᴛᴇᴅ", f"🆕 **Name:** {channel.name}\n👤 **Created by:** {executor}\n📂 **Type:** {channel.type}"))

@bot.event
async def on_guild_channel_delete(channel):
    log_ch = bot.get_channel(LOG_CHANNELS["channels"])
    executor = "Unknown"
    async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
        executor = entry.user.mention
        break
    await log_ch.send(embed=create_log_embed("ᴄʜᴀɴɴᴇʟ ᴅᴇʟᴇᴛᴇᴅ", f"🗑️ **Name:** {channel.name}\n👤 **Deleted by:** {executor}", color=0xe74c3c))

@bot.event
async def on_guild_channel_update(before, after):
    if before.name != after.name:
        log_ch = bot.get_channel(LOG_CHANNELS["channels"])
        entry = None
        
        # Căutăm în Audit Logs cine a făcut schimbarea
        async for e in after.guild.audit_logs(action=discord.AuditLogAction.channel_update, limit=1):
            entry = e
            break
            
        executor = entry.user.mention if entry else "Necunoscut"
        
        desc = (f"📝 **Channel Renamed**\n"
                f"👤 **By:** {executor}\n"
                f"❌ **Old Name:** {before.name}\n"
                f"✅ **New Name:** {after.name}\n")
        
        await log_ch.send(embed=create_log_embed("ᴄʜᴀɴɴᴇʟ ᴜᴘᴅᴀᴛᴇᴅ", desc, color=0x3498db))

# --- 5. MODERATOR LOGS (Ban/Kick/Timeout) ---
@bot.event
async def on_member_ban(guild, user):
    await asyncio.sleep(1.0)  # Așteptăm o secundă pentru sync
    channel = bot.get_channel(LOG_CHANNELS["moderator"])
    executor = "Unknown"
    reason = "No reason provided"

    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=5):
        if entry.target.id == user.id:
            executor = entry.user.mention
            reason = entry.reason if entry.reason else "No reason provided"
            break
            
    desc = f"🔨 {user.name} was banned.\n🛠️ **Moderator:** {executor}\n📝 **Reason:** {reason}"
    await channel.send(embed=create_log_embed("ᴍᴇᴍʙᴇʀ ʙᴀɴɴᴇᴅ", desc, color=0x000000))
@bot.event
async def on_member_remove(member):
    # --- LOGICA PENTRU MODERARE (KICK) ---
    moderator_channel = bot.get_channel(LOG_CHANNELS["moderator"])
    is_kick = False
    
    # Verificăm dacă a fost kick în ultimele secunde
    async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=3):
        if entry.target and entry.target.id == member.id:
            time_diff = (discord.utils.utcnow() - entry.created_at).total_seconds()
            if time_diff < 10:
                is_kick = True
                if moderator_channel:
                    executor = entry.user.mention
                    reason = entry.reason or "No reason provided"
                    desc = f"👢 {member.mention} was **kicked** by {executor}.\n**Reason:** {reason}"
                    await moderator_channel.send(embed=create_log_embed("MEMBER KICKED", desc, color=0xe74c3c))
                break

    # --- LOGICA PENTRU MESAJUL DE LEAVE (DOAR DACĂ NU A FOST KICK) ---
    # Dacă vrei mesaj de leave chiar și la kick, scoate "if not is_kick:"
    if not is_kick:
        leave_channel = bot.get_channel(LEAVE_CHANNEL_ID)
        if leave_channel:
            human_count = len([m for m in member.guild.members if not m.bot])
            embed = discord.Embed(
                title="───── Λ L T E R Λ ─────",
                description=f"**ɢ ᴏ ᴏ ᴅ ʙ ʏ ᴇ**\n\n🚪 **{member.mention}** ʜᴀs ʟᴇꜰᴛ ᴛʜᴇ\nsᴇʀᴠᴇʀ.\nᴡᴇ ʜᴏᴘᴇ ʏᴏᴜ ʜᴀᴅ ᴀ ɢʀᴇᴀᴛ ᴛɪᴍᴇ\nʜᴇʀᴇ!",
                color=0xFF0000
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_image(url="https://i.pinimg.com/originals/56/74/96/567496ecebed7e9bfb7688a62f0c4b31.gif")
            embed.set_footer(text=f"ᴍᴇᴍʙᴇʀ ᴄᴏᴜɴᴛ: {human_count}")
            await leave_channel.send(embed=embed)

keep_alive()
bot.run(os.environ['BOT_TOKEN'])