# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic classes used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import logging
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Coroutine,
    Generator,
    Generic,
    Iterator,
    Literal,
    NoReturn,
    TypeVar,
    overload
)

import discord
from discord.ext import commands
from discord.ext import tasks
from discord.utils import MISSING

from dev.handlers import GlobalLocals
from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import Over

from dev.utils.startup import Settings

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from dev import types

    P = ParamSpec("P")
else:
    P = TypeVar("P")

_log = logging.getLogger(__name__)

T = TypeVar("T")
CogT_co = TypeVar("CogT_co", bound="Root", covariant=True)

__all__ = (
    "Command",
    "Group",
    "Root",
    "root"
)


class OperationNotAllowedError(BaseException):
    pass


class root(Generic[CogT_co]):  # noqa E302
    """A super class that allows the conversion of coroutine functions to temporary command classes
    that can later be used to register them as an actual :class:`discord.ext.commands.Command`.

    Even though this class was made for internal uses, it cannot be instantiated nor subclassed.
    It should be used as-is.
    """

    def __init__(self) -> NoReturn:
        raise OperationNotAllowedError("Cannot instantiate root.")

    def __new__(cls, *args: Any, **kwargs: Any) -> NoReturn:
        raise OperationNotAllowedError("Cannot instantiate root.")

    def __init_subclass__(cls, **kwargs: Any) -> NoReturn:
        raise OperationNotAllowedError("Cannot subclass root.")

    @staticmethod
    def command(name: str = MISSING, **kwargs: Any) -> Callable[
        [Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Coroutine[Any, Any, Any]]],
        Command[CogT_co]
    ]:
        """A decorator that converts the given function to a temporary :class:`Command` class.

        Parameters
        ----------
        name: :class:`str`
            The name of the command that should be used. If no name is provided, the function's name will be used.
        kwargs:
            Key-word arguments that'll be forwarded to the :class:`Command` class.
        """

        def decorator(
                func: Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Coroutine[Any, Any, Any]]
        ) -> Command[CogT_co]:
            if isinstance(func, Command):
                raise TypeError("Callback is already a command.")
            return Command(func, name=name, **kwargs)

        return decorator

    @staticmethod
    def group(name: str = MISSING, **kwargs: Any) -> Callable[
        [Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Any]],
        Group[CogT_co]
    ]:
        """A decorator that converts the given function to a temporary :class:`Group` class.

        Parameters
        ----------
        name: :class:`str`
            The name of the command that should be used. If no name is provided, the function's name will be used.
        kwargs:
            Key-word arguments that'll be forwarded to the :class:`Group` class.
        """

        def decorator(func: Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Any]) -> Group[CogT_co]:
            if isinstance(func, Group):
                raise TypeError("Callback is already a group.")
            return Group(func, name=name, **kwargs)

        return decorator


class _DiscordCommand(commands.Command[Any, ..., Any]):
    def __init__(
            self,
            func: Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Coroutine[Any, Any, Any]],
            **kwargs: Any
    ) -> None:
        self.__global_use: bool | None = kwargs.pop("global_use", None)
        self.__virtual_vars: bool = kwargs.pop("virtual_vars", False)
        self.__root_placeholder: bool = kwargs.pop("root_placeholder", False)
        super().__init__(func, **kwargs)

    @property
    def global_use(self) -> bool | None:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.__global_use

    @global_use.setter
    def global_use(self, value: bool) -> None:
        if self.__global_use is None:
            raise TypeError("Cannot toggle global use value for a command that didn't have it enabled on startup")
        if not isinstance(value, bool):
            raise TypeError(f"Expected type bool but received {type(value).__name__}")
        self.__global_use = value

    @property
    def virtual_vars(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the use of out-of-scope variables.
        """
        return self.__virtual_vars

    @property
    def root_placeholder(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the `|root|` placeholder text.
        """
        return self.__root_placeholder


class _DiscordGroup(commands.Group[Any, ..., Any]):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__global_use: bool | None = kwargs.pop("global_use", None)
        self.__virtual_vars: bool = kwargs.pop("virtual_vars", False)
        self.__root_placeholder: bool = kwargs.pop("root_placeholder", False)
        super().__init__(*args, **kwargs)

    @property
    def global_use(self) -> bool | None:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.__global_use

    @global_use.setter
    def global_use(self, value: bool) -> None:
        if self.__global_use is None:
            raise TypeError("Cannot toggle global use value for a command that didn't have it enabled on startup")
        if not isinstance(value, bool):
            raise TypeError(f"Expected type bool but received {type(value).__name__}")
        self.__global_use = value

    @property
    def virtual_vars(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the use of out-of-scope variables.
        """
        return self.__virtual_vars

    @property
    def root_placeholder(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the `|root|` placeholder text.
        """
        return self.__root_placeholder


class BaseCommand(Generic[CogT_co, P, T]):
    def __init__(
            self,
            func: Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Coroutine[Any, Any, T]],
            **kwargs: Any
    ) -> None:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Callback must be a coroutine.")
        name: str = kwargs.pop("name", None) or func.__name__
        if not isinstance(name, str):
            raise TypeError("Name of a command must be a string.")
        self.name: str = name
        self.callback: Callable[Concatenate[CogT_co, commands.Context[types.Bot], P], Coroutine[Any, Any, T]] = func
        self.parent: str | None = kwargs.pop("parent", None)
        self.kwargs: dict[str, Any] = kwargs

        self.level: int = 0
        if self.parent:
            self.level = len(self.parent.split())

        self.on_error: Callable[
                           [CogT_co, commands.Context[types.Bot], commands.CommandError],
                           Coroutine[Any, Any, Any]
                       ] | None = None
        self.cog: CogT_co | None = None

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name}>"

    async def __call__(self, context: commands.Context[types.Bot], /, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.cog is None:  # should never happen
            raise RuntimeError(f"Command {self.name!r} missing cog.")
        return await self.callback(self.cog, context, *args, **kwargs)

    @property
    def qualified_name(self) -> str:
        if self.parent is not None:
            return f"{self.parent} {self.name}"
        return self.name

    def to_instance(
            self,
            command_mapping: dict[str, types.Command],
            /
    ) -> types.Command | NoReturn:
        raise NotImplementedError

    def error(
            self,
            func: Callable[[CogT_co, commands.Context[types.Bot], commands.CommandError], Coroutine[Any, Any, Any]]
    ) -> Callable[[CogT_co, commands.Context[types.Bot], commands.CommandError], Coroutine[Any, Any, Any]]:
        """Set a local error handler"""
        self.on_error = func
        return func


class Command(BaseCommand[CogT_co, ..., Any]):
    """A class that simulates :class:`commands.Command`.

    This class is used to keep track of which functions should be commands, and it shouldn't get called manually.
    Instead, consider using :meth:`root.command` to instantiate this class.
    """

    def to_instance(
            self,
            command_mapping: dict[str, types.Command],
            /
    ) -> commands.Command[CogT_co, ..., Any] | NoReturn:
        """Converts this class to an instance of its respective simulation.

        Parameters
        ----------
        command_mapping: Dict[str, types.Command]
            A mapping of commands from which this command will get their corresponding parents from.

        Returns
        -------
        discord.ext.commands.Command
            The command class made using the given attributes of this temporary class.
        """
        if self.parent:
            command = command_mapping.get(self.parent)
            if not command:
                raise RuntimeError(f"Couldn't find {self.qualified_name} command's parent")
            if not isinstance(command, commands.Group):
                raise RuntimeError("Command's parent command is not commands.Group instance")
            deco = command.command
        else:
            deco = commands.command
        cmd: commands.Command[CogT_co, ..., Any] = deco(
            name=self.name,
            cls=_DiscordCommand,
            **self.kwargs
        )(self.callback)
        if self.on_error:
            cmd.error(self.on_error)
        return cmd


class Group(BaseCommand[CogT_co, ..., Any]):
    """A class that simulates :class:`discord.ext.commands.Group`.

    This class is used to keep track of which functions be groups, and it shouldn't get called manually.
    Instead, consider using :meth:`root.group` to instantiate this class.
    """

    def to_instance(
            self,
            command_mapping: dict[str, types.Command],
            /
    ) -> commands.Group[CogT_co, ..., Any] | NoReturn:
        """Converts this class to an instance of its respective simulation.

        Parameters
        ----------
        command_mapping: Dict[str, types.Command]
            A mapping of commands from which this group will get their corresponding parents from.

        Returns
        -------
        discord.ext.commands.Group
            The group class made using the given attributes of this temporary class.
        """
        if self.parent:
            command = command_mapping.get(self.parent)
            if not command:
                raise RuntimeError(f"Couldn't find {self.qualified_name} command's parent")
            if not isinstance(command, commands.Group):
                raise RuntimeError("Group's parent command is not commands.Group instance")
            deco = command.group
        else:
            deco = commands.group
        cmd: commands.Group[CogT_co, ..., Any] = deco(
            name=self.name,
            cls=_DiscordGroup,
            **self.kwargs
        )(self.callback)
        if self.on_error:
            cmd.error(self.on_error)
        return cmd


class Root(commands.Cog):
    """A cog subclass that implements a global check and some default functionality that the dev extension should have.

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
        A dictionary that stores all modifications made in the `dev override`/`dev overwrite` commands.
    """

    scope: ClassVar[GlobalLocals] = GlobalLocals()
    cached_messages: ClassVar[dict[int, discord.Message]] = {}
    _subclasses: set[type[Root]] = set()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        #  Only allow direct subclasses of Root to be added, otherwise cog conflict may occur.
        if cls.__base__ == Root:
            Root._subclasses.add(cls)
        super().__init_subclass__()

    def __init__(self, bot: types.Bot) -> None:
        self.bot: types.Bot = bot
        if frontend_cog := bot.get_cog("Dev"):
            children: set[types.Command] = set()
            for cmd in sorted(_get_commands(type(self).__mro__), key=lambda c: c.level):
                if cmd.qualified_name in frontend_cog.commands:  # type: ignore
                    original: type[_DiscordCommand] | type[_DiscordGroup] = frontend_cog.commands.get(  # type: ignore
                        cmd.qualified_name
                    )
                    mapping: dict[Any, Any] = {
                        _DiscordCommand: Command,
                        _DiscordGroup: Group,
                        Group: "group",
                        Command: "command"
                    }
                    as_method: type[Command[Root]] | type[Group[Root]] | None = mapping.get(type(original))
                    if as_method != type(cmd):
                        raise RuntimeError(
                            f"Overrided command {cmd!r} in {self} has been set as a {mapping.get(type(cmd))} when "
                            f"its original is a {mapping.get(as_method)}"
                        )
                    if isinstance(cmd, Command) and cmd.parent:
                        parent: _DiscordGroup = frontend_cog.commands.get(cmd.parent)  # type: ignore
                        parent.remove_command(cmd.name)
                    elif isinstance(cmd, Group):
                        subcommands: commands.Group[Any, ..., Any] = frontend_cog.commands.get(  # type: ignore
                            cmd.qualified_name
                        )
                        for child in subcommands.commands:
                            children.add(child)
                        if cmd.parent:
                            parent: _DiscordGroup = frontend_cog.commands.get(cmd.parent)  # type: ignore
                            parent.remove_command(cmd.name)
                        else:
                            bot.remove_command(cmd.name)
                actual = cmd.to_instance(frontend_cog.commands)  # type: ignore
                if isinstance(actual, _DiscordGroup):
                    for child in children:
                        actual.add_command(child)
                if actual.qualified_name == actual.name:
                    #  Top level command
                    bot.add_command(actual)
                if type(self).__base__ == Root:
                    actual.cog = frontend_cog  # type: ignore
                else:
                    self.__dict__.update(frontend_cog.__dict__)
                    actual.cog = self
                frontend_cog.commands[actual.qualified_name] = actual  # type: ignore
            return
        if type(self).__base__ == Root:
            return
        self.commands: dict[str, types.Command] = {}
        self.registrations: dict[int, CommandRegistration | SettingRegistration] = {}

        root_commands: list[Command[Root] | Group[Root]] = list(_get_commands(tuple(Root._subclasses)))
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

    def get_all_implementations(self, qualified_name: str) -> Generator[CommandRegistration, None, None]:
        base = self.get_base_command(qualified_name)
        if base is not None:
            yield base.to_command()
        for cmd in self.registrations.values():
            if isinstance(cmd, CommandRegistration) and cmd.qualified_name == qualified_name:
                yield cmd

    def get_last_implementation(self, qualified_name: str, /) -> CommandRegistration | None:
        cmd = discord.utils.find(
            lambda c: isinstance(c, CommandRegistration) and c.qualified_name == qualified_name,
            reversed(self.registrations.values())
        )
        if cmd is not None:
            return cmd  # type: ignore
        base = self.get_base_command(qualified_name)
        if base is not None:
            return base.to_command()

    def get_first_implementation(self, qualified_name: str, /) -> CommandRegistration | None:
        cmd = discord.utils.find(
            lambda c: isinstance(c, CommandRegistration) and c.qualified_name == qualified_name,
            self.registrations.values()
        )
        if cmd is not None:
            return cmd  # type: ignore
        base = self.get_base_command(qualified_name)
        if base is not None:
            return base.to_command()

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
            /
    ) -> None:
        if mode is Over.DELETE and register not in self.registrations.values():
            raise IndexError("Registration cannot be deleted because it does not exist")
        if mode is Over.DELETE:
            for k, v in self.registrations.copy().items():
                if v == register:
                    del self.registrations[k]
        else:
            self.registrations[len(self.registrations)] = register

    async def cog_check(self, ctx: commands.Context[types.Bot]) -> bool:  # type: ignore
        """A check that is called every time a dev command is invoked.
        This check is called internally, and shouldn't be called elsewhere.

        It first checks if the command is allowed for global use.
        If that check fails, it checks if the author of the invoked command is specified in :attr:`Settings.OWNERS`.
        If the owner list is empty, it'll lastly check if the author owns the bot.

        If all checks fail, :class:`discord.ext.commands.NotOwner` is raised. This is done so that you can
        customize the message that is sent by the bot through an error handler.

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
        if isinstance(ctx.command, (_DiscordCommand, _DiscordGroup)):
            if ctx.command.global_use and Settings.allow_global_uses:
                return True
        if ctx.author.id in Settings.owners:
            return True
        elif await self.bot.is_owner(ctx.author) and not Settings.owners:
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")

    @tasks.loop(minutes=10)
    async def _clear_cached_messages(self):

        def function(msg_id: int) -> bool:
            created_at = discord.utils.snowflake_time(msg_id).timestamp()
            time_since_created = int(discord.utils.utcnow().timestamp() - created_at)
            return time_since_created >= 120

        message_ids: Iterator[int] = filter(function, Root.cached_messages.copy())
        for _id in message_ids:
            del Root.cached_messages[_id]


def _get_commands(cls: tuple[type, ...]) -> set[Command[Root] | Group[Root]]:
    cmds: set[Command[Root] | Group[Root]] = set()
    for kls in cls:
        if issubclass(kls, Root):
            _log.debug("Loading Root class %r", kls)
        for val in kls.__dict__.values():
            if isinstance(val, (Command, Group)):
                cmd: Command[Root] | Group[Root] = val
                cmds.add(cmd)
    return cmds
