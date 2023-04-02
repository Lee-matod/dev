# -*- coding: utf-8 -*-

"""
dev.types
~~~~~~~~~

Type shortcuts used for type hinting and type checking as well as enums.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Coroutine, Optional, Protocol, TypeVar, Union

import discord
from discord.ext import commands

__all__ = ("Bot", "Channel", "Command", "Invokeable", "MessageContent", "User")

if TYPE_CHECKING:
    from typing import Sequence

    from typing_extensions import Annotated

    from dev.root import Plugin

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

    class Annotated:
        #  This doesn't need to be really complicated, just want to
        #  save the typehint somewhere and metadata
        def __init__(self, typehint: Any, *meta: Any) -> None:
            self.typehint: Any = typehint
            self.metadata: tuple[Any] = meta

        def __call__(self, *args: Any, **kwds: Any) -> Any:
            return self.metadata[0](*args, **kwds)

        def __class_getitem__(cls, key: tuple[Any, ...]) -> Annotated:
            return cls(*key)


T = TypeVar("T")
Coro = Coroutine[Any, Any, T]
CogT = TypeVar("CogT", bound="Optional[Plugin]")


class Invokeable(Protocol):
    async def invoke(self, context: commands.Context[Bot], /) -> None:
        ...

    async def reinvoke(self, context: commands.Context[Bot], /, *, call_hooks: bool = False) -> None:
        ...
