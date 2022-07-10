# -*- coding: utf-8 -*-

"""
dev.config.over
~~~~~~~~~~~~~~~

Override or overwrite certain aspects and functions of the bot.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import (
    Any,
    Dict,
    Optional
)

import ast
import contextlib
import inspect
import io
import textwrap

import discord
from discord.ext import commands
from typing_extensions import Self

from dev.types import AnyCommand
from dev.converters import CodeblockConverter, convert_str_to_bool, convert_str_to_ints
from dev.handlers import ExceptionHandler, replace_vars, optional_raise
from dev.registrations import CommandRegistration, SettingRegistration

from dev.config._views import CodeView, SettingView

from dev.utils.baseclass import Root, root
from dev.utils.functs import flag_parser, generate_ctx, table_creator, send
from dev.utils.startup import Settings
from dev.utils.utils import clean_code


class OverrideSettingConverter(commands.Converter):
    default_settings: Dict[str, Any] = {}
    script: str = ""
    command_string: str = ""

    async def convert(self, ctx: commands.Context, argument: str) -> Optional[Self]:
        changed = []
        new_settings = flag_parser(argument, "=")
        for key, value in new_settings.items():
            if key.startswith("__") and key.endswith("__"):  # you sneaky person, I ain't gonna let you break it that easily
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
        await ctx.send(embed=discord.Embed(title="Settings Changed" if self.default_settings else "Nothing Changed", description="`" + '`\n`'.join(changed) + "`", colour=discord.Color.green() if self.default_settings else discord.Color.red()), delete_after=5)
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

    @root.group(name="override", parent="dev", invoke_without_command=True, ignore_extra=False)
    async def root_override(self, ctx: commands.Context):
        """Get a table of overrides that have been made with their respective IDs."""
        if overrides := self.filter_register_type("override"):
            rows = [[index, rgs.qualified_name, f"Date modified: {rgs.created_at}"] for index, rgs in enumerate(overrides, start=1)]
            return await send(ctx, f"```py\n{table_creator(rows, ['IDs', 'Names', 'Descriptions'])}\n```")
        await send(ctx, "No overrides have been made.")

    @root_override.command(name="undo")
    async def root_override_undo(self, ctx: commands.Context, id_num: int = 0):
        """Undo an override.
        If the specified override ID is not the last override that a command went through, then it will simply get deleted.
        """
        if not (overrides := self.filter_register_type("override")):
            return await send(ctx, "No overrides have been made.")
        try:
            if id_num < 0:
                raise IndexError
            override = overrides[id_num - 1]
        except IndexError:
            return await send(ctx, f"Override with ID of `{id_num}` not found.")
        self.update_register(override, "del")
        if ctx.invoked_with in ("delete", "del"):
            return await send(ctx, f"Deleted the override with the ID number of `{id_num if id_num != 0 else len(overrides)}` (command: `{override.qualified_name}`).")
        command: AnyCommand = self.bot.get_command(override.qualified_name)
        command.callback = self.to_register(override.qualified_name)[-1].callback
        await ctx.message.add_reaction("☑")

    @root_override.command(name="changes")
    async def root_override_changes(self, ctx: commands.Context, id_num: int = 0):
        """View the changes that were made between overrides.
        Setting overrides will not be shown as they are reverted to default once the command has finished doing the task.
        """
        if not (overrides := self.filter_register_type("override")):
            return await send(ctx, "No overrides have been made.")
        try:
            if id_num < 0:
                raise IndexError
            override = overrides[id_num - 1]
        except IndexError:
            return await send(ctx, f"Override with ID of `{id_num}` not found.")
        current_index: int = list(self.registrations.values()).index(override)
        previous_index: Optional[int] = None
        for position, rgs in enumerate(self.registrations.values()):
            if rgs.qualified_name == override.qualified_name and position < current_index:
                previous_index = position
            elif position == current_index:
                break
        if previous_index is not None:
            previous_script = self.to_register(override.qualified_name)[previous_index].source
        else:
            previous_script = inspect.getsource(self.get_base_command(override.qualified_name).callback)
        if previous_script == override.source:
            return await send(ctx, "No changes were made.")
        return await send(ctx, [discord.Embed(title="Previous Source Code", description=f"```py\n{previous_script}\n```", color=discord.Color.red()),
                                discord.Embed(title="Current Source Code", description=f"```py\n{override.source}\n```", color=discord.Color.green())])

    @root_override.command(name="command", virtual_vars=True, usage="<command_name> <script>", require_var_positional=True)
    async def root_override_command(self, ctx: commands.Context, *, command_code: CodeblockConverter):
        r"""Temporarily override a command. All changes will be undone once the bot is restart or the cog is reloaded. This differentiates from its counterpart `dev overwrite` which permanently changes a file.
        Override the script that a specified command executes.
        Script that will be used as overrides should be specified in between \`\`\`.
        """
        command_string, script = command_code if isinstance(command_code, tuple) else (command_code, None)
        if not command_string:
            return await send(ctx, "Malformed arguments were given.")
        command: AnyCommand = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        lines = self.to_register(command_string)[-1].source
        if not script and len(lines) > 4000:
            return await send(ctx, "The command's source code exceeds the 4000 maximum character limit.")
        if not script:
            return await send(ctx, CodeView(ctx, command, self))
        self.bot.remove_command(command_string)
        script = clean_code(replace_vars(script))
        local_vars: Dict[str, Any] = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
        }
        with contextlib.redirect_stdout(io.StringIO()):
            async with ExceptionHandler(ctx.message, lambda: self.bot.add_command(command)):
                parsed = ast.parse(script)
                if any([isinstance(x, ast.FunctionDef) for x in parsed.body]):
                    self.bot.add_command(command)
                    return await send(ctx, "There should only be 1 function in the script: the command callback.")
                if len([x for x in parsed.body if isinstance(x, ast.AsyncFunctionDef)]) > 1:
                    self.bot.add_command(command)
                    return await send(ctx, "Cannot have more than 1 asynchronous function definition in the script.")
                if not isinstance(parsed.body[-1], ast.AsyncFunctionDef):
                    self.bot.add_command(command)
                    return await send(ctx, "The last expression of the script should be an asynchronous function.")
                func: ast.AsyncFunctionDef = parsed.body[-1]  # type: ignore
                body = textwrap.indent("\n".join(script.split("\n")[len(func.decorator_list) + 1:]), "\t")
                parameters = script.split("\n")[func.lineno - 1][len(f"async def {func.name}("):]
                upper = "\n".join(script.split("\n")[:func.lineno - 1])
                exec(f"async def func():\n\t{upper}\n\tasync def {func.name}({parameters}\n{body}\n\treturn {func.name}", local_vars)
                obj = await local_vars["func"]()
                if not isinstance(obj, (commands.Command, commands.Group)):
                    self.bot.add_command(command)
                    return await send(ctx, "The asynchronous function of the script should be a decorated function returning an instance of either `commands.Command` or `commands.Group`.")
                if obj.name != command_string:
                    self.bot.remove_command(obj.qualified_name)
                    self.bot.add_command(command)
                    return await send(ctx, "The command's name cannot be changed.")
                self.update_register(CommandRegistration(obj, "override", source=f"{upper.lstrip()}\nasync def {func.name}({parameters}\n{body}\n"), "add")

    @root_override.command(name="setting", virtual_vars=True, aliases=["settings"], usage="<setting>... <command_name|script>", require_var_positional=True)
    async def root_override_setting(self, ctx: commands.Context, *, greedy: OverrideSettingConverter):
        """Temporarily override a (some) setting(s). All changes will be undone once the command has finished executing. This differentiates from its counterpart `dev overwrite` which does not switch back once the command has been terminated.
        Multiple settings can be specified.
        Override a setting and execute a command or script with the new set of specified setting(s). When it is done executed, the setting will revert to default.
        Setting overrides should be specified as follows: `setting=attr`. Adding single or double quotes in between the different parameters is also a valid option.
        """
        if greedy.script:
            code = clean_code(replace_vars(greedy.script))
            local_vars = {
                "discord": discord,
                "commands": commands,
                "bot": self.bot,
                "ctx": ctx
            }
            with contextlib.redirect_stdout(io.StringIO()):
                async with ExceptionHandler(ctx.message, greedy.back_to_default):
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", local_vars)
                    await local_vars["func"]()
                greedy.back_to_default()
        elif greedy.command_string:
            kwargs = {"content": f"{ctx.prefix}{greedy.command_string}", "author": ctx.author, "channel": ctx.channel}
            context = await generate_ctx(ctx, **kwargs)
            if not context.command:
                greedy.back_to_default()
                return await ctx.send(f"Command `{context.invoked_with}` not found.")
            await context.command.invoke(context)
            greedy.back_to_default()

    @root.group(name="overwrite", parent="dev", invoke_without_command=True, ignore_extra=False)
    async def root_overwrite(self, ctx: commands.Context):
        """Get a table of overwrites that have been made with their respective IDs."""
        if overwrites := self.filter_register_type("overwrite"):
            rows = [[index, rgs.over_type, f"{rgs} ‒ {rgs.created_at}"] for index, rgs in enumerate(overwrites, start=1)]
            return await send(ctx, f"```py\n{table_creator(rows, ['IDs', 'Types', 'Descriptions'])}\n```")
        await send(ctx, "No overwrites have been made.")

    @root_overwrite.command(name="undo")
    async def root_overwrite_undo(self, ctx: commands.Context, id_num: int = 0):
        """Undoes or deletes an overwrite.
        If the specified overwrite ID is not the last override that a command went through, then it will simply get deleted.
        However, settings will get converted back to the value of the previous overwrite, unlike commands.
        """
        if not (overwrites := self.filter_register_type("overwrite")):
            return await send(ctx, "No overwrites have been made.")
        try:
            if id_num < 0:
                raise IndexError
            overwrite = overwrites[id_num - 1]
        except IndexError:
            return await send(ctx, f"Overwrite with ID of `{id_num}` not found.")
        if ctx.invoked_with in ("delete", "del"):
            self.update_register(overwrite, "del")
            return await send(ctx, f"Deleted the override with the ID number of `{id_num if id_num != 0 else len(overwrites)}`.\n{overwrite}")
        if overwrite.over_type == "command":
            directory = inspect.getsourcefile(overwrite.callback)
            lines = [line + "\n" for line in overwrite.source.split("\n")]
            with open(directory, "r") as f:
                read_lines = f.readlines()
                rev_read_lines = read_lines.copy()
                rev_read_lines.reverse()
            # find what lines we have to edit
            start_counter, end_counter = 0, len(lines) - 1
            start, end = None, None
            # sometimes there could be a repeated line of code which may raise a false positive,
            # this is why we have to make sure there's the correct difference between the start
            # and end lines of the file and the one's we're searching for
            while start is None and end is None:
                if read_lines[start_counter] == lines[0]:
                    start = start_counter
                if read_lines[end_counter] == lines[-1]:
                    end = end_counter
                start_counter += 1
                end_counter += 1
            if None in (start, end):
                return await send(ctx, f"Couldn't find the correct source lines for the command.")
            self.update_register(overwrite, "del")
            old_lines = self.to_register(overwrite.qualified_name)[-1].source
            # make sure that we have the correct amount of lines necessary to include the new script
            if len(old_lines.split("\n")) > len(lines):
                with open(directory, "w") as f:
                    read_lines[end] = read_lines[end] + "\n" * (len(old_lines.split("\n")) - len(lines))
                    end += len(old_lines.split("\n")) - len(lines)
                    f.writelines(read_lines)
                with open(directory, "r") as f:
                    # since we edited the file, we have to get our new set of lines
                    read_lines = f.readlines()

            with open(directory, "w") as f:
                count = 0
                for line in range(start, end + 1):
                    try:
                        read_lines[line] = old_lines.split("\n")[count] + "\n" if line != end else old_lines.split("\n")[count]
                        count += 1
                    except IndexError:
                        # deal with any extra lines, so we don't get a huge whitespace
                        read_lines[line] = ""
                f.writelines(read_lines)
            await ctx.message.add_reaction("☑")

        elif overwrite.over_type == "setting":
            for module, option in overwrite.defaults.items():
                setattr(Settings, module, option)
            self.update_register(overwrite, "del")
            await ctx.message.add_reaction("☑")

    @root_overwrite.command(name="command", virtual_vars=True, usage=r"<command_name> <script>", require_var_positional=True)
    async def root_overwrite_command(self, ctx: commands.Context, *, command_code: CodeblockConverter):
        r"""Completely change a command's execution script to be permanently overwritten.
        Script that will be used as the command overwrite should be specified in between \`\`\`.
        This command edit the command's filed with the new script, therefore changes will be seen once the bot gets restarted.
        """
        command_string, script = command_code
        if not command_string or not script:
            return await ctx.send("Malformed arguments were given.")
        command: AnyCommand = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        callback = self.get_base_command(command_string).callback
        directory = inspect.getsourcefile(callback)
        lines, _ = inspect.getsourcelines(callback)
        code = clean_code(replace_vars(script))
        async with ExceptionHandler(ctx.message):
            parsed = ast.parse(code)
            if [type(stmt) for stmt in parsed.body] != [ast.AsyncFunctionDef]:
                return await send(ctx, "The script should only be an asynchronous function being the command's callback.")
        code = code.split("\n")
        new_code = []
        indentation = 0
        for char in lines[0]:
            if char == " ":
                indentation += 1
            else:
                break
        # since discord's intents are a multiple of 2 we convert them to a multiples of 4.
        # we also add the correct indentation level if necessary
        for line in code:
            amount = 0
            for char in line:
                if char == " ":
                    amount += 1
                amount *= 2
                break
            new_code.append(f"{' ' * indentation}{line.replace('  ', '    ', amount)}")
        code = "\n".join(new_code)
        # we don't want to override the command's actual callback,
        # so we set it to a variable which we can later change if the
        # command's name is found in the callbacks dictionary

        with open(directory, "r") as f:
            read_lines = f.readlines()
            rev_read_lines = read_lines.copy()
            rev_read_lines.reverse()
        # find what lines we have to edit
        start_counter, end_counter = 0, len(lines)
        start, end = None, None
        # sometimes there could be a repeated line of code which is why we have to make sure there's the correct
        # difference between the start and end lines of the file and the one's we're searching for
        while not all((end, start)):
            if read_lines[start_counter] == lines[0]:
                start = start_counter
            if read_lines[end_counter] == lines[-1]:
                end = end_counter
            start_counter += 1
            end_counter += 1
        if None in (start, end):
            return await send(ctx, f"Couldn't find the correct source lines for the command `{command_string}`.")

        # make sure that we have the correct amount of lines necessary to include the new script
        if len(code.split("\n")) > len(lines):
            with open(directory, "w") as f:
                read_lines[end] = read_lines[end] + "\n" * (len(code.split("\n")) - len(lines))
                end += len(code.split("\n")) - len(lines)
                f.writelines(read_lines)
            with open(directory, "r") as f:
                # since we edited the file, we have to get our new set of lines
                read_lines = f.readlines()

        with open(directory, "w") as f:
            count = 0
            for line in range(start, end + 1):
                try:
                    read_lines[line] = code.split("\n")[count] + "\n"
                    count += 1
                except IndexError:
                    # deal with any extra lines, so we don't get a huge whitespace
                    read_lines[line] = ""
            f.writelines(read_lines)
        self.update_register(CommandRegistration(command, "overwrite", source=code), "add")
        await ctx.message.add_reaction("☑")

    @root_overwrite.command(name="setting", aliases=["settings"])
    async def root_overwrite_setting(self, ctx: commands.Context, *, settings: Optional[str] = None):
        """Temporarily change a setting's value. Settings will be reverted once the bot has been restarted.
        Command execution after setting specification isn't available on this mode. Check out `dev override setting|settings` for that.
        Multiple settings can be specified.
        A setting format should be specified as follows: `setting=attr`. Adding single or double quotes in between the different parameters is also a valid option.
        """
        if settings is None:
            return await send(ctx, SettingView(ctx.author))
        default = {k: v for k, v in Settings.__dict__.items() if not (k.startswith("__") and k.endswith("__"))}
        changed = []  # a formatted version of the settings that were changed
        raw_changed = {}
        new_settings = flag_parser(settings, "=")
        for key, value in new_settings.items():
            if key.startswith("__") and key.endswith("__"):  # sneaky fella, don't try me
                continue
            if not hasattr(Settings, key.upper()):
                return await ctx.message.add_reaction("❗")
            setting = getattr(Settings, key.upper())
            raw_changed[key] = setting
            if isinstance(setting, bool):
                setattr(Settings, key.upper(), convert_str_to_bool(value))
            elif isinstance(setting, set):
                setattr(Settings, key.upper(), set(convert_str_to_ints(value)))
            else:
                setattr(Settings, key.upper(), value)
            changed.append(f"Settings.{key.upper()}={value}")
        self.update_register(SettingRegistration(default, raw_changed), "add")
        await send(ctx, discord.Embed(title="Settings Changed" if changed else "Nothing Changed", description="`" + '`\n`'.join(changed) + "`" if changed else "No changes were made to the current version of the settings.", colour=discord.Color.green() if changed else discord.Color.red()))

    @root_override.error
    async def root_override_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.TooManyArguments):
            return await send(ctx, f"`dev override` has no subcommand called `{ctx.subcommand_passed}`.")
        optional_raise(ctx, error)

    @root_overwrite.error
    async def root_overwrite_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.TooManyArguments):
            return await send(ctx, f"`dev overwrite` has no subcommand called `{ctx.subcommand_passed}`.")
        optional_raise(ctx, error)
