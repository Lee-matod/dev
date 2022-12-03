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
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Coroutine, Generic, Literal, NoReturn, TypeVar, overload

import discord
from discord.ext import commands
from discord.utils import MISSING

from dev.handlers import GlobalLocals
from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import Over

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from dev import types

    P = ParamSpec("P")
else:
    P = TypeVar("P")


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
        if not isinstance(value, bool):  # pyright: ignore [reportUnnecessaryIsInstance]
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
        if not isinstance(value, bool):  # pyright: ignore [reportUnnecessaryIsInstance]
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
        if not isinstance(name, str): #  pyright: ignore [reportUnnecessaryIsInstance]
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

    def to_instance(
            self,
            command_mapping: dict[str, types.Command],
            /
    ) -> types.Command | NoReturn:
        raise NotImplementedError

    def error(
            self,
            func: Callable[[CogT_co, commands.Context[types.Bot], commands.CommandError], Coroutine[Any, Any, Any]]
    ) -> Callable[[CogT_co, commands.Context[types.Bot], commands.CommandError], Coroutine[Any, Any , Any]]:
        """Set a local error handler"""
        self.on_error = func
        return func


class Command(BaseCommand[CogT_co, ..., Any]):
    """A class that simulates :class:`commands.Command`

    This class is used to keep track of which functions should be commands, and it shouldn't get called manually.
    Instead, consider using :meth:`root.command` to instantiate this class.
    """

    def to_instance(
            self,
            command_mapping: dict[str, types.Command],
            /
    ) -> commands.Command[Root, ..., Any] | NoReturn:
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
                raise RuntimeError("Couldn't find command command's parent")
            if not isinstance(command, commands.Group):
                raise RuntimeError("Command's parent command is not commands.Group instance")
            deco = command.command
        else:
            deco = commands.command
        cmd: commands.Command[Root, ..., Any] = deco(
            name=self.name,
            cls=_DiscordCommand,
            **self.kwargs
        )(self.callback)  # type: ignore
        if self.on_error:
            cmd.error(self.on_error)  # type: ignore
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
    ) -> commands.Group[Root, ..., Any] | NoReturn:
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
                raise RuntimeError("Couldn't find group command's parent")
            if not isinstance(command, commands.Group):
                raise RuntimeError("Group's parent command is not commands.Group instance")
            deco = command.group
        else:
            deco = commands.group
        cmd: commands.Group[Root, ..., Any] = deco(
            name=self.name,
            cls=_DiscordGroup,
            **self.kwargs
        )(self.callback)  # type: ignore
        if self.on_error:
            cmd.error(self.on_error)  # type: ignore
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

    def __init__(self, bot: types.Bot) -> None:
        self.bot: types.Bot = bot
        self.commands: dict[str, types.Command] = {}
        self.registrations: dict[int, CommandRegistration | SettingRegistration] = {}
        self._base_registrations: tuple[BaseCommandRegistration, ...] = tuple(
            [BaseCommandRegistration(cmd) for cmd in self.bot.walk_commands()]
        )

        root_commands: list[Command[Root] | Group[Root]] = []
        for kls in type(self).__mro__:
            for val in kls.__dict__.values():
                if isinstance(val, (Command, Group)):
                    cmd: Command[Root] | Group[Root] = val
                    root_commands.append(cmd)

        root_commands.sort(key=lambda c: c.level)
        for command in root_commands:
            command.cog = self
            command = command.to_instance(self.commands)
            self.commands[command.qualified_name] = command
            self.commands[command.qualified_name].cog = self
        root_command = self.commands.get("dev")
        if root_command is None:
            raise RuntimeError("Could not get root command")
        bot.add_command(root_command)

    def get_base_command(self, command_name: str, /) -> BaseCommandRegistration | None:
        for base in self._base_registrations:
            if command_name == base.qualified_name:
                return base

    @overload
    def registers_from_type(self, rgs_type: Literal[Over.OVERRIDE]) -> list[CommandRegistration]:
        ...

    @overload
    def registers_from_type(self, rgs_type: Literal[Over.OVERWRITE]) -> list[CommandRegistration | SettingRegistration]:
        ...

    def registers_from_type(self, rgs_type: Any) -> Any:
        return [rgs for rgs in self.registrations.values() if rgs.register_type is rgs_type]  #  type: ignore

    def match_register_command(self, qualified_name: str) -> list[CommandRegistration]:
        command_list: list[CommandRegistration] = []
        for rgs in self.registrations.values():
            if isinstance(rgs, CommandRegistration):
                if rgs.command.qualified_name == qualified_name:
                    command_list.append(rgs)
        other = self.get_base_command(qualified_name)
        if other is None:
            other = []
        else:
            other = [other]
        return command_list or other  # type: ignore

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
        from dev.utils.startup import Settings  # circular import

        if isinstance(ctx.command, (_DiscordCommand, _DiscordGroup)):
            if ctx.command.global_use and Settings.ALLOW_GLOBAL_USES:
                return True
        if ctx.author.id in Settings.OWNERS:
            return True
        elif await self.bot.is_owner(ctx.author) and not Settings.OWNERS:
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")
