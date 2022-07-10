# -*- coding: utf-8 -*-

"""
dev.config._views
~~~~~~~~~~~~~~~~~

Views and Modals to be used in ``dev.config.over``.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


import ast
import contextlib
import io
import textwrap
from typing import Any, Dict

import discord
from discord.ext import commands

from dev.converters import convert_str_to_ints
from dev.handlers import ExceptionHandler
from dev.registrations import CommandRegistration
from dev.types import AnyUser, AnyCommand

from dev.utils.baseclass import Root
from dev.utils.startup import Settings


class _SettingEditor(discord.ui.Modal):
    def __init__(self, author: AnyUser, setting: str):
        self.author = author
        self.setting = setting
        self.setting_obj = getattr(Settings, setting)
        self.item = discord.ui.TextInput(label=setting.replace("_", " ").title(), default=", ".join([str(i) for i in self.setting_obj]))
        super().__init__(title=f"{setting.replace('_', ' ').title()} Editor")
        self.add_item(self.item)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if isinstance(self.setting_obj, set):
            setattr(Settings, self.setting, set(convert_str_to_ints(self.item.value)))
        else:
            setattr(Settings, self.setting, self.item.value)
        await interaction.response.edit_message(view=SettingView(self.author))


class _Button(discord.ui.Button):
    def __init__(self, setting: str, author: AnyUser, *, label: str):
        super().__init__(label=label)
        self.author = author
        self.setting = setting
        if setting in ("Allow Global Uses", "Invoke on Edit"):
            self.style = discord.ButtonStyle.green if getattr(Settings, setting.replace(" ", "_").upper()) else discord.ButtonStyle.red
        else:
            self.style = discord.ButtonStyle.blurple

    async def callback(self, interaction: discord.Interaction):
        if self.setting not in ("Allow Global Uses", "Invoke on Edit"):
            return await interaction.response.send_modal(_SettingEditor(self.author, self.label.replace(" ", "_").upper()))
        setting = self.setting.upper().replace(" ", "_")
        if self.style == discord.ButtonStyle.green:
            setattr(Settings, setting, False)
            self.style = discord.ButtonStyle.red
        else:
            setattr(Settings, setting, True)
            self.style = discord.ButtonStyle.green
        await interaction.response.edit_message(view=SettingView(self.author))


class SettingView(discord.ui.View):
    def __init__(self, author: AnyUser):
        super().__init__()
        self.author = author

        for setting in ("Allow Global Uses", "Flag Delimiter", "Invoke on Edit", "Owners", "Path to File", "Root Folder", "Virtual Vars"):
            self.add_item(_Button(setting, self.author, label=setting))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user


class _CodeEditor(discord.ui.Modal):
    code = discord.ui.TextInput(label="Code Inspection for 'command'", style=discord.TextStyle.long)

    def __init__(self, ctx: commands.Context, command: AnyCommand, root: Root):
        self.code.label = self.code.label.replace("command", command.name)
        self.code.default = root.to_register(command.qualified_name)[-1].source
        super().__init__(title=f"{command.name}'s Script")
        self.command: AnyCommand = command
        self.ctx: commands.Context = ctx
        self.root: Root = root

    async def on_submit(self, interaction: discord.Interaction):
        self.ctx.bot.remove_command(self.command.qualified_name)
        local_vars: Dict[str, Any] = {
            "discord": discord,
            "commands": commands,
            "bot": self.ctx.bot,
        }
        with contextlib.redirect_stdout(io.StringIO()):
            async with ExceptionHandler(self.ctx.message, on_error=lambda: self.ctx.bot.add_command(self.command)):
                parsed = ast.parse(self.code.value)
                if any([isinstance(x, ast.FunctionDef) for x in parsed.body]):
                    self.ctx.bot.add_command(self.command)
                    return await interaction.response.edit_message(content="There should only be 1 function in the script: the command callback.", view=None)
                if len([x for x in parsed.body if isinstance(x, ast.AsyncFunctionDef)]) > 1:
                    self.ctx.bot.add_command(self.command)
                    return await interaction.response.edit_message(content="Cannot have more than 1 asynchronous function definition in the script.", view=None)
                if not isinstance(parsed.body[-1], ast.AsyncFunctionDef):
                    self.ctx.bot.add_command(self.command)
                    return await interaction.response.edit_message(content="The last expression of the script should be an asynchronous function.", view=None)
                func: ast.AsyncFunctionDef = parsed.body[-1]  # type: ignore
                body = textwrap.indent("\n".join(self.code.value.split("\n")[len(func.decorator_list) + func.lineno - 1:]), "\t")
                parameters = self.code.value.split("\n")[func.lineno - 1][len(f"async def {func.name}("):]
                upper = textwrap.indent("\n".join(self.code.value.split("\n")[:func.lineno - 1]), "\t")
                exec(f"async def func():\n{upper}\n\tasync def {func.name}({parameters}\n{body}\n\treturn {func.name}", local_vars)
                obj = await local_vars["func"]()
                if not isinstance(obj, (commands.Command, commands.Group)):
                    self.ctx.bot.add_command(self.command)
                    return await interaction.response.edit_message(content="The asynchronous function of the script should be a decorated function returning an instance of either `commands.Command` or `commands.Group`.", view=None)
                if obj.name != self.command.qualified_name:
                    self.ctx.bot.remove_command(obj.qualified_name)
                    self.ctx.bot.add_command(self.command)
                    return await interaction.response.edit_message(content="The command's name cannot be changed.", view=None)
                self.root.update_register(CommandRegistration(obj, "override", source=f"{upper.lstrip()}\nasync def {func.name}({parameters}\n{body}"), "add")
        await interaction.response.edit_message(content="New script has been submitted.", view=None)


class CodeView(discord.ui.View):
    def __init__(self, ctx: commands.Context, command: AnyCommand, root: Root):
        super().__init__()
        self.ctx: commands.Context = ctx
        self.command: AnyCommand = command
        self.root: Root = root

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.ctx.author == interaction.user

    @discord.ui.button(label="View Code", style=discord.ButtonStyle.blurple)
    async def view_code(self, interaction: discord.Interaction, _):  # 'button' is not being used
        await interaction.response.send_modal(_CodeEditor(self.ctx, self.command, self.root))
