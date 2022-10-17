# -*- coding: utf-8 -*-

"""
dev.handlers
~~~~~~~~~~~~

Handlers and evaluators used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import contextlib
import inspect
from traceback import format_exception
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Tuple, Type, Optional, Union

import discord
from discord.ext import commands

from dev import types

from dev.utils.startup import Settings

if TYPE_CHECKING:
    from types import TracebackType

__all__ = (
    "BoolInput",
    "ExceptionHandler",
    "GlobalLocals",
    "replace_vars",
    "optional_raise"
)


class GlobalLocals:
    """Allows variables to be stored within a class instance, instead of a global scope or a dictionary.

    Parameters
    ----------
    __globals: Optional[Dict[:class:`str`, Any]]
        Global scope variables. Acts the same way as :meth:`globals()`.
        Defaults to ``None``.
    __locals: Optional[Dict[:class:`str`, Any]]
        Local scope variables. Acts the same way as :meth:`locals()`.
        Defaults to ``None``.
    """

    def __init__(
            self,
            __globals: Optional[Dict[str, Any]] = None,
            __locals: Optional[Dict[str, Any]] = None,
            /
    ) -> None:
        self.globals: Dict[str, Any] = __globals or {}
        self.locals: Dict[str, Any] = __locals or {}

    def __bool__(self) -> bool:
        return bool(self.globals or self.locals)

    def __delitem__(self, key: Any) -> None:
        glob_exc, loc_exc = False, False
        try:
            del self.globals[key]
        except KeyError:
            glob_exc = True
        try:
            del self.locals[key]
        except KeyError:
            loc_exc = True

        if glob_exc and loc_exc:
            raise KeyError(key)

    def __getitem__(self, item: Any) -> Tuple[Any, Any]:
        glob, loc = None, None
        glob_exc, loc_exc = False, False
        try:
            glob = self.globals[item]
        except KeyError:
            glob_exc = True
        try:
            loc = self.locals[item]
        except KeyError:
            loc_exc = True

        if glob_exc and loc_exc:
            raise KeyError(item)
        return glob, loc

    def __len__(self) -> int:
        return len(self.globals) + len(self.locals)

    def items(self) -> Tuple[Tuple[str, ...], Tuple[Any, ...]]:
        """Returns a tuple of all global and local scopes with their respective key-value pairs.

        Returns
        -------
        Tuple[Tuple[:class:`str`, ...], Tuple[Any, ...]]
            A joined tuple of global and local variables from the current scope.
        """
        return tuple(self.globals.items()), tuple(self.locals.items())

    def keys(self) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
        """Returns a tuple of keys of all global and local scopes.

        Returns
        -------
        Tuple[Tuple[:class:`str`, ...], Tuple[:class:`str`, ...]]
            A tuple containing the list of global and local keys from the current scope.
        """
        return tuple(self.globals.keys()), tuple(self.locals.keys())

    def values(self) -> Tuple[Tuple[Any, ...], Tuple[Any, ...]]:
        """Returns a tuple of values of all global and local scopes.

        Returns
        -------
        Tuple[Tuple[Any, ...], Tuple[Any, ...]]
            A tuple containing the list of global and local values from the current scope.
        """
        return tuple(self.globals.values()), tuple(self.locals.values())

    def get(self, item: str, default: Any = None) -> Any:
        """Get an item from either the global scope or the locals scope.

        Global scope will be searched first, then local scope and if no item is found, the default will be returned.
        It's best to use this when you are just trying to get a value without worrying about the scope.

        Parameters
        ----------
        item: :class:`str`
            The item that should be searched for in the scopes.
        default: Any
            An argument that should be returned if no value was found. Defaults to ``None``.

        Returns
        -------
        Any
            The value of the item that was found, if it was found.
        """
        try:
            res = self.globals[item]
        except KeyError:
            try:
                res = self.locals[item]
            except KeyError:
                return default
        return res

    def update(
            self,
            __new_globals: Optional[Dict[str, Any]] = None,
            __new_locals: Optional[Dict[str, Any]] = None,
            /
    ) -> None:
        """Update the current instance of variables with new ones.

        Parameters
        ----------
        __new_globals: Optional[Dict[:class:`str`, Any]]
            New instances of global variables.
        __new_locals: Optional[Dict[:class:`str`, Any]]
            New instances of local variables.
        """
        if __new_globals is not None:
            self.globals.update(__new_globals)
        if __new_locals is not None:
            self.locals.update(__new_locals)


class BoolInput(discord.ui.View):
    """Allows the user to submit a true or false answer through buttons.

    If the user clicks on "Yes", a function is called and the view is removed.

    Subclass of :class:`discord.ui.View`.

    Examples
    --------
    .. codeblock:: python3
        # inside a command
        async def check():
            await ctx.send("We shall continue!")
        await ctx.send("Would you like to continue?", view=BoolInput(ctx.author, check))

    Parameters
    ----------
    author: Union[types.User, :class:`int`]
        The author of the message. It can be either their ID or Discord object.
    func: Optional[Callable[[], Any]]
        The function that should get called if the user clicks on the "Yes" button. This function cannot have arguments.
    """

    def __init__(self, author: Union[types.User, int], func: Optional[Callable[[], Any]] = None) -> None:
        super().__init__()
        self.func: Optional[Callable[[], Any]] = func
        self.author: int = author.id if isinstance(author, types.User) else author

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user.id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _):
        if self.func is not None:
            if inspect.iscoroutinefunction(self.func):
                await self.func()
            else:
                self.func()
        await interaction.delete_original_response()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _):
        await interaction.delete_original_response()


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
    on_error: Optional[Callable[[], Any]]
        An optional, argument-less function that is called whenever an exception is raised inside the context manager.
        This function *can* be a coroutine.
    save_traceback: :class:`bool`
        Whether to save a traceback if an exception is raised.
        Defaults to `False`.
    """
    error: List[Tuple[str, str]] = []
    debug: bool = False

    def __init__(
            self,
            message: discord.Message,
            /,
            on_error: Optional[Callable[[], Any]] = None,
            save_traceback: bool = False
    ) -> None:
        self.message: discord.Message = message
        self.on_error: Optional[Callable[..., Any]] = on_error
        if save_traceback:
            ExceptionHandler.debug = True

    async def __aenter__(self) -> ExceptionHandler:
        return self

    async def __aexit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType) -> bool:
        if exc_val is None:
            if not self.debug:
                with contextlib.suppress(discord.NotFound):
                    await self.message.add_reaction("☑")
            return False
        with contextlib.suppress(discord.NotFound):
            if isinstance(exc_val, (EOFError, IndentationError, SyntaxError)):
                await self.message.add_reaction("💢")
            elif isinstance(exc_val, (TimeoutError, asyncio.TimeoutError)):
                await self.message.add_reaction("⏰")
            elif isinstance(exc_val, (AssertionError, ImportError, NameError, UnboundLocalError)):
                await self.message.add_reaction("❓")
            elif isinstance(
                    exc_val,
                    (
                            AttributeError,
                            IndexError,
                            KeyError,
                            TypeError,
                            UnicodeError,
                            ValueError,
                            commands.CommandInvokeError
                    )
            ):
                if isinstance(exc_val, commands.CommandInvokeError):
                    exc_val = getattr(exc_val, "original", exc_val)
                    exc_tb = exc_val.__traceback__
                await self.message.add_reaction("❗")
            elif isinstance(exc_val, ArithmeticError):
                await self.message.add_reaction("⁉")
            else:  # error doesn't fall under any other category
                await self.message.add_reaction("‼")
        if self.on_error:
            if inspect.iscoroutinefunction(self.on_error):
                await self.on_error()
            else:
                self.on_error()

        if self.debug:
            ExceptionHandler.error.append(
                (type(exc_val).__name__, "".join(format_exception(exc_type, exc_val, exc_tb)))
            )
        return True

    @classmethod
    def cleanup(cls) -> None:
        """Deletes any tracebacks that were saved if send_traceback was set to True.
        This method should always get called once you have finished handling any tracebacks
        """
        cls.error = []
        cls.debug = False


def optional_raise(ctx: commands.Context, error: commands.CommandError, /) -> None:
    # We have to somehow check if the on_command_error event was overridden, the most logical way I could think of was
    # checking if the functions were the same which is the aim of this bit. Do note, however, that this might fail under
    # certain circumstances.
    events = ctx.bot.on_command_error.__code__ == commands.Bot.on_command_error.__code__  # type: ignore
    listeners = ctx.bot.extra_events.get("on_command_error")
    if events or listeners:
        ctx.bot.dispatch("command_error", ctx, error)
    else:
        raise error


def replace_vars(string: str, scope: GlobalLocals) -> str:
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
    for key, value in scope.globals.items():
        string = string.replace(Settings.VIRTUAL_VARS % key, value)
    return string
