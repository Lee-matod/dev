# -*- coding: utf-8 -*-

"""
dev.experimental.sh
~~~~~~~~~~~~~~~~~~~

Shell interpreter commands.

:copyright: Copyright 2023 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dev.interpreters import ShellSession
from dev.components.views import SigKill

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.utils import clean_code

if TYPE_CHECKING:
    from dev import types


class RootShell(Root):
    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.active_shell_sessions: list[int] = []

    @root.command(name="shell", parent="dev", aliases=["sh", "cmd", "bash", "ps"])
    async def root_shell(self, ctx: commands.Context[types.Bot], *, script: clean_code):  # type: ignore
        if ctx.author.id in self.active_shell_sessions:
            return await send(ctx, "A shell session is already active, please close it before starting a new one.")
        self.active_shell_sessions.append(ctx.author.id)
        shell = ShellSession()
        with shell(script) as process:  # type: ignore
            _, paginator = await send(
                ctx,
                shell.raw,
                SigKill(process),
                forced_pagination=False,
                paginator=None
            )
            shell.paginator = paginator
            await process.run_until_complete(ctx)

        def check(msg: discord.Message) -> bool:
            return (
                    msg.author == ctx.author
                    and msg.channel == ctx.channel
                    and msg.content.startswith(shell.interface.lower())
            )

        while not shell.terminated and not process.is_alive:
            try:
                message: discord.Message = await self.bot.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                self.active_shell_sessions.remove(ctx.author.id)
                return await send(
                    ctx,
                    shell.set_exit_message(f"Return code: `{process.close_code}`"),
                    forced_pagination=False,
                    paginator=shell.paginator
                )
            with shell(message.content[len(shell.interface):].strip()) as process:
                await process.run_until_complete(ctx)
        await send(
            ctx,
            shell.set_exit_message(f"Return code: `{process.close_code}`"),
            forced_pagination=False,
            paginator=shell.paginator
        )
        self.active_shell_sessions.remove(ctx.author.id)

