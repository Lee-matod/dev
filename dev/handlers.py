# -*- coding: utf-8 -*-

"""
dev.handlers
~~~~~~~~~~~~

Handlers that are used in the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import (
    Any,
    Callable,
    List,
    Tuple,
    Type,
    TypeVar,
    Optional,
    Union,
    TYPE_CHECKING
)

import asyncio
import contextlib
import discord
import inspect
import re

from discord.ext import commands
from traceback import format_exception
from types import TracebackType

from dev.utils.startup import Settings
from dev.utils.utils import escape, local_globals

if TYPE_CHECKING:
    from typing_extensions import ParamSpec
    P = ParamSpec("P")
else:
    P = TypeVar("P")

__all__ = (
    "BoolInput",
    "ExceptionHandler",
    "Paginator",
    "replace_vars"
)


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

    def __init__(self, author: Union[discord.abc.User, int], func: Callable[P, Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.func = func
        self.author: int = author.id if isinstance(author, discord.Member) else author
        self.args = args
        self.kwargs = kwargs

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.author:
            return
        if inspect.isawaitable(self.func):
            await self.func(*self.args, **self.kwargs)
        else:
            self.func(*self.args, **self.kwargs)
        await interaction.response.edit_message(content="Task has been executed.", view=None)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _):
        if interaction.user.id != self.author:
            return
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
    send_traceback: :class:`bool`
        Whether to send a traceback if an exception is raised.
        Defaults to ``False``.
    """
    error: List[Tuple[str, str]] = []
    debug: bool = False

    def __init__(self, message: discord.Message, *, send_traceback: bool = False):
        self.message = message
        self.send_traceback = send_traceback
        if send_traceback:
            ExceptionHandler.debug = True

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
            elif isinstance(exc_val, (AttributeError, IndexError, KeyError, TypeError, UnicodeError, ValueError, commands.CommandInvokeError)):
                if isinstance(exc_val, commands.CommandInvokeError):
                    exc_val = exc_val.original
                await self.message.add_reaction("❗")
            elif isinstance(exc_val, ArithmeticError):
                await self.message.add_reaction("⁉")
            else:  # error doesn't fall under any other category
                await self.message.add_reaction("‼")

        if self.debug:
            ExceptionHandler.error.append((exc_val.__class__.__name__, "".join(format_exception(exc_type, exc_val, exc_tb))))
        return True

    @classmethod
    def cleanup(cls):
        """Deletes any tracebacks that were saved if send_traceback was set to True.
        This method should always get called once you have finished handling any tracebacks
        """
        cls.error = []
        cls.debug = False


class Paginator(discord.ui.View):
    """A paginator interface that allows you to iterate through pages
    if a message exceeds character limits using buttons.

    Examples
    --------
    .. codeblock:: python3

        paginator = commands.Paginator(...)
        for line in some_long_text.split("\n"):
            paginator.add_line(line)
        interface = dev.Paginator(paginator, ctx.author.id)
        await ctx.send(interface.pages[0], view=interface)

    Parameters
    ----------
    paginator: :class:`commands.Paginator`
        The paginator class from where to get the pages from.
    owner: :class:`int`
        The ID of the author of the command's invoked message.
    embed: Optional[:class:`discord.Embed`]
        If the message is an embed, then the embed should be passed here.
    """

    def __init__(self, paginator: commands.Paginator, owner: int, *, embed: discord.Embed = None):
        super().__init__()
        self.paginator = paginator
        self.display_page = 0
        self.owner = owner
        self.embed = embed  # type: ignore

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary, disabled=True)
    async def first_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page = 0
        self.enable_or_disable(rewind=True, previous=True)
        self.update_display_page()
        if self.embed:
            self.embed.description = self.paginator.pages[self.display_page]
            return await interaction.response.edit_message(embed=self.embed, view=self)
        await interaction.response.edit_message(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.success, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page -= 1
        if self.display_page == 0:
            self.enable_or_disable(rewind=True, previous=True)
        else:
            self.enable_or_disable(next_=False, fastforward=False)
        self.update_display_page()
        if self.embed:
            self.embed.description = self.paginator.pages[self.display_page]
            return await interaction.response.edit_message(embed=self.embed, view=self)
        await interaction.response.edit_message(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.red)
    async def current_stop(self, interaction: discord.Interaction, _) -> None:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        button: discord.Button
        for button in self.children:
            if not button.custom_id == "delete":
                button.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.success)
    async def next_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page += 1
        try:
            pages = self.paginator.pages[self.display_page]
            if self.display_page == len(self.paginator.pages) - 1:
                self.update_display_page()
                self.enable_or_disable(next_=True, fastforward=True)
                if self.embed:
                    self.embed.description = self.paginator.pages[self.display_page]
                    return await interaction.response.edit_message(embed=self.embed, view=self)
                return await interaction.response.edit_message(content=f"{pages}", view=self)
            self.enable_or_disable(rewind=False, previous=False)
            self.update_display_page()
            if self.embed:
                self.embed.description = self.paginator.pages[self.display_page]
                return await interaction.response.edit_message(embed=self.embed, view=self)
            await interaction.response.edit_message(content=f"{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind=True, previous=True, next_=True, fastforward=True)
            await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.primary)
    async def last_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page = len(self.paginator.pages) - 1
        try:
            pages = self.paginator.pages[self.display_page]
            self.enable_or_disable(next_=True, fastforward=True)
            self.update_display_page()
            if self.embed:
                self.embed.description = self.paginator.pages[self.display_page]
                return await interaction.response.edit_message(embed=self.embed, view=self)
            await interaction.response.edit_message(content=f"{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind=True, previous=True, next_=True, fastforward=True)
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete", emoji="🗑️")
    async def delete_page(self, interaction: discord.Interaction, _) -> None:  # 'button' is not being used
        await interaction.message.delete()

    def enable_or_disable(self, *, rewind=False, previous=False, next_=False, fastforward=False) -> None:
        self.last_page.disabled = rewind
        self.previous_page.disabled = previous
        self.next_page.disabled = next_
        self.first_page.disabled = fastforward

    def update_display_page(self) -> None:
        self.current_stop.label = self.display_page + 1


def replace_vars(string: str) -> str:
    """Replaces any instance of a virtual variables with their respective values and return it the parsed string.

    Instances of the variables will not get converted if a value is not found.

    Parameters
    ----------
    string: :class:`str`
        The string that should get converted.

    Returns
    -------
    str
        The converted string with the values of the virtual variables.
    """
    formatter = escape(Settings.VIRTUAL_VARS.replace("$var$", "(.+?)"))
    matches = re.finditer(formatter, string)
    if matches:
        for match in matches:
            if match.group(1) in local_globals:
                string = string.replace(match.string, local_globals[match.group(1)])
            else:
                continue
    return string
