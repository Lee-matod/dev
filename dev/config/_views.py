# -*- coding: utf-8 -*-

"""
dev.config._views
~~~~~~~~~~~~~~~~~

Views and Modals to be used in dev.config.over.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import ast
import contextlib
import io
import textwrap
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dev.converters import str_ints
from dev.handlers import ExceptionHandler
from dev.registrations import CommandRegistration
from dev.types import InteractionResponseType, Over

from dev.utils.baseclass import Root
from dev.utils.functs import interaction_response
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from dev import types


class _SettingEditor(discord.ui.Modal):
    def __init__(self, author: types.User, setting: str) -> None:
        self.author: types.User = author
        self.setting: str = setting
        self.setting_obj: types.Setting = getattr(Settings, setting)
        self.item = discord.ui.TextInput(
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
        await interaction_response(interaction, InteractionResponseType.EDIT, SettingView(self.author))


class _Button(discord.ui.Button):
    def __init__(self, setting: str, author: types.User, *, label: str) -> None:
        super().__init__(label=label)
        self.author: types.User = author
        self.setting: str = setting
        if label in ("Allow Global Uses", "Invoke on Edit"):
            self.style = discord.ButtonStyle.green if getattr(Settings, setting) else discord.ButtonStyle.red
        else:
            self.style = discord.ButtonStyle.blurple

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.setting not in [sett for sett, ann in Settings.__annotations__.items() if ann == "bool"]:
            return await interaction.response.send_modal(
                _SettingEditor(self.author, self.label.replace(" ", "_").upper())
            )
        setting = self.setting.upper().replace(" ", "_")
        if self.style == discord.ButtonStyle.green:
            setattr(Settings, setting, False)
            self.style = discord.ButtonStyle.red
        else:
            setattr(Settings, setting, True)
            self.style = discord.ButtonStyle.green
        await interaction_response(interaction, InteractionResponseType.EDIT, SettingView(self.author))


class SettingView(discord.ui.View):
    def __init__(self, author: types.User) -> None:
        super().__init__()
        self.author: types.User = author

        for setting in [setting for setting in Settings.__dict__.keys() if not setting.startswith("__")]:
            self.add_item(_Button(setting, self.author, label=_format_setting(setting)))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user


class _CodeEditor(discord.ui.Modal):
    code = discord.ui.TextInput(label="Code Inspection for 'command'", style=discord.TextStyle.long)

    def __init__(self, ctx: commands.Context, command: types.Command, root: Root) -> None:
        self.code.label = self.code.label.replace("command", command.qualified_name)
        self.code.default = root.match_register_command(command.qualified_name)[-1].source

        super().__init__(title=f"{command.name}'s Script")
        self.command: types.Command = command
        self.ctx: commands.Context = ctx
        self.root: Root = root

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self.ctx.bot.remove_command(self.command.qualified_name)
        lcls = {"discord": discord, "commands": commands, "bot": self.ctx.bot}
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
                obj = await lcls["func"]()
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
                        obj,
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


class CodeView(discord.ui.View):
    def __init__(self, ctx: commands.Context, command: types.Command, root: Root) -> None:
        super().__init__()
        self.ctx: commands.Context = ctx
        self.command: types.Command = command
        self.root: Root = root

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.ctx.author == interaction.user

    @discord.ui.button(label="View Code", style=discord.ButtonStyle.blurple)
    async def view_code(self, interaction: discord.Interaction, _) -> None:
        await interaction.response.send_modal(_CodeEditor(self.ctx, self.command, self.root))


def _format_setting(setting: str) -> str:
    setting_name = []
    for word in setting.split("_"):
        if len(word) <= 2:
            setting_name.append(word.lower())
        else:
            setting_name.append(word.title())
    return " ".join(setting_name)
