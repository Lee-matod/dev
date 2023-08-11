# -*- coding: utf-8 -*-

"""
dev.plugins.__main__
~~~~~~~~~~~~~~~~~~~~

Root command and other that do not fall under any other category.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import logging
import math
import sys
import time
from importlib import metadata as import_meta
from typing import TYPE_CHECKING

import discord
import psutil
from discord.ext import commands

from dev import root
from dev.scope import Settings
from dev.utils.functs import send
from dev.utils.utils import plural

if TYPE_CHECKING:
    from dev import types

_log = logging.getLogger(__name__)


def _as_readable(percent: float, bytes_size: int) -> str:
    if bytes_size == 0:
        return "0B"
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    power = math.floor(math.log(abs(bytes_size), 1024))
    return f"{round(bytes_size / (1024 ** power), 2)} {units[power]} ({percent:.2f}%)"


class RootCommand(root.Plugin):
    """Cog containing the parent command of this extension"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.load_time: int = int(time.time())

    @root.group("dev", global_use=True, ignore_extra=False, invoke_without_command=True)
    async def root_(self, ctx: commands.Context[types.Bot]):
        """Root command for the dev extension.

        Show a briefing of this extension, bot information, and process statistics.
        """
        process = psutil.Process()
        version = sys.version.replace("\n", "")
        load_time = f"<t:{self.load_time}:R>"

        #  Extension info
        brief = [
            f"dev {import_meta.version('dev')} was loaded {load_time} with a total of "
            f"{plural(len(self.bot.commands), 'command')}, {len(self.commands)} of which are unique to this extension.",
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
        brief.append("")
        if isinstance(self.bot, commands.AutoShardedBot):
            bot_summary = (
                f"This bot is automatically sharded with {len(self.bot.shards)} out of {self.bot.shard_count}, "
            )
        elif self.bot.shard_count:
            bot_summary = f"This bot is manually sharded with shard {self.bot.shard_id} of {self.bot.shard_count}, "
        else:
            bot_summary = f"This bot is not sharded, "
        brief.append(
            bot_summary
            + f"and can see {plural(len(self.bot.guilds), 'guild')} and {plural(len(self.bot.users), 'user')}."
        )
        translator = {True: "enabled", False: "disabled", None: "unknown"}
        intent_info: list[str] = []
        for intent in ("Members", "message_content", "presences"):
            is_enabled = getattr(self.bot.intents, intent.lower(), None)
            intent_info.append(f"{intent.replace('_', ' ')} intent is {translator[is_enabled]}")
        brief.append(
            f"Average websocket latency is {round(self.bot.latency, 2) * 1000}ms. " + "; ".join(intent_info) + "."
        )
        await send(ctx, "\n".join(brief))

    @root.command("exit", parent="dev", aliases=["quit", "close"])
    async def root_exit(self, ctx: commands.Context[types.Bot]):
        """Exit the whole code at once, or close the bot.

        If the bot does not close within 5 seconds, `sys.exit()` is called regardless.
        """
        status = 0
        await ctx.message.add_reaction("\N{WAVING HAND SIGN}")
        if ctx.invoked_with == "close":
            _log.info("Closing the bot now...")
            await self.bot.close()
            await asyncio.sleep(5)
            if self.bot.is_closed():
                return
            status = -1
        if status == -1:
            _log.debug("Bot failed to close within 5 seconds")
        _log.info("Forcing shutdown by exiting the program...")
        sys.exit(status)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        #  Some other stuff might have happened to the
        #  message which caused this event to trigger.
        #  We do not care about that stuff, so just ignore.
        if before.content == after.content:
            return
        if Settings.INVOKE_ON_EDIT:
            prefix = await self.bot.get_prefix(after)
            if isinstance(prefix, list):
                prefix = tuple(prefix)
            if before.content.startswith(prefix) and after.content.startswith(prefix):
                if before.id in root.Plugin._messages:
                    message = root.Plugin._messages.pop(before.id)
                    root.Plugin._messages[after.id] = message
                await after.clear_reactions()
                await self.bot.process_commands(after)
