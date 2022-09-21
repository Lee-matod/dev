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
import re
from traceback import format_exception
from types import TracebackType
from typing import Any, Callable, Dict, List, Tuple, Type, Optional, Union

import discord
from discord.ext import commands

from dev import types

from dev.utils.startup import Settings
from dev.utils.utils import escape


__all__ = (
    "BoolInput",
    "ExceptionHandler",
    "GlobalLocals",
    "replace_vars",
    "optional_raise"
)


class GlobalLocals:
    """This allows variables to be stored within a class instance, instead of a global scope or dictionary.

    All parameters are positional-only.

    Parameters
    ----------
    __globals: Optional[Dict[:class:`str`, Any]]
        Global scope variables. Acts the same way as :meth:`globals()`.
        Defaults to ``None``.
    __locals: Optional[Dict[:class:`str`, Any]]
        Local scope variables. Acts the same way as :meth:`locals()`.
        Defaults to ``None``.
    """

    def __init__(self, __globals: Optional[Dict[str, Any]] = None, __locals: Optional[Dict[str, Any]] = None, /):
        self.globals: Dict[str, Any] = __globals or {}
        self.locals: Dict[str, Any] = __locals or {}

    def __bool__(self) -> bool:
        return bool(self.globals or self.locals)

    def __delitem__(self, key: Any):
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

    def items(self):
        """Returns a list of all global and local scopes with their respective key-value pairs.

        Returns
        -------
        Tuple[List[:class:`str`], List[Any]]
            A joined list of global and local variables from the current scope.
        """
        return self.globals.items(), self.locals.items()

    def keys(self):
        """Returns a list of keys of all global and local scopes.

        Returns
        -------
        Tuple[List[:class:`str`], List[:class:`str`]]
            A tuple containing the list of global and local keys from the current scope.
        """
        return self.globals.keys(), self.locals.keys()

    def values(self):
        """Returns a list of values of all global and local scopes.

        Returns
        -------
        Tuple[Tuple[Any, ...], Tuple[Any, ...]]
            A tuple containing the list of global and local values from the current scope.
        """
        return self.globals.values(), self.locals.values()

    def get(self, item: str, default: Any = None) -> Any:
        """Get an item from either the global scope or the locals scope.

        Global scope will be search first, then local scope and if no item is found, the default will be returned.
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

    def update(self, __new_globals: Optional[Dict[str, Any]] = None, __new_locals: Optional[Dict[str, Any]] = None, /):
        """Update the current instance of variables with new ones.

        All parameters are positional-only.

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
    """Allows the user to submit a yes or no answer through buttons.
    If the user clicks on yes, a function is called and the view is removed.

    Examples
    --------
    .. codeblock:: python3
        async def check(ctx: commands.Context):
            await ctx.send("We shall continue!")
        await ctx.send("Would you like to continue?", view=BoolInput(ctx.author, check, ctx))

    Parameters
    ----------
    author: Union[:class:`discord.abc.User`, :class:`int`]
        The author of the message. It can be either their ID or User object.
    func: :class:`callable`[Any, Any]
        The function that should get called if the user clicks on the yes button.
    args: :class:`Any`
        The arguments that should be passed into the function once it gets executed, if any.
    kwargs: :class:`Any`
        The keyword arguments that should be passed into the function once it gets executed, if any.
    """

    def __init__(
            self,
            author: Union[types.User, int],
            func: Optional[Callable[..., Any]] = None,
            *args: Any,
            **kwargs: Any
    ):
        super().__init__()
        self.func: Optional[Callable[..., Any]] = func
        self.author: int = author.id if isinstance(author, types.User) else author
        self.args = args
        self.kwargs = kwargs

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user.id

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _):
        if self.func is not None:
            if inspect.isawaitable(self.func):
                await self.func(*self.args, **self.kwargs)
            else:
                self.func(*self.args, **self.kwargs)
        await interaction.response.edit_message(content="Task has been executed.", view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _):
        await interaction.response.edit_message(content="Task has been canceled.", view=None)


class ExceptionHandler:
    """Handle any exceptions in an async context manager.
    If any exceptions are raised during the process' lifetime, the bot will try to add
    reactions depending on the exception value.

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
        Defaults to ``False``.

    Raises
    ------
    TypeError
        The function passed into on_error has a keyword-only parameter in its signature.
    """
    error: List[Tuple[str, str]] = []
    debug: bool = False

    def __init__(
            self,
            message: discord.Message,
            /,
            on_error: Optional[Callable[[], Any]] = None,
            save_traceback: bool = False
    ):
        self.message: discord.Message = message
        self.on_error: Optional[Callable[..., Any]] = on_error
        if save_traceback:
            ExceptionHandler.debug = True
        if self.on_error:
            if inspect.signature(self.on_error).parameters:
                raise TypeError("Parameters aren't supported in 'on_error' function")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type: Type[Exception], exc_val: Exception, exc_tb: TracebackType):
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
                    exc_val = exc_val.original
                    exc_tb = exc_val.__traceback__
                await self.message.add_reaction("❗")
            elif isinstance(exc_val, ArithmeticError):
                await self.message.add_reaction("⁉")
            else:  # error doesn't fall under any other category
                await self.message.add_reaction("‼")
        if self.on_error:
            if inspect.isawaitable(self.on_error):
                await self.on_error()
            else:
                self.on_error()

        if self.debug:
            ExceptionHandler.error.append(
                (type(exc_val).__name__, "".join(format_exception(exc_type, exc_val, exc_tb)))
            )
        return True

    @classmethod
    def cleanup(cls):
        """Deletes any tracebacks that were saved if send_traceback was set to True.
        This method should always get called once you have finished handling any tracebacks
        """
        cls.error = []
        cls.debug = False


def optional_raise(ctx: commands.Context, error: commands.CommandError, /):
    # we have to somehow check if the on_command_error event was overridden,
    # the most logical way I could think of was checking if the functions were the same
    # which is the aim of this bit. Do note, however, that this might fail under certain circumstances
    events = ctx.bot.on_command_error.__code__.co_code == commands.Bot.on_command_error.__code__.co_code  # type: ignore
    listeners = ctx.bot.extra_events.get("on_command_error")
    if events or listeners:
        ctx.bot.dispatch("command_error", ctx, error)
    else:
        raise error


def replace_vars(string: str, scope: GlobalLocals) -> str:
    """Replaces any instance of a virtual variables with their respective values and return it the parsed string.

    Instances of the variables will not get converted if a value is not found.

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
    formatter = escape(Settings.VIRTUAL_VARS.replace("$var$", "(.+?)"))
    matches = re.finditer(re.compile(formatter), string)
    if matches:
        for match in matches:
            glob, loc = scope.keys()
            if match.group(1) in [*glob, *loc]:
                var = Settings.VIRTUAL_VARS.replace("$var$", match.group(1))
                glob, loc = scope[match.group(1)]
                string = string.replace(var, glob or loc, 1)

    return string
