# -*- coding: utf-8 -*-

"""
dev.config.management
~~~~~~~~~~~~~~~~~~~~~

Files, folders and anything that has to do with directory-related commands.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import io
import os
import pathlib
import shutil
from typing import TYPE_CHECKING, List, Optional

import discord

from dev.handlers import BoolInput
from dev.registrations import ManagementRegistration
from dev.types import ManagementOperation

from dev.utils.baseclass import Root, root
from dev.utils.functs import send, table_creator
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types


class RootManagement(Root):
    def __init__(self, bot: types.Bot):
        super().__init__(bot)
        self.cwd: str = os.getcwd() + "/"
        self.files_rgs: List[ManagementRegistration] = []
        self.folders_rgs: List[ManagementRegistration] = []

    @root.command(name="cwd", parent="dev", root_placeholder=True, aliases=["change_cwd"])
    async def root_files_cwd(self, ctx: commands.Context, *, new_cwd: Optional[str] = None):
        """Change or view the current working directory that the bot should use."""
        if new_cwd is None:
            return await send(ctx, f"Current working directory is: `{self.cwd}`")
        new_cwd = new_cwd.replace("|root|", Settings.ROOT_FOLDER)
        if not pathlib.Path(new_cwd).exists():
            return await send(ctx, f"Directory `{new_cwd.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        self.cwd = new_cwd + "/" if not new_cwd.endswith("/") else new_cwd
        await ctx.message.add_reaction("☑")

    @root.group(name="files", parent="dev", aliases=["file"], invoke_without_command=True)
    async def root_files(self, ctx: commands.Context):
        """View modifications made to files."""
        if files := self.files_rgs:
            rows = [
                [index, rgs.operation_type.name, f"{rgs}. Date modified: {rgs.created_at}"]
                for index, rgs in enumerate(files, start=1)
            ]
            return await send(ctx, f"```py\n{table_creator(rows, ['IDs', 'Types', 'Descriptions'])}\n```")
        await send(ctx, "No modifications have been made.")

    @root.command(name="upload", parent="dev files", root_placeholder=True, aliases=["new"])
    async def root_files_upload(
            self,
            ctx: commands.Context,
            attachment: discord.Attachment,
            *,
            directory: Optional[str] = None
    ):
        """Upload a new file to a given directory.
        If `directory` is None, then it will be set to the current working directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory or self.cwd)
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"Directory `{directory}` does not exist.")
        if pathlib.Path(directory + attachment.filename).is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` already exists.")
        with open(directory + attachment.filename, "x") as file:
            content = await attachment.read()
            file.write(content.decode("utf-8"))
        self.files_rgs.append(ManagementRegistration(directory + attachment.filename, ManagementOperation.UPLOAD))
        await ctx.message.add_reaction("☑")

    @root.command(
        name="edit",
        parent="dev files",
        root_placeholder=True,
        aliases=["change"],
        require_var_positional=True
    )
    async def root_files_edit(self, ctx: commands.Context, attachment: discord.Attachment, *, directory: str):
        """Edit an existing file.
        This command does not change the file's name. Consider using `dev files|file rename`.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory, back=False)
        if not pathlib.Path(directory).is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        with open(directory, "w") as file:
            content = await attachment.read()
            file.write(content.decode("utf-8"))
        self.files_rgs.append(ManagementRegistration(directory, ManagementOperation.EDIT))
        await ctx.message.add_reaction("☑")

    @root.command(name="rename", parent="dev files", root_placeholder=True, require_var_positional=True)
    async def root_files_rename(self, ctx: commands.Context, new_name: str, *, directory: str):
        """Rename an existing file.
        The directory path should include the full name of the file that should be renamed.
        Use `!` at the beginning of the directory to ignore the current working directory.
        The new file name can't already exist.
        """
        directory = self.format_path(directory)
        new_name = self.format_path(new_name, back=False)
        path = pathlib.Path(directory)
        if not path.is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        new_name = new_name.lstrip('/').lstrip("\\")
        renamed = f"{(parent := '/'.join(directory.split('/')[:-1])) + ('/' if parent else '')}{new_name}"
        if pathlib.Path(renamed).exists():
            return await send(ctx, f"A file with the name {new_name} already exists in this directory.")
        path.rename(renamed)
        self.files_rgs.append(ManagementRegistration(directory, ManagementOperation.RENAME, new_name))
        await ctx.message.add_reaction("☑")

    @root.command(name="show", parent="dev files", root_placeholder=True, aliases=["view"], require_var_positional=True)
    async def root_files_show(self, ctx: commands.Context, *, directory: str):
        """Show an existing file.
        Files are checked before sending, so the token of this bot will be replaced with `[token]`.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory, back=False)
        if not pathlib.Path(directory).is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        with open(directory, "r") as file:
            await send(ctx, discord.File(fp=io.BytesIO(file.read().encode('utf-8')), filename=directory.split("/")[-1]))

    @root.command(
        name="delete",
        parent="dev files",
        root_placeholder=True,
        aliases=["del", "remove", "rm"],
        require_var_positional=True
    )
    async def root_files_delete(self, ctx: commands.Context, *, directory: str):
        """Delete an existing file.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory)
        path = pathlib.Path(directory)
        if not path.is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        path.unlink()
        self.files_rgs.append(ManagementRegistration(directory, ManagementOperation.DELETE))
        await ctx.message.add_reaction("☑")

    @root.group(name="folders", parent="dev", aliases=["folder", "dir", "directory"], invoke_without_command=True)
    async def root_folders(self, ctx: commands.Context):
        """View modifications made to folders."""
        if folders := self.folders_rgs:
            rows = [
                [index, rgs.operation_type.name, f"{rgs}. Date modified: {rgs.created_at}"]
                for index, rgs in enumerate(folders, start=1)
            ]
            return await send(ctx, f"```py\n{table_creator(rows, ['IDs', 'Types', 'Descriptions'])}\n```")
        await send(ctx, "No modifications have been made.")

    @root.command(
        name="new",
        parent="dev folders",
        root_placeholder=True,
        aliases=["create", "mkdir"],
        require_var_positional=True
    )
    async def root_folders_new(self, ctx: commands.Context, *, directory: str):
        """Create a new folder.
        The name of the new folder cannot already exist in the directory given.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory)
        path = pathlib.Path(directory)
        if path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` already exists.")
        path.mkdir()
        self.folders_rgs.append(ManagementRegistration(directory, ManagementOperation.CREATE))
        await ctx.message.add_reaction("☑")

    @root.command(name="rename", parent="dev folders", root_placeholder=True, require_var_positional=True)
    async def root_folders_rename(self, ctx: commands.Context, new_name: str, *, directory: str):
        """Rename an already existing folder.
        The directory path should include the full name of the folder that should be renamed.
        Use `!` at the beginning of the directory to ignore the current working directory.
        The new folder name can't already exist.
        """
        directory = self.format_path(directory)
        new_name = self.format_path(new_name, back=False)
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        path.rename(new_name)
        self.folders_rgs.append(ManagementRegistration(directory, ManagementOperation.RENAME, new_name))
        await ctx.message.add_reaction("☑")

    @root.command(name="tree", parent="dev folders", root_placeholder=True, aliases=["tree!"])
    async def root_folders_tree(self, ctx: commands.Context, *, directory: Optional[str] = None):
        """Get the files and folders inside a given directory.
        If `directory` is None, then it will show the tree of the current working directory.
        Execute `tree!` instead of `tree` to show the full path of the files and folders.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory or self.cwd)
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        replace = not ctx.invoked_with.endswith("!")
        tree = [
            "```",
            directory.replace(Settings.PATH_TO_FILE, '') if replace else directory,
            *[f"   ├─ {str(file).replace(Settings.PATH_TO_FILE, '') if replace else file} "
              f"({'file' if file.is_file() else 'folder'})" for file in path.iterdir()]
        ]
        tree[-1] = f"{tree[-1].replace('├', '└')}"
        tree.append("```")
        await send(ctx, "\n".join(tree))

    @root.command(
        name="delete",
        parent="dev folders",
        root_placeholder=True,
        aliases=["del", "remove", "rmdir", "rm"],
        require_var_positional=True
    )
    async def root_folders_delete(self, ctx: commands.Context, *, directory: str):
        """Delete an already existing folder.
        If the folder is not empty, a prompt will be sent asking if you're sure you want to delete the directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = self.format_path(directory)
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        if path.iterdir():
            async def func():
                shutil.rmtree(path.name)  # thank you aperture!
                self.folders_rgs.append(ManagementRegistration(directory, ManagementOperation.DELETE))
                await ctx.message.add_reaction("☑")
            await send(
                ctx,
                f":warning: The directory that you specified is not empty. "
                f"Deleting it will delete all files and folders inside it. Do you want to proceed?",
                BoolInput(ctx.author, func)
            )
        else:
            path.rmdir()
            self.folders_rgs.append(ManagementRegistration(directory, ManagementOperation.DELETE))
            await ctx.message.add_reaction("☑")

    def format_path(self, directory: str, *, back: bool = True) -> str:
        directory = directory.replace("\\", "/").replace("|root|", Settings.ROOT_FOLDER)
        if not directory.startswith("!"):
            directory = self.cwd + directory.lstrip("/")
        if back and not directory.endswith("/"):
            directory += "/"
        elif not back and directory.endswith("/"):
            directory = directory[:-1]
        return directory
