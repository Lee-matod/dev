# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import io
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from dev.handlers import ExceptionHandler, GlobalLocals, replace_vars
from dev.interpreters import Execute

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import clean_code, codeblock_wrapper

if TYPE_CHECKING:
    from dev import types


class RootPython(Root):
    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.retain: bool = False
        self._vars: GlobalLocals | None = None

    @property
    def inst(self) -> GlobalLocals:
        if self.retain and self._vars is not None:
            return self._vars
        elif self.retain and self._vars is None:
            self._vars = GlobalLocals()
            return self._vars
        elif not self.retain and self._vars is not None:
            self._vars = None
            return GlobalLocals()
        else:
            return GlobalLocals()

    @root.command(name="retain", parent="dev")
    async def root_retain(self, ctx: commands.Context[types.Bot], toggle: bool | None = None) -> discord.Message | None:
        if toggle is None:
            translate_dict = {True: "enabled", False: "disabled"}
            await send(ctx, f"Retention is currently {translate_dict[self.retain]}.")
        elif toggle:
            if self.retain is True:
                return await send(ctx, f"Retention is already enabled.")
            self.retain = True
            await send(ctx, f"Retention has been enabled.")
        else:
            if self.retain is False:
                return await send(ctx, f"Retention is already disabled.")
            self.retain = False
            await send(ctx, f"Retention has been disabled.")

    @root.command(
        name="python",
        parent="dev",
        root_placeholder=True,
        virtual_vars=True,
        aliases=["py"],
        require_var_positional=False,
    )
    async def root_python(self, ctx: commands.Context[types.Bot], *, code: str | None = None) -> discord.Message | None:
        """
        Evaluate or execute Python code.
        You may specify `__previous__` in the code, and it'll get replaced with the previous script that was executed.
        The bot will search through the history of the channel with a limit of 25 messages.
        """
        assert ctx.command is not None
        if code is None and ctx.message.attachments:
            filed_code = await ctx.message.attachments[0].read()
            try:
                code = filed_code.decode("utf-8")
            except UnicodeDecodeError:
                return await send(ctx, "Unable to decode attachment. Make sure it is UTF-8 compatible.")
        elif code is None and not ctx.message.attachments:
            raise commands.MissingRequiredArgument(ctx.command.clean_params.get("code"))  # type: ignore
        assert code is not None
        stdout = io.StringIO()
        args: dict[str, Any] = {
            "bot": self.bot,
            "ctx": ctx,
            # Stdout redirect shouldn't be used with async code, but I still don't like print outputting to the console,
            # so this is probably the simplest workaround I could think of. Output can still be printed to the console
            # if 'file' is passed within the method.
            "print": lambda *a, **kw: print(*a, **kw, file=kw.pop("file", stdout))  # type: ignore
        }
        code = clean_code(replace_vars(code.replace("|root|", Settings.ROOT_FOLDER), Root.scope))

        async with ExceptionHandler(ctx.message):
            async for expr in Execute(code, self.inst, args):
                if expr is None:
                    continue
                elif isinstance(expr, (discord.ui.View, discord.Embed, discord.File)) or (
                        isinstance(expr, Iterable) and (
                        all(isinstance(i, discord.Embed) for i in expr) or  # type: ignore
                        all(isinstance(i, discord.File) for i in expr)  # type: ignore
                )
                ):
                    await send(ctx, expr, forced=True)  # type: ignore
                else:
                    await send(ctx, codeblock_wrapper(repr(expr), "py"), forced=True)  # type: ignore

        if out := stdout.getvalue():
            await send(ctx, codeblock_wrapper(out, "py"), forced=True)
