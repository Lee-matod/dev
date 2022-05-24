import discord
import io
import os
import pathlib

from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.startup import Settings


class RootManagement(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.cwd: str = os.getcwd()

    @root.command(name="cwd", parent="dev")
    async def root_files_cwd(self, ctx: commands.Context, *, new_cwd: str = None):
        """Change the current working directory that the bot should focus on."""
        if new_cwd is None:
            return await send(ctx, f"Current working directory: `{self.cwd}`")
        new_cwd = new_cwd.replace("|root|", Settings.ROOT_FOLDER)
        if not pathlib.Path(new_cwd).exists():
            return await send(ctx, f"Directory `{new_cwd.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        self.cwd = new_cwd
        await ctx.message.add_reaction("☑")

    @root.group(name="files", parent="dev", aliases=["file"])
    async def root_files(self, ctx: commands.Context):
        """Everything related to file management"""

    @root_files.command(name="upload", aliases=["new", "create"])
    async def root_files_upload(self, ctx: commands.Context, attachment: discord.Attachment, *, directory: str = None):
        """Create a new file"""
        if directory is None:
            directory = self.cwd
        directory = f"{directory.replace('|root|', Settings.ROOT_FOLDER)}/{attachment.filename}"
        if pathlib.Path(directory).exists():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` already exists.")
        with open(directory, "x") as file:
            content = await attachment.read()
            file.write(content.decode("utf-8"))
        await ctx.message.add_reaction("☑")

    @root_files.command(name="edit", aliases=["change"], require_var_positional=True)
    async def root_files_edit(self, ctx: commands.Context, attachment: discord.Attachment, *, directory: str):
        """Edit an existing file"""
        directory = f"{self.cwd + '/' if directory.startswith('|') else ''}{directory.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        with open(directory, "w") as file:
            content = await attachment.read()
            file.write(content.decode("utf-8"))
        await ctx.message.add_reaction("☑")

    @root_files.command(name="rename")
    async def root_files_rename(self, ctx: commands.Context, current_name: str, new_name: str):
        """Rename an existing file."""
        directory = f"{self.cwd + '/' if current_name.startswith('|') else ''}{current_name.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        pathlib.Path(directory).rename(
            f"{(parent := '/'.join(directory.split('/')[:-1])) + ('/' if parent else '')}{new_name}")
        await ctx.message.add_reaction("☑")

    @root_files.command(name="show", aliases=["view"])
    async def root_files_show(self, ctx: commands.Context, *, directory: str):
        """Show an existing file"""
        directory = f"{self.cwd + '/' if directory.startswith('|') else ''}{directory.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"File `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        with open(directory, "r") as file:
            await send(ctx, discord.File(fp=io.BytesIO(file.read().encode('utf-8')), filename=directory.split("/")[-1]))

    @root_files.command(name="delete", aliases=["del", "remove"], require_var_positional=True)
    async def root_files_delete(self, ctx: commands.Context, *, directory: str):
        """Delete an existing file."""
        directory = f"{self.cwd + '/' if directory.startswith('|') else ''}{directory.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory.replace(Settings.PATH_TO_FILE, '')).exists():
            return await send(ctx, f"File `{directory}` does not exist.")
        os.remove(directory)
        await ctx.message.add_reaction("☑")

    @root.group(name="folders", parent="dev", aliases=["folder"])
    async def root_folders(self, ctx: commands.Context):
        """Everything related to folder management"""

    @root_folders.command(name="new", aliases=["create"])
    async def root_folders_new(self, ctx: commands.Context, *, directory: str):
        """Create a new folder."""
        directory = f"{self.cwd + '/' if directory.startswith('|') else ''}{directory.replace('|root|', Settings.ROOT_FOLDER)}"
        if pathlib.Path(directory).exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` already exists.")
        pathlib.Path(directory).mkdir()
        await ctx.message.add_reaction("☑")

    @root_folders.command(name="rename")
    async def root_folders_rename(self, ctx: commands.Context, current_name: str, new_name: str):
        """Rename an already existing folder."""
        directory = f"{self.cwd + '/' if current_name.startswith('|') else ''}{current_name.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        pathlib.Path(directory).rename(new_name)
        await ctx.message.add_reaction("☑")

    @root_folders.command(name="tree", aliases=["tree!"])
    async def root_folders_tree(self, ctx: commands.Context, *, directory: str = None):
        """Get the files and folders inside a given directory.
        Execute `tree!` instead of `tree` to show the full path of the files and folders.
        """
        if directory is None:
            directory = self.cwd
        directory = f"{self.cwd + '/' if directory.startswith('|') else ''}{directory.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        replace = False if ctx.invoked_with.endswith("!") else True
        tree = ["```", directory.replace(Settings.PATH_TO_FILE, '') if replace else directory, *[
            f"   ├─ {str(file).replace(Settings.PATH_TO_FILE, '') if replace else file} ({'file' if file.is_file() else 'folder'})"
            for file in pathlib.Path(directory).iterdir()]]
        tree[-1] = f"{tree[-1].replace('├', '└')}"
        tree.append("```")
        await send(ctx, "\n".join(tree))

    @root_folders.command(name="delete", aliases=["del", "remove"])
    async def root_folders_delete(self, ctx: commands.Context, *, directory):
        """Delete an already existing folder."""
        directory = f"{self.cwd + '/' if directory.startswith('|') else ''}{directory.replace('|root|', Settings.ROOT_FOLDER)}"
        if not pathlib.Path(directory).exists():
            return await send(ctx, f"Directory `{directory.replace(Settings.PATH_TO_FILE, '')}` does not exist.")
        pathlib.Path(directory).rmdir()
        await ctx.message.add_reaction("☑")
