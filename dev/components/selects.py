# -*- coding: utf-8 -*-

"""
dev.components.selects
~~~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.Select` related classes.

:copyright: Copyright 2023 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, ClassVar

import discord

from dev.components.views import AuthoredView

if TYPE_CHECKING:
    from dev import types

__all__ = (
    "PermissionsSelector",
    "SearchCategory"
)


class PermissionsSelector(discord.ui.Select[AuthoredView]):
    OPTIONS: ClassVar[tuple[discord.SelectOption, ...]] = (
        discord.SelectOption(
            label="General",
            value="general",
            description="All 'General' permissions from the official Discord UI.",
            default=True
        ),
        discord.SelectOption(
            label="All Channel",
            value="all_channel",
            description="All channel-specific permissions."
        ),
        discord.SelectOption(
            label="Membership",
            value="membership",
            description="All 'Membership' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Text",
            value="text",
            description="All 'Text' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Voice",
            value="voice",
            description="All 'Voice' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Stage",
            value="stage",
            description="All 'Stage Channel' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Stage Moderator",
            value="stage_moderator",
            description="All permissions for stage moderators."
        ),
        discord.SelectOption(
            label="Elevated",
            value="elevated",
            description="All permissions that require 2FA (2 Factor Authentication)."
        ),
        discord.SelectOption(
            label="Advanced",
            value="advanced",
            description="All 'Advanced' permissions from the official Discord UI."
        )
    )

    def __init__(self, *, target: discord.Member, channel: types.Channel | None = None) -> None:
        super().__init__(options=list(self.OPTIONS))
        self.member_target: discord.Member = target
        self.channel_target: types.Channel | None = channel

    async def callback(self, interaction: discord.Interaction) -> None:
        for option in self.options:
            if option.value != self.values[0]:
                option.default = False
            else:
                option.default = True
        permissions = ["```ansi", *self.sort_perms(self.values[0]), "```"]
        await interaction.response.edit_message(
            embed=discord.Embed(description="\n".join(permissions), color=discord.Color.blurple()),
            view=self.view
        )

    def sort_perms(self, permission: str) -> list[str]:
        perms = getattr(discord.Permissions, permission)()
        perms_list: list[str] = []
        for perm, value in perms:
            if not value:
                continue
            if self.channel_target is not None:
                toggled = dict(self.channel_target.permissions_for(self.member_target)).get(perm)  # type: ignore
                perms_list.append(
                    f"\x1b[1;37m{perm.replace('_', ' ').title():26}\x1b[0;{'32' if toggled else '31'}m{toggled}"
                )
            else:
                toggled = dict(self.member_target.guild_permissions).get(perm)
                perms_list.append(
                    f"\x1b[1;37m{perm.replace('_', ' ').title():26}\x1b[0;{'32' if toggled else '31'}m{toggled}"
                )
        return perms_list


class SearchCategory(discord.ui.Select[AuthoredView]):
    OPTIONS: ClassVar[tuple[discord.SelectOption, ...]] = (
        discord.SelectOption(label="All", value="all", default=True),
        discord.SelectOption(label="Cogs", value="cogs"),
        discord.SelectOption(label="Commands", value="commands"),
        discord.SelectOption(label="Emojis", value="emojis"),
        discord.SelectOption(label="Text Channels", value="text_channels"),
        discord.SelectOption(label="Members", value="members"),
        discord.SelectOption(label="Roles", value="roles")
    )

    def __init__(
            self,
            embed:
            discord.Embed,
            /,
            *,
            cogs: list[str],
            cmds: list[str],
            channels: list[str],
            emojis: list[str],
            members: list[str],
            roles: list[str]
    ):
        options: list[discord.SelectOption] = [
            option for option, value in zip(self.OPTIONS, (True, cogs, cmds, emojis, channels, members, roles))
            if value
        ]
        super().__init__(options=options)
        self.embed: discord.Embed = embed
        self.mapping: dict[str, str] = {
            "all": "\n".join(
                list(itertools.chain(cogs[:3], cmds[:3], channels[:3], emojis[:3], members[:3], roles[:3]))[:8]
            ),
            "cogs": "\n".join(cogs),
            "commands": "\n".join(cmds),
            "text_channels": "\n".join(channels),
            "emojis": "\n".join(emojis),
            "members": "\n".join(members),
            "roles": "\n".join(roles)
        }

    async def callback(self, interaction: discord.Interaction) -> None:
        for option in self.options:
            if option.value != self.values[0]:
                option.default = False
            else:
                option.default = True
        self.embed.description = self.mapping.get(self.values[0])
        self.embed.set_footer(text=f'Category: {self.values[0].capitalize().replace("_", " ")}')
        await interaction.response.edit_message(embed=self.embed, view=self.view)