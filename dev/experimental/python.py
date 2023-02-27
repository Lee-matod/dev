# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import contextlib
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from dev import root
from dev.handlers import ExceptionHandler, GlobalLocals, RelativeStandard, replace_vars
from dev.interpreters import Execute
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import clean_code, codeblock_wrapper

if TYPE_CHECKING:
    from types import TracebackType

    from dev import types


def _maybe_raw_send(item: Any, /) -> bool:
    if isinstance(item, (discord.Embed, discord.File, discord.ui.View)):
        return True
    if isinstance(item, Sequence) and item:
        if len(item[:11]) > 10:  # type: ignore # Early return check
            return False
        same_type = all(isinstance(i, type(item[0])) for i in item)  # type: ignore
        if not same_type:
            return False
        if type(item[0]) in (discord.Embed, discord.File):  # type: ignore
            return True
    return False


class RootPython(root.Container):
    """Python evaluation commands"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.retain: bool = False
        self._vars: GlobalLocals | None = None
        self.last_output: Any = None

    @property
    def repl(self) -> GlobalLocals:
        """Get the scope that a REPL session will use"""
        if self.retain and self._vars is not None:
            return self._vars
        if self.retain and self._vars is None:
            self._vars = GlobalLocals()
            return self._vars
        if not self.retain and self._vars is not None:
            self._vars = None
            return GlobalLocals()
        return GlobalLocals()

    @root.command(name="retain", parent="dev")
    async def root_retain(self, ctx: commands.Context[types.Bot], toggle: bool | None = None):
        """Toggle whether variables from REPL sessions should be kept for any future ones."""
        if toggle is None:
            translate_dict = {True: "enabled", False: "disabled"}
            await send(ctx, f"Retention is currently {translate_dict[self.retain]}.")
        elif toggle:
            if self.retain is True:
                return await send(ctx, "Retention is already enabled.")
            self.retain = True
            await send(ctx, "Retention has been enabled.")
        else:
            if self.retain is False:
                return await send(ctx, "Retention is already disabled.")
            self.retain = False
            await send(ctx, "Retention has been disabled.")

    @root.command(
        name="python",
        parent="dev",
        root_placeholder=True,
        virtual_vars=True,
        aliases=["py"],
        require_var_positional=False,
    )
    async def root_python(self, ctx: commands.Context[types.Bot], *, code: str | None = None):
        """Evaluate or execute Python code.
        Just like in any REPL session, you can use the '_' to gain access to the
        last value outputed by the previous session.
        """
        assert ctx.command is not None
        if code is None and ctx.message.attachments:
            filed_code = await ctx.message.attachments[0].read()
            try:
                code = filed_code.decode("utf-8")
            except UnicodeDecodeError:
                return await send(
                    ctx,
                    "Unable to decode attachment. Make sure it is UTF-8 compatible.",
                )
        elif code is None and not ctx.message.attachments:
            raise commands.MissingRequiredArgument(ctx.command.clean_params["code"])
        assert code is not None

        args: dict[str, Any] = {"bot": self.bot, "ctx": ctx}
        if self.last_output is not None:
            args["_"] = self.last_output
        code = clean_code(replace_vars(code.replace("|root|", Settings.root_folder), self.scope))
        output: list[str] = []

        async def on_error(
            exc_type: type[Exception] | None,
            exc_val: Exception | None,
            exc_tb: TracebackType | None,
        ) -> None:
            if handler.debug or exc_type is None or exc_val is None or exc_tb is None:
                return
            if isinstance(exc_val, (SyntaxError, ImportError, NameError, AttributeError)):
                await send(ctx, codeblock_wrapper(f"{exc_type.__name__}: {exc_val}", "py"))

        reader_task: asyncio.Task[None] = self.bot.loop.create_task(self._on_update(ctx, output))
        executor = Execute(code, self.repl, args)
        stdout = RelativeStandard(
            callback=lambda s: output.append(s),
            filename=executor.filename,
        )
        stderr = RelativeStandard(
            sys.__stderr__,
            lambda s: output.append(s),
            filename=executor.filename,
        )
        try:
            async with ExceptionHandler(ctx.message, on_error=on_error) as handler:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    async for expr in executor:
                        if expr is None:
                            continue
                        if _maybe_raw_send(expr):
                            await send(ctx, expr, forced=True)
                        else:
                            await send(ctx, codeblock_wrapper(repr(expr), "py"), forced=True)
                    await asyncio.sleep(1)
            try:
                self.last_output = expr  # type: ignore
            except NameError:
                self.last_output = None
        finally:
            reader_task.cancel()

    async def _on_update(self, ctx: commands.Context[types.Bot], view: list[str], /) -> None:
        current = len(view)
        if view:
            await send(
                ctx,
                "[stdout/stderr]\n" + codeblock_wrapper("".join(view).strip("\n"), "py"),
            )
        while True:
            if current != len(view):
                await send(
                    ctx,
                    "[stdout/stderr]\n" + codeblock_wrapper("".join(view).strip("\n"), "py"),
                )
            await asyncio.sleep(0)
