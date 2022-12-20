# -*- coding: utf-8 -*-

"""
dev.components.views
~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.View` related classes.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Generator, overload

import discord

from dev.types import InteractionResponseType
from dev.components.buttons import SettingsToggler
from dev.components.modals import CodeEditor, VariableValueSubmitter

from dev.utils.functs import interaction_response
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types
    from dev.interpreters import Process

    from dev.utils.baseclass import Root


__all__ = (
    "BoolInput",
    "CodeView",
    "PermissionsViewer",
    "SearchResultCategory",
    "SigKill",
    "ToggleSettings",
    "VariableModalSender"
)


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

    @overload
    def __init__(self, author: types.User | int, func: Callable[[], Coroutine[Any, Any, Any]] | None = ...) -> None:
        ...

    @overload
    def __init__(self, author: types.User | int, func: Callable[[], Any] | None = ...) -> None:
        ...

    def __init__(self, author: Any, func: Any = None) -> None:
        super().__init__()
        self.func: Callable[[], Any] | None = func
        self.author: int = author.id if isinstance(author, types.User) else author  # type: ignore

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user.id

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


class ToggleSettings(discord.ui.View):
    def __init__(self, author: types.User) -> None:
        super().__init__()
        self.author: types.User = author
        self.add_buttons()

    def add_buttons(self):
        for setting in [setting for setting in Settings.kwargs.keys()]:
            fmt = " ".join(word.lower() if len(word) <= 2 else word.title() for word in setting.split("_"))
            self.add_item(SettingsToggler(setting, self.author, label=fmt))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user


class CodeView(discord.ui.View):
    def __init__(self, ctx: commands.Context[types.Bot], command: types.Command, root: Root) -> None:
        super().__init__()
        self.ctx: commands.Context[types.Bot] = ctx
        self.command: types.Command = command
        self.root: Root = root

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.ctx.author == interaction.user

    @discord.ui.button(label="View Code", style=discord.ButtonStyle.blurple)
    async def view_code(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(CodeEditor(self.ctx, self.command, self.root))


class VariableModalSender(discord.ui.View):
    def __init__(self, name: str, new: bool, author: types.User, default: str | None = None) -> None:
        super().__init__()
        self.name = name
        self.new = new
        self.author = author
        self.default = default

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user

    @discord.ui.button(label="Submit Variable Value", style=discord.ButtonStyle.gray)
    async def submit_value(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(VariableValueSubmitter(self.name, self.new, self.default))


class SearchResultCategory(discord.ui.View):
    options = [
        discord.SelectOption(label="All", value="all", default=True),
        discord.SelectOption(label="Cogs", value="cogs"),
        discord.SelectOption(label="Commands", value="commands"),
        discord.SelectOption(label="Emojis", value="emojis"),
        discord.SelectOption(label="Text Channels", value="text_channels"),
        discord.SelectOption(label="Members", value="members"),
        discord.SelectOption(label="Roles", value="roles")
    ]

    def __init__(
            self,
            ctx: commands.Context[types.Bot],
            embed: discord.Embed,
            *,
            cogs: list[str],
            cmds: list[str],
            channels: list[str],
            emojis: list[str],
            members: list[str],
            roles: list[str]
    ) -> None:
        self.mapping = {
            "all": self.join_multi_iter([cogs, cmds, channels, emojis, members, roles], max_amount=7),
            "cogs": "\n".join(cogs),
            "commands": "\n".join(cmds),
            "text_channels": "\n".join(channels),
            "emojis": "\n".join(emojis),
            "members": "\n".join(members),
            "roles": "\n".join(roles)
        }
        for option in self.options.copy():
            if not self.mapping[option.value]:
                self.options.remove(option)
        super().__init__()
        self.ctx = ctx
        self.embed = embed
        self.message: discord.Message | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.ctx.author == interaction.user

    @discord.ui.select(options=options)
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select[SearchResultCategory]) -> None:
        for option in select.options:
            if option.value != select.values[0]:
                option.default = False
            else:
                option.default = True
        self.embed.description = self.mapping.get(select.values[0])
        self.embed.set_footer(text=f'Category: {select.values[0].capitalize().replace("_", " ")}')
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def on_timeout(self) -> None:
        self.callback.disabled = True
        message = self.message
        if message is None:
            raise RuntimeError("Message could not be set")
        await message.edit(view=self)

    @staticmethod
    def join_multi_iter(iterables: list[list[str]], delimiter: str = "\n", max_amount: int | None = None) -> str:
        joined_iter: list[str] = []
        for iterable in iterables:
            if iterable:
                joined_iter.append(f"{delimiter}".join(iterable))
        return f"{delimiter}".join(joined_iter[:max_amount]).strip(f"{delimiter}")


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


class PermissionsViewer(discord.ui.View):
    options = [
        discord.SelectOption(
            label="General",
            value="general",
            description="All 'General' permissions from the official Discord UI.",
            default=True
        ),
        discord.SelectOption(
            label="All Channel",
            value="all_channel",
            description="All channel-specific permissions."
        ),
        discord.SelectOption(
            label="Membership",
            value="membership",
            description="All 'Membership' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Text",
            value="text",
            description="All 'Text' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Voice",
            value="voice",
            description="All 'Voice' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Stage",
            value="stage",
            description="All 'Stage Channel' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Stage Moderator",
            value="stage_moderator",
            description="All permissions for stage moderators."
        ),
        discord.SelectOption(
            label="Elevated",
            value="elevated",
            description="All permissions that require 2FA (2 Factor Authentication)."
        ),
        discord.SelectOption(
            label="Advanced",
            value="advanced",
            description="All 'Advanced' permissions from the official Discord UI."
        )
    ]

    def __init__(self, target: discord.Member, channel: types.Channel | None = None) -> None:
        super().__init__()
        self.user_target: discord.Member = target
        self.channel_target: types.Channel | None = channel

    @discord.ui.select(options=options)
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select[PermissionsViewer]) -> None:
        for option in select.options:
            if option.value != select.values[0]:
                option.default = False
            else:
                option.default = True
        permissions = ["```ansi", *self.sort_perms(select.values[0]), "```"]
        await interaction.response.edit_message(
            embed=discord.Embed(description="\n".join(permissions), color=discord.Color.blurple()),
            view=self
        )

    def sort_perms(self, permission: str) -> Generator[str, None, None]:
        perms = getattr(discord.Permissions, permission)()
        for perm, value in perms:
            if not value:
                continue
            if self.channel_target is not None:
                toggled = dict(self.channel_target.permissions_for(self.user_target)).get(perm)
                yield f"\u001b[1;37m{perm.replace('_', ' ').title():26}\u001b[0;{'32' if toggled else '31'}m{toggled}"
            else:
                toggled = dict(self.user_target.guild_permissions).get(perm)
                yield f"\u001b[1;37m{perm.replace('_', ' ').title():26}\u001b[0;{'32' if toggled else '31'}m{toggled}"