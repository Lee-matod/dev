# -*- coding: utf-8 -*-

"""
dev.types
~~~~~~~~~

Type shortcuts used for type hinting and type checking as well as enums.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Sequence, TypeVar, Union
from typing_extensions import Concatenate, ParamSpec

import discord
from discord.ext import commands


__all__ = (
    "Bot",
    "Callback",
    "Channel",
    "CogT",
    "Command",
    "CommandT",
    "ContextT",
    "GroupT",
    "InteractionResponseType",
    "ManagementOperation",
    "MessageContent",
    "Over",
    "OverType",
    "Setting",
    "User"
)

T = TypeVar("T")
P = ParamSpec("P")

CogT = TypeVar("CogT", bound="Optional[Cog]")
CommandT = TypeVar("CommandT", bound="Command")
ContextT = TypeVar("ContextT", bound="Context")
GroupT = TypeVar("GroupT", bound="Group")

Callback = Callable[[Concatenate[CogT, ContextT, P]], Coroutine[Any, Any, T][T]]

if TYPE_CHECKING:
    Bot = Union[commands.Bot, commands.AutoShardedBot]
    Channel = Union[
        discord.TextChannel,
        discord.VoiceChannel,
        discord.CategoryChannel,
        discord.StageChannel,
        discord.ForumChannel
    ]
    Command = Union[commands.Command, commands.Group]
    MessageContent = Union[
        str,
        discord.Embed,
        Sequence[discord.Embed],
        discord.File,
        Sequence[discord.File],
        Union[discord.GuildSticker, discord.StickerItem],
        discord.ui.View
    ]
    Setting = Union[bool, set, str]
    User = Union[discord.ClientUser, discord.Member, discord.User]

else:
    Bot = (commands.Bot, commands.AutoShardedBot)
    Channel = (
        discord.TextChannel,
        discord.VoiceChannel,
        discord.CategoryChannel,
        discord.StageChannel,
        discord.ForumChannel
    )
    Command = (commands.Command, commands.Group)
    MessageContent = (
        str,
        discord.Embed,
        Sequence[discord.Embed],
        discord.File,
        Sequence[discord.File],
        Union[discord.GuildSticker, discord.StickerItem],
        discord.ui.View
    )
    Setting = (bool, set, str)
    User = (discord.ClientUser, discord.Member, discord.User)


class Over(Enum):
    OVERRIDE = 1
    OVERWRITE = 2
    ADD = 3
    DELETE = 4


class OverType(Enum):
    COMMAND = 1
    SETTING = 2


class InteractionResponseType(Enum):
    SEND = 1
    EDIT = 2
    MODAL = 3


class ManagementOperation(Enum):
    UPLOAD = 1
    EDIT = 2
    RENAME = 3
    DELETE = 4

    # Aliases
    CREATE = 1
