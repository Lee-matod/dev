# -*- coding: utf-8 -*-

"""
dev.components.views
~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.View` related classes.

:copyright: Copyright 2023 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable, Coroutine, overload

import discord

from dev import types
from dev.types import InteractionResponseType

from dev.utils.functs import interaction_response

if TYPE_CHECKING:
    from dev.interpreters import Process

__all__ = (
    "AuthoredView",
    "BoolInput",
    "ModalSender",
    "SigKill"
)


class AuthoredView(discord.ui.View):
    """A :class:`discord.ui.View` wrapper that automatically adds an owner-only interaction check.

    Parameters
    ----------
    author: Union[types.User, :class:`int`]
        The only user that is allowed to interact with this view.
    components: :class:`discord.ui.Item`
        Components that will be automatically added to the view.

    Attributes
    ----------
    author: :class:`int`
        The ID of the user that was passed to the constructor of this class.
    """

    def __init__(self, author: types.User | int, *components: discord.ui.Item[AuthoredView]) -> None:
        super().__init__()
        self.author: int = author.id if isinstance(author, types.User) else author  # type: ignore
        for item in components:
            self.add_item(item)

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        return interaction.user.id == self.author


class ModalSender(AuthoredView):
    """A view that automatically creates a button that sends a modal.

    Subclass of :class:`AuthoredView`.

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

    def __init__(self, modal: discord.ui.Modal, /, author: types.User | int, **kwargs: Any) -> None:
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


class BoolInput(AuthoredView):
    """Allows the user to submit a true or false answer through buttons.

    If the user clicks on "Yes", a function is called and the view is removed.

    Subclass of :class:`AuthoredView`.

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

    @overload
    def __init__(self, author: types.User | int, func: Callable[[], Coroutine[Any, Any, Any]] | None = ...) -> None:
        ...

    @overload
    def __init__(self, author: types.User | int, func: Callable[[], Any] | None = ...) -> None:
        ...

    def __init__(self, author: Any, func: Any = None) -> None:
        super().__init__(author)
        self.func: Callable[[], Any] | None = func
        self.author: int = author.id if isinstance(author, types.User) else author  # type: ignore

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes_button(self, interaction: discord.Interaction, _) -> None:
        if self.func is not None:
            if inspect.iscoroutinefunction(self.func):
                await self.func()
            else:
                self.func()
        await interaction.delete_original_response()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no_button(self, interaction: discord.Interaction, _) -> None:
        await interaction.delete_original_response()


class SigKill(discord.ui.View):
    def __init__(self, process: Process, /):
        super().__init__()
        self.session: ShellSession = process._Process__session  # type: ignore
        self.process: Process = process

    @discord.ui.button(label="Kill", emoji="\u26D4", style=discord.ButtonStyle.danger)
    async def signalkill(self, interaction: discord.Interaction, button: discord.ui.Button[SigKill]):
        self.process.process.kill()
        self.process.process.terminate()
        self.process.force_kill = True
        await interaction_response(
            interaction,
            InteractionResponseType.EDIT,
            self.session.raw,  # type: ignore
            view=None,
            paginator=self.session.paginator  # type: ignore
        )
