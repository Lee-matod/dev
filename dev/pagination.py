# -*- coding: utf-8 -*-

"""
dev.pagination
~~~~~~~~~~~~~~

Pagination interface and objects.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

import discord
from discord.ext import commands

from dev import types


__all__ = (
    "Interface",
    "Paginator"
)

TypeT = TypeVar("TypeT", str, discord.Embed)


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
        await interaction.response.edit_message(**self.view.paginator.to_dict(self.view.display_page), view=self.view)


class Paginator(commands.Paginator, Generic[TypeT]):
    """A :class:`discord.ext.commands.Paginator` wrapper.

    This subclass deals with lines that are greater than the maximum page size by splitting them.

    Subclass of `discord.ext.commands.Paginator`.

    See Also
    --------
    :class:`discord.ext.commands.Paginator`

    Parameters
    ----------
    paginator_type: Union[discord.Embed, :class:`str`]
        Content pagination form to use.
    prefix: :class:`str`
        From :attr:`discord.ext.commands.Paginator.prefix`. Character sequence in which all pages should start with.
        Defaults to '```'.
    suffix: :class:`str`
        From :attr:`discord.ext.commands.Paginator.suffix`. Character sequence in which all pages should end with.
        Defaults to '```'.
    max_size: :class:`int`
        From :attr:`discord.ext.commands.Paginator.max_size`. Maximum amount of characters allowed per page.
        Defaults to 2000.
    linesep: :class:`str`
        From :attr:`discord.ext.commands.Paginator.linesep`. Character sequence inserted between each line.
        Defaults to a new line ('\n').

    Attributes
    ----------
    type: Union[discord.Embed, :class:`str`]
        The content type passed to the constructor.
    """

    def __init__(
            self,
            paginator_type: TypeT,
            *,
            prefix: str = "```",
            suffix: str = "```",
            max_size: int = 2000,
            linesep: str = "\n"
    ) -> None:
        super().__init__(prefix, suffix, max_size, linesep)
        self.type: TypeT = paginator_type

    def to_dict(self, content: str) -> dict[str, TypeT]:
        """A useful helper function that can be sent to a :meth:`discord.abc.Messageable.send` as key-word arguments.

        Parameters
        ----------
        content: :class:`str`
            The new content that the dictionary's value should have.

        Returns
        -------
        Dict[:class:`str`, Union[discord.Embed, :class:`str`]]
            A single item dictionary with the content type as its key, and the pagination type as its value.
        """
        if isinstance(self.type, discord.Embed):
            self.type.description = content
            return {"embed": self.type}
        assert isinstance(self.type, str)
        return {"content": content}

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
                super().add_line(l, empty=empty)
            return
        super().add_line(line, empty=empty)


class Interface(discord.ui.View):
    """A paginator interface that implements basic pagination functionality.

    Note that the paginator passed should have more than one page, otherwise IndexError might be raised.

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

    def __init__(self, paginator: Paginator[Any], author: types.User | int) -> None:
        super().__init__()
        self.paginator: Paginator[Any] = paginator
        self.author: int = author.id if isinstance(author, types.User) else author
        self._display_page: int = 1
        self._real_page: int = 0

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

    @discord.ui.button(label="≪", disabled=True)
    async def first_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page = 1
        await interaction.response.edit_message(**self.paginator.to_dict(self.display_page), view=self)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.blurple, disabled=True)
    async def previous_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page -= 1
        await interaction.response.edit_message(**self.paginator.to_dict(self.display_page), view=self)

    @discord.ui.button(label="1", style=discord.ButtonStyle.green)
    async def current(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(_PageSetter(self))

    @discord.ui.button(label="▶", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page += 1
        await interaction.response.edit_message(**self.paginator.to_dict(self.display_page), view=self)

    @discord.ui.button(label="≫")
    async def last_page(self, interaction: discord.Interaction, _) -> None:
        self.current_page = len(self.paginator.pages)
        await interaction.response.edit_message(**self.paginator.to_dict(self.display_page), view=self)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.danger)
    async def remove(self, interaction: discord.Interaction, _) -> None:
        if interaction.message is not None:
            await interaction.message.delete()
