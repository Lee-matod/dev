# -*- coding: utf-8 -*-

"""
dev.plugins.files
~~~~~~~~~~~~~~~~~

Files and folders manager.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import os
import pathlib
import shutil
from typing import TYPE_CHECKING, List, Optional

import discord
from discord.ext import commands

from dev import root
from dev.components import Prompt
from dev.scope import Settings
from dev.utils.functs import send
from dev.utils.utils import escape

if TYPE_CHECKING:
    from dev import types


class RootFiles(root.Plugin):
    """File, folder, and directory management"""

    @root.group("explorer", parent="dev", aliases=["explr", "explorer!", "explr!"], invoke_without_command=True)
    async def root_explorer(self, ctx: commands.Context[types.Bot], *, path: Optional[pathlib.Path] = None):
        """View the tree of a directory or send a file.

        Parameters
        ----------
        path: Optional[:class:`pathlib.Path`]
            View a specific file or directory. If not provided, defaults to the current working directory.
        """
        assert ctx.invoked_with is not None
        if path is None:
            path = pathlib.Path(Settings.CWD)
        if not path.exists():
            return await send(ctx, "File or directory not found.")
        if path.is_file():
            return await send(ctx, discord.File(path))
        folders: List[str] = []
        files: List[str] = []
        for item in path.iterdir():
            if item.is_dir():
                folders.append("\N{FILE FOLDER} " + escape(str(item.absolute())))
            elif item.is_file():
                files.append("\N{PAGE FACING UP} " + escape(str(item.absolute())))
        if not folders and not files:
            return await send(ctx, "Directory is empty.")
        *finalized, last = [
            f"\N{BOX DRAWINGS DOUBLE VERTICAL AND RIGHT}\N{BOX DRAWINGS DOUBLE HORIZONTAL} {item.replace(str(path.absolute()), '', 1)}"
            for item in (*folders, *files)
        ]
        last = f"\N{BOX DRAWINGS DOUBLE UP AND RIGHT}{last[1:]}"
        await send(
            ctx,
            f"\N{OPEN FILE FOLDER} {escape(str(path.absolute()))}\n" + "\n".join(finalized) + f"\n{last}",
            path_to_file=not ctx.invoked_with.endswith("!"),
        )

    @root.command("mkdir", parent="dev explorer", aliases=["touch"])
    async def root_explorer_mkdir(self, ctx: commands.Context[types.Bot], *, path: Optional[pathlib.Path] = None):
        """Create a new file or directory. Use touch or mkdir respectively.

        If attachments are provided, they will be uploaded to the given directory.

        Parameters
        ----------
        path: Optional[:class:`pathlib.Path`]
            The file or directory name to create. Defaults to the current working directory if attachments
            are also provided.
        """
        assert ctx.invoked_with is not None
        assert ctx.command is not None

        attachments = ctx.message.attachments
        if path is None:
            path = pathlib.Path(Settings.CWD)
            if not attachments:
                # We know Current Working Directory already exists
                raise commands.MissingRequiredArgument(ctx.command.params["name"])
        if path.exists():
            if path.is_dir() and attachments:
                skipped: List[pathlib.Path] = []
                for attach in attachments:
                    content = await attach.read()
                    as_path = path / attach.filename
                    if as_path.exists():
                        skipped.append(as_path)
                        continue
                    with as_path.open("wb") as fp:
                        fp.write(content)
                fmt = (
                    (
                        "\n\nSkipped the following attachments because duplicates were found:\n"
                        + "\n".join(map(lambda p: escape(str(p)), skipped))
                    )
                    if skipped
                    else ""
                )
                return await send(ctx, f"Successfully finished uploading attachments to directory.{fmt}")
            return await send(ctx, "File or directory already exists.")
        if ctx.invoked_with == "mkdir":
            path.mkdir()
            return await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")
        path.touch()
        await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")

    @root.command("move", parent="dev explorer", aliases=["mv"], require_var_positional=True)
    async def root_explorer_move(
        self, ctx: commands.Context[types.Bot], target: pathlib.Path, *, destination: pathlib.Path
    ):
        """Move an item from one directory to another.

        Parameters
        ----------
        target: :class:`pathlib.Path`
            The file or directory that will be moved.
        destination: :class:`pathlib.Path`
            The directory where the given file or folder will be moved to.
        """
        if destination.is_file():
            return await send(ctx, "Target directory is a file.")
        if not destination.exists():
            return await send(ctx, "Target directory does not exist.")
        if not target.exists():
            return await send(ctx, "Origin file or folder does not exist.")

        async def move():
            if duplicate is not None:
                if duplicate.is_file():
                    duplicate.unlink()
                else:
                    duplicate.rmdir()
            shutil.move(str(target.absolute()), destination)
            await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")

        duplicate = discord.utils.get(destination.iterdir(), name=target.name)
        if duplicate is not None:
            return await send(
                ctx,
                "\N{WARNING SIGN}\N{VS16} Target directory has an item with the same name!\n"
                "Proceeding might cause it to be replaced by the new item. Are you sure?",
                Prompt(ctx.author.id, move),
            )
        await move()

    @root.command("rename", parent="dev explorer", require_var_positional=True)
    async def root_explorer_rename(self, ctx: commands.Context[types.Bot], origin: pathlib.Path, *, name: str):
        """Rename a given item. The new name should be provided without any parent directories.

        Parameters
        ----------
        origin: :class:`pathlib.Path`
            The file or directory that should be renamed.
        name: :class:`str`
            The new name that the item should receive.
        """
        if pathlib.Path(name).exists():
            return await send(ctx, "New path name already exists.")
        if not origin.exists():
            return await send(ctx, "File or directory not found.")
        parent = origin.parent if origin.is_file() else origin
        try:
            origin.rename(parent / name)
        except FileNotFoundError:
            # We already checked if the origin exists, so this means that something went wrong with name
            return await send(ctx, "Invalid new name provided.")
        await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")

    @root.command(
        "delete", parent="dev explorer", aliases=["del", "remove", "rm", "rmdir"], require_var_positional=True
    )
    async def root_explorer_delete(self, ctx: commands.Context[types.Bot], *, path: pathlib.Path):
        """Delete a file or directory. For security reasons, current working directory is blacklisted.

        If provided with a directory that is not empty, a prompt will show before deleting.

        Parameters
        ----------
        path: :class:`pathlib.Path`
            The file or directory that will be removed.
        """
        if not path.exists():
            return await send(ctx, "File or directory not found.")
        if str(path.absolute()) == os.getcwd():
            return await send(ctx, "For security reasons, deleting current working directory is not allowed.")
        if path.is_file():
            path.unlink()
            return await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")
        try:
            path.rmdir()
        except OSError:

            async def func() -> None:
                shutil.rmtree(path)
                await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")

            return await send(
                ctx,
                "\N{WARNING SIGN}\N{VS16} Directory is not empty!\n"
                "Deleting it will delete all files and folders inside it. Do you want to proceed?",
                Prompt(ctx.author.id, func),
            )
        await ctx.message.add_reaction("\N{BALLOT BOX WITH CHECK}")
