# -*- coding: utf-8 -*-

"""
dev.config.management
~~~~~~~~~~~~~~~~~~~~~

Files, folders and anything that has to do with directory-related commands.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


import discord
import io
import os
import pathlib
import shutil

from discord.ext import commands
from typing import Optional

from dev.handlers import BoolInput
from dev.types import BotT

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings


class RootManagement(Root):
    def __init__(self, bot: BotT):
        super().__init__(bot)
        self.cwd: str = os.getcwd() + "/"

    @root.command(name="cwd", parent="dev", aliases=["change_cwd"], root_placeholder=True)
    async def root_files_cwd(self, ctx: commands.Context, *, new_cwd: Optional[str] = None):
        """Change the current working directory that the bot should focus on.
        Don't specify `new_cwd` to get the current working directory.
        """
        if new_cwd is None:
            return await send(ctx, f"Current working directory: `{self.cwd}`")
        new_cwd = new_cwd.replace("|root|", Settings.ROOT_FOLDER)
        if not pathlib.Path(new_cwd).exists():
            return await send(ctx, f"Directory `{new_cwd.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        self.cwd = new_cwd + "/" if not new_cwd.endswith("/") else new_cwd
        await ctx.message.add_reaction("☑")

    @root.group(name="files", parent="dev", aliases=["file"])
    async def root_files(self, ctx: commands.Context):
        """Everything related to file management."""

    @root_files.command(name="upload", aliases=["new", "create"], root_placeholder=True)
    async def root_files_upload(self, ctx: commands.Context, attachment: discord.Attachment, *, directory: Optional[str] = None):
        """Create a new file.
        If `directory` is None, then it will be set to the current working directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.PATH_TO_FILE) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"Directory `{directory}` does not exist.")
        if pathlib.Path(directory + attachment.filename).is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` already exists.")
        with open(directory + attachment.filename, "x") as file:
            content = await attachment.read()
            file.write(content.decode("utf-8"))
        await ctx.message.add_reaction("☑")

    @root_files.command(name="edit", aliases=["change"], require_var_positional=True, root_placeholder=True)
    async def root_files_edit(self, ctx: commands.Context, attachment: discord.Attachment, *, directory: str):
        """Edit an existing file.
        Note that if a file is specified with another name, the file's name will not change. Use `dev files|file rename` for that.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.PATH_TO_FILE) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        if not pathlib.Path(directory).is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        with open(directory, "w") as file:
            content = await attachment.read()
            file.write(content.decode("utf-8"))
        await ctx.message.add_reaction("☑")

    @root_files.command(name="rename", root_placeholder=True)
    async def root_files_rename(self, ctx: commands.Context, current_name: str, new_name: str):
        """Rename an existing file.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if current_name is None else current_name.replace('|root|', Settings.PATH_TO_FILE) if current_name.startswith('!') else self.cwd + current_name.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        path = pathlib.Path(directory)
        if not path.is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        path.rename(f"{(parent := '/'.join(directory.split('/')[:-1])) + ('/' if parent else '')}{new_name}")
        await ctx.message.add_reaction("☑")

    @root_files.command(name="show", aliases=["view"], require_var_positional=True, root_placeholder=True)
    async def root_files_show(self, ctx: commands.Context, *, directory: str):
        """Show an existing file.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.PATH_TO_FILE) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        if not pathlib.Path(directory).is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        with open(directory, "r") as file:
            await send(ctx, discord.File(fp=io.BytesIO(file.read().encode('utf-8')), filename=directory.split("/")[-1]))

    @root_files.command(name="delete", aliases=["del", "remove", "rm"], require_var_positional=True, root_placeholder=True)
    async def root_files_delete(self, ctx: commands.Context, *, directory: str):
        """Delete an existing file.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.PATH_TO_FILE) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        path = pathlib.Path(directory)
        if not path.is_file():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        path.unlink()
        await ctx.message.add_reaction("☑")

    @root.group(name="folders", parent="dev", aliases=["folder", "dir", "directory"])
    async def root_folders(self, ctx: commands.Context):
        """Everything related to folder management."""

    @root_folders.command(name="new", aliases=["create", "mkdir"], require_var_positional=True, root_placeholder=True)
    async def root_folders_new(self, ctx: commands.Context, *, directory: str):
        """Create a new folder.
        The folder's name cannot already exist.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.PATH_TO_FILE) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        path = pathlib.Path(directory)
        if path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` already exists.")
        path.mkdir()
        await ctx.message.add_reaction("☑")

    @root_folders.command(name="rename", root_placeholder=True)
    async def root_folders_rename(self, ctx: commands.Context, current_name: str, new_name: str):
        """Rename an already existing folder.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if current_name is None else current_name.replace('|root|', Settings.PATH_TO_FILE) if current_name.startswith('!') else self.cwd + current_name.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        path.rename(new_name)
        await ctx.message.add_reaction("☑")

    @root_folders.command(name="tree", aliases=["tree!"], root_placeholder=True)
    async def root_folders_tree(self, ctx: commands.Context, *, directory: Optional[str] = None):
        """Get the files and folders inside a given directory.
        If `directory` is None, then it will show the tree of the current working directory.
        Execute `tree!` instead of `tree` to show the full path of the files and folders.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.PATH_TO_FILE) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        replace = False if ctx.invoked_with.endswith("!") else True
        tree = ["```", directory.replace(Settings.PATH_TO_FILE, '') if replace else directory, *[f"   ├─ {str(file).replace(Settings.PATH_TO_FILE, '') if replace else file} ({'file' if file.is_file() else 'folder'})" for file in path.iterdir()]]
        tree[-1] = f"{tree[-1].replace('├', '└')}"
        tree.append("```")
        await send(ctx, "\n".join(tree))

    @root_folders.command(name="delete", aliases=["del", "remove", "rmdir", "rm"], require_var_positional=True, root_placeholder=True)
    async def root_folders_delete(self, ctx: commands.Context, *, directory: str):
        """Delete an already existing folder.
        If the folder is not empty, a prompt will pop up asking if you're sure you want to delete the directory.
        Use `!` at the beginning of the directory to ignore the current working directory.
        """
        directory = (cwd := f"{self.cwd if directory is None else directory.replace('|root|', Settings.ROOT_FOLDER) if directory.startswith('!') else self.cwd + directory.replace('|root|', Settings.ROOT_FOLDER)}") + f"{'/' if not cwd.endswith('/') else ''}".rstrip("/")
        path = pathlib.Path(directory)
        if not path.exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        if path.iterdir():
            async def func():
                shutil.rmtree(path.name)  # thank you aperture!
                await ctx.message.add_reaction("☑")
            await send(ctx, f":warning: The directory that you specified is not empty. Deleting it will delete all files and folders inside it. Do you want to proceed?", BoolInput(ctx.author, func))
        else:
            path.rmdir()
            await ctx.message.add_reaction("☑")
