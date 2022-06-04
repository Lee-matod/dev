# -*- coding: utf-8 -*-

"""
dev.__main__
~~~~~~~~~~~~

Includes the root command for the dev extension, as well as other commands that do not fall under any other category.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


import discord
import os
import psutil
import sys
import time

from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import plural


class RootCommand(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.load_time = str(time.time()).split(".")[0]

    @root.group(name="dev", invoke_without_command=True, ignore_extra=False, usage="[--help|--man] [--source|-src|--sourceFile|-srcF] [--inspect|-i] <command>")
    async def root_(self, ctx: commands.Context):
        """Root command for the `dev` extension.
        Execute `dev --help [command]` for more information on a subcommand.
        `--help`|`--man` [command] = Shows a custom made help command.
        `--source`|`-src` <command> = Shows the source code of a command.
        `--sourceFile`|`-srcF` <command> = Shows the source file of a command.
        `--inspect`|`-i` <command> = Get the signature of a command as well as some information of it.
        """
        process = psutil.Process()
        version = sys.version.replace("\n", "")
        files = []
        for _, _, file in os.walk(os.getcwd()):
            for f in file:
                files.append(f)
        description = f"dev is a simple debugging, testing and editing extension for discord.py. " \
                      f"It features a total of {plural(len(root.all_commands), 'command')} which were loaded <t:{self.load_time}:R>.\n" \
                      f"\nThis process (`{process.name()} {str(__file__).split('/')[-1]}`) is currently running on Python version `{version}` on a `{sys.platform}` machine, " \
                      f"with discord version `{discord.__version__}` and dev version `{sys.modules['dev'].__version__}`.\n" \
                      f"\nRunning with a PID of `{os.getpid()}` and {plural(process.num_threads(), 'thread')} which are using " \
                      f"`{round((psutil.getloadavg()[2] / os.cpu_count()) * 100, 2)}%` of CPU power and `{round(process.memory_percent(), 2)}%` of memory.\n" \
                      f"A total of {plural(len(files), 'file')} are to be found in the current working directory, {len([file for file in files if file.endswith('.py')])} of which are Python files " \
                      f"and {(pyc_len := len([file for file in files if '.cpython-' in file]))} of which {plural(pyc_len, 'is', False)} CPython {plural(pyc_len, 'file', False)}."
        await send(ctx, description)

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
            return await send(ctx, f"`dev` has no subcommand called `{ctx.subcommand_passed}`.")
        raise error

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.command.qualified_name in self.command_uses:
            self.command_uses[ctx.command.qualified_name] += 1
        else:
            self.command_uses[ctx.command.qualified_name] = 1

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if Settings.INVOKE_ON_EDIT:
            prefix = await self.bot.get_prefix(after)
            if before.content.startswith(prefix) and after.content.startswith(prefix):
                await after.clear_reactions()
                await self.bot.process_commands(after)
