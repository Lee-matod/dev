# -*- coding: utf-8 -*-

"""
dev.handlers
~~~~~~~~~~~~~~~

Handlers and custom converters that are used in the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from typing import *

import re
import asyncio
import discord

from discord.ext import commands
from traceback import format_exception

from dev.utils.utils import local_globals


__all__ = (
    "ExceptionHandler",
    "StringCodeblockConverter",
    "VirtualVarReplacer"
)


class ExceptionHandler:
    error: Tuple[Exception, str] = ()
    debug: bool = False

    def __init__(self, message: discord.Message, *, is_debug: bool = False):
        self.message = message
        self.is_debug = is_debug

    async def __aenter__(self):
        if not self.debug and self.is_debug:
            setattr(ExceptionHandler, "debug", self.is_debug)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not exc_val:
            await self.message.add_reaction("☑")
            return

        error = "".join(format_exception(exc_type, exc_val, exc_tb))
        if self.debug:
            setattr(ExceptionHandler, "error", (exc_val, error))

        if isinstance(exc_val, (EOFError, IndentationError, RuntimeError, SyntaxError, TimeoutError, asyncio.TimeoutError)):
            await self.message.add_reaction("💢")
        elif isinstance(exc_val, (AssertionError, ImportError, ModuleNotFoundError, UnboundLocalError)):
            await self.message.add_reaction("❓")
        elif isinstance(exc_val, (AttributeError, IndexError, KeyError, NameError, TypeError, UnicodeError, ValueError, commands.CommandInvokeError)):
            await self.message.add_reaction("❗")
        elif isinstance(exc_val, ArithmeticError):
            await self.message.add_reaction("⁉")
        elif isinstance(exc_val, (EnvironmentError, IOError, OSError, SystemError, SystemExit, WindowsError)):
            await self.message.add_reaction("‼")
        else:
            await self.message.add_reaction("⛔")

        setattr(ExceptionHandler, "debug", self.is_debug)
        if self.debug:
            setattr(ExceptionHandler, "error", ())

        return True


class VirtualVarReplacer:
    """Replace any instance of a virtual variable with its value and return it.

    Attributes
    ----------
    settings: :class:`Dict[str, Any]`
        The settings of the bot. The only setting that is used is the 'virtual_vars_format'.
    string: :class:`str`
        The string that should get converted.
    Returns
    -------
    str
        The converted string with the values of the virtual variables.
    """

    def __init__(self, settings: dict, string: str):
        self.settings = settings
        self.string = string

    def __enter__(self) -> str:
        formatter = self._format()
        matches = re.finditer(formatter, self.string)
        if matches:
            for match in matches:
                var_string, var_name = match.groups()
                if var_name in local_globals:
                    self.string = self.string.replace(var_string, local_globals[var_name])
                else:
                    continue
        return self.string

    def __exit__(self, exc_type, exc_val, exc_tb):
        # we don't really care about any errors.
        # If anything goes wrong, the variable will just stay with its format name
        pass

    def _format(self) -> str:
        format_style = re.compile(r"(%\(name\)s)")
        match = re.search(format_style, self.settings['virtual_vars_format'])
        compiler = "("
        added = False
        for i in range(len(self.settings['virtual_vars_format'])):
            if i in range(match.start(), match.end()):
                if match and not added:
                    compiler += r"(.+?)"
                    added = True
                    continue
                continue
            elif self.settings['virtual_vars_format'][i] in [".", "^", "$", "*", "+", "?", "{", "[", "(", ")", "|"]:
                compiler += f"\\{self.settings['virtual_vars_format'][i]}"
                continue
            compiler += self.settings['virtual_vars_format'][i]
        compiler += ")"
        return compiler


class StringCodeblockConverter(commands.Converter):
    """A custom converter that identifies and separates normal string args and codeblocks.

    Codeblock cleaning should be done later on as this does not automatically return the clean code.

    Returns
    -------
    Tuple[str, str]
        A tuple with index position 0 being the arguments, and index position 1 being the codeblock.
    """

    async def convert(self, ctx: commands.Context, argument: str) -> Tuple[str, str]:
        start: Optional[int] = None
        end: Optional[int] = None

        for i in range(len(argument)):
            if "".join([argument[i], argument[i + 1], argument[i + 2]]) == "```":
                if start is None and end is None:
                    start = i
                elif end is None and start is not None:
                    end = i + 3
                    break
        codeblock = argument[start:end]
        arguments = argument[:start]
        return arguments.strip(), codeblock