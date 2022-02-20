import io
import re
import shlex
import inspect
import discord
import textwrap
import contextlib

from discord.ext import commands

from dev.utils.settings import settings
from dev.utils.baseclass import commands_
from dev.utils.functs import is_owner, clean_code


class RootOverrideBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.command(name="override", parent="dev", version=1)
    @is_owner()
    async def root_override(ctx: commands.Context, mode: str = commands.Option(description="The mode to override"), *, attrs: str = commands.Option(description="Attributes to the mode.")):
        r"""
        Temporarily override a selected mode. All changed will be undone once the bot is restart or in some cases a cog is reloaded. This differentiates from its counterpart `overwrite` which permanently changes a file.
        Script that will override should be specified in between \`\`\`.
        **Modes:**
        `command <command> <script>` = Override the script that a specified command executes. Undo by either reloading the cog of the command or restarting the bot.
        `settings <[module][setting]>=<attr> <command|script>` = Override a setting and execute a command or script. When it is done executed, the setting will revert to default.
        """
        if mode == "command":
            attr = ""
            for i in attrs.split():
                if i.startswith("```"):
                    break
                attr += i
            if not attr:
                return await ctx.send(f"Please specify a command to override.")
            command = ctx.bot.get_command(attr)
            if not command:
                return await ctx.send(f"Command `{attr}` is not found.")
            ctx.bot.remove_command(attr)
            attrs = clean_code(attrs[len(attr) + 1:])
            local_vars = {
                "discord": discord,
                "commands": commands,
                "bot": ctx.bot,
            }
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    exec(f"async def func():\n{textwrap.indent(attrs, '    ')}", local_vars)
                    await local_vars["func"]()
                    await ctx.message.add_reaction("☑")
            except Exception:
                await ctx.message.add_reaction("❗")
        elif mode == "settings":
            msa_patter = re.compile(r"\[(.+)]\[(.+)]=(.+)")
            attrs_ = attrs.split()
            default_settings = {}
            for attr in attrs_:
                matches = re.finditer(pattern=msa_patter, string=attr)
                if matches:
                    for match in matches:
                        if match.group(1) not in settings:
                            return await ctx.message.add_reaction("❗")
                        elif match.group(2) not in settings[match.group(1)]:
                            return await ctx.message.add_reaction("❗")
                        attrs = attrs.replace(match.string, "")
                        default_settings[match.group(1)] = {match.group(2): settings[match.group(1)][match.group(2)]}
                        settings[match.group(1)][match.group(2)] = match.group(3)
            attrs = attrs.strip()
            if attrs.startswith("```") and attrs.endswith("```"):
                code = clean_code(attrs)
                local_vars = {
                    "discord": discord,
                    "commands": commands,
                    "bot": ctx.bot,
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
                    for module in default_settings:
                        for setting in default_settings[module]:
                            settings[module][setting] = default_settings[module][setting]
            else:
                command = ctx.bot.get_command(attrs)
                if not command:
                    for module in default_settings:
                        for setting in default_settings[module]:
                            settings[module][setting] = default_settings[module][setting]
                    return await ctx.send(f"Command `{attrs}` is not found.")
                signature = inspect.signature(command.callback).parameters
                args = []; kwargs = []
                args_ = []; kwargs_ = {}
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
                        specified_args: discord.Message = await ctx.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id)
                        args_.append(specified_args.content)
                if kwargs:
                    for kwarg in kwargs:
                        await ctx.send(f"Please send the `{kwarg}` kwargs.")
                        specified_kwargs: discord.Message = await ctx.bot.wait_for("message", check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id)
                        kwargs_[kwarg] = specified_kwargs.content
                await command.__call__(ctx, *args_, **kwargs_)
                for module in default_settings:
                    for setting in default_settings[module]:
                        settings[module][setting] = default_settings[module][setting]
                return await ctx.message.add_reaction("☑")

    @commands_.command(name="overwrite", parent="dev", version=1)
    @is_owner()
    async def root_overwrite(ctx: commands.Context, mode: str = commands.Option(description="The mode to overwrite."), *, attrs: str = commands.Option(description="Attributes to the mode.")):
        r"""
        Completely change a file's content to be permanently overwriten. Changes can be undone by executing a command that is yet to be created.
        Character sequence that will overwrite the file should be specified in between \`\`\`.
        **Modes:**
        `command <command> <script>` = Overwrite the entire code of a specified command. Undo by executing a command that is yet to be created.
        `settings <[module][setting]>=<attr>` = Overwrite a setting. Multiple setting overwrites can be done. Unlike other overwrites, this mode will restore the default value once the bot is restarted.
        """
        if mode == "command":
            attr = ""
            for i in attrs.split():
                if i.startswith("```"):
                    break
                attr += i
            code = clean_code(attrs[len(attr) + 1:])
            code = code.replace('  ', '    ', 1)
            if not attr:
                return await ctx.send(f"Please specify a command to overwrite.")
            command = ctx.bot.get_command(attr)
            if not command:
                return await ctx.send(f"Command `{attr}` is not found.")
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

        elif mode == "settings":
            msa_patter = re.compile(r"\[(.+)]\[(.+)]=(.+)")
            attrs = attrs.split()
            for attr in attrs:
                matches = re.finditer(pattern=msa_patter, string=attr)
                if matches:
                    for match in matches:
                        if match.group(1) not in settings:
                            return await ctx.message.add_reaction("❗")
                        elif match.group(2) not in settings[match.group(1)]:
                            return await ctx.message.add_reaction("❗")
                        settings[match.group(1)][match.group(2)] = match.group(3)
            await ctx.message.add_reaction("☑")


def setup(bot: commands.Bot):
    bot.add_cog(RootOverrideBot(bot))