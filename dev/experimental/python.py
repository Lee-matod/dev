# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import ast
import inspect
import io
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, AsyncGenerator, Optional, TypeVar

import discord
from discord.ext import commands

from dev.converters import __previous__
from dev.handlers import ExceptionHandler, GlobalLocals, replace_vars

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings
from dev.utils.utils import clean_code, codeblock_wrapper

if TYPE_CHECKING:
    from dev import types


T = TypeVar("T")


CODE_TEMPLATE = """
async def _executor({0}):
    import asyncio

    import discord
    from discord.ext import commands

    import dev

    try:
        pass
    finally:
        _self_variables.update(locals())
    """


class Execute:
    def __init__(self, code: str, global_locals: GlobalLocals, args: dict[str, Any]) -> None:
        self.args_name = ["_self_variables", *args.keys()]
        self.args_value = [global_locals, *args.values()]
        self.code = code
        self.vars = global_locals

    async def __aiter__(self) -> AsyncGenerator[Any, Any]:
        exec(compile(self.wrapper(), "<func>", "exec"), self.vars.globals, self.vars.locals)
        func = self.vars.get("_executor")
        if inspect.isasyncgenfunction(func):
            async for result in func(*self.args_value):
                yield result
        else:
            yield await func(*self.args_value)

    def wrapper(self) -> ast.Module:
        code = ast.parse(self.code)
        function: ast.Module = ast.parse(CODE_TEMPLATE.format(", ".join(self.args_name)))
        function.body[-1].body[-1].body.extend(code.body)  # type: ignore
        ast.fix_missing_locations(function)
        ast.NodeTransformer().generic_visit(function.body[-1].body[-1])  # type: ignore
        expressions = function.body[-1].body[-1].body  # type: ignore

        for index, expr in enumerate(reversed(expressions), start=1):
            if not isinstance(expr, ast.Expr):
                return function

            if not isinstance(expr.value, ast.Yield):
                yield_stmt = ast.Yield(expr.value)
                ast.copy_location(yield_stmt, expr)  # type: ignore
                yield_expr = ast.Expr(yield_stmt)
                ast.copy_location(yield_expr, expr)  # type: ignore
                function.body[-1].body[-1].body[-index] = yield_expr  # type: ignore
        return function


class RootPython(Root):
    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.retain: bool = False
        self._vars: Optional[GlobalLocals] = None

    @property
    def scope(self) -> GlobalLocals:
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
    async def root_retain(self, ctx: commands.Context, toggle: Optional[bool] = None) -> Optional[discord.Message]:
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
    async def root_python(self, ctx: commands.Context, *, code: Optional[str] = None) -> Optional[discord.Message]:
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
        args = {
            "bot": self.bot,
            "ctx": ctx,
            # Stdout redirect shouldn't be used with async code, but I still don't like print outputting to the console,
            # so this is probably the simplest workaround I could think of. Output can still be printed to the console
            # if 'file' is passed within the method.
            "print": lambda *a, **kw: print(*a, **kw, file=stdout) if "file" not in kw else print(*a, **kw)
        }
        code = await __previous__(
            ctx,
            f"{' '.join(ctx.invoked_parents)} {ctx.invoked_with}",
            clean_code(replace_vars(code.replace("|root|", Settings.ROOT_FOLDER), Root.scope))
        )

        async with ExceptionHandler(ctx.message):
            async for expr in Execute(code, self.scope, args):
                if expr is None:
                    continue
                await send(ctx, self._check(expr), forced=True)

        if out := stdout.getvalue():
            await send(ctx, codeblock_wrapper(out, "py"), forced=True)

    def _check(self, item: T) -> T | str:  # noqa  # PyCharm silently complains that this should be a function instead
        if isinstance(item, (discord.ui.View, discord.Embed, discord.File)):
            return item
        elif isinstance(item, Iterable):
            if all(isinstance(i, discord.Embed) for i in item) or all(isinstance(i, discord.File) for i in item):
                return item
        return codeblock_wrapper(repr(item), "py")
