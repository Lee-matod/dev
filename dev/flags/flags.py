import discord
import inspect
import pathlib

from discord.ext import commands
from typing import Optional, Union, TYPE_CHECKING

from dev.utils.functs import send
from dev.utils.startup import settings
from dev.utils.baseclass import root, Paginator

if TYPE_CHECKING:
    from dev.utils.baseclass import Group, Command


class RootFlags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="--version", aliases=["-V"], parent="dev", version=1)
    async def root_flag_version(self, ctx: commands.Context, *, command: str = None):
        """
        View the version of a command. This is exclusive to `dev` commands.
        `dev --version|-V` is the version of the extension.
        """
        dev: Optional[Group] = self.bot.get_command("dev")
        cmd: Union[Command, Group] = self.bot.get_command(f"dev {command}")
        if not command:
            return await send(ctx, embed=discord.Embed(title=f"Version {dev.version}", color=discord.Color.gold()))
        elif command:
            return await send(ctx, embed=discord.Embed(title=f"Version {cmd.version}", color=discord.Color.gold()))
        await send(ctx, f"Command `dev {command}` not found.")

    @root.command(name="--source", aliases=["-src"], parent="dev", version=1)
    async def root_flag_source(self, ctx: commands.Context, flag: str, *, cmd: str = ""):
        """
        View the source code of a command. 
        Unlike other flags, this is not exclusive to the `?dev` extension.
        The bot's token is hidden as `TOKEN`.
        Add the `--file` flag before specifying the command to showcase the command's source code file instead of the plain command source code.
        """
        if flag != "--file":
            cmd: str = f"{flag} {cmd}".strip()
            flag: bool = False
        else:
            flag: bool = True
        command = self.bot.get_command(cmd)
        if not command:
            return await send(ctx, f"Command `{cmd}` not found.")
        directory = inspect.getsourcefile(command.callback)
        filename = settings["source"]["filename"] or pathlib.Path(inspect.getfile(command.callback)).name

        if not flag:
            lines, _ = inspect.getsourcelines(command.callback)
            paginator = commands.Paginator(prefix="```py\n", suffix="```", max_size=1985, linesep='')
            for line in lines:
                if "`" in line:
                    line = line.replace("`", "\u200b`")
                if self.bot.http.token in line:
                    line = line.replace(self.bot.http.token, "TOKEN")
                paginator.add_line(line)
            if settings["folder"]["root_folder"]:
                directory = directory.replace(settings["folder"]["root_folder"], "/root/")
            return await ctx.send(f"{f'**{directory}**' if settings['source']['show_path'] else ''}\n{paginator.pages[0]}", view=Paginator(paginator, ctx.author.id, PATH=directory, show_path=settings["source"]["show_path"]))

        with open(directory) as source:
            if settings["source"]["use_file"]:
                return await ctx.send(file=discord.File(directory))
            paginator = commands.Paginator(prefix="```py\n", suffix="```", max_size=1985, linesep='')
            for line in source.readlines():
                if "`" in line:
                    line = line.replace("`", "\u200b`")
                if self.bot.http.token in line:
                    line = line.replace(self.bot.http.token, "TOKEN")
                paginator.add_line(line)
            if settings["folder"]["root_folder"]:
                directory = directory.replace(settings["folder"]["root_folder"], "/root/")
            await ctx.send(f"{f'**{directory}**' if settings['source']['show_path'] else ''}\n{paginator.pages[0]}", view=Paginator(paginator, ctx.author.id, PATH=directory, show_path=settings["source"]["show_path"]))


async def setup(bot: commands.Bot):
    await bot.add_cog(RootFlags(bot))
