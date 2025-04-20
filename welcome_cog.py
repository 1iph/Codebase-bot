import discord
from discord.ext import commands
from discord import app_commands

welcome_channel_id = None


class WelcomeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setwelcome", description="Set the welcome channel for new members.")
    async def setwelcome(self, interaction):
        global welcome_channel_id
        welcome_channel_id = interaction.channel.id
        await interaction.response.send_message(
            f"✅ Welcome channel set to {interaction.channel.mention}!",
            ephemeral=True
        )

# Event to send welcome message


@commands.Cog.listener()
async def on_member_join(member):
    if welcome_channel_id is None:
        print("No welcome channel set.")
        return  # No welcome channel set

    channel = member.guild.get_channel(welcome_channel_id)
    if not channel:
        print(f"Could not find the channel with ID: {welcome_channel_id}")
        return  # Could not find the welcome channel

    print(f"Sending welcome message to {member.mention} in {channel.name}")

    embed = discord.Embed(
        title="☕ Welcome to Codebase!",
        description=f"Hey {member.mention}, we're glad you're here!\nGet cozy, grab a coffee, and join the chat!",
        color=discord.Color.from_rgb(139, 69, 19)  # Custom brown color
    )
    embed.set_image(url="attachment://welcome.png")
    embed.set_footer(text="Your journey starts now — let’s code together!")

    await channel.send(
        embed=embed,
        file=discord.File(
            "coffee_pics/Adobe Express - file.png", filename="welcome.png")
    )

# Setup the cog


async def setup(bot):
    await bot.add_cog(WelcomeCog(bot))
