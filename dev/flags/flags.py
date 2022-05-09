# -*- coding: utf-8 -*-

"""
dev.flags.flags
~~~~~~~~~~~~~~~

Other types of flag commands such as checking the version of a command or the source code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import discord
import inspect

from discord.ext import commands
from typing import Union, TYPE_CHECKING

from dev.utils.functs import send
from dev.utils.baseclass import root, Root


if TYPE_CHECKING:
    from dev.utils.baseclass import Command, Group


class RootFlags(Root, command_attrs={"hidden": True}):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @root.command(name="--help", aliases=["--man"], parent="dev", hidden=True)
    async def root_help(self, ctx: commands.Context, *, command_string: str = ""):
        """Help command made exclusively for the `dev` cog.
        Flags are hidden, but they can still be accessed and attributes can still be viewed using their respective commands.
        """
        command: Union[Command, Group] = self.bot.get_command(f"dev {command_string}".strip())
        if not command:
            return await send(ctx, f"Command `dev {command_string}` not found.")
        docs = '\n'.join(command.help.split("\n")[1:]) or 'No docs available.'
        embed = discord.Embed(title=command.qualified_name, description=command.short_doc or 'No description found.', color=discord.Color.darker_gray())
        embed.add_field(name="usage", value=f"dev {command.name}{'|' + '|'.join(alias for alias in command.aliases) if command.aliases else ' '} {command.usage or command.signature}", inline=False)
        embed.add_field(name="docs", value=docs, inline=False)
        embed.set_footer(text=f"Supports virtual variables: {command.supports_virtual_vars}")
        if isinstance(command, commands.Group):
            command_list = [cmd.name for cmd in command.commands]
            command_list.sort()
            subcommands = '\n'.join(command_list)
            embed.add_field(name="subcommands", value=subcommands or 'No subcommands')
        return await ctx.send(embed=embed)

    @root.command(name="--source", parent="dev", aliases=["-src", "--sourceFile", "-srcF"], hidden=True)
    async def root_source(self, ctx: commands.Context, *, cmd: str = ""):
        """View the source code of a command.
        Unlike other flags, this is not exclusive to the `?dev` extension.
        The bot's token is hidden as `TOKEN`.
        Alternatively, use `dev --sourceFile|-srcF` to show the command's source code file.
        """
        if ctx.invoked_with in ["--sourceFile", "-srcF"]:
            file: bool = True
        else:
            file: bool = False
        command = self.bot.get_command(cmd)
        if not command:
            return await send(ctx, f"Command `{cmd}` not found.")
        override_callback = None
        if command.qualified_name in self.OVERRIDE_CALLBACKS:
            override_callback = self.OVERRIDE_CALLBACKS[command.qualified_name]

        if not file:
            if override_callback:
                return await send(ctx, override_callback)
            lines, _ = inspect.getsourcelines(command.callback)
            return await send(ctx, f"{''.join(lines)}", is_py_bt=True)

        if command.qualified_name in self.COMMAND_CALLBACKS:
            command.callback = self.COMMAND_CALLBACKS[command.qualified_name]
        directory = inspect.getsourcefile(command.callback)
        with open(directory) as source:
            await send(ctx, f"{''.join(source.readlines())}", is_py_bt=True)
