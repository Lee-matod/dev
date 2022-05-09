# -*- coding: utf-8 -*-

"""
dev.handlers
~~~~~~~~~~~~

Handlers that are used in the dev extension.

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
from dev.utils.startup import virtual_vars_format

__all__ = (
    "replace_vars",
    "ExceptionHandler",
    "Paginator"
)


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
        elif isinstance(exc_val, (AssertionError, ImportError, ModuleNotFoundError, UnboundLocalError)):
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

    Attributes
    ----------
    paginator: :class:`commands.Paginator`
        Paginator that this interface will use.
    user_id: :class:`int`
        The command author's ID.
    is_embed: Optional[:class:`discord.Embed`]
        If an embed is passed to this argument, the interface will use its description to change pages
        instead of sending it as a message.
    """

    def __init__(self, paginator: commands.Paginator, user_id: int, **kwargs):
        super().__init__()
        self.paginator = paginator
        self.display_page = 0
        self.user_id = user_id
        self.is_embed: discord.Embed = kwargs.pop("embed", False)

    @discord.ui.button(emoji="⏪", style=discord.ButtonStyle.primary, disabled=True, custom_id="rewind")
    async def first_page(self, interaction: discord.Interaction, button: discord.Button) -> Optional[discord.Message]:
        if interaction.user.id != self.user_id:
            return
        self.display_page = 0
        self.enable_or_disable(rewind_=True, previous_=True)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.response.edit_message(embed=self.is_embed, view=self)
        await interaction.response.edit_message(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.success, disabled=True, custom_id="previous")
    async def previous_page(self, interaction: discord.Interaction, button: discord.Button) -> Optional[discord.Message]:
        if interaction.user.id != self.user_id:
            return
        self.display_page -= 1
        if self.display_page == 0:
            self.update_display_page()
            self.enable_or_disable(rewind_=True, previous_=True)
            if self.is_embed:
                self.is_embed.description = self.paginator.pages[self.display_page]
                return await interaction.response.edit_message(embed=self.is_embed, view=self)
            return await interaction.response.edit_message(content=f"{self.paginator.pages[self.display_page]}", view=self)
        self.enable_or_disable(next_=False, fastforward_=False)
        self.update_display_page()
        if self.is_embed:
            self.is_embed.description = self.paginator.pages[self.display_page]
            return await interaction.response.edit_message(embed=self.is_embed, view=self)
        await interaction.response.edit_message(content=f"{self.paginator.pages[self.display_page]}", view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.red, custom_id="current_stop")
    async def current_stop(self, interaction: discord.Interaction, button: discord.Button) -> None:
        if interaction.user.id != self.user_id:
            return
        button: discord.Button
        for button in self.children:
            if not button.custom_id == "delete":
                button.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="▶", style=discord.ButtonStyle.success, custom_id="next")
    async def next_page(self, interaction: discord.Interaction, button: discord.Button) -> Optional[discord.Message]:
        if interaction.user.id != self.user_id:
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

    @discord.ui.button(emoji="⏩", style=discord.ButtonStyle.primary, custom_id="fastforward")
    async def last_page(self, interaction: discord.Interaction, button: discord.Button) -> Optional[discord.Message]:
        if interaction.user.id != self.user_id:
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
    async def delete_page(self, interaction: discord.Interaction, button: discord.Button) -> None:
        await interaction.message.delete()

    def enable_or_disable(self, *, rewind_=False, previous_=False, next_=False, fastforward_=False) -> None:
        button: discord.Button
        b_rewind = [button for button in self.children if button.custom_id == "rewind"][0]
        b_previous = [button for button in self.children if button.custom_id == "previous"][0]
        b_next = [button for button in self.children if button.custom_id == "next"][0]
        b_fastforward = [button for button in self.children if button.custom_id == "fastforward"][0]
        b_rewind.disabled = rewind_
        b_previous.disabled = previous_
        b_next.disabled = next_
        b_fastforward.disabled = fastforward_

    def update_display_page(self) -> None:
        b: discord.Button
        current_stop = [b for b in self.children if b.custom_id == "current_stop"][0]
        current_stop.label = self.display_page + 1


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
    formatter = virtual_vars_format()
    matches = re.finditer(formatter, string)
    if matches:
        for match in matches:
            var_string, var_name = match.groups()
            if var_name in local_globals:
                string = string.replace(var_string, local_globals[var_name])
            else:
                continue
    return string