# -*- coding: utf-8 -*-

"""
dev.misc.search
~~~~~~~~~~~~~~~

Global search command.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

import discord

from dev.components.views import SearchResultCategory

from dev.utils.baseclass import Root, root
from dev.utils.functs import send

if TYPE_CHECKING:
    from discord.ext import commands

    from dev import types


class RootSearch(Root):
    @root.command(name="search", parent="dev", require_var_positional=True, global_use=True)
    async def root_search(self, ctx: commands.Context[types.Bot], *, query: str):
        """Search for different items given a query.
        Items include cogs, command names, channels, emojis, members, and roles.
        """
        if ctx.guild is not None:
            channels = match(query, [(channel.name, channel.mention) for channel in ctx.guild.channels])
            members = match(query, [(member.name, member.mention) for member in ctx.guild.members])
            emojis = match(query, [(emoji.name, f"{emoji}") for emoji in ctx.guild.emojis])
            roles = match(query, [(role.name, role.mention) for role in ctx.guild.roles])
        else:
            channels = members = emojis = roles = []
        cmds = match(
            query,
            [(cmd.qualified_name, f"`{cmd.qualified_name}`") for cmd in self.bot.walk_commands()]
        )
        cogs = match(query, [(cog, f"`{cog}`") for cog in self.bot.cogs])
        if not any(_ for _ in [channels, members, cmds, emojis, cogs, roles]):
            return await send(ctx, "Couldn't find anything.")
        embed = discord.Embed(
            title=f"Query {query} returned...",
            description=SearchResultCategory.join_multi_iter(
                [cogs, cmds, channels, emojis, members, roles],
                max_amount=7
            ),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Category: All")
        view = SearchResultCategory(
            ctx,
            embed,
            cogs=cogs,
            cmds=cmds,
            channels=channels,
            emojis=emojis,
            members=members,
            roles=roles
        )
        message = await send(ctx, embed, view)
        view.message = message


def match(query: str, array: list[tuple[str, str]]) -> list[str]:
    results: list[str] = []
    for m in difflib.get_close_matches(query, [item[0] for item in array], 7, 0.5):
        results.append([item[1] for item in array][[item[0] for item in array].index(str(m))])
    return results
