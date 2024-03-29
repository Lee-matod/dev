# -*- coding: utf-8 -*-

"""
dev.plugins.python
~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import contextlib
import re
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple, Type

import discord
from discord.ext import commands

from dev import root
from dev.converters import str_ints
from dev.handlers import ExceptionHandler, RelativeStandard, replace_vars
from dev.interpreters import Execute
from dev.scope import Scope, Settings
from dev.types import Annotated
from dev.utils.functs import send
from dev.utils.utils import clean_code, codeblock_wrapper

if TYPE_CHECKING:
    from types import TracebackType

    from dev import types

try:
    import black
    from black.mode import TargetVersion
    from black.parsing import InvalidInput
except ModuleNotFoundError:
    _HASBLACK: bool = False  # type: ignore
else:
    _HASBLACK: bool = True

_comment = r"^#[ ]*black:[ ]*"
_BLACK_BOOL = re.compile(
    _comment
    + r"(enable|disable)[ ]*=[ ]*(string-normalization|pyi|skip-source-first-line|magic-trailing-comma|preview)$",
    re.MULTILINE,
)
_BLACK_LINELENGTH = re.compile(_comment + r"line-length=([0-9]+)$", re.MULTILINE)
_BLACK_PYVERSION = re.compile(_comment + r"target-versions?=([0-9, ]+)$", re.MULTILINE)


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


class RootPython(root.Plugin):
    """Python evaluation commands"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self._vars: Optional[Scope] = None
        self.last_output: Any = None

    @root.command(
        "python", parent="dev", root_placeholder=True, virtual_vars=True, aliases=["py"], require_var_positional=False
    )
    async def root_python(self, ctx: commands.Context[types.Bot], *, code: Optional[str] = None):
        """Evaluate or execute Python code.

        Just like in any REPL session, you can use '_' to gain access to the last value evaluated.
        Sending a file instead of using a codeblock is also supported.

        Parameters
        ----------
        code: Optional[:class:`str`]
            The code to evaluate. If this is not given, then a file is expected.
        """
        assert ctx.command is not None
        if code is None and ctx.message.attachments:
            filed_code = await ctx.message.attachments[0].read()
            try:
                code = filed_code.decode("utf-8")
            except UnicodeDecodeError:
                return await send(ctx, "Unable to decode attachment. Make sure it is UTF-8 compatible.")
        elif code is None and not ctx.message.attachments:
            raise commands.MissingRequiredArgument(ctx.command.clean_params["code"])
        assert code is not None

        args: Dict[str, Any] = {"bot": self.bot, "ctx": ctx}
        if self.last_output is not None:
            args["_"] = self.last_output
        code = clean_code(replace_vars(code.replace("|root|", Settings.ROOT_FOLDER), self.scope))
        output: List[str] = []

        async def on_error(exc_type: Type[Exception], exc_val: Exception, _: Optional[TracebackType]) -> None:
            if isinstance(exc_val, (SyntaxError, ImportError, NameError, AttributeError)):
                await send(ctx, codeblock_wrapper(f"{exc_type.__name__}: {exc_val}", "py"))

        reader_task: asyncio.Task[None] = self.bot.loop.create_task(self._on_update(ctx, output))
        executor = Execute(code, self._get_scope(), args)
        stdout = RelativeStandard(callback=lambda s: output.append(s), filename=executor.filename)
        stderr = RelativeStandard(sys.__stderr__, lambda s: output.append(s), filename=executor.filename)
        exception_handler: ExceptionHandler[Literal[False]] = ExceptionHandler(ctx.message, on_error=on_error)
        try:
            async with exception_handler:
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

    def _get_scope(self) -> Scope:
        retention = Settings.RETAIN
        if retention and self._vars is not None:
            return self._vars
        if retention and self._vars is None:
            self._vars = Scope()
            return self._vars
        if not retention and self._vars is not None:
            self._vars = None
            return Scope()
        return Scope()

    if _HASBLACK:

        @root.command("black", parent="dev", require_var_positional=True)
        async def root_black(self, ctx: commands.Context[types.Bot], *, code: Annotated[str, clean_code]):
            """Format a piece of code using the uncompromising black formatter.

            Adjust the formatter to your liking by using comments
            (e.g. `# black: line-length=120`, `# black: disable=string-normalization`).

            Enabling or disabling multiple settings in a single comment is not supported.

            This feature is only available if the black module is installed and detected.

            Parameters
            ----------
            code: :class:`str`
                The code to format.
            """
            fm = black.FileMode()
            pyversion = _BLACK_PYVERSION.search(code)
            linelength = _BLACK_LINELENGTH.search(code)
            bool_settings: List[Tuple[str, bool]] = [
                (setting, toggled == "enable") for toggled, setting in _BLACK_BOOL.findall(code)
            ]
            if pyversion is not None:
                versions: Set[int] = set(str_ints(pyversion.group(1).replace(".", "")))
                target_versions: Set[TargetVersion] = set()
                for ver in versions:
                    try:
                        obj = TargetVersion[f"PY{ver}"]
                    except ValueError:
                        continue
                    target_versions.add(obj)
                fm.target_versions = target_versions
            if linelength is not None:
                fm.line_length = int(linelength.group(1))
            for setting, toggled in bool_settings:
                setattr(fm, setting.replace("-", "_"), toggled)
            try:
                formatted = black.format_str(code, mode=fm)
            except InvalidInput as exc:
                return await send(ctx, f"Syntax error: {exc}")
            await send(ctx, codeblock_wrapper(formatted, "py"))

    async def _on_update(self, ctx: commands.Context[types.Bot], view: List[str], /) -> None:
        current = len(view)
        if view:
            await send(ctx, "[stdout/stderr]\n" + codeblock_wrapper("".join(view).strip("\n"), "py"))
        while True:
            if current != len(view):
                await send(ctx, "[stdout/stderr]\n" + codeblock_wrapper("".join(view).strip("\n"), "py"))
            await asyncio.sleep(0)
