# -*- coding: utf-8 -*-

"""
dev.config.over
~~~~~~~~~~~~~~~

Override or overwrite certain aspects and functions of the bot.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import ast
import contextlib
import inspect
import io
import textwrap
from random import choice
from string import ascii_letters
from typing import Any, Dict, Optional

import discord
from discord.ext import commands

from dev import types

from dev.types import Over, OverType
from dev.converters import CodeblockConverter, convert_str_to_bool, convert_str_to_ints
from dev.handlers import ExceptionHandler, replace_vars
from dev.registrations import CommandRegistration, SettingRegistration

from dev.config._views import CodeView, SettingView

from dev.utils.baseclass import Root, root
from dev.utils.functs import flag_parser, generate_ctx, table_creator, send
from dev.utils.startup import Settings
from dev.utils.utils import clean_code, codeblock_wrapper, plural


class OverrideSettingConverter(commands.Converter):
    default_settings: Dict[str, Any] = {}
    script: str = ""
    command_string: str = ""

    async def convert(self, ctx: commands.Context, argument: str) -> Optional[OverrideSettingConverter]:
        changed = []
        new_settings = flag_parser(argument, "=")
        for key, value in new_settings.items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if not hasattr(Settings, key):
                await ctx.message.add_reaction("❗")
                return
            setting = getattr(Settings, key.upper())
            if isinstance(setting, bool):
                self.default_settings[key] = convert_str_to_bool(value)
                setattr(Settings, key.upper(), convert_str_to_bool(value))
            elif isinstance(setting, set):
                self.default_settings[key] = set(convert_str_to_ints(value))
                setattr(Settings, key.upper(), set(convert_str_to_ints(value)))
            else:
                self.default_settings[key] = value
                setattr(Settings, key.upper(), value)
            changed.append(f"Settings.{key.upper()}={value}")
        await send(
            ctx,
            embed=discord.Embed(
                title="Settings Changed" if self.default_settings else "Nothing Changed",
                description="`" + '`\n`'.join(changed) + "`",
                colour=discord.Color.green() if self.default_settings else discord.Color.red()
            ),
            delete_after=5
        )
        argument = argument.strip()
        if argument.startswith("```") and argument.endswith("```"):
            self.script = argument
        else:
            self.command_string = argument
        return self

    def back_to_default(self):
        for module, value in self.default_settings.items():
            setattr(Settings, module, value)


class RootOver(Root):

    @root.group(name="override", parent="dev", ignore_extra=False, invoke_without_command=True)
    async def root_override(self, ctx: commands.Context):
        """Get a table of overrides that have been made with their respective IDs.
        Name of the command and date modified are also included in the table.
        """
        if overrides := self.registers_from_type(Over.OVERRIDE):
            rows = [
                [index, rgs.qualified_name, f"Date modified: {rgs.created_at}"]
                for index, rgs in enumerate(overrides, start=1)
            ]
            return await send(ctx, f"```py\n{table_creator(rows, ['IDs', 'Names', 'Descriptions'])}\n```")
        await send(ctx, "No overrides have been made.")

    @root.command(name="undo", parent="dev override")
    async def root_override_undo(self, ctx: commands.Context, index: int = 0):
        """Undo an override.
        If the specified override ID is not the last override, then it will simply get deleted.
        """
        if not (overrides := self.registers_from_type(Over.OVERRIDE)):
            return await send(ctx, "No overrides have been made.")
        try:
            if index < 0:
                raise IndexError
            override = overrides[index - 1]
        except IndexError:
            return await send(ctx, f"Override with ID of `{index}` not found.")
        self.update_register(override, Over.DELETE)
        command: types.Command = self.bot.get_command(override.qualified_name)
        command.callback = self.match_register_command(override.qualified_name)[-1].callback
        await ctx.message.add_reaction("☑")

    @root.command(name="changes", parent="dev override")
    async def root_override_changes(self, ctx: commands.Context, index1: int = 0, index2: int = None):
        """Compare changes made between overrides. Optionally compare unique overrides."""
        if not (overrides := self.registers_from_type(Over.OVERRIDE)):
            return await send(ctx, "No overrides have been made.")
        try:
            if index1 < 0:
                raise IndexError
            override = overrides[index1 - 1]
        except IndexError:
            return await send(ctx, f"Override with ID of `{index1}` not found.")
        override2 = None
        if index2 is not None:
            try:
                if index2 < 0:
                    raise IndexError
                override2 = overrides[index2 - 1]
            except IndexError:
                return await send(ctx, f"Override with ID of `{index2}` not found.")
        if override2 is None:
            try:
                if index1 - 2 < 0:
                    raise IndexError
                previous = overrides[index1 - 2]
            except IndexError:
                previous = self.get_base_command(override.qualified_name)
            # source could raise an OSError when trying to be fetched inside BaseCommandRegistration
            if not hasattr(previous, "source"):
                return await send(ctx, "Couldn't compare source codes.")
            if override.source == previous.source:
                return await send(ctx, "No changes were made.")
            return await send(
                ctx,
                [
                    discord.Embed(
                        title=f"Previous Source",
                        description=codeblock_wrapper(override.source, "py"),
                        color=discord.Color.red()
                    ),
                    discord.Embed(
                        title="Current Source",
                        description=codeblock_wrapper(previous.source, "py"),
                        color=discord.Color.green()
                    )
                ]
            )
        if override.source == override2.source:
            return await send(ctx, "No changes were made.")
        first_embed, second_embed = (index1, index2) if index1 < index2 else (index2, index1)
        return await send(
            ctx,
            [
                discord.Embed(
                    title=f"Override #{first_embed}",
                    description=codeblock_wrapper(override.source, "py"),
                    color=discord.Color.red()
                ),
                discord.Embed(
                    title=f"Override #{second_embed}",
                    description=codeblock_wrapper(override2.source, "py"),
                    color=discord.Color.green()
                )
            ]
        )

    @root.command(
        name="command",
        parent="dev override",
        virtual_vars=True,
        require_var_positional=True,
        usage="<command_name> <script>"
    )
    async def root_override_command(self, ctx: commands.Context, *, command_code: CodeblockConverter):
        r"""Temporarily override a command.
        All changes will be undone once the bot is restart or the cog is reloaded.
        This differentiates from its counterpart `dev overwrite` which permanently changes a file.
        Script that will be used as override should be specified between \`\`\`.
        """
        command_string, script = command_code if isinstance(command_code, tuple) else (command_code, None)
        if not command_string:
            return await send(ctx, "Malformed arguments were given.")
        command: types.Command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        # modals have a maximum of 4000 characters
        if not script and len(self.match_register_command(command_string)[-1].source) > 4000:
            return await send(ctx, "The command's source code exceeds the 4000 maximum character limit.")
        if not script:
            return await send(ctx, CodeView(ctx, command, self))
        self.bot.remove_command(command_string)

        # Get file imports, functions and any other top-level expression,
        # so you don't have to rewrite everything yourself
        base_command = self.get_base_command(command.qualified_name)
        additional_attrs = {}
        if base_command is not None:
            file = inspect.getsourcefile(base_command.callback)
            with open(file, "r") as f:
                read = f.read()
            command_registrations = [cmd for cmd in self.registers_from_type(OverType.COMMAND)
                                     if cmd.qualified_name == command.qualified_name][-1]
            file = read.replace(command_registrations.source, "")
            additional_attrs = {}
            exec(compile(file, "<exec>", "exec"), additional_attrs)

        script = clean_code(replace_vars(script, Root.scope))
        scope = {"discord": discord, "commands": commands, "bot": self.bot}
        scope.update(additional_attrs)
        function_name = "__command_getter_"
        # Prevent scoping issues
        while function_name in scope:
            function_name += choice(ascii_letters)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            async with ExceptionHandler(ctx.message, lambda: self.bot.add_command(command)):
                # Make sure everything is parsed correctly
                parsed = ast.parse(script)
                if [ast.AsyncFunctionDef] != [type(expr) for expr in parsed.body]:
                    self.bot.add_command(command)
                    return await send(
                        ctx,
                        "The entire parent body should only consist of a single asynchronous function definition."
                    )
                # Prepare variables for script wrapping
                func: ast.AsyncFunctionDef = parsed.body[-1]  # type: ignore
                body = textwrap.indent("\n".join(script.split("\n")[len(func.decorator_list) + 1:]), "\t")
                parameters = script.split("\n")[func.lineno - 1][len(f"async def {func.name}("):]
                upper = "\n".join(script.split("\n")[:func.lineno - 1])

                exec(
                    f"async def {function_name}():\n"
                    f"\t{upper}\n"
                    f"\tasync def {func.name}({parameters}\n"
                    f"{body}\n"
                    f"\treturn {func.name}",
                    scope
                )
                obj = await scope[f"{function_name}"]()
                # check after execution
                if not isinstance(obj, (commands.Command, commands.Group)):
                    self.bot.add_command(command)
                    return await send(
                        ctx,
                        "The asynchronous function should return an instance of `commands.Command`."
                    )
                if obj.qualified_name != command_string:
                    self.bot.remove_command(obj.qualified_name)
                    self.bot.add_command(command)
                    return await send(ctx, "The command's name cannot be changed.")
                self.update_register(
                    CommandRegistration(
                        obj,
                        Over.OVERRIDE,
                        source=f"{upper.lstrip()}\nasync def {func.name}({parameters}\n{body}\n"),
                    Over.ADD
                )

    @root.command(
        name="setting",
        parent="dev override",
        virtual_vars=True,
        aliases=["settings"],
        require_var_positional=True,
        usage="<setting>... <command_name|script>"
    )
    async def root_override_setting(self, ctx: commands.Context, *, greedy: OverrideSettingConverter):
        """Temporarily override a (some) setting(s).
        All changes will be undone once the command has finished executing.
        This differentiates from `dev overwrite`, which does not switch back once the command has been terminated.
        Multiple settings can be specified.
        Setting overrides should be specified as follows: `setting=attr`.
        Adding single or double quotes in between the different parameters is also a valid option.
        """
        if greedy.script:
            code = clean_code(replace_vars(greedy.script, Root.scope))
            lcls = {"discord": discord, "commands": commands, "bot": self.bot, "ctx": ctx}
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                async with ExceptionHandler(ctx.message, greedy.back_to_default):
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", lcls)
                    await lcls["func"]()
                greedy.back_to_default()
        elif greedy.command_string:
            context = await generate_ctx(
                ctx,
                content=f"{ctx.prefix}{greedy.command_string}",
                author=ctx.author,
                channel=ctx.channel
            )
            if not context.command:
                greedy.back_to_default()
                return await ctx.send(f"Command `{context.invoked_with}` not found.")
            await context.command.invoke(context)
            greedy.back_to_default()

    @root.group(name="overwrite", parent="dev", ignore_extra=False, invoke_without_command=True)
    async def root_overwrite(self, ctx: commands.Context):
        """Get a table of overwrites that have been made with their respective IDs.
        Overwrite type, changes made, and date modified are also included in the table.
        """
        if overwrites := self.registers_from_type(Over.OVERWRITE):
            rows = [
                [index, rgs.over_type.name, f"{rgs} ‒ {rgs.created_at}"]
                for index, rgs in enumerate(overwrites, start=1)
            ]
            return await send(ctx, codeblock_wrapper(table_creator(rows, ['IDs', 'Types', 'Descriptions']), "py"))
        await send(ctx, "No overwrites have been made.")

    @root.command(name="undo", parent="dev overwrite", aliases=["del", "delete"])
    async def root_overwrite_undo(self, ctx: commands.Context, index: int = 0):
        """Undoes or deletes an overwrite.
        If the specified overwrite ID is not the last overwrite, then it will simply get deleted.
        However, settings will get converted back to the value of the previous overwrite, unlike commands.
        """
        if not (overwrites := self.registers_from_type(Over.OVERWRITE)):
            return await send(ctx, "No overwrites have been made.")
        try:
            if index < 0:
                raise IndexError
            overwrite = overwrites[index - 1]
        except IndexError:
            return await send(ctx, f"Overwrite with ID of `{index}` not found.")
        if ctx.invoked_with in ("delete", "del"):
            self.update_register(overwrite, Over.DELETE)
            return await send(
                ctx,
                f"Deleted the override with the ID number of `{index if index != 0 else len(overwrites)}`.\n{overwrite}"
            )
        if overwrite.over_type is OverType.COMMAND:
            assert isinstance(overwrite, CommandRegistration)
            directory = inspect.getsourcefile(self.get_base_command(overwrite.command.qualified_name).callback)
            lines = overwrite.source.split("\n")
            base_command = self.get_base_command(overwrite.qualified_name)
            if not hasattr(base_command, "line_no"):
                return await send(ctx, f"Couldn't get source lines for the command `{overwrite.qualified_name}`.")
            line_no = base_command.line_no
            with open(directory, "r") as f:
                read_lines = f.readlines()
            start, end = line_no, line_no + (len(lines) - 1)
            self.update_register(overwrite, Over.DELETE)
            old_command = self.match_register_command(overwrite.qualified_name)[-1]
            if not hasattr(old_command, "source"):
                return await send(ctx, f"Couldn't get source lines for the command `{overwrite.qualified_name}`.")
            old_lines = old_command.source
            old_lines_split = old_lines.split("\n")
            # make sure that we have the correct amount of lines necessary to include the new script
            if len(old_lines_split) > len(lines):
                with open(directory, "w") as f:
                    read_lines[end] = read_lines[end] + "\n" * (len(old_lines_split) - len(lines))
                    end += len(old_lines_split) - len(lines)
                    f.writelines(read_lines)
                with open(directory, "r") as f:
                    # since we edited the file, we have to get our new set of lines
                    read_lines = f.readlines()
            count = 0
            for line in range(start, end + 1):
                try:
                    read_lines[line] = old_lines_split[count] + "\n" if line != end else old_lines_split[count]
                    count += 1
                except IndexError:
                    # deal with any extra lines, so we don't get a huge whitespace
                    read_lines[line] = ""
            with open(directory, "w") as f:
                f.writelines(read_lines)
            await ctx.message.add_reaction("☑")

        elif overwrite.over_type is OverType.SETTING:
            assert isinstance(overwrite, SettingRegistration)
            for module, option in overwrite.defaults.items():
                setattr(Settings, module, option)
            self.update_register(overwrite, Over.DELETE)
            await ctx.message.add_reaction("☑")

    @root.command(
        name="command",
        parent="dev overwrite",
        virtual_vars=True,
        require_var_positional=True,
        usage="<command_name> <script>"
    )
    async def root_overwrite_command(self, ctx: commands.Context, *, command_code: CodeblockConverter):
        r"""Completely change a command's execution script to be permanently overwritten.
        Script that will be used as the command overwrite should be specified in between \`\`\`.
        This command edits the command's file with the new script, thus changes will be seen once the bot is restarted.
        """
        command_string, script = command_code
        if not all([command_string, script]):
            return await ctx.send("Malformed arguments were given.")
        command: types.Command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        callback = self.get_base_command(command_string).callback
        directory = inspect.getsourcefile(callback)
        lines, line_no = inspect.getsourcelines(callback)
        line_no -= 1
        code = clean_code(replace_vars(script, Root.scope))
        async with ExceptionHandler(ctx.message):
            parsed = ast.parse(code)
            if [ast.AsyncFunctionDef] != [type(expr) for expr in parsed.body]:
                return await send(
                    ctx,
                    "The entire parent body should only consist of a single asynchronous function definition."
                )
        code = code.split("\n")
        indentation = 0
        for char in lines[0]:
            if char == " ":
                indentation += 1
            else:
                break
        # since discord's intents are a multiple of 2 we convert them to multiples of 4.
        # we also add the correct indentation level if necessary
        parsed_code = []
        for line in code:
            amount = 0
            for char in line:
                if char == " ":
                    amount += 1
                amount *= 2
                break
            parsed_code.append(f"{' ' * indentation}{line.replace('  ', '    ', amount)}")
        code = "\n".join(parsed_code)
        with open(directory, "r") as f:
            read_lines = f.readlines()
        start, end = line_no, line_no + (len(lines) - 1)
        # make sure that we have the correct amount of lines necessary to include the new script
        code_split = code.split("\n")
        if len(code_split) > len(lines):
            with open(directory, "w") as f:
                read_lines[end] = read_lines[end] + "\n" * (len(code_split) - len(lines))
                end += len(code_split) - len(lines)
                f.writelines(read_lines)
            with open(directory, "r") as f:
                # since we edited the file, we have to get our new set of lines
                read_lines = f.readlines()
        count = 0
        for line in range(start, end + 1):
            try:
                read_lines[line] = code_split[count] + "\n"
                count += 1
            except IndexError:
                # deal with any extra lines, so we don't get a huge whitespace
                read_lines[line] = ""
        with open(directory, "w") as f:
            f.writelines(read_lines)
        self.update_register(CommandRegistration(command, Over.OVERWRITE, source=code), Over.ADD)
        await ctx.message.add_reaction("☑")

    @root.command(name="setting", parent="dev overwrite", aliases=["settings"])
    async def root_overwrite_setting(self, ctx: commands.Context, *, settings: Optional[str] = None):
        """Temporarily change a setting's value. Settings will be reverted once the bot has been restarted.
        Command execution after setting specification isn't available in this mode.
        Multiple settings can be specified.
        A setting format should be specified as follows: `setting=attr`.
        Adding single or double quotes in between the different parameters is also a valid option.
        """
        if settings is None:
            return await send(ctx, SettingView(ctx.author))
        default = {k: v for k, v in Settings.__dict__.items() if not (k.startswith("__"))}
        changed = []  # a formatted version of the settings that were changed
        raw_changed = {}
        new_settings = flag_parser(settings, "=")
        error_settings = []
        for key, value in new_settings.items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if not hasattr(Settings, key.upper()):
                error_settings.append(key.upper())
        if error_settings:
            return await send(
                ctx,
                f"{plural(len(error_settings), 'Setting', False)} not found: {', '.join(error_settings)}"
            )
        for key, attr in new_settings.items():
            str_setting = key.upper()
            setting = getattr(Settings, str_setting)
            raw_changed[key] = setting
            if isinstance(setting, bool):
                setattr(Settings, str_setting, convert_str_to_bool(attr))
            elif isinstance(setting, set):
                setattr(Settings, str_setting, set(convert_str_to_ints(attr)))
            else:
                setattr(Settings, str_setting, attr)
            changed.append(f"Settings.{str_setting}={attr}")
        self.update_register(SettingRegistration(default, raw_changed), Over.ADD)
        await send(
            ctx,
            discord.Embed(
                title="Settings Changed" if changed else "Nothing Changed",
                description="`" + '`\n`'.join(changed) + "`" if changed else
                "No changes were made to the current version of the settings.",
                color=discord.Color.green() if changed else discord.Color.red()
            )
        )
