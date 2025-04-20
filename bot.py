import discord  # <-- Make sure this is at the top
from discord.ext import commands
import os
import random
import requests
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import re


# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
HYPIXEL_API_KEY = os.getenv("HYPIXEL_API_KEY")

# Intents setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class MyBot(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("welcome_cog")
        await self.tree.sync()


bot = MyBot(command_prefix='!', intents=intents)


@bot.command(name="matrix")
async def matrix(ctx, ign: str):
    api_key = HYPIXEL_API_KEY
    if not api_key:
        await ctx.send("❌ API Key is not set.")
        return

    try:
        response = requests.get(
            f"https://api.hypixel.net/player?key={api_key}&name={ign}")
        data = response.json()

        if not data.get('success'):
            await ctx.send(f"❌ Error: {data.get('cause', 'Unknown error')}")
            return

        player = data.get('player')
        if not player:
            await ctx.send("❌ Player not found.")
            return

        username = player.get('displayname', ign)
        networkExp = player.get('networkExp', 0)
        networkLevel = round(1 + (networkExp / 10000) ** 0.5, 2)

        bedwars_exp = player.get('stats', {}).get(
            'Bedwars', {}).get('Experience', 0)
        if bedwars_exp < 500:
            bedwars_stars = 1
        elif bedwars_exp < 1000:
            bedwars_stars = 2
        elif bedwars_exp < 2000:
            bedwars_stars = 3
        elif bedwars_exp < 3500:
            bedwars_stars = 4
        else:
            bedwars_stars = 4 + (bedwars_exp - 3500) // 5000

        duel_wins = player.get('stats', {}).get('Duels', {}).get('wins', 0)

        await ctx.send("```diff\n+ ACCESS GRANTED\n```")

        embed = discord.Embed(
            title=f"🟢 Accessing {username}'s Profile...",
            description=random.choice([
                "`Running user lookup...`",
                "`Decrypting player stats...`",
                "`Injecting Matrix feed...`"
            ]),
            color=discord.Color.dark_green()
        )
        embed.add_field(name="💾 Network Level",
                        value=f"`{networkLevel}`", inline=False)
        embed.add_field(name="⭐ Bedwars Stars",
                        value=f"`{bedwars_stars}`", inline=False)
        embed.add_field(name="⚔️ Duels Wins",
                        value=f"`{duel_wins}`", inline=False)
        embed.set_footer(text="SYSTEM ONLINE ░█░█░█░█░█░█░█░█░█░")

        await ctx.send(embed=embed)

    except requests.exceptions.RequestException:
        await ctx.send("❌ Error: Could not connect to Hypixel API.")


@bot.command()
async def guildstats(ctx, ign):
    try:
        uuid_url = f"https://api.mojang.com/users/profiles/minecraft/{ign}"
        uuid_response = requests.get(uuid_url)

        if uuid_response.status_code != 200:
            await ctx.send(f"❌ The IGN `{ign}` was not found on Mojang.")
            return

        uuid = uuid_response.json().get("id")
        guild_url = f"https://api.hypixel.net/guild?key={HYPIXEL_API_KEY}&player={uuid}"
        guild_response = requests.get(guild_url).json()

        if not guild_response.get("success") or not guild_response.get("guild"):
            await ctx.send(f"⚠️ `{ign}` is not in a guild or the guild data couldn't be retrieved.")
            return

        guild = guild_response["guild"]
        guild_name = guild.get("name", "Unknown Guild")
        guild_tag = guild.get("tag", "No Tag")
        guild_tag_color = guild.get("tagColor", "WHITE")
        guild_members = len(guild.get("members", []))
        guild_level = guild.get("level") or "Unknown"

        created_timestamp = guild.get("created")
        created_date = datetime.utcfromtimestamp(
            created_timestamp / 1000).strftime('%Y-%m-%d') if created_timestamp else "Unknown"

        embed = discord.Embed(
            title=f"🏰 Guild Stats: {guild_name}",
            description=f"Tag: **[{guild_tag}]** — Color: `{guild_tag_color}`",
            color=discord.Color.gold()
        )
        embed.add_field(name="Level", value=guild_level, inline=True)
        embed.add_field(name="Members", value=str(guild_members), inline=True)
        embed.add_field(name="Created On", value=created_date, inline=True)
        embed.set_footer(text="Data fetched live from Hypixel API.")

        await ctx.send(embed=embed)

    except Exception as e:
        print(e)
        await ctx.send("🚨 Something went wrong while fetching guild data. Try again later!")


@bot.command(name="quote")
async def quote(ctx):
    quotes = [
        "“Code is like humor. When you have to explain it, it’s bad.” – Cory House",
        "Minecraft fact: The Enderman language is just English in reverse.",
        "When life gives you bugs, write a patch!"
    ]
    await ctx.send(random.choice(quotes))


@bot.command(name="brew")
async def brew(ctx):
    await ctx.send("Here is your coffee! ☕")
    await ctx.send(file=discord.File("coffee_pics/pexels-chevanon-312418.jpg"))


@bot.command(name="remindme")
async def remindme(ctx, time: str, *, reminder: str):
    match = re.match(r"(\d+)(s|m|hr)$", time.lower())
    if not match:
        await ctx.send("❌ Invalid format! Use `s` for seconds, `m` for minutes, or `hr` for hours.\nExample: `!remindme 10m Take a break!`")
        return

    amount, unit = match.groups()
    amount = int(amount)
    seconds = {'s': 1, 'm': 60, 'hr': 3600}.get(unit, 0) * amount

    await ctx.send(f"⏰ Reminder set! I'll DM you in {amount} {unit}.")
    await asyncio.sleep(seconds)

    try:
        await ctx.author.send(f"🔔 Reminder: {reminder}")
    except discord.Forbidden:
        await ctx.send(f"{ctx.author.mention}, I couldn't DM you! Make sure your DMs are open.")

# Application system
applications = {}

APPLICATION_CHANNEL_ID = 1329159564469342360


@bot.command()
async def setapply(ctx):
    # Create the button and view
    view = discord.ui.View()
    button = discord.ui.Button(
        label="Apply", style=discord.ButtonStyle.green)

    # Define the button callback
    async def button_callback(interaction):
        # Send a DM to the user to start the application process
        await interaction.user.send("Let's get started! What's your IGN?")

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        # Collect responses from the user
        ign = await bot.wait_for('message', check=check)
        await interaction.user.send("How old are you?")
        age = await bot.wait_for('message', check=check)
        await interaction.user.send("Tell me about your experience in coding:")
        experience = await bot.wait_for('message', check=check)
        await interaction.user.send("Thank you for your answers, we will get back to you shortly!")

        # Send the responses to the applications channel
        channel = bot.get_channel(APPLICATION_CHANNEL_ID)
        embed = discord.Embed(title="New Application", color=0x3498db)
        embed.add_field(name="IGN", value=ign.content, inline=False)
        embed.add_field(name="Age", value=age.content, inline=False)
        embed.add_field(name="Experience",
                        value=experience.content, inline=False)

        # Create Accept/Deny buttons
        review_view = discord.ui.View()
        accept = discord.ui.Button(
            label="Accept", style=discord.ButtonStyle.green)
        deny = discord.ui.Button(label="Deny", style=discord.ButtonStyle.red)

        # Define the accept callback
        async def accept_callback(ia):
            await interaction.user.send("✅ Your application has been accepted!")
            await ia.message.delete()

        # Define the deny callback
        async def deny_callback(ia):
            await interaction.user.send("❌ Your application has been denied.")
            await ia.message.delete()

        accept.callback = accept_callback
        deny.callback = deny_callback
        review_view.add_item(accept)
        review_view.add_item(deny)

        # Send the application details with buttons to the applications channel
        await channel.send(embed=embed, view=review_view)

    # Set the button callback for the "Apply Here!" button
    button.callback = button_callback
    view.add_item(button)

    # Send the setup message with the button in the current channel
    await ctx.send("Application setup complete! Click below to apply.", view=view)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands!')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
bot.run(TOKEN)
