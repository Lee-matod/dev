# -*- coding: utf-8 -*-

"""
dev.config.over
~~~~~~~~~~~~~~~

Override or overwrite certain aspects and functions of the bot.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import ast
import inspect
import textwrap
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from dev import root
from dev.components import AuthoredView, CodeEditor, ModalSender, SettingsToggler
from dev.converters import CodeblockConverter, str_bool, str_ints
from dev.handlers import ExceptionHandler, replace_vars
from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import Over, OverType
from dev.utils.functs import flag_parser, send, table_creator
from dev.utils.startup import Settings
from dev.utils.utils import clean_code, codeblock_wrapper, escape, plural

if TYPE_CHECKING:
    from typing_extensions import Annotated

    from dev import types


class RootOver(root.Container):
    """Override and overwrite different attributes"""

    @root.group(name="override", parent="dev", ignore_extra=True, invoke_without_command=True)
    async def root_override(self, ctx: commands.Context[types.Bot]):
        """Get a table of overrides that have been made with their respective IDs.
        Name of the command and date modified are also included in the table.
        """
        if overrides := self.registers_from_type(Over.OVERRIDE):
            rows = [
                [index, rgs.qualified_name, f"Date modified: {rgs.created_at}"]
                for index, rgs in enumerate(overrides, start=1)
            ]
            return await send(
                ctx,
                f"```py\n{table_creator(rows, ['IDs', 'Names', 'Descriptions'])}\n```",
            )
        await send(ctx, "No overrides have been made.")

    @root.command(name="undo", parent="dev override")
    async def root_override_undo(self, ctx: commands.Context[types.Bot], index: int = 0):
        """Undo an override.
        If the specified override ID is not the last override, then it will simply get deleted.
        """
        overrides = self.registers_from_type(Over.OVERRIDE)
        if not overrides:
            return await send(ctx, "No overrides have been made.")
        try:
            if index < 0:
                raise IndexError
            override = overrides[index - 1]
        except IndexError:
            return await send(ctx, f"Override with ID of `{index}` not found.")
        self.update_register(override, Over.DELETE)
        command: types.Command = self.bot.get_command(override.qualified_name)  # type: ignore
        impl = self.get_last_implementation(override.qualified_name)
        assert impl is not None, "Managed to try to undo an override that was never an override"
        command.callback = impl.callback
        await ctx.message.add_reaction("\u2611")

    @root.command(name="view", parent="dev override")
    async def root_override_view(self, ctx: commands.Context[types.Bot], index: int = 0):  # type: ignore
        """Similar to `dev --source|-src`, with the added functionality of specifying an override.
        By default, this will call `dev --source|-src` and return whatever the last override is.
        """
        overrides = self.registers_from_type(Over.OVERRIDE)
        if not overrides:
            return await send(ctx, "No overrides have been made.")
        if index < 0 or index > len(overrides):
            return await send(ctx, "Invalid override.")
        if index in [0, len(overrides)]:
            last = overrides[-1]
            return await self.root_source(ctx, command_string=last.qualified_name)  # type: ignore
        override = overrides[index - 1]  # Shouldn't raise IndexError because we sanitized it before
        if not override.source:
            return await send(ctx, "Could not get source of command.")
        await send(ctx, codeblock_wrapper(override.source, "py"))

    @root.command(
        name="command",
        parent="dev override",
        virtual_vars=True,
        require_var_positional=True,
        usage="<command_name> <script>",
    )
    async def root_override_command(
        self,
        ctx: commands.Context[types.Bot],
        *,
        command_code: Annotated[tuple[str | None, str | None], CodeblockConverter],
    ):
        r"""Temporarily override a command.
        All changes will be undone once the bot is restarted.
        If the command belongs to a cog, its first argument in the callback should be the instance of the binding.
        This differentiates from its counterpart `dev overwrite` which permanently changes a file.
        The script that will be used as override should be specified in a codeblock.
        """
        command_string, script = command_code
        command_string: str | None
        script: str | None
        if not command_string:
            return await send(ctx, "Malformed arguments were given.")
        command: types.Command = self.bot.get_command(command_string)  # type: ignore
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        impl: CommandRegistration = self.get_last_implementation(command_string)  # type: ignore
        # modals have a maximum of 4000 characters
        if not script and len(impl.source) > 4000:
            return await send(
                ctx,
                "The command's source code exceeds the 4000 maximum character limit.",
            )
        if not script:
            return await send(
                ctx,
                ModalSender(
                    CodeEditor(ctx, command, self),
                    ctx.author,
                    label="View Code",
                    style=discord.ButtonStyle.blurple,
                ),
            )
        self.bot.remove_command(command_string)

        base_command = self.get_base_command(command.qualified_name)
        scope: dict[str, Any] = {}
        if base_command is not None:
            scope.update(base_command.callback.__globals__)

        script = clean_code(replace_vars(script, self.scope))
        async with ExceptionHandler(ctx.message, lambda *_: self.bot.add_command(command)):  # type: ignore
            # Make sure everything is parsed correctly
            parsed = ast.parse(script)
            if [ast.AsyncFunctionDef] != [type(expr) for expr in parsed.body]:
                self.bot.add_command(command)
                return await send(
                    ctx,
                    "Top-level code should consist of a single asynchronous function.",
                )
            # Prepare variables for script wrapping
            func: ast.AsyncFunctionDef = parsed.body[-1]  # type: ignore
            body = textwrap.indent("\n".join(script.split("\n")[len(func.decorator_list) + 1 :]), "\t")
            parameters = script.split("\n")[func.lineno - 1][len(f"async def {func.name}(") : -2]
            upper = "\n".join(script.split("\n")[: func.lineno - 1])

            exec(
                f"async def __command_getter__():\n"
                f"\t{upper}\n"
                f"\tasync def {func.name}({parameters}):\n"
                f"{body}\n"
                f"\treturn {func.name}",
                scope,
            )
            obj = await scope["__command_getter__"]()
            # check after execution
        if not isinstance(obj, (commands.Command, commands.Group)):
            self.bot.add_command(command)
            return await send(
                ctx,
                "Top-level function should be a command-like object.",
            )
        if obj.qualified_name != command_string:
            self.bot.remove_command(obj.qualified_name)
            self.bot.add_command(command)
            return await send(ctx, "Command name cannot be changed.")
        if isinstance(command, commands.Group):
            if not isinstance(obj, commands.Group):
                await send(
                    ctx, "The command provided was initially a group, but override did not make this attribute persist."
                )
            for child in command.commands:
                obj.add_command(child)  # type: ignore
        if command.parent is not None:
            command.parent.add_command(obj)  # type: ignore
        elif obj not in self.bot.commands:
            self.bot.add_command(obj)  # type: ignore
        self.update_register(
            CommandRegistration(
                obj,  # type: ignore
                Over.OVERRIDE,
                source=f"{upper.lstrip()}\nasync def {func.name}({parameters}):\n{body}\n",
            ),
            Over.ADD,
        )

    @root.group(name="overwrite", parent="dev", ignore_extra=True, invoke_without_command=True)
    async def root_overwrite(self, ctx: commands.Context[types.Bot]):
        """Get a table of overwrites that have been made with their respective IDs.
        Overwrite type, changes made, and date modified are also included in the table.
        """
        if overwrites := self.registers_from_type(Over.OVERWRITE):
            overwrites: list[CommandRegistration | SettingRegistration]
            rows = [
                [index, rgs.over_type.name, f"{rgs} ‒ {rgs.created_at}"]
                for index, rgs in enumerate(overwrites, start=1)
            ]
            return await send(
                ctx,
                codeblock_wrapper(table_creator(rows, ["IDs", "Types", "Descriptions"]), "py"),
            )
        await send(ctx, "No overwrites have been made.")

    @root.command(name="undo", parent="dev overwrite", aliases=["del", "delete"])
    async def root_overwrite_undo(self, ctx: commands.Context[types.Bot], index: int = 0):
        """Undoes or deletes an overwrite.
        If the specified overwrite ID is not the last overwrite, then it will simply get deleted.
        However, settings will get converted back to the value of the previous overwrite.
        """
        if not (overwrites := self.registers_from_type(Over.OVERWRITE)):
            overwrites: list[CommandRegistration | SettingRegistration]
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
                f"Successfully deleted override: {overwrite}",
            )
        if overwrite.over_type is OverType.COMMAND:
            assert isinstance(overwrite, CommandRegistration)
            base = self.get_base_command(overwrite.command.qualified_name)
            if base is None:
                return await send(ctx, "Could not find base command.")
            directory = inspect.getsourcefile(base.callback)
            if directory is None:
                return await send(ctx, "Could not find source.")
            lines = overwrite.source.split("\n")
            base_command = self.get_base_command(overwrite.qualified_name)
            if base_command is None or not hasattr(base_command, "line_no"):
                return await send(
                    ctx,
                    f"Could not get source lines for the command `{overwrite.qualified_name}`.",
                )
            line_no = base_command.line_no
            with open(directory, "r", encoding="utf-8") as fp:
                read_lines = fp.readlines()
            start, end = line_no, line_no + (len(lines) - 1)
            self.update_register(overwrite, Over.DELETE)
            old_command = self.get_last_implementation(overwrite.qualified_name)
            if old_command is None or not old_command.source:
                return await send(
                    ctx,
                    f"Could not get source lines for the command `{overwrite.qualified_name}`.",
                )
            old_lines = old_command.source
            old_lines_split = old_lines.split("\n")
            # make sure that we have the correct amount of lines necessary to include the new script
            if len(old_lines_split) > len(lines):
                with open(directory, "w", encoding="utf-8") as fp:
                    read_lines[end] += "\n" * (len(old_lines_split) - len(lines))
                    end += len(old_lines_split) - len(lines)
                    fp.writelines(read_lines)
                with open(directory, "r", encoding="utf-8") as fp:
                    # since we edited the file, we have to get our new set of lines
                    read_lines = fp.readlines()
            count = 0
            for line in range(start, end + 1):
                try:
                    read_lines[line] = old_lines_split[count] + "\n" if line != end else old_lines_split[count]
                    count += 1
                except IndexError:
                    # deal with any extra lines, so we don't get a huge whitespace
                    read_lines[line] = ""
            with open(directory, "w", encoding="utf-8") as fp:
                fp.writelines(read_lines)
            await ctx.message.add_reaction("\u2611")

        elif overwrite.over_type is OverType.SETTING:
            assert isinstance(overwrite, SettingRegistration)
            for module, option in overwrite.defaults.items():
                setattr(Settings, module, option)
            self.update_register(overwrite, Over.DELETE)
            await ctx.message.add_reaction("\u2611")

    @root.command(name="view", parent="dev overwrite")
    async def root_overwrite_view(self, ctx: commands.Context[types.Bot], index: int = 0):
        """Shows the source code of the given overwrite."""
        overwrites = self.registers_from_type(Over.OVERWRITE)
        if not overwrites:
            return await send(ctx, "No overwrites have been made")
        if index < 0 or index > len(overwrites):
            return await send(ctx, "Invalid overwrite.")
        if index in [0, len(overwrites)]:
            last = overwrites[-1]
            if isinstance(last, CommandRegistration):
                if not last.source:
                    return await send(ctx, "Could not get source of command.")
                return await send(ctx, codeblock_wrapper(last.source, "py"))
            assert isinstance(last, SettingRegistration)
            return await send(
                ctx,
                "\n".join(f"Settings.{sett.lower()} = `{escape(value)}`" for sett, value in last.changed.items()),
            )
        overwrite = overwrites[index - 1]  # Shouldn't raise IndexError because we sanitized it before
        if isinstance(overwrite, CommandRegistration):
            if not overwrite.source:
                return await send(ctx, "Could not get source of command.")
            return await send(ctx, codeblock_wrapper(overwrite.source, "py"))
        assert isinstance(overwrite, SettingRegistration)
        await send(
            ctx,
            "\n".join(f"Settings.{sett.lower()} = `{escape(value)}`" for sett, value in overwrite.changed.items()),
        )

    @root.command(
        name="command",
        parent="dev overwrite",
        virtual_vars=True,
        require_var_positional=True,
        usage="<command_name> <script>",
    )
    async def root_overwrite_command(
        self,
        ctx: commands.Context[types.Bot],
        *,
        command_code: Annotated[tuple[str | None, str | None], CodeblockConverter],
    ):
        r"""Completely change a command's execution script to be permanently overwritten.
        The script that will be used as the command overwrite should be specified inside a codeblock
        (or in between \`\`\`).
        This command edits the command's file with the new script.
        """
        command_string, script = command_code
        command_string: str | None
        script: str | None
        if not all([command_string, script]):
            return await send(ctx, "Malformed arguments were given.")
        command: types.Command = self.bot.get_command(command_string)  # type: ignore
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        base: BaseCommandRegistration | None = self.get_base_command(command_string)  # type: ignore
        if base is None:
            return await send(ctx, "Could not find base command.")
        callback = base.callback
        directory = inspect.getsourcefile(callback)
        if directory is None:
            return await send(ctx, "Could not find source.")
        lines, line_no = inspect.getsourcelines(callback)
        line_no -= 1
        code = clean_code(replace_vars(script, Root.scope))  # type: ignore
        async with ExceptionHandler(ctx.message):
            parsed: ast.Module = ast.parse(code)
            if [ast.AsyncFunctionDef] != [type(expr) for expr in parsed.body]:
                return await send(
                    ctx,
                    "Top-level code should consist of a single asynchronous function.",
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
        parsed_code: list[str] = []
        for line in code:
            amount = 0
            for char in line:
                if char == " ":
                    amount += 1
                amount *= 2
                break
            parsed_code.append(f"{' ' * indentation}{line.replace('  ', '    ', amount)}")
        code = "\n".join(parsed_code)
        with open(directory, "r", encoding="utf-8") as fp:
            read_lines = fp.readlines()
        start, end = line_no, line_no + (len(lines) - 1)
        # make sure that we have the correct amount of lines necessary to include the new script
        code_split = code.split("\n")
        if len(code_split) > len(lines):
            with open(directory, "w", encoding="utf-8") as fp:
                read_lines[end] += "\n" * (len(code_split) - len(lines))
                end += len(code_split) - len(lines)
                fp.writelines(read_lines)
            with open(directory, "r", encoding="utf-8") as f:
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
        with open(directory, "w", encoding="utf-8") as fp:
            fp.writelines(read_lines)
        self.update_register(CommandRegistration(command, Over.OVERWRITE, source=code), Over.ADD)
        await ctx.message.add_reaction("\u2611")

    @root.command(name="setting", parent="dev overwrite", aliases=["settings"])
    async def root_overwrite_setting(self, ctx: commands.Context[types.Bot], *, settings: str | None = None):
        """Temporarily change a setting's value.
        Settings will be reverted once the bot has been restarted.
        Command execution after setting specification isn't available in this mode.
        Multiple settings can be specified, and they should be specified as follows: `setting=attr`.
        Adding single or double quotes in between the different parameters is also a valid option.
        """
        if settings is None:
            view = AuthoredView(ctx.author)
            SettingsToggler.add_buttons(view)
            return await send(ctx, view)
        default = Settings.kwargs.copy()
        changed: list[str] = []  # a formatted version of the settings that were changed
        raw_changed = {}
        new_settings = flag_parser(settings, "=")
        if isinstance(new_settings, str):
            return await send(ctx, new_settings)
        assert isinstance(new_settings, dict)
        error_settings: list[str] = []
        for key in new_settings:
            key = key.lower()
            if key.startswith("_"):
                continue
            if not hasattr(Settings, key):
                error_settings.append(key)
        if error_settings:
            return await send(
                ctx,
                f"{plural(len(error_settings), 'Setting')} not found: {', '.join(error_settings)}",
            )
        for key, attr in new_settings.items():
            str_setting = key.lower()
            setting = getattr(Settings, str_setting)
            raw_changed[key] = setting
            try:
                if isinstance(setting, bool):
                    setattr(Settings, str_setting, str_bool(attr))
                elif isinstance(setting, set):
                    setattr(Settings, str_setting, set(str_ints(attr)))
                else:
                    setattr(Settings, str_setting, attr)
            except (ValueError, NotADirectoryError) as exc:
                for k, v in raw_changed.items():  # type: ignore
                    setattr(Settings, k, v)  # type: ignore
                return await send(ctx, f"Invalid value for Settings.{key}: `{exc}`")
            changed.append(f"Settings.{str_setting}={attr}")
        self.update_register(SettingRegistration(default, raw_changed), Over.ADD)
        await send(
            ctx,
            discord.Embed(
                title="Settings Changed" if changed else "Nothing Changed",
                description="`" + "`\n`".join(changed) + "`"
                if changed
                else "No changes were made to the current version of the settings.",
                color=discord.Color.green() if changed else discord.Color.red(),
            ),
        )
