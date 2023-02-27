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
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Iterable, Literal, overload

import discord
from discord.ext import commands, tasks
from discord.utils import MISSING

from dev.handlers import GlobalLocals
from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import Over
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from dev import types
    from dev.types import CogT, Coro
    from dev.utils.baseclass import Command, DiscordCommand, DiscordGroup, Group

    P = ParamSpec("P")

__all__ = ("Container", "command", "group")

_log = logging.getLogger(__name__)


def command(
    name: str = MISSING, **kwargs: Any
) -> Callable[[Callable[Concatenate[CogT, commands.Context[types.Bot], P], Coro[Any],]], Command[CogT],]:
    """A decorator that converts the given function to a temporary :class:`Command` class.

    Parameters
    ----------
    name: :class:`str`
        The name of the command that should be used. If no name is provided, the function's
        name will be used.
    kwargs:
        Keyword arguments that will be forwarded to the :class:`Command` class.
    """

    def decorator(
        func: Callable[
            Concatenate[CogT, commands.Context[types.Bot], P],
            Coro[Any],
        ]
    ) -> Command[CogT]:
        if isinstance(func, Command):
            raise TypeError("Callback is already a command.")
        return Command(func, name=name, **kwargs)

    return decorator


def group(
    name: str = MISSING, **kwargs: Any
) -> Callable[[Callable[Concatenate[CogT, commands.Context[types.Bot], P], Any]], Group[CogT],]:
    """A decorator that converts the given function to a temporary :class:`Group` class.

    Parameters
    ----------
    name: :class:`str`
        The name of the command that should be used. If no name is provided, the function's
        name will be used.
    kwargs:
        Keyword arguments that will be forwarded to the :class:`Group` class.
    """

    def decorator(func: Callable[Concatenate[CogT, commands.Context[types.Bot], P], Any]) -> Group[CogT]:
        if isinstance(func, Group):
            raise TypeError("Callback is already a group.")
        return Group(func, name=name, **kwargs)

    return decorator


class Container(commands.Cog):
    """A cog subclass that implements a global check and some default functionality
    that the dev extension should have.

    All other dev cogs will derive from this base class.

    Command registrations are stored in here for quick access between different dev cogs.

    Subclass of :class:`discord.ext.commands.Cog`

    Parameters
    ----------
    bot: :class:`discord.ext.commands.Bot`
        The bot instance that gets passed to :meth:`discord.ext.commands.Bot.add_cog`.

    Attributes
    ----------
    bot: :class:`commands.Bot`
        The bot instance that was passed to the constructor of this class.
    commands: Dict[:class:`str`, types.Command]
        A dictionary that stores all dev commands.
    registrations: Dict[int, Union[CommandRegistration, SettingRegistration]]
        A dictionary that stores all modifications made in over commands.
    """

    scope: ClassVar[GlobalLocals] = GlobalLocals()
    cached_messages: ClassVar[dict[int, discord.Message]] = {}
    _subclasses: set[type[Container]] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        #  Only allow direct subclasses of Container to be added, otherwise cog conflict may occur.
        if cls.__base__ == Container:
            Container._subclasses.add(cls)
        super().__init_subclass__()

    def __init__(self, bot: types.Bot) -> None:
        self.bot: types.Bot = bot
        if frontend_cog := bot.get_cog("Dev"):
            children: set[types.Command] = set()
            for cmd in sorted(_get_commands(type(self).__mro__), key=lambda c: c.level):
                if cmd.qualified_name in frontend_cog.commands:  # type: ignore
                    original = frontend_cog.commands[cmd.qualified_name]  # type: ignore
                    mapping: dict[Any, Any] = {
                        DiscordCommand: Command,
                        DiscordGroup: Group,
                        Group: "group",
                        Command: "command",
                    }
                    as_method: type[Command[Container]] | type[Group[Container]] | None = mapping.get(
                        type(original)  # type: ignore
                    )
                    if as_method != type(cmd):
                        raise RuntimeError(
                            f"Overrided command {cmd!r} in {self} has been set as a "
                            f"{mapping.get(type(cmd))} when its original is a "
                            f"{mapping.get(as_method)}"
                        )
                    if isinstance(cmd, Command) and cmd.parent:
                        parent = frontend_cog.commands[cmd.parent]  # type: ignore
                        parent.remove_command(cmd.name)  # type: ignore
                    elif isinstance(cmd, Group):
                        subcommands = frontend_cog.commands[cmd.qualified_name]  # type: ignore
                        for child in subcommands.commands:  # type: ignore
                            children.add(child)  # type: ignore
                        if cmd.parent:
                            parent = frontend_cog.commands.get(cmd.parent)  # type: ignore
                            parent.remove_command(cmd.name)  # type: ignore
                        else:
                            bot.remove_command(cmd.name)
                actual = cmd.to_instance(frontend_cog.commands)  # type: ignore
                if isinstance(actual, DiscordGroup):
                    for child in children:
                        actual.add_command(child)
                if actual.qualified_name == actual.name:
                    #  Top level command
                    bot.add_command(actual)
                if type(self).__base__ == Container:
                    actual.cog = frontend_cog  # type: ignore
                else:
                    self.__dict__.update(frontend_cog.__dict__)
                    actual.cog = self
                frontend_cog.commands[actual.qualified_name] = actual  # type: ignore
            return
        if type(self).__base__ == Container:
            return
        self.commands: dict[str, types.Command] = {}
        self.registrations: dict[int, CommandRegistration | SettingRegistration] = {}

        root_commands: list[Command[Container] | Group[Container]] = list(_get_commands(tuple(Container._subclasses)))
        root_commands.sort(key=lambda c: c.level)
        for command in root_commands:
            command.cog = self
            command = command.to_instance(self.commands)
            self.commands[command.qualified_name] = command
            self.commands[command.qualified_name].cog = self
        for r in self.commands.values():
            if r.qualified_name == r.name:
                # Top level command
                bot.add_command(r)

        self._base_registrations: tuple[BaseCommandRegistration, ...] = ()
        self._refresh_base_registrations()

        self._clear_cached_messages.start()

    def _refresh_base_registrations(self) -> list[BaseCommandRegistration]:
        base_list: list[BaseCommandRegistration] = []
        for cmd in self.bot.walk_commands():
            base = BaseCommandRegistration(cmd)
            if hasattr(base, "line_no"):
                # Source could be found, probably an actual "hard coded" command
                base_list.append(base)
        self._base_registrations = tuple(base_list)
        return base_list

    def get_base_command(self, command_name: str, /) -> BaseCommandRegistration | None:
        return discord.utils.find(lambda c: c.qualified_name == command_name, self._base_registrations)

    def get_all_implementations(self, qualified_name: str) -> Iterable[CommandRegistration]:
        base = self.get_base_command(qualified_name)
        if base is not None:
            yield base.to_command()
        for cmd in self.registrations.values():
            if isinstance(cmd, CommandRegistration) and cmd.qualified_name == qualified_name:
                yield cmd

    def get_last_implementation(self, qualified_name: str, /) -> CommandRegistration | None:
        cmd = discord.utils.find(
            lambda c: isinstance(c, CommandRegistration) and c.qualified_name == qualified_name,
            reversed(self.registrations.values()),
        )
        if cmd is not None:
            return cmd  # type: ignore
        base = self.get_base_command(qualified_name)
        if base is not None:
            return base.to_command()
        return None

    def get_first_implementation(self, qualified_name: str, /) -> CommandRegistration | None:
        cmd = discord.utils.find(
            lambda c: isinstance(c, CommandRegistration) and c.qualified_name == qualified_name,
            self.registrations.values(),
        )
        if cmd is not None:
            return cmd  # type: ignore
        base = self.get_base_command(qualified_name)
        if base is not None:
            return base.to_command()
        return None

    @overload
    def registers_from_type(self, rgs_type: Literal[Over.OVERRIDE]) -> list[CommandRegistration]:
        ...

    @overload
    def registers_from_type(self, rgs_type: Literal[Over.OVERWRITE]) -> list[CommandRegistration | SettingRegistration]:
        ...

    def registers_from_type(self, rgs_type: Any) -> Any:
        return [rgs for rgs in self.registrations.values() if rgs.register_type is rgs_type]

    def update_register(
        self,
        register: CommandRegistration | SettingRegistration,
        mode: Literal[Over.ADD] | Literal[Over.DELETE],
        /,
    ) -> None:
        if mode is Over.DELETE and register not in self.registrations.values():
            raise IndexError("Registration cannot be deleted because it does not exist")
        if mode is Over.DELETE:
            for (
                k,
                v,
            ) in self.registrations.copy().items():
                if v == register:
                    del self.registrations[k]
        else:
            self.registrations[len(self.registrations)] = register

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

        if not isinstance(ctx.command.cog, type(self.bot.get_cog("Dev"))):
            return True
        if isinstance(ctx.command, (DiscordCommand, DiscordGroup)):
            if ctx.command.global_use and Settings.allow_global_uses:
                return True
        if ctx.author.id in Settings.owners:
            return True
        if await self.bot.is_owner(ctx.author) and not Settings.owners:
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")

    @tasks.loop(minutes=10)
    async def _clear_cached_messages(self):
        def function(msg_id: int) -> bool:
            created_at = discord.utils.snowflake_time(msg_id).timestamp()
            time_since_created = int(discord.utils.utcnow().timestamp() - created_at)
            return time_since_created >= 120

        message_ids: Iterable[int] = filter(function, Container.cached_messages.copy())
        for _id in message_ids:
            del Container.cached_messages[_id]


def _get_commands(cls: tuple[type, ...]) -> set[Command[Container] | Group[Container]]:
    cmds: set[Command[Container] | Group[Container]] = set()
    for kls in cls:
        if issubclass(kls, Container):
            _log.debug("Loading Container class %r", kls)
        for val in kls.__dict__.values():
            if isinstance(val, (Command, Group)):
                cmd: Command[Container] | Group[Container] = val
                cmds.add(cmd)
    return cmds
