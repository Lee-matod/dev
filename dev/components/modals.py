# -*- coding: utf-8 -*-

"""
dev.components.modals
~~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.Modal` related classes.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import ast
import contextlib
import io
import textwrap
from typing import TYPE_CHECKING, Any

import discord

from dev.converters import str_ints
from dev.handlers import ExceptionHandler
from dev.registrations import CommandRegistration, Over
from dev.types import InteractionResponseType

from dev.utils.functs import interaction_response
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types
    from dev.components.views import CodeView, ToggleSettings, VariableModalSender

    from dev.utils.baseclass import Root


__all__ = (
    "CodeEditor",
    "SettingEditor",
    "VariableValueSubmitter"
)


class VariableValueSubmitter(discord.ui.Modal):
    value: discord.ui.TextInput[VariableModalSender] = discord.ui.TextInput(
        label="Value",
        style=discord.TextStyle.paragraph
    )

    def __init__(self, name: str, new: bool, default: str | None = None) -> None:
        self.value.default = default
        super().__init__(title="Value Submitter")
        self.name = name
        self.new = new

    async def on_submit(self, interaction: discord.Interaction) -> None:
        Root.scope.update({self.name: self.value.value})
        await interaction.response.edit_message(
            content=f"Successfully {'created a new variable called' if self.new else 'edited'} `{self.name}`",
            view=None
        )


class CodeEditor(discord.ui.Modal):
    code: discord.ui.TextInput[CodeView] = discord.ui.TextInput(
        label="Code inspection for 'command'",
        style=discord.TextStyle.long
    )

    def __init__(self, ctx: commands.Context[types.Bot], command: types.Command, root: Root) -> None:
        impl = root.get_last_implementation(command.qualified_name)
        assert impl is not None, "Managed to get to modal __init__ even though no registrations were found"
        self.code.label = self.code.label.replace("command", command.qualified_name)
        self.code.default = impl.source

        super().__init__(title=f"{command.name}'s Script")
        self.command: types.Command = command
        self.ctx: commands.Context[types.Bot] = ctx
        self.root: Root = root

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.ctx.bot.remove_command(self.command.qualified_name)
        lcls: dict[str, Any] = {"discord": discord, "commands": commands, "bot": self.ctx.bot}
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            async with ExceptionHandler(self.ctx.message, lambda: self.ctx.bot.add_command(self.command)):
                # make sure everything is parsed correctly
                parsed = ast.parse(self.code.value)
                if [ast.AsyncFunctionDef] != [type(expr) for expr in parsed.body]:
                    self.ctx.bot.add_command(self.command)
                    return await interaction_response(
                        interaction,
                        InteractionResponseType.EDIT,
                        "The entire parent body should only consist of a single asynchronous function definition.",
                        view=None
                    )
                # prepare variables for script wrapping
                func: ast.AsyncFunctionDef = parsed.body[-1]  # type: ignore
                body = textwrap.indent("\n".join(self.code.value.split("\n")[len(func.decorator_list) + 1:]), "\t")
                parameters = self.code.value.split("\n")[func.lineno - 1][len(f"async def {func.name}("):]
                upper = "\n".join(self.code.value.split("\n")[:func.lineno - 1])

                exec(
                    f"async def func():\n\t{upper}\n\tasync def {func.name}({parameters}\n{body}\n\treturn {func.name}",
                    lcls
                )
                obj: commands.Command[Any, ..., Any] | commands.Group[Any, ..., Any] = await lcls["func"]()
                # check after execution
                if not isinstance(obj, (commands.Command, commands.Group)):
                    self.ctx.bot.add_command(self.command)
                    return await interaction_response(
                        interaction,
                        InteractionResponseType.EDIT,
                        "The asynchronous function should return an instance of `commands.Command`.",
                        view=None
                    )
                if obj.qualified_name != self.command.qualified_name:
                    self.ctx.bot.remove_command(obj.qualified_name)
                    self.ctx.bot.add_command(self.command)
                    return await interaction_response(
                        interaction,
                        InteractionResponseType.EDIT,
                        "The command's name cannot be changed.",
                        view=None
                    )
                self.root.update_register(
                    CommandRegistration(
                        obj,  # type: ignore
                        Over.OVERRIDE,
                        source=f"{upper.lstrip()}\nasync def {func.name}({parameters}\n{body}"),
                    Over.ADD
                )
        await interaction_response(
            interaction,
            InteractionResponseType.EDIT,
            "New script has been submitted.",
            view=None
        )


class SettingEditor(discord.ui.Modal):
    def __init__(self, author: types.User, setting: str) -> None:
        self.author: types.User = author
        self.setting: str = setting
        self.setting_obj: set[int] | str = getattr(Settings, setting)
        self.item: discord.ui.TextInput[ToggleSettings] = discord.ui.TextInput(
            label=setting.replace("_", " ").title(),
            default=", ".join([str(i) for i in self.setting_obj])
        )
        super().__init__(title=f"{setting.replace('_', ' ').title()} Editor")
        self.add_item(self.item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if isinstance(self.setting_obj, set):
            setattr(Settings, self.setting, set(str_ints(self.item.value)))
        #  bool instances are toggleable buttons
        else:
            setattr(Settings, self.setting, self.item.value)
        await interaction_response(
            interaction,
            InteractionResponseType.EDIT,
            type(self.item.view)(self.author)  # type: ignore
        )