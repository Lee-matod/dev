# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import discord

from discord.ext import commands

from dev.utils.baseclass import root


class RootBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

# TODO: Everything


async def setup(bot):
    await bot.add_cog(RootBot(bot))