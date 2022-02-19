import discord

from discord.ext import commands

from dev.utils.functs import is_owner
from dev.utils.baseclass import commands_


class RootBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(RootBot(bot))