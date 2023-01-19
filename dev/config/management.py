# -*- coding: utf-8 -*-

"""
dev.config.management
~~~~~~~~~~~~~~~~~~~~~

Directory and path-related commands.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import io
import os
import pathlib
import shutil
from typing import TYPE_CHECKING

import discord

from dev.components import BoolInput
from dev.handlers import optional_raise
from dev.registrations import ManagementRegistration
from dev.types import ManagementOperation
from dev.utils.baseclass import Root, root
from dev.utils.functs import send, table_creator
from dev.utils.startup import Settings
from dev.utils.utils import escape, parse_invoked_subcommand, plural

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types


class RootManagement(Root):
    """Files, folders, and directory managing commands"""

    def __init__(self, bot: types.Bot) -> None:
        super().__init__(bot)
        self.cwd: str = os.getcwd() + "/"
        self.explorer_rgs: list[ManagementRegistration] = []

    @root.command(name="cwd", parent="dev", root_placeholder=True, aliases=["change_cwd"])
    async def root_files_cwd(self, ctx: commands.Context[types.Bot], *, new_cwd: str | None = None):
        """Change or view the current working directory that the bot should use."""
        if new_cwd is None:
            return await send(ctx, f"Current working directory is: `{self.cwd}`")
        new_cwd = new_cwd.replace("|root|", Settings.root_folder)
        if not pathlib.Path(new_cwd).exists():
            return await send(ctx, f"Directory `{new_cwd}` does not exist.")
        self.cwd = new_cwd + "/" if not new_cwd.endswith("/") else new_cwd
        await ctx.message.add_reaction("☑")

    @root.group(name="explorer", parent="dev", invoke_without_command=True, ignore_extra=True)
    async def root_explorer(self, ctx: commands.Context[types.Bot]):
        """View modifications made to directories."""
        if operations := self.explorer_rgs:
            rows = [
                [
                    index,
                    index,
                    rgs.operation_type.name,
                    f"{rgs}. Date modified: {rgs.created_at}",
                ]
                for index, rgs in enumerate(operations, start=1)
            ]
            return await send(
                ctx,
                f"```py\n{table_creator(rows, ['IDs', 'Types', 'Descriptions'])}\n```",
            )
        await send(ctx, "No modifications have been made.")

    @root.command(
        name="new",
        parent="dev explorer",
        root_placeholder=True,
        aliases=["upload", "mkdir", "create"],
        usage="<folder>",
    )
    async def root_explorer_new(self, ctx: commands.Context[types.Bot], *, folder: str = ""):
        """Create an empty file/directory or upload a series of files.
        If `directory` is None, then it will be set to the current working directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        attachments = ctx.message.attachments
        if folder is None and not attachments:
            raise commands.MissingRequiredArgument(ctx.command.clean_params["folder"])  # type: ignore
        directory = self.format_path(folder) or self.cwd
        if attachments:  # upload files
            files_exist: list[str] = []
            for attachment in attachments:
                data = await attachment.read()
                try:
                    with open(directory + attachment.filename, "xb") as fp:
                        fp.write(data)
                except FileExistsError:
                    files_exist.append(attachment.filename)
                else:
                    self.explorer_rgs.append(
                        ManagementRegistration(directory + attachment.filename, ManagementOperation.UPLOAD)
                    )
            if files_exist:
                await send(
                    ctx,
                    f"{plural(len(files_exist), 'File', False)} " f"{', '.join(files_exist)} already exist.",
                )
            return await ctx.message.add_reaction("☑")
        path = pathlib.Path(directory)
        if path.exists() and ctx.invoked_with == "upload":
            await self.root_explorer_show(ctx, directory=folder)
        elif not path.exists() and not path.suffix:  # create new directory
            path.mkdir()
            self.explorer_rgs.append(ManagementRegistration(f"{path.absolute()}", ManagementOperation.CREATE))
            await ctx.message.add_reaction("☑")
        elif path.suffix:  # create new empty file
            try:
                fh = path.open("x", encoding="utf-8")
                fh.close()
            except (FileExistsError, UnicodeError):
                return await send(ctx, f"File {str(path.absolute())} already exists.")
            self.explorer_rgs.append(ManagementRegistration(f"{path.absolute()}", ManagementOperation.CREATE))
            await ctx.message.add_reaction("☑")
        elif path.exists():
            await send(ctx, f"Path {str(path.absolute())} already exists.")

    @root.command(
        name="edit",
        parent="dev explorer",
        root_placeholder=True,
        aliases=["change"],
        require_var_positional=True,
    )
    async def root_explorer_edit(
        self,
        ctx: commands.Context[types.Bot],
        attachment: discord.Attachment,
        *,
        directory: str,
    ):
        """Edit an existing file.
        This command does not change the file's name. Consider using `dev explorer rename`.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory, tailing=False)
        path = pathlib.Path(directory)
        if not path.is_file():
            return await send(ctx, f"File `{directory}` does not exist.")
        with path.open("wb") as file:
            file.write(await attachment.read())
        self.explorer_rgs.append(ManagementRegistration(f"{path.absolute()}", ManagementOperation.EDIT))
        await ctx.message.add_reaction("☑")

    @root.command(name="rename", parent="dev explorer", root_placeholder=True)
    async def root_explorer_rename(self, ctx: commands.Context[types.Bot], old_name: str, new_name: str):
        """Rename an existing file or directory.
        By default, the new path will be relative to the old path. Use `?` at the beginning
        of `new_name` to ignore this behavior and use the current working directory instead.
        Use `!` at the beginning of `old_name` and/or `new_name` to ignore the current working
        directory.
        The new item's name can't already exist.
        """
        old_name = self.format_path(old_name)
        old_path = pathlib.Path(old_name)
        new_name = new_name.lstrip("/")
        if new_name.startswith("?"):
            new_path = pathlib.Path(self.format_path(new_name.lstrip("?")))
        elif new_name.startswith("!"):
            new_path = pathlib.Path(self.format_path(new_name))
        else:
            new_path = pathlib.Path(str(old_path.parent.absolute()) + "/" + self.format_path("!" + new_name))
        if not old_path.exists():
            return await send(ctx, f"Path `{str(old_path.absolute())}` does not exist.")
        if new_path.exists():
            return await send(ctx, f"Path `{str(old_path.absolute())}` already exists.")
        try:
            old_path.rename(new_path)
        except FileNotFoundError:
            return await send(ctx, "Could not locate parent directory or it simply does not exist.")
        self.explorer_rgs.append(ManagementRegistration(f"{old_path}", ManagementOperation.RENAME, f"{new_path}"))
        await ctx.message.add_reaction("☑")

    @root.command(
        name="show",
        parent="dev explorer",
        root_placeholder=True,
        aliases=["view", "tree", "tree!"],
    )
    async def root_explorer_show(self, ctx: commands.Context[types.Bot], *, directory: str = ""):
        """Uploads an existing file to Discord or shows the tree of a directory.
        Execute `tree!` instead of `tree` to show the full path of the files and folders.
        Files are checked before sending, so the token of this bot will be replaced with `[token]`.
        If `directory` is None, then it will show the tree of the current working directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory, tailing=False) or self.cwd
        path = pathlib.Path(directory)
        assert ctx.invoked_with is not None
        if not path.exists():
            return await send(ctx, f"Path `{str(path.absolute())}` does not exist.")
        if ctx.invoked_with.startswith("tree"):
            if not path.is_dir():
                return await send(ctx, "Path is not a directory.")
            tree = [
                f"📂 {escape(directory) or '/'}",
                *[f"\t ├─ {'📄' if sub.is_file() else '📁'} " + escape(f"{sub.name}") for sub in path.iterdir()],
            ]
            if len(tree) == 1:
                return await send(ctx, "Directory is empty.")
            tree[-1] = tree[-1].replace("├", "└", 1)
            return await send(
                ctx,
                discord.Embed(description="\n".join(tree), color=discord.Color.blurple()),
                path_to_file=not ctx.invoked_with.endswith("!"),
            )
        if not path.is_file():
            return await send(ctx, "Path is not a file.")
        await send(ctx, discord.File(fp=io.BytesIO(path.read_bytes()), filename=path.name))

    @root.command(
        name="delete",
        parent="dev explorer",
        root_placeholder=True,
        aliases=["del", "remove", "rm", "rmdir"],
        require_var_positional=True,
    )
    async def root_explorer_delete(self, ctx: commands.Context[types.Bot], *, directory: str):
        """Delete an existing file or directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        A prompt will be shown if a directory is specified, and it is not empty.
        """
        directory = self.format_path(directory)
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Path `{str(path.absolute())}` does not exist.")
        if path.is_file():
            path.unlink()
            return await ctx.message.add_reaction("☑")
        if any(path.iterdir()):

            async def func() -> None:
                shutil.rmtree(path.name)  # thank you aperture!
                self.explorer_rgs.append(ManagementRegistration(f"{path.absolute()}", ManagementOperation.DELETE))
                await ctx.message.add_reaction("☑")

            await send(
                ctx,
                "\u26a0 The directory that you specified is not empty. "
                "Deleting it will delete all files and folders inside it. Do you want to proceed?",
                BoolInput(ctx.author, func),
            )
        else:
            path.rmdir()
            self.explorer_rgs.append(ManagementRegistration(f"{path.absolute()}", ManagementOperation.DELETE))
            await ctx.message.add_reaction("☑")

    @root_explorer.error
    async def root_files_error(self, ctx: commands.Context[types.Bot], exception: commands.CommandError):
        if isinstance(exception, commands.TooManyArguments):
            assert ctx.prefix is not None and ctx.invoked_with is not None
            return await send(
                ctx,
                f"`dev {ctx.invoked_with}` has no subcommand " f"`{parse_invoked_subcommand(ctx)}`.",
            )
        optional_raise(ctx, exception)

    def format_path(self, directory: str, *, tailing: bool = True) -> str:
        """Format the given filepath to the correct directory."""
        directory = directory.replace("\\", "/").replace("|root|", Settings.root_folder)
        if not directory.startswith("!"):
            directory = self.cwd + directory.lstrip("/")
        if tailing and not directory.endswith("/"):
            directory += "/"
        elif not tailing and directory.endswith("/"):
            directory = directory[:-1]
        if directory.startswith("!"):
            directory = "/" + directory.replace("!", "", 1).lstrip("/")
        return directory
