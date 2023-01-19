# -*- coding: utf-8 -*-

"""
dev.misc.flags
~~~~~~~~~~~~~~

Flag-like commands for command analysis.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import send
from dev.utils.utils import codeblock_wrapper

if TYPE_CHECKING:
    from dev import types
    from dev.utils.baseclass import _DiscordCommand  # type: ignore
    from dev.utils.baseclass import _DiscordGroup  # type: ignore


class RootFlags(Root):
    """Root command flags"""

    @root.command(name="--help", parent="dev", global_use=True, aliases=["--man"], hidden=True)
    async def root_help(self, ctx: commands.Context[types.Bot], *, command_string: str = ""):
        """Help command made exclusively made for the `dev` extensions.
        Flags are hidden, but they can still be accessed and attributes can still be viewed.
        """
        command: _DiscordCommand | _DiscordGroup = self.bot.get_command(f"dev {command_string}".strip())  # type: ignore
        if not command:
            return await send(ctx, f"Command `dev {command_string}` not found.")
        docs = "\n".join((command.help or "").split("\n")[1:]) or "No docs available."
        embed = discord.Embed(
            title=command.qualified_name,
            description=command.short_doc or "No description found.",
            color=discord.Color.darker_gray(),
        )
        embed.add_field(
            name="usage",
            value=f"{ctx.clean_prefix}"
            f"{command.qualified_name}"
            f"{'|' + '|'.join(alias for alias in command.aliases) if command.aliases else ' '} "
            f"{command.usage or command.signature}",
            inline=False,
        )
        embed.add_field(name="docs", value=docs, inline=False)
        if isinstance(command, commands.Group):
            command_list = [cmd.name for cmd in command.commands if not cmd.hidden]
            command_list.sort()
            subcommands = "\n".join(command_list)
            embed.add_field(name="subcommands", value=subcommands or "No subcommands", inline=False)
        embed.add_field(
            name="misc",
            value=f"Supports Variables: `{command.virtual_vars}`\n"
            f"Supports Root Placeholder: `{command.root_placeholder}`\n"
            f"Global Use: `{command.global_use}`",
            inline=False,
        )
        return await send(ctx, embed)

    @root.command(
        name="--inspect",
        parent="dev",
        global_use=True,
        aliases=["-i"],
        hidden=True,
        require_var_positional=True,
    )
    async def root_types(self, ctx: commands.Context[types.Bot], *, command_string: str):
        """Inspect a command.
        This is not exclusive to the `dev` extension.
        Command signature, as well as some useful attributes will be returned.
        """
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        params: list[str] = []
        for name, sign in command.clean_params.items():
            if sign.kind == inspect.Parameter.KEYWORD_ONLY:
                params.append(
                    f"`*, {name}"
                    f"{'*' if sign.required else ''}`: "
                    f"_{getattr(sign.converter, '__name__', sign.converter)}_" + " = " + str(sign.default)
                    if not isinstance(sign.default, type)
                    else sign.default.__name__
                    if sign.default is inspect.Parameter.empty
                    else ""
                )
            elif sign.kind == inspect.Parameter.VAR_POSITIONAL:
                params.append(
                    f"`*{name}"
                    f"{'*' if sign.required else ''}`: "
                    f"_{getattr(sign.converter, '__name__', sign.converter)}_" + " = " + str(sign.default)
                    if not isinstance(sign.default, type)
                    else sign.default.__name__
                    if sign.default is inspect.Parameter.empty
                    else ""
                )
            else:
                params.append(
                    f"`{name}"
                    f"{'*' if sign.required else ''}`: "
                    f"_{getattr(sign.converter, '__name__', sign.converter)}_" + " = " + str(sign.default)
                    if not isinstance(sign.default, type)
                    else sign.default.__name__
                    if sign.default is inspect.Parameter.empty
                    else ""
                )
        embed = discord.Embed(
            title=command_string,
            description=command.description or "None",
            color=discord.Color.darker_gray(),
        )
        embed.add_field(name="Aliases", value=f"`{'`, `'.join(command.aliases) or 'None'}`")
        embed.add_field(name="Cog", value=f"`{command.cog_name}`")
        embed.add_field(name="Command ID", value=f"`{hex(id(command))}`")
        embed.add_field(name="Enabled", value=f"`{command.enabled}`")
        embed.add_field(name="Has Error Handler", value=f"`{command.has_error_handler()}`")
        embed.add_field(name="Module", value=f"`{command.module}`")
        embed.add_field(name="Type", value=f"`{type(command).__name__}`")
        embed.add_field(name="Signature", value="\n".join(params) or "`None`")
        await send(ctx, embed)

    @root.command(
        name="--source",
        parent="dev",
        aliases=["-src"],
        hidden=True,
        require_var_positional=True,
    )
    async def root_source(self, ctx: commands.Context[types.Bot], *, command_string: str):
        """View the source code of a command.
        This is not exclusive to the `dev` extension.
        The token of the bot will be hidden as `[token]` if it is found within the source code.
        """
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")

        over = self.get_last_implementation(command.qualified_name)
        if over is None or not over.source:
            try:
                source, _ = inspect.getsource(command.callback)
            except OSError:
                return await send(
                    ctx,
                    f"Couldn't get source lines for the command `{command_string}`.",
                )
            else:
                self._refresh_base_registrations()
        else:
            source = over.source
        return await send(ctx, codeblock_wrapper(source, "py"))

    @root.command(
        name="--file",
        parent="dev",
        aliases=["-f"],
        hidden=True,
        require_var_positional=True,
    )
    async def root_file(self, ctx: commands.Context[types.Bot], *, command_string: str):
        """View the file of a command.
        This is not exclusive to the `dev` extension.
        The token of the bot will be hidden as `[token]` if it is found within the file.
        """
        command = self.bot.get_command(command_string)
        if not command:
            return await send(ctx, f"Command `{command_string}` not found.")
        base = self.get_base_command(command.qualified_name)
        if base is None:
            return await send(ctx, "Could not find base command.")
        try:
            directory = inspect.getsourcefile(base.callback)
        except OSError:
            return await send(
                ctx,
                f"Could not get the source file for the command `{command_string}`.",
            )
        if directory is None:
            return await send(ctx, "Could not find source.")
        with open(directory, "r", encoding="utf-8") as source:
            await send(ctx, discord.File(fp=source.read(), filename=command.module))
