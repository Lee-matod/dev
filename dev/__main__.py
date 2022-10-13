# -*- coding: utf-8 -*-

"""
dev.__main__
~~~~~~~~~~~~

Root command and other that do not fall under any other category.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import os
import sys
import time
from typing import Optional

import discord
import psutil
from discord.ext import commands

from dev.handlers import optional_raise

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import plural


class RootCommand(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.load_time: str = str(round(time.time()))

    @root.group(
        name="dev",
        global_use=True,
        ignore_extra=False,
        invoke_without_command=True,
        usage="[--help|--man] [--source|-src] [--file|--f] [--inspect|-i] <command>"
    )
    async def root_(self, ctx: commands.Context):
        """Root command for the `dev` extension.
        Gives a briefing of the dev extension, as well as process statistics.
        Execute `dev --help [command]` for more information on a subcommand.
        `--help`|`--man` [command] = Shows a custom made help command.
        `--source`|`-src` <command> = Shows the source code of a command.
        `--file`|`-f` <command> = Shows the source file of a command.
        `--inspect`|`-i` <command> = Get the signature of a command as well as some information of it.
        """
        process = psutil.Process()
        version = sys.version.replace("\n", "")
        description = f"dev is a simple debugging, testing and editing extension for discord.py. " \
                      f"It features a total of {plural(len(self.commands), 'command')} which were loaded <t:{self.load_time}:R>.\n" \
                      f"\nThis process (`{process.name()} {str(__file__).split('/')[-1]}`) is currently running on Python version `{version}` on a `{sys.platform}` machine, " \
                      f"with discord version `{discord.__version__}` and dev version `{sys.modules['dev'].__version__}`.\n" \
                      f"Running with a PID of `{os.getpid()}` and {plural(process.num_threads(), 'thread')} which are using " \
                      f"`{round((psutil.getloadavg()[2] / os.cpu_count()) * 100, 2)}%` of CPU power and `{round(process.memory_percent(), 2)}%` of memory.\n"
        await send(ctx, description)

    @root.command(name="exit", parent="dev", aliases=["quit", "kys"])
    async def root_exit(self, ctx: commands.Context):
        """Exit the whole code at once. Note that this may cause issues.
        This uses the :meth:`exit` method, so beware!
        """
        await ctx.message.add_reaction("👋")
        exit()

    @root.command(name="visibility", parent="dev")
    async def root_visibility(self, ctx: commands.Context, toggle: Optional[bool] = None):
        """Toggle whether the dev command is hidden.
        Pass no arguments to check current status
        """
        root_command = self.commands.get("dev")
        if toggle:
            if root_command.hidden:
                return await send(ctx, f"`dev` is already hidden.")
            root_command.hidden = True
            await ctx.message.add_reaction("☑")
        elif toggle is None:
            translate = {True: "hidden", False: "visible"}
            await send(ctx, f"`dev` is currently {translate.get(root_command.hidden)}.")
        else:
            if not root_command.hidden:
                return await send(ctx, f"`dev` is already visible.")
            root_command.hidden = False
            await ctx.message.add_reaction("☑")

    @root_.error
    async def root_error(self, ctx: commands.Context, exception: commands.CommandError):
        if isinstance(exception, commands.TooManyArguments):
            return await send(
                ctx,
                f"`{ctx.invoked_with}` has no subcommand "
                f"`{ctx.message.content.removeprefix(ctx.prefix + ctx.invoked_with).strip()}`."
            )
        optional_raise(ctx, exception)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if Settings.INVOKE_ON_EDIT:
            prefix = await self.bot.get_prefix(after)
            if callable(prefix):
                prefix = prefix(self.bot, after)
            if before.content.startswith(prefix) and after.content.startswith(prefix):
                if before.id in Root.cached_messages.keys():
                    message = Root.cached_messages.pop(before.id)
                    Root.cached_messages[after.id] = message
                await after.clear_reactions()
                await self.bot.process_commands(after)
