# -*- coding: utf-8 -*-

"""
dev.pagination
~~~~~~~~~~~~~~

Pagination interface and objects.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import discord
from discord.ext import commands

from dev import types


__all__ = (
    "Interface",
    "Paginator"
)


class _PageSetter(discord.ui.Modal):
    page_num: discord.ui.TextInput[Interface] = discord.ui.TextInput(label="Page Number", min_length=1)

    def __init__(self, view: Interface) -> None:
        self.page_num.max_length = len(view.paginator.pages)
        super().__init__(title="Skip to page...")
        self.view: Interface = view

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not self.page_num.value.isnumeric():
            return await interaction.response.send_message("Input value should be numeric.", ephemeral=True)
        if int(self.page_num.value) not in range(1, len(self.view.paginator.pages) + 1):
            return await interaction.response.send_message("Page number does not exist.", ephemeral=True)
        self.view.current_page = int(self.page_num.value)
        await interaction.response.edit_message(content=self.view.display_page, view=self.view)


class Paginator(commands.Paginator):
    """A :class:`discord.ext.commands.Paginator` wrapper.

    This subclass deals with lines that are greater than the maximum page size by splitting them.

    Subclass of `discord.ext.commands.Paginator`.

    See Also
    --------
    :class:`discord.ext.commands.Paginator`
    """

    def __init__(
            self,
            prefix: str = "```",
            suffix: str = "```",
            max_size: int = 2000,
            linesep: str = "\n",
            force_last_page: bool = False
    ):
        super().__init__(prefix, suffix, max_size, linesep)
        self.force_last_page: bool = force_last_page
        self.__pages: list[str] = []

    @property
    def pages(self) -> list[str]:
        assert self.suffix is not None
        return [page.strip("\n") + self.suffix for page in self.__pages]

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
            lines = [line[:max_page_size]]
            checker = ""
            for char in line[max_page_size:]:
                if len(checker) < max_page_size:
                    checker += char
                else:
                    lines.append(checker)
                    checker = ""
            if checker:
                lines.append(checker)
            for l in lines:  # noqa: E741
                self.line_handler(l, max_page_size, empty=empty)
            return
        self.line_handler(line, max_page_size, empty=empty)

    def line_handler(self, line: str, /, max_page_size: int, *, empty: bool) -> None:
        if len(self.__pages) == 0 or len(line) + len(self.__pages[-1]) > max_page_size:
            self.__pages.append(f"{self.prefix}\n{line}" + ("\n" if empty else ''))
        else:
            self.__pages[-1] += f"\n{line}"


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
        self.paginator: commands.Paginator = paginator
        self.author: int = author.id if isinstance(author, types.User) else author  # type: ignore
        if hasattr(paginator, "force_last_page") and paginator.force_last_page:  # type: ignore
            self.last_page.disabled = True
            self.next_page.disabled = True
            if len(paginator.pages) <= 1:
                self.first_page.disabled = True
                self.previous_page.disabled = True
            self._display_page: int = len(paginator.pages)
            self._real_page: int = self._display_page - 1
        else:
            self.first_page.disabled = True
            self.previous_page.disabled = True
            if len(paginator.pages) <= 1:
                self.last_page.disabled = True
                self.next_page.disabled = True
            self._display_page: int = 1
            self._real_page: int = 0
        self.current.label = str(self._display_page)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.author

    @property
    def display_page(self) -> str:
        """:class:`str`: Returns the current page of the paginator."""
        return self.paginator.pages[self._real_page]

    @property
    def current_page(self) -> int:
        """:class:`int`: Returns the current page number of the paginator."""
        return self._display_page

    @current_page.setter
    def current_page(self, item: int) -> None:
        self._display_page = item
        self._real_page = item - 1
        self.current.label = str(item)
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

    @discord.ui.button(label="\u226a")
    async def first_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page = 1
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="\u25c0", style=discord.ButtonStyle.blurple)
    async def previous_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page -= 1
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="0", style=discord.ButtonStyle.green)
    async def current(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(_PageSetter(self))

    @discord.ui.button(label="\u25b6", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page += 1
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="\u226b")
    async def last_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page = len(self.paginator.pages)
        await interaction.response.edit_message(content=self.display_page, view=self)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, _) -> None:
        if interaction.message is not None:
            await interaction.message.delete()

