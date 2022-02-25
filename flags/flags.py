import io
import os
import discord
import inspect
import pathlib

from discord.ext import commands

from dev.utils.settings import settings
from dev.utils.baseclass import commands_, command_, Paginator


class DevFlags(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands_.command(name="--version", aliases=["-V"], parent="dev", version=1)
    async def root_flag_version(ctx: commands.Context, command: str = commands.Option(description="Command that should be fetched.", default=None)):
        """
        View the version of a command. This is exclusive to `?dev` commands.
        `?dev --version|-V` is the version of the extension.
        """
        dev_cmd: command_.Group = ctx.bot.get_command("dev")
        if not command:
            await ctx.send(embed=discord.Embed(title=f"Version {dev_cmd.version}", color=discord.Color.gold()))
        elif command in [cmd.name for cmd in dev_cmd.commands]:
            command: command_.Command = ctx.bot.get_command(f"dev {command}")
            await ctx.send(embed=discord.Embed(title=f"Version {command.version}", color=discord.Color.gold()))
        else:
            await ctx.send(f"Command `{command}` is not found.")

    @commands_.command(name="--source", aliases=["-src"], parent="dev", version=1)
    async def root_flag_source(ctx: commands.Context, flag: str = commands.Option(description="An optional flag that determines whether or not the source code should be just the command or the whole file."), *, cmd: str = commands.Option(name="command", description="Command that should be fetched.", default="")):
        """
        View the source code of a command. 
        This flag is not exclusive to the `?dev` extension, however commands that aren't part of the cog should start with the specified character(s) in `settings["source"]["not_dev_cmd"]`.
        The bot's token is hidden as `TOKEN`.
        Add the `--file` flag before specifying the command to showcase the command's source code file instead of the plain command source code.
        """
        if flag != "--file":
            cmd = f"{flag} {cmd}".strip()
            flag = False
        else:
            flag = True
        command = ctx.bot.get_command(f"dev {cmd}" if not cmd.startswith(settings["source"]["not_dev_cmd"]) else cmd)
        if not command:
            return await ctx.send(f"Command `{cmd}` is not found.")
        directory = inspect.getsourcefile(command.callback)
        filename = settings["source"]["filename"] or pathlib.Path(inspect.getfile(command.callback)).name

        if not flag:
            lines, _ = inspect.getsourcelines(command.callback)
            if settings["source"]["use_file"]:
                return await ctx.send(file=discord.File(filename), fp=io.BytesIO(''.join(lines).encode('utf-8')))
            paginator = commands.Paginator(prefix="```py\n", suffix="```", max_size=1985, linesep='')
            for line in lines:
                if "`" in line:
                    line = line.replace("`", "\u200b`")
                if ctx.bot.http.token in line:
                    line = line.replace(ctx.bot.http.token, "TOKEN")
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
                if ctx.bot.http.token in line:
                    line = line.replace(ctx.bot.http.token, "TOKEN")
                paginator.add_line(line)
            if settings["folder"]["root_folder"]:
                directory = directory.replace(settings["folder"]["root_folder"], "/root/")
            await ctx.send(f"{f'**{directory}**' if settings['source']['show_path'] else ''}\n{paginator.pages[0]}", view=Paginator(paginator, ctx.author.id, PATH=directory, show_path=settings["source"]["show_path"]))

    @commands_.command(name="--file", parent="dev", version=1)
    async def root_flag_file(ctx: commands.Context, *, directory: str):
        """
        View a file. If `directory` starts with the character(s) specified in `settings['file']['/']` then the directory will be treated as the root folder instead of the current working directory.
        By default, the file is sent as a paginator, however this can be changed in `settings["file"]["use_file"]`. The bot's token is hidden as `TOKEN`.
        """
        raw_dir = directory
        if "/root/" in directory:
            directory = directory.replace("/root/", settings["folder"]["root_folder"])
        directory = f"{f'{os.getcwd()}/' if not directory.startswith(settings['file']['/']) else ''}{directory}"
        if not os.path.exists(directory):
            return await ctx.send(f"Path `{directory}` doesn't exist.")
        if settings["file"]["use_file"]:
            return await ctx.send(file=discord.File(directory))
        paginator = commands.Paginator(prefix=f"```{directory.split('.')[-1]}\n", suffix="```", max_size=1985, linesep='')
        with open(directory, "r") as file:
            for line in file.readlines():
                if "`" in line:
                    line = line.replace("`", "\u200b`")
                if ctx.bot.http.token in line:
                    line = line.replace(ctx.bot.http.token, "TOKEN")
                paginator.add_line(line)
        await ctx.send(f"{f'**{raw_dir}**' if settings['file']['show_path'] else ''}\n{paginator.pages[0]}", view=Paginator(paginator, ctx.author.id, PATH=raw_dir, show_path=settings["file"]["show_path"]))


def setup(bot: commands.Bot):
    bot.add_cog(DevFlags(bot))