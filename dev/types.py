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
from typing import TYPE_CHECKING, Any, Callable, Coroutine, TypeVar, Union

import discord
from discord.ext import commands


__all__ = (
    "Bot",
    "Callback",
    "Channel",
    "CogT",
    "Command",
    "ContextT",
    "ErrorCallback",
    "InteractionResponseType",
    "ManagementOperation",
    "MessageContent",
    "Over",
    "OverType",
    "Setting",
    "User"
)

T = TypeVar("T")

CogT = TypeVar("CogT", bound=commands.Cog)
ContextT = TypeVar("ContextT", bound=commands.Context)

if TYPE_CHECKING:
    from typing import Sequence
    from typing_extensions import Concatenate, ParamSpec

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

    P = ParamSpec("P")

    Callback = Callable[[Concatenate[CogT, ContextT, P]], Coroutine[Any, Any, T]]
    ErrorCallback = Callable[[CogT, ContextT, commands.CommandError], Coroutine[Any, Any, T]]

else:
    from collections.abc import Sequence

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
        discord.GuildSticker,
        discord.StickerItem,
        discord.ui.View
    )
    Setting = (bool, set, str)
    User = (discord.ClientUser, discord.Member, discord.User)


# Enums

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
