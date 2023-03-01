# -*- coding: utf-8 -*-

"""
dev.misc.search
~~~~~~~~~~~~~~~

Global search command.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

import discord

from dev import root
from dev.components import AuthoredView, SearchCategory
from dev.utils.functs import send

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types


class RootSearch(root.Container):
    """Search for different attributes that fuzzy match the given query"""

    @root.command(name="search", parent="dev", require_var_positional=True, global_use=True)
    async def root_search(self, ctx: commands.Context[types.Bot], *, query: str):
        """Search for different items given a query.
        Items include cogs, command names, channels, emojis, members, and roles.
        """
        if ctx.guild is not None:
            channels = _match(
                query,
                [(channel.name, channel.mention) for channel in ctx.guild.channels],
            )
            members = _match(query, [(member.name, member.mention) for member in ctx.guild.members])
            emojis = _match(query, [(emoji.name, f"{emoji}") for emoji in ctx.guild.emojis])
            roles = _match(query, [(role.name, role.mention) for role in ctx.guild.roles])
        else:
            channels = members = emojis = roles = []
        cmds = _match(
            query,
            [(cmd.qualified_name, f"`{cmd.qualified_name}`") for cmd in self.bot.walk_commands()],
        )
        cogs = _match(query, [(cog, f"`{cog}`") for cog in self.bot.cogs])
        if not any(_ for _ in [channels, members, cmds, emojis, cogs, roles]):
            return await send(ctx, "Couldn't find anything.")
        embed = discord.Embed(title=f"Query {query} returned...", color=discord.Color.blurple())
        embed.set_footer(text="Category: All")
        select = SearchCategory(
            embed,
            cogs=cogs,
            cmds=cmds,
            channels=channels,
            emojis=emojis,
            members=members,
            roles=roles,
        )
        embed.description = select.mapping.get("all")
        await send(ctx, embed, AuthoredView(ctx.author, select))


def _match(query: str, array: list[tuple[str, str]]) -> list[str]:
    results: list[str] = []
    for match in difflib.get_close_matches(query, [item[0] for item in array], 10, 0.5):
        results.append([item[1] for item in array][[item[0] for item in array].index(str(match))])
    return results
