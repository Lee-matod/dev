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
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    final,
    overload,
)

import discord
from discord.ext import commands

from dev.scope import Scope, Settings

if TYPE_CHECKING:
    from typing_extensions import Self

    from dev.types import Coro

__all__ = ("ExceptionHandler", "RelativeStandard", "TimedInfo", "replace_vars")

T = TypeVar("T")
DebugT = TypeVar("DebugT", bound=bool)


class RelativeStandard(io.StringIO):
    def __init__(
        self,
        origin: TextIO = sys.__stdout__,
        callback: Optional[Callable[[str], Any]] = None,
        *,
        initial_value: Optional[str] = None,
        newline: Optional[str] = None,
        filename: Optional[str] = None,
    ):
        super().__init__(initial_value, newline)
        self.origin: TextIO = origin
        self.callback: Optional[Callable[[str], Any]] = callback
        self.filename: Optional[str] = filename

    def write(self, __s: str) -> int:
        stack: Optional[inspect.FrameInfo] = discord.utils.get(inspect.stack(), filename=self.filename)
        if stack:
            if self.callback is not None:
                self.callback(__s)
            return super().write(__s)
        self.origin.write(__s)
        return 0


class TimedInfo:
    """Helper class that deals with timing processes."""

    def __init__(self, *, timeout: Optional[float] = None) -> None:
        self.timeout: Optional[float] = timeout
        self.start: Optional[float] = None
        self.end: Optional[float] = None

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

    async def wait_for(self, coro: Coro[T], /) -> Optional[T]:
        """Wait for the timeout to end. If timeout is reached and :attr:`end` is not set, react to the given message.

        This function should be called as a task.
        """
        timeout = self.timeout
        if timeout is None:
            raise ValueError("Timeout cannot be None")
        await asyncio.sleep(timeout)
        if self.end is None:
            return await coro


@final
class ExceptionHandler(Generic[DebugT]):
    """Handle any exceptions in an async context manager.
    If any exceptions are raised during the process' lifetime, the bot will try to add reactions depending on the
    exception value.

    💢 - Syntax errors (EOFError, IndentationError).
    ⏰ - Timeout errors (asyncio.TimeoutError, TimeoutError).
    ❓ - Reference errors (ImportError, NameError).
    ❗ - Runtime errors (IndexError, KeyError, TypeError, ValueError).
    ⁉ - Arithmatic errors (ZeroDivisionError, FloatingPointError).
    ‼ - Any other errors that don't fall under any of the previous categories.

    Parameters
    ----------
    message: :class:`discord.Message`
        The message that the reactions will be added to.
    on_error: Optional[Callable[[Type[:class:`Exception`], :class:`Exception`, :class:`TracebackType`], Any]]
        An optional function that will receive any raised exceptions inside the context manager.
        This function *can* be a coroutine.
    debug: :class:`bool`
        Whether to save a traceback if an exception is raised.
        Defaults to `False`.
    """

    _exceptions: ClassVar[Dict[discord.Message, List[Tuple[Type[Exception], Exception, TracebackType]]]] = {}

    def __init__(
        self,
        message: discord.Message,
        /,
        on_error: Optional[Callable[[Type[Exception], Exception, TracebackType], Any]] = None,
        debug: DebugT = False,
    ) -> None:
        self.message: discord.Message = message
        self.on_error: Optional[Callable[[Type[Exception], Exception, TracebackType], Any]] = on_error
        self.debug: DebugT = debug
        if debug:
            type(self)._exceptions[message] = []

    @overload
    async def __aenter__(
        self: ExceptionHandler[Literal[True]],
    ) -> List[Tuple[Type[Exception], Exception, TracebackType]]:
        ...

    @overload
    async def __aenter__(self: ExceptionHandler[Literal[False]]) -> ExceptionHandler[Literal[False]]:
        ...

    async def __aenter__(self: ExceptionHandler[DebugT]):  # type: ignore
        if self.debug:
            try:
                tracebacks = type(self)._exceptions[self.message]
            except KeyError:
                return []  # type: ignore
            return tracebacks
        return self

    async def __aexit__(
        self, exc_type: Optional[Type[Exception]], exc_val: Optional[Exception], exc_tb: Optional[TracebackType]
    ) -> bool:
        if exc_val is None:
            try:
                await self.message.add_reaction("\N{BALLOT BOX WITH CHECK}")
            except discord.NotFound:
                pass
            return False

        with contextlib.suppress(discord.NotFound):
            if isinstance(exc_val, (EOFError, SyntaxError)):
                await self.message.add_reaction("\N{ANGER SYMBOL}")
            elif isinstance(exc_val, (TimeoutError, asyncio.TimeoutError)):
                await self.message.add_reaction("\N{ALARM CLOCK}")
            elif isinstance(exc_val, (AssertionError, ImportError, NameError)):
                await self.message.add_reaction("\N{BLACK QUESTION MARK ORNAMENT}")
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
                    if TYPE_CHECKING:
                        assert exc_val is not None
                    exc_tb = exc_val.__traceback__
                await self.message.add_reaction("\N{HEAVY EXCLAMATION MARK SYMBOL}")
            elif isinstance(exc_val, ArithmeticError):
                await self.message.add_reaction("\N{EXCLAMATION QUESTION MARK}")
            else:  # error doesn't fall under any other category
                await self.message.add_reaction("\N{DOUBLE EXCLAMATION MARK}")

        if TYPE_CHECKING:
            assert exc_type is not None
            assert exc_val is not None
            assert exc_tb is not None

        if self.on_error is not None:
            if inspect.iscoroutinefunction(self.on_error):
                await self.on_error(exc_type, exc_val, exc_tb)
            else:
                self.on_error(exc_type, exc_val, exc_tb)

        if self.message in type(self)._exceptions:
            if self.debug:
                del type(self)._exceptions[self.message]
            else:
                type(self)._exceptions[self.message].append((exc_type, exc_val, exc_tb))
        return True


def replace_vars(string: str, scope: Scope) -> str:
    """Replaces any instance of virtual variables with their respective values and returns the parsed string.

    Parameters
    ----------
    string: :class:`str`
        The string that should get converted.
    scope: :class:`Scope`
        The scope that will be used when dealing with variables.

    Returns
    -------
    :class:`str`
        The converted string with the values of the virtual variables.
    """
    for key, value in scope.items():
        string = string.replace(Settings.VIRTUAL_VARS % key, value)
    return string

