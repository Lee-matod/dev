# -*- coding: utf-8 -*-

"""
dev.__main__
~~~~~~~~~~~~

Includes the root command for the dev extension, as well as other commands that do not fall under any other category.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from discord.ext import commands

from dev.utils.startup import setup_
from dev.utils.baseclass import root
from dev.utils.functs import is_owner
from dev.utils.startup import set_settings


class Root(commands.Cog, name="Dev"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.group(name="dev", invoke_without_command=True, version=1)
    @is_owner()
    async def root_(self, ctx: commands.Context):
        pass

    @root.command(name="exit", aliases=["kys"], version=1, parent="dev")
    @is_owner()
    async def root_stop(self, ctx: commands.Context):
        """
        Exit the whole program at once.
        Not recommended using unless a critical event happens that requires the bot to be terminated immediately
        """
        await ctx.message.add_reaction("👋")
        exit()

    @root.command(name="close", version=1, parent="dev")
    @is_owner()
    async def root_quit(self, ctx: commands.Context):
        """
        Close the bot.
        Safely exit out of the bot.
        """
        await ctx.message.add_reaction("👋")
        await ctx.bot.close


async def setup(bot: commands.Bot):
    set_settings(bot)
    await bot.add_cog(Root(bot))
    await setup_(bot, "dev.flags.help_command", "dev.flags.flags", "dev.config.over", "dev.config.bot", "dev.config.variables", "dev.experimental.invoke", "dev.experimental.python", "dev.experimental.http")