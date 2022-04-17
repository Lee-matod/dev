import discord

from discord.ext import commands

from dev.utils.baseclass import root


class RootBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(RootBot(bot))