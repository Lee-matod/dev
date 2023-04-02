# -*- coding: utf-8 -*-

"""
dev.handlers
~~~~~~~~~~~~

Handlers and evaluators used within the dev extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import contextlib
import inspect
import io
import sys
import time
from typing import TYPE_CHECKING, Any, Callable, TextIO, TypeVar

import discord
from discord.ext import commands

from dev.scope import Scope, Settings
from dev.utils.utils import format_exception

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self

    from dev.types import Coro

__all__ = ("ExceptionHandler", "RelativeStandard", "TimedInfo", "replace_vars")

T = TypeVar("T")


class RelativeStandard(io.StringIO):
    def __init__(
        self,
        origin: TextIO = sys.__stdout__,
        callback: Callable[[str], Any] | None = None,
        *,
        initial_value: str | None = None,
        newline: str | None = None,
        filename: str | None = None,
    ):
        super().__init__(initial_value, newline)
        self.origin: TextIO = origin
        self.callback: Callable[[str], Any] | None = callback
        self.filename: str | None = filename

    def write(self, __s: str) -> int:
        stack: inspect.FrameInfo | None = discord.utils.get(inspect.stack(), filename=self.filename)
        if stack:
            if self.callback is not None:
                self.callback(__s)
            return super().write(__s)
        self.origin.write(__s)
        return 0


class TimedInfo:
    """Helper class that deals with timing processes."""

    def __init__(self, *, timeout: float | None = None) -> None:
        self.timeout: float | None = timeout
        self.start: float | None = None
        self.end: float | None = None

    def __repr__(self) -> str:
        return f"<{type(self).__name__} start={self.start} end={self.end} timeout={self.timeout}>"

    def __int__(self) -> int:
        return int(self.duration)

    def __float__(self) -> float:
        return self.duration

    def __str__(self) -> str:
        mins, secs = divmod(self.duration, 60)
        hrs, mins = divmod(mins, 60)
        return f"{int(hrs) or '00'}:{int(mins) or '00'}:{secs:.3}"

    def __enter__(self) -> Self:
        self.start = time.perf_counter()
        return self

    def __exit__(self, *_: Any) -> None:
        self.end = time.perf_counter()

    @property
    def duration(self) -> float:
        if self.start is None:
            raise ValueError("Start time has not been set")
        elif self.end is None:
            raise ValueError("End time has not been set")
        return self.end - self.start

    async def wait_for(self, coro: Coro[T], /) -> T | None:
        """Wait for the timeout to end. If timeout is reached and :attr:`end` is not set, react to the given message.

        This function should be called as a task.
        """
        timeout = self.timeout
        if timeout is None:
            raise ValueError("Timeout cannot be None")
        await asyncio.sleep(timeout)
        if self.end is None:
            return await coro


class ExceptionHandler:
    """Handle any exceptions in an async context manager.
    If any exceptions are raised during the process' lifetime, the bot will try to add reactions depending on the
    exception value.

    💢 – Syntax errors (EOFError, IndentationError).
    ⏰ – Timeout errors (asyncio.TimeoutError, TimeoutError).
    ❓ – Reference errors (ImportError, NameError).
    ❗ – Runtime errors (IndexError, KeyError, TypeError, ValueError).
    ⁉ – Arithmatic errors (ZeroDivisionError, FloatingPointError).
    ‼ – Any other errors that don't fall under any of the previous categories.

    Parameters
    ----------
    message: :class:`discord.Message`
        The message that the reactions will be added to.
    on_error: Optional[Callable[[Optional[Type[Exception]], Optional[Exception], Optional[TracebackType]], Any]]
        An optional function that will receive any raised exceptions inside the context manager.
        This function *can* be a coroutine.
    save_traceback: :class:`bool`
        Whether to save a traceback if an exception is raised.
        Defaults to `False`.
    """

    error: list[tuple[str, str]] = []
    debug: bool = False

    def __init__(
        self,
        message: discord.Message,
        /,
        on_error: Callable[[type[Exception] | None, Exception | None, TracebackType | None], Any] | None = None,
        save_traceback: bool = False,
    ) -> None:
        self.message: discord.Message = message
        self.on_error: Callable[[type[Exception] | None, Exception | None, TracebackType | None], Any] | None = on_error
        if save_traceback:
            ExceptionHandler.debug = True

    async def __aenter__(self) -> ExceptionHandler:
        return self

    async def __aexit__(
        self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: TracebackType | None
    ) -> bool:
        if exc_val is None:
            if not self.debug:
                with contextlib.suppress(discord.NotFound):
                    await self.message.add_reaction("\u2611")
            return False
        with contextlib.suppress(discord.NotFound):
            if isinstance(exc_val, (EOFError, SyntaxError)):
                await self.message.add_reaction("\U0001f4a2")
            elif isinstance(exc_val, (TimeoutError, asyncio.TimeoutError)):
                await self.message.add_reaction("\u23f0")
            elif isinstance(exc_val, (AssertionError, ImportError, NameError)):
                await self.message.add_reaction("\u2753")
            elif isinstance(
                exc_val,
                (
                    AttributeError,
                    IndexError,
                    KeyError,
                    TypeError,
                    UnicodeError,
                    ValueError,
                    commands.CommandInvokeError,
                ),
            ):
                if isinstance(exc_val, commands.CommandInvokeError):
                    exc_val = getattr(exc_val, "original", exc_val)
                    exc_tb = exc_val.__traceback__
                await self.message.add_reaction("\u2757")
            elif isinstance(exc_val, ArithmeticError):
                await self.message.add_reaction("\u2049")
            else:  # error doesn't fall under any other category
                await self.message.add_reaction("\u203c")
        if self.on_error is not None:
            if inspect.iscoroutinefunction(self.on_error):
                await self.on_error(exc_type, exc_val, exc_tb)
            else:
                self.on_error(exc_type, exc_val, exc_tb)

        if self.debug:
            ExceptionHandler.error.append((type(exc_val).__name__, format_exception(exc_val)))
        return True

    @classmethod
    def cleanup(cls) -> None:
        """Deletes any tracebacks that were saved if send_traceback was set to True.
        This method should always get called once you have finished handling any tracebacks
        """
        cls.error = []
        cls.debug = False


def replace_vars(string: str, scope: Scope) -> str:
    """Replaces any instance of virtual variables with their respective values and returns the parsed string.

    Parameters
    ----------
    string: :class:`str`
        The string that should get converted.
    scope: :class:`GlobalLocals`
        The scope that will be used when dealing with variables.

    Returns
    -------
    :class:`str`
        The converted string with the values of the virtual variables.
    """
    for (key, value) in scope.items():
        string = string.replace(Settings.VIRTUAL_VARS % key, value)
    return string
