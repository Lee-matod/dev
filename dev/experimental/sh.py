# -*- coding: utf-8 -*-

"""
dev.experimental.sh
~~~~~~~~~~~~~~~~~~~

Shell interpreter commands.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Annotated

import discord
from discord.ext import commands

from dev.interpreters import ShellSession
from dev.utils import root
from dev.utils.functs import send
from dev.utils.utils import clean_code

if TYPE_CHECKING:
    from dev import types


class RootShell(root.Container):
    """Shell interpreter commands"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.active_shell_sessions: list[int] = []

    @root.command(name="shell", parent="dev", aliases=["sh", "cmd", "bash", "ps"])
    async def root_shell(self, ctx: commands.Context[types.Bot], *, script: Annotated[str, clean_code]):
        """Invoke and evaluate shell commands.
        After initiating a new session, all new commands must be prefixed with the interface's
        prefix (e.g `$` for bash/shell, `PS>` for powershell, etc).
        Type `exit` to quit the session.
        """
        if ctx.author.id in self.active_shell_sessions:
            return await send(
                ctx,
                "A shell session is already active, please close it before starting a new one.",
            )
        self.active_shell_sessions.append(ctx.author.id)
        shell = ShellSession()
        try:
            with shell(script) as process:
                await process.run_until_complete(ctx)

            def check(msg: discord.Message) -> bool:
                return (
                    msg.author == ctx.author
                    and msg.channel == ctx.channel
                    and msg.content.startswith(shell.interface.lower())
                )

            while not shell.terminated and not process.is_alive:
                try:
                    message: discord.Message = await self.bot.wait_for(  # type: ignore
                        "message", check=check, timeout=30
                    )
                except asyncio.TimeoutError:
                    return await send(
                        ctx,
                        shell.set_exit_message(f"Return code: `{process.close_code}`"),
                        forced_pagination=False,
                        paginator=shell.paginator,
                    )
                with shell(message.content[len(shell.interface) :].strip()) as process:
                    await process.run_until_complete(ctx)
            await send(
                ctx,
                shell.set_exit_message(f"Return code: `{process.close_code}`"),
                forced_pagination=False,
                paginator=shell.paginator,
            )
        finally:
            self.active_shell_sessions.remove(ctx.author.id)
