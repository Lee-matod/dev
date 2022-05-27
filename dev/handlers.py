# -*- coding: utf-8 -*-

"""
dev.handlers
~~~~~~~~~~~~

Handlers that are used in the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


from typing import *

import asyncio
import discord
import inspect
import re

from discord.ext import commands
from traceback import format_exception

from dev.utils.startup import Settings
from dev.utils.utils import escape, local_globals


__all__ = (
    "BoolInput",
    "ExceptionHandler",
    "Paginator",
    "replace_vars"
)


class BoolInput(discord.ui.View):
    """Request the user a yes or no answer.

    Parameters
    ----------
    author: Union[:class:`discord.Member`, :class:`int`]
        The author of the message, a.k.a. ctx.author

    func: :class:`callable`[Any, Any]
        The function that should be executed if the user clicks on the yes button.

    args: :class:`Any`
        The arguments that should be passed into the function, if any.

    kwargs: :class:`Any`
        The key-word arguments that should be passed into the function, if any.

    """
    def __init__(self, author: Union[discord.Member, int], func: Callable[Any, Any], *args: Any, **kwargs: Any):
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

    Parameters
    ----------
    message: :class:`discord.Message`
        The message that the reactions will be added to.

    is_debug: :class:`bool`
        Whether the instance of this :class:`ExceptionHandler` is a debugger or not.

    Attributes
    ----------
    error: :class:`list[tuple[Exception, str]]`
        The errors that occurred during the lifetime of the process inside the context manager.

    debug: :class:`bool`
        Whether debug mode is currently enabled.
        ``True`` if debug mode is enabled, this also means that ``error`` will be modified.

    Returns
    -------
    self
        When entering the context manager, the instance of it is returned.

    bool
        When exiting the context manager, a boolean is returned. ``True`` if errors occurred during runtime.
    """
    error: List[Tuple[Exception, str]] = []
    debug: bool = False

    def __init__(self, message: discord.Message, *, is_debug: bool = False):
        self.message = message
        if is_debug:
            setattr(type(self), "debug", is_debug)
        self.error = self.error
        self.debug = self.debug

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            if not self.debug:
                await self.message.add_reaction("☑")
            return False

        error = "".join(format_exception(exc_type, exc_val, exc_tb))
        if self.debug:
            previous: List[Tuple[Exception, str]] = getattr(type(self), "error")
            previous.append((exc_val, error))
            setattr(type(self), "error", previous)

        if isinstance(exc_val, (EOFError, IndentationError, SyntaxError)):
            await self.message.add_reaction("💢")
        elif isinstance(exc_val, (TimeoutError, asyncio.TimeoutError)):
            await self.message.add_reaction("⏰")
        elif isinstance(exc_val, (AssertionError, ImportError, UnboundLocalError)):
            await self.message.add_reaction("❓")
        elif isinstance(exc_val, (AttributeError, IndexError, KeyError, NameError, TypeError, UnicodeError, ValueError, commands.CommandInvokeError)):
            await self.message.add_reaction("❗")
        elif isinstance(exc_val, ArithmeticError):
            await self.message.add_reaction("⁉")
        else:  # error doesn't fall under any other category
            await self.message.add_reaction("‼")

        return True


class Paginator(discord.ui.View):
    """Creates a paginator interface.

    Parameters
    ----------
    paginator: :class:`commands.Paginator`
        Paginator that this interface will use.
    user_id: :class:`int`
        The command author's ID.
    is_embed: Optional[:class:`discord.Embed`]
        If an embed is passed to this argument, the interface will use its description to change pages
        instead of sending it as a message.
    """

    def __init__(self, paginator: commands.Paginator, owner: int, **kwargs):
        super().__init__()
        self.paginator = paginator
        self.display_page = 0
        self.owner = owner
        self.is_embed: discord.Embed = kwargs.pop("embed", False)

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary, disabled=True)
    async def first_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page = 0
        self.enable_or_disable(rewind_=True, previous_=True)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.response.edit_message(embed=self.is_embed, view=self)
        await interaction.response.edit_message(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.success, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page -= 1
        if self.display_page == 0:
            self.enable_or_disable(rewind_=True, previous_=True)
        else:
            self.enable_or_disable(next_=False, fastforward_=False)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.response.edit_message(embed=self.is_embed, view=self)
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
                self.enable_or_disable(next_=True, fastforward_=True)
                if self.is_embed:
                    self.is_embed.description = self.paginator.pages[self.display_page]
                    return await interaction.response.edit_message(embed=self.is_embed, view=self)
                return await interaction.response.edit_message(content=f"{pages}", view=self)
            self.enable_or_disable(rewind_=False, previous_=False)
            self.update_display_page()
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.response.edit_message(embed=self.is_embed, view=self)
            await interaction.response.edit_message(content=f"{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind_=True, previous_=True, next_=True, fastforward_=True)
            await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.primary)
    async def last_page(self, interaction: discord.Interaction, _) -> Optional[discord.Message]:  # 'button' is not being used
        if interaction.user.id != self.owner:
            return
        self.display_page = len(self.paginator.pages) - 1
        try:
            pages = self.paginator.pages[self.display_page]
            self.enable_or_disable(next_=True, fastforward_=True)
            self.update_display_page()
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.response.edit_message(embed=self.is_embed, view=self)
            await interaction.response.edit_message(content=f"{pages}", view=self)
        except IndexError:
            self.enable_or_disable(rewind_=True, previous_=True, next_=True, fastforward_=True)
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.danger, custom_id="delete", emoji="🗑️")
    async def delete_page(self, interaction: discord.Interaction, _) -> None:  # 'button' is not being used
        await interaction.message.delete()

    def enable_or_disable(self, *, rewind_=False, previous_=False, next_=False, fastforward_=False) -> None:
        self.last_page.disabled = rewind_
        self.previous_page.disabled = previous_
        self.next_page.disabled = next_
        self.first_page.disabled = fastforward_

    def update_display_page(self) -> None:
        self.current_stop.label = self.display_page + 1


def replace_vars(string: str) -> str:
    """Replace any instance of a virtual variable with its value and return it.

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
