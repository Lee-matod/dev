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

    @root.group(name="dev", invoke_without_command=True, ignore_extra=False, usage="[--help|--man] [--source|-src|--sourceFile|-srcF] [--inspect|-i] <command>")
    async def root_(self, ctx: commands.Context):
        """Root command for the `dev` extension.
        Execute `dev --help [command]` for more information on a subcommand.
        `--help`|`--man` [command] = Shows a custom made help command.
        `--source`|`-src` <command> = Shows the source code of a command.
        `--sourceFile`|`-srcF` <command> = Shows the source file of a command.
        `--inspect`|`-i` <command> = Get the signature of a command.
        """

    @root_.command(name="exit", aliases=["quit", "kys"])
    async def root_exit(self, ctx: commands.Context):
        """Exit the whole code at once. Note that this may cause issues."""
        await ctx.message.add_reaction("👋")
        exit()

    @root_.command(name="visibility")
    async def root_visibility(self, ctx: commands.Context, toggle: bool = None):
        """Toggle whether the dev command is hidden."""
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

    @root_.error
    async def root_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.TooManyArguments):
            return await send(ctx, f"`dev` has no subcommand called `{ctx.message.content.lstrip(ctx.prefix).removeprefix(ctx.command.qualified_name).strip()}`.")
        raise error

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if Settings.INVOKE_ON_EDIT:
            prefix = await self.bot.get_prefix(after)
            if before.content.startswith(prefix) and after.content.startswith(prefix):
                await after.clear_reactions()
                await self.bot.process_commands(after)
