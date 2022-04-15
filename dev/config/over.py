from typing import *

import io
import re
import shlex
import inspect
import discord
import textwrap
import contextlib

from discord.ext import commands

from dev.utils.startup import settings
from dev.utils.functs import is_owner, clean_code
from dev.utils.baseclass import root, StringCodeblockConverter


class OverrideSettingConverter(commands.Converter):
    default_settings: Dict[AnyStr, Dict[AnyStr, AnyStr]] = {}
    script: Optional[str] = None
    command_string: str = ""

    async def convert(self, ctx: commands.Context, argument: str):
        changed = []
        setting_patter = re.compile(r"\[[\"|\']?(.+)[\"|\']?]\[[\"|\']?(.+)[\"|\']?]=[\"|\']?(.+)[\"|\']?")
        split_args = shlex.split(argument)
        for arg in split_args:
            match = re.match(setting_patter, arg)
            if match:
                if match.group(1) not in settings:
                    return await ctx.message.add_reaction("❗")
                elif match.group(2) not in settings[match.group(1)]:
                    return await ctx.message.add_reaction("❗")
                argument = argument.replace(match.string, "")
                self.default_settings[match.group(1)] = {match.group(2): settings[match.group(1)][match.group(2)]}
                settings[match.group(1)][match.group(2)] = match.group(3)
                changed.append(f"[{match.group(1)}][{match.group(2)}]={match.group(3)}")
        await ctx.send(embed=discord.Embed(title="Settings Changed" if self.default_settings else "Nothing Changed", description="`" + '`\n`'.join(changed) + "`", colour=discord.Color.green() if self.default_settings else discord.Color.red()), delete_after=5)
        argument = argument.strip()
        if argument.startswith("```") and argument.endswith("```"):
            self.script = argument
        else:
            self.command_string = argument
        return self


class RootOverrideBot(commands.Cog):
    COMMAND_OVERRIDES: Dict[str, Callable] = {}
    COMMAND_OVERWRITES: Dict[str, Callable] = {}

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.group(name="override", parent="dev", version=1.1, invoke_without_command=True)
    @is_owner()
    async def root_override(self, ctx: commands.Context):
        pass

    @root_override.command(name="command", version=1, usage=r"<command_name> <script>")
    @is_owner()
    async def root_override_command(self, ctx: commands.Context, *, command_code: StringCodeblockConverter):
        r"""Temporarily override a command. All changes will be undone once the bot is restart or the cog is reloaded. This differentiates from its counterpart `dev overwrite` which permanently changes a file.
        Override the script that a specified command executes.
        Script that will be used as overrides should be specified in between \`\`\`.
        """
        # `self` is passed as :type commands.Context: hence why we use `getattr` to get our class attributes.
        COMMAND_OVERRIDES: Dict[str, Callable] = getattr(RootOverrideBot, "COMMAND_OVERRIDES", None)
        command_string, script = command_code
        if not command_string or not script:
            return await ctx.send("Malformed arguments were given.")
        command: Union[commands.Command, commands.Group] = self.bot.get_command(command_string)
        if not command:
            return await ctx.send(f"Command `{command_string}` not found.")
        COMMAND_OVERRIDES[command_string] = command.callback
        self.bot.remove_command(command_string)
        attrs = clean_code(script)
        local_vars = {
            "discord": discord,
            "commands": commands,
            "bot": self.bot,
        }
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                exec(f"async def func():\n{textwrap.indent(attrs, '    ')}", local_vars)
                await local_vars["func"]()
                await ctx.message.add_reaction("☑")
        except Exception as e:
            print(e)
            await ctx.message.add_reaction("❗")

    @root_override.command(name="setting", version=1, aliases=["settings"], usage=r"<setting>... <command_name|script>")
    @is_owner()
    async def root_override_setting(self, ctx: commands.Context, *, greedy: OverrideSettingConverter):
        """Temporarily override a (some) setting(s). All changes will be undone once the command has finished executing. This differentiates from its counterpart `dev overwrite` which does not switch back once the command has been terminated.
        Multiple settings can be specified.
        Override a setting and execute a command or script with the new set of specified setting(s). When it is done executed, the setting will revert to default.
        Setting overrides should be specified as follows: `[module][setting]=attr`. Adding single or double quotes in between the different parameters is also a valid option.
        """
        if greedy.script:
            code = clean_code(greedy.script)
            local_vars = {
                "discord": discord,
                "commands": commands,
                "bot": self.bot,
                "ctx": ctx
            }
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(f"async def func():\n{textwrap.indent(code, '    ')}", local_vars)
                    await local_vars["func"]()
                    await ctx.message.add_reaction("☑")
            except Exception:
                await ctx.message.add_reaction("❗")
            finally:
                for module in greedy.default_settings:
                    for setting in greedy.default_settings[module]:
                        settings[module][setting] = greedy.default_settings[module][setting]
        elif greedy.command_string:  # this thing might be very broken. Still under development
            command = self.bot.get_command(greedy.command_string)
            if not command:
                for module in greedy.default_settings:
                    for setting in greedy.default_settings[module]:
                        settings[module][setting] = greedy.default_settings[module][setting]
                return await ctx.send(f"Command `{greedy.command_string}` is not found.")
            signature = inspect.signature(command.callback).parameters
            args = []; kwargs = []; args_ = []; kwargs_ = {}
            for sign in signature:
                if sign == "ctx":
                    continue
                elif signature[sign].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
                    args.append(sign)
                elif signature[sign].kind == inspect.Parameter.KEYWORD_ONLY:
                    kwargs.append(sign)
            if args:
                for arg in args:
                    await ctx.send(f"Please send the `{arg}` args.")
                    specified_args: discord.Message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id)
                    args_.append(specified_args.content)
            if kwargs:
                for kwarg in kwargs:
                    await ctx.send(f"Please send the `{kwarg}` kwargs.")
                    specified_kwargs: discord.Message = await self.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id)
                    kwargs_[kwarg] = specified_kwargs.content
            await command.__call__(ctx, *args_, **kwargs_)
            for module in greedy.default_settings:
                for setting in greedy.default_settings[module]:
                    settings[module][setting] = greedy.default_settings[module][setting]
            return await ctx.message.add_reaction("☑")

    @root.group(name="overwrite", parent="dev", version=1.1)
    @is_owner()
    async def root_overwrite(self, ctx: commands.Context):
        pass

    @root_overwrite.command(name="command", version=1, usage=r"<command_name> <script>")
    async def root_overwrite_command(self, ctx: commands.Context, *, command_code: StringCodeblockConverter):
        r"""Completely change a command's execution script to be permanently overwritten.
        Script that will be used as the command overwrite should be specified in between \`\`\`.
        """
        # `self` is passed as :type commands.Context: hence why we use `getattr` to get our class attributes.
        COMMAND_OVERRIDES: Dict[str, Callable] = getattr(RootOverrideBot, "COMMAND_OVERRIDES", None)
        COMMAND_OVERWRITES: Dict[str, Callable] = getattr(RootOverrideBot, "COMMAND_OVERWRITES", None)  # this has no use yet, but will probably serve a purpose in order to undo any unwanted overwrites
        command_string, script = command_code
        if not command_string or not script:
            return await ctx.send("Malformed arguments were given.")
        code = clean_code(script)
        code = code.split("\n")
        new_code = []
        for line in code:
            amount = 0
            for char in line:
                if char == " ":
                    amount += 1
                amount *= 2
                break
            new_code.append(line.replace("  ", "    ", amount))
        code = "\n".join(new_code)
        command = self.bot.get_command(command_string)
        if not command:
            return await ctx.send(f"Command `{command_string}` not found.")
        COMMAND_OVERWRITES[command_string] = command.callback
        if command_string in COMMAND_OVERRIDES:
            command.callback = COMMAND_OVERRIDES[command_string]  # since the command specified had previously been overridden, we can't use the default callback
        directory = inspect.getsourcefile(command.callback)
        lines, _ = inspect.getsourcelines(command.callback)
        with open(directory, "r") as f:
            rl = f.readlines()
        with open(directory, "w") as f:
            rev_rl = rl.copy(); rev_rl.reverse()
            start = 0
            end = 0
            for line in range(len(rl)):
                if rev_rl[line] == lines[-1]:
                    end = line
                elif end != 0:
                    if (start - end) == len(lines):
                        start = line
                        break
                    start = line + 1
            start = len(rl) - start
            end = end - len(rl)
            count = 0
            for line in range(start, abs(end)):
                try:
                    rl[line] = code.split("\n")[count] + "\n"
                    count += 1
                except IndexError:
                    rl[line] = ""
            f.writelines(rl)
            await ctx.message.add_reaction("☑")

    @root_overwrite.command(name="setting", version=1, aliases=["settings"], usage=r"<setting>... <command_name|script>")
    async def root_overwrite_setting(self, ctx: commands.Context, *, setting: str):
        """Temporarily change a setting's value. Normal settings will be reverted once the bot has been restarted.
        Command execution after setting specification isn't available on this mode. Check out `dev override setting|settings` for that.
        Multiple settings can be specified.
        A setting format should be specified as follows: `[module][setting]=attr`. Adding single or double quotes in between the different parameters is also a valid option.
        `settings <[module][setting]>=<attr>` = Overwrite a setting. Multiple setting overwrites can be done. Unlike other overwrites, this mode will restore the default value once the bot is restarted.
        """
        changed = []
        setting_patter = re.compile(r"\[[\"|\']?(.+)[\"|\']?]\[[\"|\']?(.+)[\"|\']?]=[\"|\']?(.+)[\"|\']?")
        split_args = shlex.split(setting)
        for arg in split_args:
            match = re.match(setting_patter, arg)
            if match:
                if match.group(1) not in settings:
                    return await ctx.message.add_reaction("❗")
                elif match.group(2) not in settings[match.group(1)]:
                    return await ctx.message.add_reaction("❗")
                settings[match.group(1)][match.group(2)] = match.group(3)
                changed.append(f"[{match.group(1)}][{match.group(2)}]={match.group(3)}")
        await ctx.send(embed=discord.Embed(title="Settings Changed" if changed else "Nothing Changed", description="`" + '`\n`'.join(changed) + "`" if changed else "No changes were made to the current version of the settings.", colour=discord.Color.green() if changed else discord.Color.red()),)


async def setup(bot: commands.Bot):
    await bot.add_cog(RootOverrideBot(bot))