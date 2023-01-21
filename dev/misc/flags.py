# -*- coding: utf-8 -*-

"""
dev.misc.flags
~~~~~~~~~~~~~~

Flag-like commands for command analysis.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import send

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
