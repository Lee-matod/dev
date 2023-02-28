# -*- coding: utf-8 -*-

"""
dev.pagination
~~~~~~~~~~~~~~

Pagination interface and objects.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from textwrap import wrap

import discord
from discord.ext import commands

from dev import types

__all__ = ("Interface", "Paginator")


class _PageSetter(discord.ui.Modal):
    page_num: discord.ui.TextInput[Interface] = discord.ui.TextInput(label="Page Number", min_length=1)

    def __init__(self, view: Interface) -> None:
        self.page_num.max_length = len(view.paginator.pages)
        super().__init__(title="Skip to page...")
        self.view: Interface = view

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        try:
            page_num = int(self.page_num.value)
        except ValueError:
            return await interaction.response.send_message("Input value should be numeric.", ephemeral=True)
        if page_num not in range(1, len(self.view.paginator.pages) + 1):
            return await interaction.response.send_message("Page number does not exist.", ephemeral=True)
        self.view.page_num = page_num
        await interaction.response.edit_message(content=self.view.display_page, view=self.view)


class Paginator(commands.Paginator):
    """A :class:`discord.ext.commands.Paginator` wrapper.

    This subclass deals with lines that are greater than the maximum page size by splitting them.

    Subclass of `discord.ext.commands.Paginator`.

    See Also
    --------
    :class:`discord.ext.commands.Paginator`
    """

    def add_line(self, line: str = "", *, empty: bool = False) -> None:
        """A wrapper to the default :meth:`discord.ext.commands.Paginator.add_line`.

        Difference being that no TypeErrors are raised if the line exceeds the maximum page length.

        Parameters
        ----------
        line: :class:`str`
            From :meth:`discord.ext.commands.Paginator.add_line`. The line that should be added to the paginator.
        empty: :class:`bool`
            From :meth:`discord.ext.commands.Paginator.add_line`. Whether an empty line should be added too.
        """
        max_page_size = self.max_size - self._prefix_len - self._suffix_len - 2 * self._linesep_len
        if len(line) > max_page_size:
            lines: list[str] = wrap(line, max_page_size)
            for l in lines:
                super().add_line(l)
        else:
            super().add_line(line)
        if empty:
            self._current_page.append('')
            self._count += self._linesep_len


class Interface(discord.ui.View):
    """A paginator interface that implements basic pagination functionality.

    Subclass of :class:`discord.ui.View`.

    Parameters
    ----------
    paginator: :class:`Paginator`
        A pagination instance from which to get the pages from.
    author: Union[types.User, :class:`int`]
        The user that should be able to interact with this paginator. User ID or object can be passed.

    Attributes
    ----------
    paginator: :class:`Paginator`
        The pagination instance that was passed to the constructor.
    author: :class:`int`
        The ID of the user that is able to interact with this paginator.
        This is the result of the user ID or object that was passed to the constructor.
    """

    def __init__(self, paginator: commands.Paginator, author: types.User | int) -> None:
        super().__init__()
        self.author: int = getattr(author, "id", author)  # type: ignore
        self.paginator: commands.Paginator = paginator

        self.reset()

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        return interaction.user.id == self.author

    def reset(self) -> None:
        """Resets the entire interface, setting the current page to the last one."""
        if len(self.paginator.pages) <= 1:
            self.first_page.disabled = True
            self.previous_page.disabled = True
        self.last_page.disabled = True
        self.next_page.disabled = True

        self._display_page_count: int = len(self.paginator.pages)
        self._page_count: int = self._display_page_count - 1
        self.current.label = f"{self._display_page_count}/{self._display_page_count}"

    @property
    def display_page(self) -> str:
        """:class:`str`: Returns the current page of the paginator."""
        return self.paginator.pages[self._page_count]

    @property
    def page_num(self) -> int:
        """:class:`int`: Returns the current page number of the paginator."""
        return self._display_page_count

    @page_num.setter
    def page_num(self, item: int) -> None:
        self._display_page_count = item
        self._page_count = item - 1
        if item == len(self.paginator.pages):
            self.last_page.disabled = True
            self.next_page.disabled = True
        if item == 1:
            self.first_page.disabled = True
            self.previous_page.disabled = True
        else:
            self.first_page.disabled = False
            self.previous_page.disabled = False
        if item < len(self.paginator.pages):
            self.last_page.disabled = False
            self.next_page.disabled = False
        self.current.label = f"{item}/{len(self.paginator.pages)}"

    @discord.ui.button(label="\u226a")
    async def first_page(self, interaction: discord.Interaction, _) -> None:
        self.page_num = 1
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="\u25c0", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, _) -> None:
        self.page_num -= 1
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="0", style=discord.ButtonStyle.green)
    async def current(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(_PageSetter(self))

    @discord.ui.button(label="\u25b6", style=discord.ButtonStyle.blurple, disabled=True)
    async def next_page(self, interaction: discord.Interaction, _) -> None:
        self.page_num += 1
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="\u226b", disabled=True)
    async def last_page(self, interaction: discord.Interaction, _) -> None:
        self.page_num = len(self.paginator.pages)
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, _) -> None:
        if interaction.message is not None:
            await interaction.message.delete()
