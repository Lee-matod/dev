# -*- coding: utf-8 -*-

"""
dev.__main__
~~~~~~~~~~~~

Root command and other that do not fall under any other category.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import math
import sys
import time
from importlib import metadata as import_meta
from typing import TYPE_CHECKING

import discord
import psutil
from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import plural

if TYPE_CHECKING:
    from dev import types


def _as_readable(percent: float, bytes_size: int) -> str:
    if bytes_size == 0:
        return "0B"
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    power = math.floor(math.log(abs(bytes_size), 1024))
    return f"{round(bytes_size / (1024 ** power), 2)} {units[power]} ({percent * 100:.2f}%)"


class RootCommand(Root):
    """Cog containing the parent command of this extension"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.load_time: str = str(round(time.time()))

    @root.group(
        name="dev",
        global_use=True,
        ignore_extra=True,
        invoke_without_command=True,
        usage="[--help|--man] [--source|-src] [--file|--f] [--inspect|-i] <command>",
    )
    async def root_(self, ctx: commands.Context[types.Bot]):
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
        load_time = f"<t:{self.load_time}:R>"

        #  Extension info
        brief = [
            f"dev {import_meta.version('dev')} was loaded {load_time} with a total of "
            f"{plural(len(self.commands), 'command')} which are unique to this extension.",
            "",
        ]
        with process.oneshot():
            process.cpu_percent()
            try:
                discord_version = import_meta.version("discord.py")
            except import_meta.PackageNotFoundError:
                discord_version = discord.__version__
            #  Process and version info
            brief.append(
                f"Process `{process.name()}` started <t:{round(process.create_time())}:R> on `Python {version}` with "
                f"discord.py v{discord_version}."
            )
            brief.append(
                f"Running on PID {process.pid} with {plural(process.num_threads(), 'thread')} "
                f"on a `{sys.platform}` machine."
            )
            brief.append("")

            cpu_percent = process.cpu_percent()
            cpu_count = psutil.cpu_count()
            mem = process.memory_full_info()

            physical = _as_readable(process.memory_percent(), mem.rss)
            virtual = _as_readable(process.memory_percent("vms"), mem.vms)
            unique = _as_readable(process.memory_percent("uss"), mem.uss)
            brief.append(
                f"Using {cpu_percent:.2f}% of total CPU power with {cpu_count or 'unknown'} "
                f"logical {plural(cpu_count or 2, 'CPU', False)}, {physical} of physical memory and "
                f"{virtual} of virtual memory, {unique} of which is unique to this process."
            )
        await send(ctx, "\n".join(brief))

    @root.command(name="exit", parent="dev", aliases=["quit", "kys"])
    async def root_exit(self, ctx: commands.Context[types.Bot]):
        """Exit the whole code at once. Note that this may cause issues.
        This uses the :meth:`exit` method, so beware!
        """
        await ctx.message.add_reaction("\U0001f44b")
        sys.exit(0)

    @root.command(name="visibility", parent="dev")
    async def root_visibility(self, ctx: commands.Context[types.Bot], toggle: bool | None = None):
        """Toggle whether the dev command is hidden.
        Pass no arguments to check current status
        """
        root_command = self.commands.get("dev")
        assert root_command is not None
        if toggle:
            if root_command.hidden:
                return await send(ctx, "`dev` is already hidden.")
            root_command.hidden = True
            await ctx.message.add_reaction("\u2502")
        elif toggle is None:
            translate = {True: "hidden", False: "visible"}
            await send(ctx, f"`dev` is currently {translate.get(root_command.hidden)}.")
        else:
            if not root_command.hidden:
                return await send(ctx, "`dev` is already visible.")
            root_command.hidden = False
            await ctx.message.add_reaction("\u2502")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        #  There was an issue that occurred when using dev sh.
        #  Commands would get reinvoked for some reason, and caused
        #  some pretty annoying inputs. This is just an early exit
        #  that fixes the issue.
        if before.content == after.content:
            return
        if Settings.invoke_on_edit:
            prefix = await self.bot.get_prefix(after)
            if isinstance(prefix, list):
                prefix = tuple(prefix)
            if before.content.startswith(prefix) and after.content.startswith(prefix):
                if before.id in Root.cached_messages:
                    message = Root.cached_messages.pop(before.id)
                    Root.cached_messages[after.id] = message
                await after.clear_reactions()
                await self.bot.process_commands(after)
