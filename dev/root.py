# -*- coding: utf-8 -*-

"""
dev.utils.root
~~~~~~~~~~~~~~

Command decorators and cogs used to register commands.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Dict, Iterable, List, Optional, OrderedDict, TypeVar, Union

import discord
from discord.ext import commands
from discord.utils import MISSING

from dev.scope import Scope, Settings
from dev.utils.baseclass import Command, DiscordCommand, DiscordGroup, Group

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec, Self

    from dev import types
    from dev.types import CogT, Coro

    P = ParamSpec("P")

__all__ = ("Plugin", "command", "group")

KT = TypeVar("KT")
VT = TypeVar("VT")

_log = logging.getLogger(__name__)


class _DictDeque(OrderedDict[KT, VT]):
    def __init__(self, *args: Any, maxlen: Optional[int] = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._maxlen: Optional[int] = maxlen

    def __setitem__(self, key: KT, value: VT) -> None:
        super().__setitem__(key, value)
        if self._maxlen is not None and len(self) > self._maxlen:
            self.popitem(False)


def command(
    name: str = MISSING, **kwargs: Any
) -> Callable[[Callable[Concatenate[CogT, commands.Context[Any], P], Coro[Any],]], Command[CogT],]:
    """A decorator that converts the given function to a temporary :class:`Command` class.

    Parameters
    ----------
    name: :class:`str`
        The name of the command that should be used. If no name is provided, the function's
        name will be used.
    kwargs:
        Keyword arguments that will be forwarded to the :class:`Command` class.
    """

    def decorator(func: Callable[Concatenate[CogT, commands.Context[Any], P], Coro[Any],]) -> Command[CogT]:
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return Command(func, name=name, **kwargs)

    return decorator


def group(
    name: str = MISSING, **kwargs: Any
) -> Callable[[Callable[Concatenate[CogT, commands.Context[Any], P], Any]], Group[CogT],]:
    """A decorator that converts the given function to a temporary :class:`Group` class.

    Parameters
    ----------
    name: :class:`str`
        The name of the command that should be used. If no name is provided, the function's
        name will be used.
    kwargs:
        Keyword arguments that will be forwarded to the :class:`Group` class.
    """

    def decorator(func: Callable[Concatenate[CogT, commands.Context[Any], P], Any]) -> Group[CogT]:
        if isinstance(func, Group):
            raise TypeError("Callback is already a group.")
        return Group(func, name=name, **kwargs)

    return decorator


class Plugin(commands.Cog):
    """A cog subclass that implements a global check and some default functionality
    that the dev extension should have.

    All other dev cogs will derive from this base class.

    Command registrations are stored in here for quick access between different dev cogs.

    Subclass of :class:`discord.ext.commands.Cog`

    Parameters
    ----------
    bot: :class:`discord.ext.commands.Bot`
        The bot that this cog should belong to.

    Attributes
    ----------
    bot: :class:`commands.Bot`
        The bot instance that was passed to the constructor of this class.
    commands: Dict[:class:`str`, types.Command]
        A dictionary that stores all dev commands.
    """

    __plugin_commands__: List[commands.Command[Self, ..., Any]] = []

    scope: ClassVar[Scope] = Scope()
    _messages: _DictDeque[int, discord.Message] = _DictDeque(maxlen=50)

    def __init__(self, bot: types.Bot) -> None:
        self.bot: types.Bot = bot
        self.commands: Dict[str, types.Command] = {}
        root_commands: List[Union[Command[Plugin], Group[Plugin]]] = list(self.__get_commands())
        root_commands.sort(key=lambda c: c.level)
        for command in root_commands:
            command = command.to_instance(
                self.bot, {**self.commands, **{c.qualified_name: c for c in Plugin.__plugin_commands__}}
            )
            command.cog = self
            self.commands[command.qualified_name] = command

        Plugin.__plugin_commands__.extend(self.commands.values())
        self.__cog_commands__ = list({*self.commands.values(), *self.__cog_commands__})

    async def _eject(self, bot: types.Bot, guild_ids: Optional[Iterable[int]]) -> None:  # type: ignore
        await super()._eject(bot, guild_ids)
        for command in self.commands.values():
            Plugin.__plugin_commands__.remove(command)
            if command.parent is not None:
                command.parent.remove_command(command.name)
                add_command = command.parent.add_command
            else:
                add_command = bot.add_command
            second_command = discord.utils.get(
                reversed(Plugin.__plugin_commands__), qualified_name=command.qualified_name
            )
            if second_command is not None:
                add_command(second_command)

    def __get_commands(self) -> List[Union[Command[Plugin], Group[Plugin]]]:
        cmds: Dict[str, Union[Command[Plugin], Group[Plugin]]] = {}
        for kls in reversed(type(self).__mro__):
            if issubclass(kls, Plugin):
                _log.debug("Loading Plugin class %r", kls)
            for val in kls.__dict__.values():
                if isinstance(val, (Command, Group)):
                    val.cog = self
                    cmds[val.qualified_name] = val
        return list(cmds.values())

    async def cog_check(self, ctx: commands.Context[types.Bot]) -> bool:  # type: ignore
        """A check that is called every time a dev command is invoked.
        This check is called internally, and shouldn't be called elsewhere.

        It first checks if the command is allowed for global use.
        If that check fails, it checks if the author of the invoked command is
        specified in :attr:`Settings.OWNERS`.
        If the owner list is empty, it'll lastly check if the author owns the bot.

        If all checks fail, :class:`discord.ext.commands.NotOwner` is raised.
        This is done so that you can customize the message that is sent by the bot
        through an error handler.

        Parameters
        ----------
        ctx: :class:`discord.ext.commands.Context`
            The invocation context in which the command was invoked.

        Returns
        -------
        bool
            Whether the user is allowed to use this command.

        Raises
        ------
        discord.ext.commands.NotOwner
            All checks failed. The user who invoked the command is not the owner of the bot.
        """
        assert ctx.command is not None

        if not isinstance(ctx.command.cog, type(self)):
            return True
        if isinstance(ctx.command, (DiscordCommand, DiscordGroup)):
            if ctx.command.global_use and Settings.GLOBAL_USE:
                return True
        if ctx.author.id in Settings.OWNERS:
            return True
        if await self.bot.is_owner(ctx.author) and not Settings.OWNERS:
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")
