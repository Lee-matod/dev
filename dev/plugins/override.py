# -*- coding: utf-8 -*-

"""
dev.plugins.override
~~~~~~~~~~~~~~~~~~~~

Override or overwrite bot commands.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import ast
import inspect
import textwrap
from typing import TYPE_CHECKING, Any, List, Literal, Optional

from discord.ext import commands
from discord.ext.commands._types import _BaseCommand  # type: ignore

from dev import root
from dev.converters import MessageCodeblock, codeblock_converter
from dev.handlers import ExceptionHandler
from dev.interpreters import Execute
from dev.scope import Scope
from dev.types import Annotated
from dev.utils.functs import send

if TYPE_CHECKING:
    from dev import types


class RootOverride(root.Plugin):
    """Override and overwrite commands"""

    @root.group(
        "override",
        parent="dev",
        invoke_without_command=True,
        require_var_positional=True,
        usage="<command_name> <code>",
    )
    async def root_override(
        self, ctx: commands.Context[types.Bot], *, command_code: Annotated[MessageCodeblock, codeblock_converter]
    ):
        """Override the current callback and attributes of a command.

        The arguments should consist of the qualified name of the command to override, and the new callback,
        which should be inside a codeblock. Decorators should be included.

        Parameters
        ----------
        command_code: :class:`MessageCodeblock`
            The qualified name of the command and its new callback.
        """
        command_string, script = command_code.content, command_code.codeblock
        if not command_string or not script:
            return await send(ctx, "Malformed arguments were given.")
        original: Optional[types.Command] = self.bot.get_command(command_string)
        if original is None:
            return await send(ctx, f"Command `{command_string}` not found.")
        original_kwargs = original.__original_kwargs__

        def on_error(*_: Any):
            try:
                self.bot.add_command(original)
            except commands.CommandRegistrationError:
                pass

        exception_handler: ExceptionHandler[Literal[False]] = ExceptionHandler(ctx.message, on_error)
        async with exception_handler:
            ast_parse = ast.parse(script)
            async_callback = isinstance(ast_parse.body[-1], ast.AsyncFunctionDef)
            imports_exprs = len([expr for expr in ast_parse.body if isinstance(expr, (ast.Import, ast.ImportFrom))])
            if not async_callback or len(ast_parse.body) > imports_exprs + 1:
                return await send(
                    ctx, "The body of the script should consist of a single asynchronous function callback."
                )
            ast_func: ast.AsyncFunctionDef = ast_parse.body[-1]  # type: ignore
            scope = Scope(original.callback.__globals__)
            if original.cog is None:
                code = f"{script}\nreturn {ast_func.name}"
            else:
                # Getting cog commands to register properly is pretty tricky.
                # discord.py uses inspect to get function parameters, which means that
                # I have to attach the callback to a class somehow.
                code = (
                    "from discord.ext import commands\n"
                    f"class _TempCogSimulator(commands.Cog):\n{textwrap.indent(script, '    ')}\n"
                    f"return _TempCogSimulator.{ast_func.name}"
                )
            executor = Execute(code, scope, {"bot": self.bot} if original.cog is None else {})
            self.bot.remove_command(original.qualified_name)
            async for obj in executor:
                if not isinstance(obj, _BaseCommand):
                    try:
                        obj = type(original)(obj, **original_kwargs)
                    except TypeError:
                        self.bot.add_command(original)
                        return await send(
                            ctx,
                            "Could not convert callback to command. "
                            f"`{type(obj)}` is incompatible with `{type(original)}`.",
                        )
                if type(obj) != type(original):
                    self.bot.remove_command(obj.qualified_name)
                    self.bot.add_command(original)
                    return await send(
                        ctx,
                        f"Original command was of type `{type(original).__name__}`, "
                        f"but modified is `{type(obj).__name__}`.",
                    )
                obj: types.Command
                if original.parent is not None:
                    if obj not in original.parent.commands:
                        original.parent.add_command(obj)
                else:
                    if obj not in self.bot.commands:
                        self.bot.add_command(obj)
                if isinstance(original, commands.Group):
                    assert isinstance(obj, commands.Group)
                    for child in original.commands:
                        obj.add_command(child)
                if original.cog is not None:
                    obj.cog = original.cog
                return await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")

    @root.group(
        "overwrite",
        parent="dev",
        invoke_without_command=True,
        require_var_positional=True,
        usage="<command_name> <code>",
    )
    async def root_overwrite(
        self, ctx: commands.Context[types.Bot], *, command_code: Annotated[MessageCodeblock, codeblock_converter]
    ):
        """Overwrite the source code of a command.

        The arguments should consist of the qualified name of the command to overwrite, and the new callback,
        which should be inside a codeblock. Decorators should be included.

        Similar to `dev override`, but this edits the source code of the command.

        Parameters
        ----------
        command_code: :class:`MessageCodeblock`
            The qualified name of the command and its new callback.
        """
        command_string, script = command_code.content, command_code.codeblock
        if not command_string or not script:
            return await send(ctx, "Malformed arguments were given.")
        origin: Optional[types.Command] = self.bot.get_command(command_string)
        if origin is None:
            return await send(ctx, f"Command `{command_string}` not found.")
        directory = inspect.getsourcefile(origin.callback)
        if directory is None:
            return await send(ctx, "Could not find source.")
        lines, line_no = inspect.getsourcelines(origin.callback)
        line_no -= 1
        exception_handler: ExceptionHandler[Literal[False]] = ExceptionHandler(ctx.message)
        async with exception_handler:
            parsed = ast.parse(script)
            if len(parsed.body) != 1 or not isinstance(parsed.body[0], ast.AsyncFunctionDef):
                return await send(
                    ctx, "The body of the script should consist of a single asynchronous function callback."
                )
        script_lines = script.split("\n")
        indentation = 0
        for char in lines[0]:
            if char == " ":
                indentation += 1
            else:
                break
        code_split: List[str] = [f"{' ' * indentation}{line}" for line in script_lines]
        with open(directory) as fp:
            file_lines = fp.readlines()
        start, end = line_no, line_no + (len(lines) - 1)
        # make sure that we have the correct amount of lines necessary to include the new script
        if len(code_split) > len(lines):
            with open(directory, "w") as fp:
                file_lines[end] += "\n" * (len(code_split) - len(lines))
                end += len(code_split) - len(lines)
                fp.writelines(file_lines)
            with open(directory) as fp:
                # since we edited the file, we have to get our new set of lines
                file_lines = fp.readlines()
        count = 0
        for line in range(start, end + 1):
            try:
                file_lines[line] = code_split[count] + "\n"
                count += 1
            except IndexError:
                # deal with any extra lines, so we don't get a huge whitespace
                file_lines[line] = ""
        with open(directory, "w") as fp:
            fp.writelines(file_lines)
        await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")
