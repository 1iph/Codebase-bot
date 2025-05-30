import discord
from discord.ext import commands
import os
import random
import requests
from dotenv import load_dotenv
from datetime import datetime
import asyncio
import re
import aiohttp
import pytz
import json
from calendar import TextCalendar

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
        try:
            await self.load_extension("welcome_cog")
        except Exception as e:
            print(f"Failed to load welcome_cog: {e}")
        await self.tree.sync()

bot = MyBot(command_prefix='!', intents=intents)

linked_users = {}
todos = {}
applications = {}
APPLICATION_CHANNEL_ID = 1329159564469342360

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

@bot.command()
async def setapply(ctx):
    view = discord.ui.View()
    button = discord.ui.Button(label="Apply", style=discord.ButtonStyle.green)

    async def button_callback(interaction):
        try:
            await interaction.user.send("Let's get started! What's your IGN?")

            def check(m):
                return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

            ign = await bot.wait_for('message', check=check)
            await interaction.user.send("How old are you?")
            age = await bot.wait_for('message', check=check)
            await interaction.user.send("Tell me about your experience in coding:")
            experience = await bot.wait_for('message', check=check)
            await interaction.user.send("Thank you for your answers, we will get back to you shortly!")

            channel = bot.get_channel(APPLICATION_CHANNEL_ID)
            embed = discord.Embed(title="New Application", color=0x3498db)
            embed.add_field(name="IGN", value=ign.content, inline=False)
            embed.add_field(name="Age", value=age.content, inline=False)
            embed.add_field(name="Experience", value=experience.content, inline=False)

            review_view = discord.ui.View()
            accept = discord.ui.Button(label="Accept", style=discord.ButtonStyle.green)
            deny = discord.ui.Button(label="Deny", style=discord.ButtonStyle.red)

            async def accept_callback(ia):
                await interaction.user.send("✅ Your application has been accepted!")
                await ia.message.delete()

            async def deny_callback(ia):
                await interaction.user.send("❌ Your application has been denied.")
                await ia.message.delete()

            accept.callback = accept_callback
            deny.callback = deny_callback
            review_view.add_item(accept)
            review_view.add_item(deny)

            await channel.send(embed=embed, view=review_view)
        except Exception as e:
            print(f"Application error: {e}")

    button.callback = button_callback
    view.add_item(button)
    await ctx.send("Application setup complete! Click below to apply.", view=view)

@bot.command()
async def link(ctx, ign):
    linked_users[str(ctx.author.id)] = ign
    await ctx.send(f"Linked your IGN to **{ign}** ✅")

async def get_hypixel_data(username):
    uuid_url = f"https://api.mojang.com/users/profiles/minecraft/{username}"
    uuid_resp = requests.get(uuid_url).json()
    uuid = uuid_resp['id']

    stats_url = f"https://api.hypixel.net/player?key={HYPIXEL_API_KEY}&uuid={uuid}"
    stats_resp = requests.get(stats_url).json()
    return stats_resp

@bot.command()
async def profile(ctx, gamemode=None):
    user_id = str(ctx.author.id)
    ign = linked_users.get(user_id)
    if not ign:
        await ctx.send("Please use `!link <ign>` first to link your account.")
        return

    data = await get_hypixel_data(ign)
    player = data.get('player', {})
    embed = discord.Embed(title=f"{ign}'s Hypixel Stats", color=0x00ff00)
    level = int(((player.get('networkExp', 0))**(1/2.0) + 1))
    embed.add_field(name="Network Level", value=str(level), inline=True)
    embed.add_field(name="Karma", value=player.get('karma', 0), inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def pomodoro(ctx, work: int, rest: int):
    await ctx.send(f"⏳ Work for {work} minutes!")
    await asyncio.sleep(work * 60)
    await ctx.send(f"🛌 Break time for {rest} minutes!")
    await asyncio.sleep(rest * 60)
    await ctx.send("✅ Pomodoro complete!")

@bot.command()
async def calendar(ctx):
    cal = TextCalendar().formatmonth(datetime.now().year, datetime.now().month)
    await ctx.send(f"```\n{cal}```")

@bot.command()
async def todo(ctx, user: discord.User, action: str, *, task):
    if action == "add":
        todos.setdefault(str(user.id), []).append(task)
        await ctx.send(f"✅ Task added for {user.display_name}.")

@bot.command()
async def tasks(ctx, user: discord.User):
    user_tasks = todos.get(str(user.id), [])
    if not user_tasks:
        await ctx.send("No tasks found.")
        return
    tasks_list = "\n".join(f"{i+1}. {task}" for i, task in enumerate(user_tasks))
    await ctx.send(f"Tasks for {user.display_name}:\n{tasks_list}")

@bot.command()
async def done(ctx, user: discord.User, number: int):
    try:
        task_list = todos[str(user.id)]
        removed = task_list.pop(number - 1)
        await ctx.send(f"✅ Removed task: {removed}")
    except:
        await ctx.send("⚠️ Task not found or invalid number.")

@bot.command()
async def cat(ctx):
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.thecatapi.com/v1/images/search") as resp:
            data = await resp.json()
            await ctx.send(data[0]['url'])

@bot.command()
async def catfacts(ctx):
    facts = [
        "Cats have five toes on their front paws, but only four on the back ones.",
        "A group of cats is called a clowder.",
        "Cats sleep for 70% of their lives."
    ]
    await ctx.send(random.choice(facts))

@bot.command()
async def tea(ctx):
    teas = ["tea_pics/green_tea.jpg", "tea_pics/black_tea.jpg"]
    await ctx.send("Here’s your tea, enjoy! 🍵")
    await ctx.send(file=discord.File(random.choice(teas)))

@bot.command()
async def facts(ctx):
    programming_facts = ["Python was named after Monty Python.", "Java was originally called Oak."]
    await ctx.send(random.choice(programming_facts))

@bot.command()
async def alias(ctx, *, name):
    await ctx.author.edit(nick=name)
    await ctx.send(f"Nickname updated to {name} ✅")

@bot.command()
async def time(ctx, timezone):
    try:
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)
        await ctx.send(f"🕒 Current time in {timezone}: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    except pytz.UnknownTimeZoneError:
        await ctx.send("Invalid timezone. Try 'America/New_York' or 'Europe/London'.")

@bot.command()
@commands.has_permissions(administrator=True)
async def print(ctx, channel: discord.TextChannel, *, message):
    embed = discord.Embed(description=message, color=0x2ecc71)
    await channel.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, user: discord.User, *, reason):
    try:
        await user.send(f"⚠️ Warning from {ctx.guild.name}: {reason}")
        await ctx.send("User warned in DMs ✅")
    except discord.Forbidden:
        await ctx.send("Couldn't send DM to user ❌")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, user: discord.Member, *, reason):
    await user.kick(reason=reason)
    await ctx.send(f"👢 {user} has been kicked. Reason: {reason}")

@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, user: discord.Member, *, reason):
    await user.ban(reason=reason)
    await ctx.send(f"🔨 {user} has been banned. Reason: {reason}")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, user: discord.Member, duration: int):
    try:
        await user.timeout(until=discord.utils.utcnow() + discord.timedelta(minutes=duration))
        await ctx.send(f"⏳ {user.mention} has been timed out for {duration} minutes.")
    except Exception as e:
        await ctx.send(f"Failed to timeout user: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands!')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

bot.run(TOKEN)
