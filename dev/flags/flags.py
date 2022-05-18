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

from dev.utils.baseclass import Root, root
from dev.utils.functs import send


if TYPE_CHECKING:
    from dev.utils.baseclass import Command, Group


class RootFlags(Root, command_attrs={"hidden": True}):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)

    @root.command(name="--help", aliases=["--man"], parent="dev")
    async def root_help(self, ctx: commands.Context, *, command_string: str = ""):
        """Help command made exclusively made for the `dev` extensions.
        Flags are hidden, but they can still be accessed and attributes can still be viewed using their respective commands.
        """
        command: Union[Command, Group] = self.bot.get_command(f"dev {command_string}".strip())
        if not command:
            return await send(ctx, f"Command `dev {command_string}` not found.")
        docs = '\n'.join(command.help.split("\n")[1:]) or 'No docs available.'
        embed = discord.Embed(title=command.qualified_name, description=command.short_doc or 'No description found.', color=discord.Color.darker_gray())
        embed.add_field(name="usage", value=f"dev {command.name}{'|' + '|'.join(alias for alias in command.aliases) if command.aliases else ' '} {command.usage or command.signature}", inline=False)
        embed.add_field(name="docs", value=docs, inline=False)
        if isinstance(command, commands.Group):
            command_list = [cmd.name for cmd in command.commands if not cmd.hidden]
            command_list.sort()
            subcommands = '\n'.join(command_list)
            embed.add_field(name="subcommands", value=subcommands or 'No subcommands')
        return await ctx.send(embed=embed)

    @root.command(name="--attributes", aliases=["-attrs"], parent="dev")
    async def root_(self, ctx: commands.Context, *, command_string: str = ""):
        """Get the attributes of a command.
        This is exclusive to the `dev` extension.
        """
        command: Union[Command, Group] = self.bot.get_command(f"dev {command_string}".strip())
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        embed = discord.Embed(title=command.qualified_name, color=discord.Color.darker_gray())
        embed.add_field(name="Cog", value=command.cog_name)
        embed.add_field(name="Requires Positional Variables", value=command.require_var_positional)
        embed.add_field(name="Supports Virtual Variables", value=command.supports_virtual_vars)
        # still have more to do

    @root.command(name="--inspect", aliases=["-i"], parent="dev")
    async def root_types(self, ctx: commands.Context, *, command_string: str):
        """Get the signature and the types expected for a command.
        This is not exclusive to the `dev` extension.
        """
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        params = []
        for name, sign in command.clean_params.items():
            if sign.kind == inspect.Parameter.KEYWORD_ONLY:
                params.append(f"`*, {name}{'*' if sign.required else ''}`: _{sign.converter.__name__ if isinstance(sign.converter, type) else sign.converter}_{' = ' + str(sign.default) if not isinstance(sign.default, type) else ''}")
            elif sign.kind == inspect.Parameter.VAR_POSITIONAL:
                params.append(f"`*{name}{'*' if sign.required else ''}`: _{sign.converter.__name__ if isinstance(sign.converter, type) else sign.converter}_{' = ' + str(sign.default) if not isinstance(sign.default, type) else ''}")
            else:  # **kwargs aren't supported in dpy
                params.append(f"`{name}{'*' if sign.required else ''}`: _{sign.converter.__name__ if isinstance(sign.converter, type) else sign.converter}_{' = ' + str(sign.default) if not isinstance(sign.default, type) else ''}")
        await send(ctx, discord.Embed(title=command_string, description="\n".join(params), color=discord.Color.darker_gray()))

    @root.command(name="--source", parent="dev", aliases=["-src", "--sourceFile", "-srcF"])
    async def root_source(self, ctx: commands.Context, *, command_string: str = ""):
        """View the source code of a command.
        This is not exclusive to the `dev` extension.
        The bot's token is hidden as `TOKEN`.
        Alternatively, use `dev --sourceFile|-srcF` to show the command's source code file.
        """
        if ctx.invoked_with in ["--sourceFile", "-srcF"]:
            file: bool = True
        else:
            file: bool = False
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")

        if not file:
            if command.qualified_name in [name[0] for name in self.CALLBACKS.values()]:
                return await send(ctx, f"{[source[2] for source in reversed(self.CALLBACKS.values()) if source[0] == command.qualified_name][0]}", py_codeblock=True)
            lines, _ = inspect.getsourcelines(command.callback)
            return await send(ctx, f"{''.join(lines)}", py_codeblock=True)

        directory = inspect.getsourcefile([callback[1] for callback in self.CALLBACKS.values() if callback[0] == command.qualified_name][0])
        with open(directory) as source:
            await send(ctx, f"{''.join(source.readlines())}", py_codeblock=True)
