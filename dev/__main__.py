# -*- coding: utf-8 -*-

"""
dev.__main__
~~~~~~~~~~~~

Includes the root command for the dev extension, as well as other commands that do not fall under any other category.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import discord

from discord.ext import commands

from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.baseclass import root, Root


class RootCommand(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @root.group(name="dev", invoke_without_command=True, usage="[--help|--man] [--source|-src [--file]] <command>")
    async def root_(self, ctx: commands.Context):
        """Root command for the `dev` extension.
        Execute `dev --help [command]` for more information on a subcommand.
        `--help`|`--man` [command] = Shows this help menu.
        `--source`|`-src` [--file] <command> = Shows the source code of a command.
        """

    @root_.command(name="visibility")
    async def root_visibility(self, ctx: commands.Context, toggle: bool = None):
        if toggle:
            if self.root_command.hidden:
                return await send(ctx, f"`dev` is already hidden.")
            self.root_command.hidden = True
            await ctx.message.add_reaction("☑")
        elif toggle is None:
            translate = {True: "hidden", False: "visible"}
            await send(ctx, f"`dev` is currently {translate.get(self.root_command.hidden)}.")
        else:
            if not self.root_command.hidden:
                return await send(ctx, f"`dev` is already visible.")
            self.root_command.hidden = False
            await ctx.message.add_reaction("☑")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if Settings.INVOKE_ON_EDIT:
            if before.content.startswith(self.bot.command_prefix) and after.content.startswith(self.bot.command_prefix):
                await before.clear_reactions()
                await self.bot.process_commands(after)
