import discord

from discord.ext import commands

bot = commands.Bot(command_prefix="?", intents=discord.Intents.all(), owner_id=531961974972481536)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}: {bot.user.id}")


@bot.command()
async def ping(ctx: commands.Context):
    async with ctx.typing():
        pong = bot.latency
    await ctx.send(f"Pong! {round(pong * 1000, 2)} :ping_pong:")

bot.load_extension("dev")


bot.run("TOKEN")
