# -*- coding: utf-8 -*-

"""
dev.components.views
~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.View` related classes.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import inspect
from typing import Any, Callable, Optional, Union

import discord

from dev import types

__all__ = ("AuthoredMixin", "Prompt", "ModalSender")


class AuthoredMixin(discord.ui.View):
    """A :class:`discord.ui.View` wrapper that optionally adds an owner-only interaction check.

    Parameters
    ----------
    author: Optional[Union[types.User, :class:`int`]]
        The only user that is allowed to interact with this view.
    components: :class:`discord.ui.Item`
        Components that will be automatically added to the view.

    Attributes
    ----------
    author: Optional[:class:`int`]
        The ID of the user that was passed to the constructor of this class.
    """

    def __init__(self, author: Optional[Union[types.User, int]], *components: discord.ui.Item[AuthoredMixin]) -> None:
        super().__init__()
        self.author: int | None = getattr(author, "id", author)  # type: ignore
        for item in components:
            self.add_item(item)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        if self.author is None:
            return True
        return interaction.user.id == self.author


class ModalSender(AuthoredMixin):
    """A view that automatically creates a button that sends a modal.

    Subclass of :class:`AuthoredMixin`.

    Parameters
    ----------
    modal: :class:`discord.ui.Modal`
        The modal that will be sent on interaction.
    author: Union[types.User, :class:`int`]
        The only user that is allowed to interact with this view.
    **kwargs: Any
        Attributes that will be forwarded to the constructor of :class:`discord.ui.Button`.

    Attributes
    ----------
    modal: :class:`discord.ui.Modal`
        The modal that was passed to the constructor of this class.

    Methods
    -------
    sender: :class:`discord.ui.Button`
        The button that handles sending the given modal.
    """

    def __init__(self, modal: discord.ui.Modal, /, author: Union[types.User, int], **kwargs: Any) -> None:
        super().__init__(author)
        self.modal: discord.ui.Modal = modal
        self.sender.label = kwargs.pop("label", None)
        if custom_id := kwargs.pop("custom_id", None):
            self.sender.custom_id = custom_id
        self.sender.disabled = kwargs.pop("disabled", False)
        self.sender.style = kwargs.pop("style", discord.ButtonStyle.secondary)
        self.sender.emoji = kwargs.pop("emoji", None)
        self.sender.row = kwargs.pop("row", None)

    @discord.ui.button()
    async def sender(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(self.modal)


class Prompt(AuthoredMixin):
    """Allows the user to submit a true or false answer through buttons.

    If the user clicks on "Yes", a function is called and the view is removed.

    Subclass of :class:`AuthoredMixin`.

    Examples
    --------
    .. codeblock:: python3
        # inside a command
        async def check():
            await ctx.send("We shall continue!")
        await ctx.send("Would you like to continue?", view=Prompt(ctx.author, check))

    Parameters
    ----------
    author: Union[types.User, :class:`int`]
        The author of the message. It can be either their ID or Discord object.
    func: Optional[Callable[[], Any]]
        The function that should get called if the user clicks on the "Yes" button.
        This function cannot have arguments.
    """

    def __init__(self, author: Union[types.User, int], func: Optional[Callable[[], Any]] = None) -> None:
        super().__init__(author)
        self.func: Optional[Callable[[], Any]] = func
        self.author: int = author.id if isinstance(author, types.User) else author

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.defer()
        if self.func is not None:
            if inspect.iscoroutinefunction(self.func):
                await self.func()
            else:
                self.func()
        await interaction.delete_original_response()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _) -> None:
        if interaction.message:
            await interaction.message.delete()
