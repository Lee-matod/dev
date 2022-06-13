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
    List,
    Literal,
    Optional,
    Tuple,
    Union
)

import contextlib
import discord
import inspect
import io
import textwrap

from discord.ext import commands
from datetime import datetime
from typing_extensions import Self

from dev.types import BotT, Callback
from dev.converters import CodeblockConverter, convert_str_to_bool, convert_str_to_ints
from dev.handlers import ExceptionHandler, replace_vars

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
        await ctx.send(embed=discord.Embed(title="Settings Changed" if self.default_settings else "Nothing Changed", description="`" + '`\n`'.join(changed) + "`", colour=discord.Color.green() if self.default_settings else discord.Color.red()), delete_after=5)
        argument = argument.strip()
        if argument.startswith("```") and argument.endswith("```"):
            self.script = argument
        else:
            self.command_string = argument
        return self


class RootOver(Root):
    def __init__(self, bot: BotT):
        super().__init__(bot)
        self.OVERRIDES: Dict[int, Tuple[str, str, Optional[Callback], Union[str, List[Any]]]] = {}
        self.OVERWRITES: Dict[int, Tuple[str, str, Optional[Callback], Union[str, List[Any]]]] = {}

    @root.group(name="override", parent="dev", invoke_without_command=True)
    async def root_override(self, ctx: commands.Context):
        """Get a table of overrides that have been made with their respective IDs."""
        content = "No overrides have been made."
        if self.OVERRIDES:
            rows = [[k, v[0], v[1]] for k, v in self.OVERRIDES.items()]
            content = table_creator(rows, ["IDs", "Types", "Descriptions"])
        await send(ctx, f"```py\n{content}\n```")

    @root_override.command(name="undo", aliases=["del", "delete"])
    async def root_override_undo(self, ctx: commands.Context, id_num: int = 0):
        """Undoes or deletes an override."""
        try:
            position, args = list(self.OVERRIDES.items())[id_num - 1]
            _, desc, callback, command_string = args
        except IndexError:
            return await send(ctx, f"Override with ID of `{id_num}` not found.")
        del self.CALLBACKS[id_num]
        if ctx.invoked_with in ("delete", "del"):
            self.sort_dict_id("override", "del", id_num if id_num != 0 else len(self.OVERRIDES))
            return await send(ctx, f"Deleted the override with the ID number of `{id_num if id_num != 0 else len(self.OVERRIDES)}`.\n{desc}")
        command = self.bot.get_command(command_string)
        command.callback = callback
        self.sort_dict_id("override", "del", id_num if id_num != 0 else len(self.OVERRIDES))
        await ctx.message.add_reaction("☑")

    @root_override.command(name="command", virtual_vars=True, usage="<command_name> <script>")
    async def root_override_command(self, ctx: commands.Context, *, command_code: CodeblockConverter):
        r"""Temporarily override a command. All changes will be undone once the bot is restart or the cog is reloaded. This differentiates from its counterpart `dev overwrite` which permanently changes a file.
        Override the script that a specified command executes.
        Script that will be used as overrides should be specified in between \`\`\`.
        """
        command_string, script = command_code
        if not command_string or not script:
            return await send(ctx, "Malformed arguments were given.")
        command: Union[commands.Command, commands.Group] = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        self.sort_dict_id("override", "add", ("command", f"Command that was overridden: {command_string} ‒ {datetime.utcnow().strftime('%b %d, %Y at %H:%M:%S UTC')}", command.callback, command_string))
        self.bot.remove_command(command_string)
        script = clean_code(replace_vars(script))
        self.CALLBACKS[len(self.OVERRIDES)] = (command.qualified_name, command.callback, script)
        local_vars: Dict[str, Any] = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
        }
        with contextlib.redirect_stdout(io.StringIO()):
            async with ExceptionHandler(ctx.message):
                exec(f"async def func():\n{textwrap.indent(script, '    ')}", local_vars)
                await local_vars["func"]()

    @root_override.command(name="setting", virtual_vars=True, aliases=["settings"], usage="<setting>... <command_name|script>")
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
                async with ExceptionHandler(ctx.message):
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", local_vars)
                    await local_vars["func"]()
                for module, value in greedy.default_settings.items():
                    setattr(Settings, module, value)
        elif greedy.command_string:
            kwargs = {"content": f"{ctx.prefix}{greedy.command_string}", "author": ctx.author, "channel": ctx.channel}
            context = await generate_ctx(ctx, **kwargs)
            if not context.command:
                for module, value in greedy.default_settings.items():
                    setattr(Settings, module, value)
                return await ctx.send(f"Command `{context.invoked_with}` not found.")
            await context.command.invoke(context)
            for module, value in greedy.default_settings.items():
                setattr(Settings, module, value)

    @root.group(name="overwrite", parent="dev", invoke_without_command=True)
    async def root_overwrite(self, ctx: commands.Context):
        """Get a table of overwrites that have been made with their respective IDs."""
        content = "No overwrites have been made."
        if self.OVERWRITES:
            rows = [[k, v[0], v[1]] for k, v in self.OVERWRITES.items()]
            content = table_creator(rows, ["IDs", "Types", "Descriptions"])
        await send(ctx, f"```py\n{content}\n```")

    @root_overwrite.command(name="undo", aliases=["del", "delete"])
    async def root_overwrite_undo(self, ctx: commands.Context, id_num: int = 0):
        """Undoes or deletes an overwrite."""
        try:
            position, args = list(self.OVERWRITES.items())[id_num - 1]
            _type, desc, callback, arg = args
        except IndexError:
            return await send(ctx, f"Overwrite with ID of `{id_num}` not found.")
        if ctx.invoked_with in ("delete", "del"):
            self.sort_dict_id("overwrite", "del", id_num if id_num != 0 else len(self.OVERWRITES))
            return await send(ctx, f"Deleted the override with the ID number of `{id_num if id_num != 0 else len(self.OVERWRITES)}`.\n{desc}")
        if _type == "command":
            directory = inspect.getsourcefile(callback)
            lines, _ = inspect.getsourcelines(callback)

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
                return await send(ctx, f"Couldn't find the correct source lines for the command.")

            # make sure that we have the correct amount of lines necessary to include the new script
            if len(arg.split("\n")) > len(lines):
                with open(directory, "w") as f:
                    read_lines[end] = read_lines[end] + "\n" * (len(arg.split("\n")) - len(lines))
                    end += len(arg.split("\n")) - len(lines)
                    f.writelines(read_lines)
                with open(directory, "r") as f:
                    # since we edited the file, we have to get our new set of lines
                    read_lines = f.readlines()

            with open(directory, "w") as f:
                count = 0
                for line in range(start, end + 1):
                    try:
                        read_lines[line] = arg.split("\n")[count] + "\n" if line != end else arg.split("\n")[count]
                        count += 1
                    except IndexError:
                        # deal with any extra lines, so we don't get a huge whitespace
                        read_lines[line] = ""
                f.writelines(read_lines)
            self.sort_dict_id("overwrite", "del", id_num if id_num != 0 else len(self.OVERWRITES))
            await ctx.message.add_reaction("☑")

        elif _type == "setting":
            for module, option in arg.items():
                setattr(Settings, module, option)
            self.sort_dict_id("overwrite", "del", id_num if id_num != 0 else len(self.OVERWRITES))
            await ctx.message.add_reaction("☑")

    @root_overwrite.command(name="command", virtual_vars=True, usage=r"<command_name> <script>")
    async def root_overwrite_command(self, ctx: commands.Context, *, command_code: CodeblockConverter):
        r"""Completely change a command's execution script to be permanently overwritten.
        Script that will be used as the command overwrite should be specified in between \`\`\`.
        This command edit's the command's filed with the new script, therefore changes will be seen once the bot gets restarted.
        """
        command_string, script = command_code
        if not command_string or not script:
            return await ctx.send("Malformed arguments were given.")
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        source = command.callback
        if command.qualified_name in [name[0] for name in self.CALLBACKS.values()]:
            # we find the original callback instead of any changed ones
            source = [callback[1] for callback in self.CALLBACKS.values() if callback[0] == command.qualified_name][0]
        directory = inspect.getsourcefile(source)
        lines, _ = inspect.getsourcelines(source)
        self.sort_dict_id("overwrite", "add", ("command", f"Command that was overwritten: {command_string} ‒ {datetime.utcnow().strftime('%b %d, %Y at %H:%M:%S UTC')}", command.callback, "".join(lines)))

        code = clean_code(replace_vars(script))
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
        await ctx.message.add_reaction("☑")

    @root_overwrite.command(name="setting", aliases=["settings"])
    async def root_overwrite_setting(self, ctx: commands.Context, *, settings: str):
        """Temporarily change a setting's value. Settings will be reverted once the bot has been restarted.
        Command execution after setting specification isn't available on this mode. Check out `dev override setting|settings` for that.
        Multiple settings can be specified.
        A setting format should be specified as follows: `setting=attr`. Adding single or double quotes in between the different parameters is also a valid option.
        """
        changed = []  # a formatted version of the settings that were changed
        raw_changed = {}
        new_settings = flag_parser(settings, "=")
        for key, value in new_settings.items():
            if key.startswith("__") and key.endswith("__"):
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
        self.sort_dict_id("overwrite", "add", ("setting", f"Settings that were overwritten: {' | '.join(changed) if changed else 'None'} ‒ {datetime.utcnow().strftime('%b %d, %Y at %H:%M:%S UTC')}", None, raw_changed))
        await send(ctx, discord.Embed(title="Settings Changed" if changed else "Nothing Changed", description="`" + '`\n`'.join(changed) + "`" if changed else "No changes were made to the current version of the settings.", colour=discord.Color.green() if changed else discord.Color.red()))

    def sort_dict_id(self, _type: Literal["overwrite", "override"], mode: Literal["del", "add"], arg: Any) -> None:
        values = []
        if _type == "override":
            dictionary = self.OVERRIDES
        else:
            dictionary = self.OVERWRITES
        for k, v in dictionary.items():
            if mode == "del":
                if k == arg:
                    continue
            values.append(v)
        if mode == "add":
            values.append(arg)
        ordered_dictionary = {}
        for num in range(len(values)):
            ordered_dictionary[num + 1] = values[num]
        dictionary.clear()
        dictionary.update(ordered_dictionary)
