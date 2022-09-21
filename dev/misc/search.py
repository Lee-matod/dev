# -*- coding: utf-8 -*-

"""
dev.misc.search
~~~~~~~~~~~~~~~

Global search command.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import difflib
from typing import List, Optional, Tuple

import discord
from discord.ext import commands

from dev.utils.baseclass import Root, root
from dev.utils.functs import all_commands, send


class Dropdown(discord.ui.View):
    options = [
        discord.SelectOption(label="All", value="all", default=True),
        discord.SelectOption(label="Cogs", value="cogs"),
        discord.SelectOption(label="Commands", value="commands"),
        discord.SelectOption(label="Emojis", value="emojis"),
        discord.SelectOption(label="Text Channels", value="text_channels"),
        discord.SelectOption(label="Members", value="members"),
        discord.SelectOption(label="Roles", value="roles")
    ]

    def __init__(
            self,
            ctx: commands.Context,
            embed: discord.Embed,
            *,
            cogs: List[str],
            cmds: List[str],
            channels: List[str],
            emojis: List[str],
            members: List[str],
            roles: List[str]
    ):
        self.mapping = {
            "all": join_multi_iter([cogs, cmds, channels, emojis, members, roles], max_amount=7),
            "cogs": "\n".join(cogs),
            "commands": "\n".join(cmds),
            "text_channels": "\n".join(channels),
            "emojis": "\n".join(emojis),
            "members": "\n".join(members),
            "roles": "\n".join(roles)
        }
        for option in self.options.copy():
            if not self.mapping[option.value]:
                self.options.remove(option)
        super().__init__()
        self.ctx = ctx
        self.embed = embed
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.ctx.author == interaction.user

    @discord.ui.select(options=options)
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        for option in select.options:
            if option.value != select.values[0]:
                option.default = False
            else:
                option.default = True
        self.embed.description = self.mapping.get(select.values[0])
        self.embed.set_footer(text=f'Category: {select.values[0].capitalize().replace("_", " ")}')
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)


class RootSearch(Root):
    @root.command(name="search", parent="dev", require_var_positional=True, global_use=True)
    async def root_search(self, ctx: commands.Context, *, query: str):
        channels = match(query, [(channel.name, channel.mention) for channel in ctx.guild.channels])
        members = match(query, [(member.name, member.mention) for member in ctx.guild.members])
        cmds = match(
            query,
            [(cmd.qualified_name, f"`{cmd.qualified_name}`") for cmd in all_commands(self.bot.commands)]
        )
        emojis = match(query, [(emoji.name, f"{emoji}") for emoji in ctx.guild.emojis])
        cogs = match(query, [(cog, f"`{cog}`") for cog in self.bot.cogs])
        roles = match(query, [(role.name, role.mention) for role in ctx.guild.roles])
        if not any(_ for _ in [channels, members, cmds, emojis, cogs, roles]):
            return await send(ctx, "Couldn't find anything.")
        embed = discord.Embed(
            title=f"Query {query} returned...",
            description=join_multi_iter([cogs, cmds, channels, emojis, members, roles], max_amount=7),
            color=discord.Color.blurple()
        )
        embed.set_footer(text="Category: All")
        view = Dropdown(
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


def join_multi_iter(iterables, delimiter: str = "\n", max_amount: int = None) -> str:
    joined_iter = []
    for iterable in iterables:
        if iterable:
            joined_iter.append(f"{delimiter}".join(iterable))
    return f"{delimiter}".join(joined_iter[:max_amount]).strip(f"{delimiter}")


def match(query: str, array: List[Tuple[str, str]]) -> List[str]:
    results = []
    for m in difflib.get_close_matches(query, [item[0] for item in array], 7, 0.5):
        results.append([item[1] for item in array][[item[0] for item in array].index(str(m))])
    return results
