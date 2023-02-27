# -*- coding: utf-8 -*-

"""
dev.types
~~~~~~~~~

Type shortcuts used for type hinting and type checking as well as enums.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Coroutine, Optional, Protocol, TypeVar, Union

import discord
from discord.ext import commands

__all__ = (
    "Bot",
    "Channel",
    "Command",
    "Invokeable",
    "ManagementOperation",
    "MessageContent",
    "Over",
    "OverType",
    "User",
)

if TYPE_CHECKING:
    from typing import Sequence

    from dev.root import Container

    Bot = Union[commands.Bot, commands.AutoShardedBot]
    Channel = Union[
        discord.TextChannel,
        discord.VoiceChannel,
        discord.CategoryChannel,
        discord.StageChannel,
        discord.ForumChannel,
        discord.Thread,
        discord.DMChannel,
        discord.GroupChannel,
    ]
    Command = Union[commands.Command[Any, ..., Any], commands.Group[Any, ..., Any]]
    MessageContent = Union[
        str,
        discord.Embed,
        Sequence[discord.Embed],
        discord.File,
        Sequence[discord.File],
        Union[discord.GuildSticker, discord.StickerItem],
        discord.ui.View,
    ]
    User = Union[discord.ClientUser, discord.Member, discord.User]

else:
    from collections.abc import Sequence

    Bot = (commands.Bot, commands.AutoShardedBot)
    Channel = (
        discord.TextChannel,
        discord.VoiceChannel,
        discord.CategoryChannel,
        discord.StageChannel,
        discord.ForumChannel,
    )
    Command = (commands.Command, commands.Group)
    MessageContent = (
        str,
        discord.Embed,
        Sequence[discord.Embed],
        discord.File,
        Sequence[discord.File],
        discord.GuildSticker,
        discord.StickerItem,
        discord.ui.View,
    )
    User = (discord.ClientUser, discord.Member, discord.User)

T = TypeVar("T")
Coro = Coroutine[Any, Any, T]
CogT = TypeVar("CogT", bound="Optional[Container]")


class Invokeable(Protocol):
    async def invoke(self, context: commands.Context[Bot], /) -> None:
        ...

    async def reinvoke(self, context: commands.Context[Bot], /, *, call_hooks: bool = False) -> None:
        ...


# Enums


class Over(Enum):
    OVERRIDE = 1
    OVERWRITE = 2
    ADD = 3
    DELETE = 4


class OverType(Enum):
    COMMAND = 1
    SETTING = 2


class ManagementOperation(Enum):
    UPLOAD = 1
    EDIT = 2
    RENAME = 3
    DELETE = 4

    # Aliases
    CREATE = 1
