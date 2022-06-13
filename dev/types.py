# -*- coding: utf-8 -*-

"""
dev.types
~~~~~~~~~

Type shortcuts used for type hinting.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


from typing import (
    Any,
    Callable,
    Coroutine,
    TypeVar,
    Union
)

from typing_extensions import Concatenate, ParamSpec
from discord.ext import commands

T = TypeVar("T")
P = ParamSpec("P")

CogT = TypeVar("CogT", bound="Optional[Cog]")
CommandT = TypeVar("CommandT", bound="Command")
ContextT = TypeVar("ContextT", bound="Context")
GroupT = TypeVar("GroupT", bound="Group")

BotT = Union[commands.Bot, commands.AutoShardedBot]
GroupMixinT = Union[commands.Group, commands.Command]

Callback = Callable[[Concatenate[CogT, ContextT, P]], Coroutine[Any, Any, T][T]]
