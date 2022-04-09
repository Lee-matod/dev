import discord

from discord.ext import commands

bot = commands.Bot(command_prefix="?", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}: {bot.user.id}")


bot.load_extension("dev")


bot.run("OTE4NTc1MjgzMjI3OTkyMTA0.YbJP5Q.OWW_nEJNPC9wL6EmF1AE4fm9jWc")
