# -*- coding: utf-8 -*-

"""
dev.components.selects
~~~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.Select` related classes.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, ClassVar, Dict, List, Optional

import discord

from dev.components.views import AuthoredMixin

if TYPE_CHECKING:
    from dev import types

__all__ = ("PermissionsSelector", "SearchCategory")

_PERMISSIONS = ("general", "membership", "text", "voice", "stage", "advanced")
_CATEGORIES = ("all", "cogs", "commands", "emojis", "text_channels", "members", "roles")


class PermissionsSelector(discord.ui.Select[AuthoredMixin]):
    OPTIONS: ClassVar[List[discord.SelectOption]] = [
        discord.SelectOption(
            label=opt.title(),
            value=opt,
            description=f"All '{opt.title()}' permissions from the official Discord UI.",
            default=opt == "general",
        )
        for opt in _PERMISSIONS
    ]

    def __init__(self, *, target: discord.Member, channel: Optional[types.Channel] = None) -> None:
        super().__init__(options=list(self.OPTIONS))
        self.target: discord.Member = target
        self.channel: Optional[types.Channel] = channel

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = discord.utils.get(self.options, default=True)
        current = discord.utils.get(self.options, value=self.values[0])
        if selected is not None:
            selected.default = False
        if current is not None:
            current.default = True
        permissions = ["```ansi", *self.sort_perms(self.values[0]), "```"]
        await interaction.response.edit_message(
            embed=discord.Embed(description="\n".join(permissions), color=discord.Color.blurple()), view=self.view
        )

    def sort_perms(self, permission: str) -> List[str]:
        perms = getattr(discord.Permissions, permission)()
        perms_list: List[str] = []
        for perm, value in perms:
            if not value:
                continue
            if self.channel is not None:
                toggled = dict(self.channel.permissions_for(self.target)).get(perm)
            else:
                toggled = dict(self.target.guild_permissions).get(perm)
            perm_name = perm.replace("_", " ").title()
            perms_list.append(f"\x1b[1;37m{perm_name:26}\x1b[0;{'32' if toggled else '31'}m{toggled}")
        return perms_list


class SearchCategory(discord.ui.Select[AuthoredMixin]):
    OPTIONS: ClassVar[List[discord.SelectOption]] = [
        discord.SelectOption(label=cat.replace("_", " ").title(), value=cat, default=cat == "all") for cat in sorted(_CATEGORIES)
    ]

    def __init__(self, embed: discord.Embed, /, **categories: List[str]):
        categories = dict(sorted([(k, v) for k, v in categories.items() if v], key=lambda x: x[0]))
        options: List[discord.SelectOption] = [
            option for option in self.OPTIONS if option.value in categories or option.value == "all"
        ]
        super().__init__(options=options)
        self.embed: discord.Embed = embed
        self._mapping: Dict[str, str] = {
            "all": "\n".join(list(itertools.chain(*[v[:3] for v in categories.values()]))[:10]),
            **{k: "\n".join(v) for k, v in categories.items() if v},
        }

    async def callback(self, interaction: discord.Interaction) -> None:
        selected = discord.utils.get(self.options, default=True)
        current = discord.utils.get(self.options, value=self.values[0])
        if selected is not None:
            selected.default = False
        if current is not None:
            current.default = True
        self.embed.description = self._mapping.get(self.values[0])
        self.embed.set_footer(text=f'Category: {self.values[0].title().replace("_", " ")}')
        await interaction.response.edit_message(embed=self.embed, view=self.view)
