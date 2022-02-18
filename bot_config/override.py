import discord
import re

from discord.ext import commands

from dev.utils.functs import is_owner
from dev.utils.baseclass import commands_


class RootOverrideBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.group(name="override", parent="dev")
    @is_owner()
    async def root_override(ctx: commands.Context):
        return

    @commands_.command(name="file", parent="dev override")
    async def root_override_file(ctx: commands.Context, line):
        pass


def setup(bot: commands.Bot):
    bot.add_cog(RootOverrideBot(bot))