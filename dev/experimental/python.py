# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import io
import ast
import inspect
import contextlib

import discord
from discord.ext import commands
from typing import Dict, Any, AsyncGenerator, Optional

from dev.converters import __previous__
from dev.handlers import ExceptionHandler, replace_vars

from dev.utils.startup import Settings
from dev.utils.functs import clean_code, send
from dev.utils.baseclass import root, Root, GlobalLocals


CODE_TEMPLATE = """
async def _executor_func({0}):
    import asyncio
    import discord
    from discord.ext import commands
    
    try:
        pass
    finally:
        _self_variables.update(locals())
"""


class Sender:
    def __init__(self, iterator: AsyncGenerator):
        self.iterator = iterator
        self.value = None

    def __aiter__(self):
        return self._internal(self.iterator.__aiter__())

    async def _internal(self, iterator: AsyncGenerator):
        try:
            while True:

                value = await iterator.asend(self.value)
                self.value = None
                yield self.set_send_value, value
        except StopAsyncIteration:
            pass

    def set_send_value(self, value):
        self.value = value


class Executor:
    def __init__(self, code: str, global_locals: GlobalLocals, args: Dict[str, Any]):
        self.args_name = ["_self_variables"]
        self.args_value = [global_locals]
        self.vars = global_locals
        for name, value in args.items():
            self.args_name.append(name)
            self.args_value.append(value)
        self.code = wrapper(code, ", ".join(self.args_name))

    async def __aiter__(self):
        exec(compile(self.code, "<func>", "exec"), self.vars.globals, self.vars.locals)
        func = self.vars.locals.get("_executor_func", None) or self.vars.globals["_executor_func"]
        if inspect.isasyncgenfunction(func):
            func_g = func
            async for sender, result in Sender(func_g(*self.args_value)):
                sender((yield result))  # type: ignore
        else:
            func_a = func
            yield await func_a(*self.args_value)


class RootPython(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.retain: bool = False
        self.vars: Optional[GlobalLocals] = None

    @root.command(name="retain", parent="dev")
    async def root_retain(self, ctx: commands.Context, toggle: bool = None):
        if toggle is None:
            translate_dict = {True: "enabled", False: "disabled"}
            await send(ctx, f"Retention is currently {translate_dict[self.retain]}.")
        elif toggle:
            if self.retain is True:
                return await send(ctx, f"Retention is already enabled.")
            self.retain = True
            self.vars = GlobalLocals()
            await send(ctx, f"Retention has been enabled.")
        else:
            if self.retain is False:
                return await send(ctx, f"Retention is already disabled.")
            self.retain = False
            self.vars = None
            await send(ctx, f"Retention has been disabled.")

    @root.command(name="python", parent="dev", supports_virtual_vars=True, aliases=["py"])
    async def root_python(self, ctx: commands.Context, *, code: str):
        """Evaluate or execute Python code.
        When specifying a script, some placeholder texts can be set.
        `__previous__` = This is replaced with the previous script that was executed. The bot will search through the history of the channel with a limit of 200 messages.
        `|root|` = Replaced with the root folder specified in `settings["folder"]["root_folder"]`.
        """
        args = {
            "bot": self.bot,
            "ctx": ctx,
        }
        stdout = io.StringIO()
        code = clean_code(replace_vars(code.replace("|root|", Settings.ROOT_FOLDER)))

        async with ExceptionHandler(ctx.message):
            with contextlib.redirect_stdout(stdout):
                executor = Executor(code, self.vars if self.retain else GlobalLocals(), args)
                async for sender, result in Sender(executor):  # type: ignore
                    if result is None:
                        continue

                    sender(await send(ctx, is_py_bt=True, embed=discord.Embed(title="Output", description=result, color=discord.Color.green())))  # type: ignore
                if stdout.getvalue():
                    await send(ctx, is_py_bt=True, embed=discord.Embed(title="Console Output", description=stdout.getvalue(), color=discord.Color.green()))


def wrapper(code: str, args: str = ''):
    parsed_code: ast.Module = ast.parse(code)
    parsed_template: ast.Module = ast.parse(CODE_TEMPLATE.format(args))
    definition = parsed_template.body[-1]
    try_finally = definition.body[-1]  # type: ignore
    try_finally.body.extend(parsed_code.body)
    ast.fix_missing_locations(parsed_template)
    ast.NodeTransformer().generic_visit(try_finally)
    last = try_finally.body[-1]
    if not isinstance(last, ast.Expr):
        return parsed_template

    if not isinstance(last.value, ast.Yield):
        yield_stmt = ast.Yield(last.value)
        ast.copy_location(yield_stmt, last)
        yield_expr = ast.Expr(yield_stmt)
        ast.copy_location(yield_expr, last)
        try_finally.body[-1] = yield_expr
    return parsed_template


