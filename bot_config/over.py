import discord
import inspect
import io
import contextlib
import textwrap

from discord.ext import commands

from dev.utils.functs import is_owner, clean_code
from dev.utils.baseclass import commands_


class RootOverrideBot(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.command(name="override", parent="dev", version=1, usage=r"<mode> <attrs> \`\`\`<code>\`\`\`")
    @is_owner()
    async def root_override(ctx: commands.Context, mode: str = commands.Option(description="The mode to override"), *, attrs: str = commands.Option(description="Attributes to the mode.\n`code`: Script that will be used as the override.")):
        r"""
        Temporarily override a selected mode. All changed will be undone once the bot is restart or in some cases a cog is reloaded. This differentiates from its counterpart `overwrite` which permanently changes a file.
        Script that will override should be specified in between \`\`\`.
        **Current modes:**
        `command`: _str_ = Override the script that a specified command executes. Undo by either reloading the cog of the command or restarting the bot.
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

    @commands_.command(name="overwrite", parent="dev", version=1, usage=r"<mode> <attrs> \`\`\`<code>\`\`\`")
    @is_owner()
    async def root_overwrite(ctx: commands.Context, mode: str = commands.Option(description="The mode to overwrite."), *, attrs: str = commands.Option(description="Attributes to the mode.\n`code`: Script that will be used as the overwrite.")):
        r"""
        Completely change a file's content to be permanently overwriten. Changes can be undone by executing a command that is yet to be created.
        Character sequence that will overwrite the file should be specified in between \`\`\`.
        **Current modes:**
        `command`: _str_ = Overwrite the entire code of a specified command. Undo by executing a command that is yet to be created.
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


def setup(bot: commands.Bot):
    bot.add_cog(RootOverrideBot(bot))