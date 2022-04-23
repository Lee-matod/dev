# -*- coding: utf-8 -*-

"""
dev.__main__
~~~~~~~~~~~~

Includes the root command for the dev extension, as well as other commands that do not fall under any other category.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from discord.ext import commands

from dev.utils.functs import send
from dev.utils.baseclass import root, Root


class RootCommand(Root):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.group(name="dev", invoke_without_command=True, version=1)
    async def root_(self, ctx: commands.Context):
        pass

    @root.command(name="visibility", parent="dev", version=1)
    async def root_visibility(self, ctx: commands.Context, toggle: bool):
        dev = self.bot.get_command("dev")
        if toggle:
            if dev.hidden:
                return await send(ctx, f"`dev` is already hidden.")
            dev.hidden = True
            await ctx.message.add_reaction("☑")
        else:
            if not dev.hidden:
                return await send(ctx, f"`dev` is already visible.")
            dev.hidden = False
            await ctx.message.add_reaction("☑")