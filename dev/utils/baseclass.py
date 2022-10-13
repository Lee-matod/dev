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
from typing import TYPE_CHECKING, Callable, Dict, Optional, List, Tuple, Union, overload

from discord.ext import commands
from discord.utils import MISSING

from dev.handlers import GlobalLocals
from dev.registrations import BaseCommandRegistration, CommandRegistration
from dev.types import Over

if TYPE_CHECKING:
    import discord

    from dev import types

    from dev.registrations import SettingRegistration
    from dev.types import Callback, ErrorCallback


__all__ = (
    "Command",
    "Group",
    "Root",
    "root"
)


class OperationNotAllowedError(BaseException):
    pass


class root:  # noqa E302
    """A super class that allows the conversion of coroutine functions to temporary command classes
    that can later be used to register them as an actual :class:`discord.ext.commands.Command`.

    Even though this class was made for internal uses, it cannot be instantiated nor subclassed.
    It should be used as-is.
    """
    def __init__(self):
        raise OperationNotAllowedError("Cannot instantiate root.")

    def __new__(cls, *args, **kwargs):
        raise OperationNotAllowedError("Cannot instantiate root.")

    def __init_subclass__(cls, **kwargs):
        raise OperationNotAllowedError("Cannot subclass root.")

    @staticmethod
    def command(name: str = MISSING, **kwargs) -> Callable[[Callback], Command]:
        """A decorator that converts the given function to a temporary :class:`Command` class.

        Parameters
        ----------
        name: :class:`str`
            The name of the command that should be used. If no name is provided, the function's name will be used.
        kwargs:
            Key-word arguments that'll be forwarded to the :class:`Command` class.
        """
        def decorator(func: Callback) -> Command:
            if isinstance(func, Command):
                raise TypeError("Callback is already a command.")
            return Command(func, name=name, **kwargs)
        return decorator

    @staticmethod
    def group(name: str = MISSING, **kwargs) -> Callable[[Callback], Group]:
        """A decorator that converts the given function to a temporary :class:`Group` class.

        Parameters
        ----------
        name: :class:`str`
            The name of the command that should be used. If no name is provided, the function's name will be used.
        kwargs:
            Key-word arguments that'll be forwarded to the :class:`Group` class.
        """
        def decorator(func: Callback) -> Group:
            if isinstance(func, Group):
                raise TypeError("Callback is already a group.")
            return Group(func, name=name, **kwargs)
        return decorator


class _DiscordCommand(commands.Command):
    def __init__(self, func: Callback, **kwargs):
        self.__global_use = kwargs.pop("global_use", None)
        self.__virtual_vars = kwargs.pop("virtual_vars", False)
        self.__root_placeholder = kwargs.pop("root_placeholder", False)
        super().__init__(func, **kwargs)

    @property
    def global_use(self) -> bool:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.__global_use

    @global_use.setter
    def global_use(self, value: bool):
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


class _DiscordGroup(commands.Group):
    def __init__(self, *args, **kwargs):
        self.__global_use = kwargs.pop("global_use", None)
        self.__virtual_vars = kwargs.pop("virtual_vars", False)
        self.__root_placeholder = kwargs.pop("root_placeholder", False)
        super().__init__(*args, **kwargs)

    @property
    def global_use(self) -> bool:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.__global_use

    @global_use.setter
    def global_use(self, value: bool):
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


class BaseCommand:
    def __init__(self, func: Callback, **kwargs):
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Callback must be a coroutine.")
        name = kwargs.pop("name", None) or func.__name__
        if not isinstance(name, str):
            raise TypeError("Name of a command must be a string.")
        self.name: str = name
        self.callback: Callback = func
        self.parent: str = kwargs.pop("parent", None)
        self.kwargs = kwargs

        self.level: int = 0
        if self.parent:
            self.level = len(self.parent.split())

        self.on_error: Optional[ErrorCallback] = None

    def to_instance(self, command_mapping: Dict[str, types.Command], /):
        raise NotImplementedError

    def error(self, func: ErrorCallback) -> ErrorCallback:
        """Set a local error handler"""
        self.on_error = func
        return func


class Command(BaseCommand):
    """A class that simulates :class:`commands.Command`

    This class is used to keep track of which functions should be commands, and it shouldn't get called manually.
    Instead, consider using :meth:`root.command` to instantiate this class.
    """

    def to_instance(self, command_mapping: Dict[str, types.Command], /) -> commands.Command:
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
        cmd = deco(name=self.name, cls=_DiscordCommand, **self.kwargs)(self.callback)
        if self.on_error:
            cmd.error(self.on_error)
        return cmd


class Group(BaseCommand):
    """A class that simulates :class:`discord.ext.commands.Group`.

    This class is used to keep track of which functions be groups, and it shouldn't get called manually.
    Instead, consider using :meth:`root.group` to instantiate this class.
    """

    def to_instance(self, command_mapping: Dict[str, types.Command], /) -> commands.Group:
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
        cmd = deco(name=self.name, cls=_DiscordGroup, **self.kwargs)(self.callback)
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

    scope: GlobalLocals = GlobalLocals()
    cached_messages: Dict[int, discord.Message] = {}

    def __init__(self, bot: types.Bot):
        from dev.utils.functs import all_commands  # circular import

        self.bot: types.Bot = bot
        self.commands: Dict[str, types.Command] = {}
        self.registrations: Dict[int, Union[CommandRegistration, SettingRegistration]] = {}
        self._base_registrations: Tuple[BaseCommandRegistration, ...] = tuple(
            [BaseCommandRegistration(cmd) for cmd in all_commands(self.bot.commands)]
        )

        root_commands: List[Union[Command, Group]] = []
        for kls in type(self).__mro__:
            for key, cmd in kls.__dict__.items():
                if isinstance(cmd, (Command, Group)):
                    root_commands.append(cmd)
        root_commands.sort(key=lambda c: c.level)
        for command in root_commands:
            command = command.to_instance(self.commands)
            self.commands[command.qualified_name] = command
            self.commands[command.qualified_name].cog = self
        bot.add_command(self.commands.get("dev"))

    def get_base_command(self, command_name: str, /) -> Optional[BaseCommandRegistration]:
        for base in self._base_registrations:
            if command_name == base.qualified_name:
                return base

    @overload
    def registers_from_type(self, rgs_type: Over.OVERRIDE) -> List[CommandRegistration]:
        ...

    @overload
    def registers_from_type(self, rgs_type: Over.OVERWRITE) -> List[Union[CommandRegistration, SettingRegistration]]:
        ...

    def registers_from_type(self, rgs_type):
        return [rgs for rgs in self.registrations.values() if rgs.register_type is rgs_type]

    def match_register_command(self, qualified_name: str) -> List[Union[BaseCommandRegistration, CommandRegistration]]:
        command_list: List[CommandRegistration] = []
        for rgs in self.registrations.values():
            if isinstance(rgs, CommandRegistration):
                if rgs.command.qualified_name == qualified_name:
                    command_list.append(rgs)
        return command_list or [self.get_base_command(qualified_name)]

    @overload
    def update_register(self, register: CommandRegistration, mode: Over, /) -> CommandRegistration:
        ...

    @overload
    def update_register(self, register: SettingRegistration, mode: Over, /) -> SettingRegistration:
        ...

    def update_register(self, register, mode: Over, /):
        if mode is Over.DELETE and register not in self.registrations.values():
            raise IndexError("Registration cannot be deleted because it does not exist")
        if mode is Over.DELETE:
            for k, v in self.registrations.copy().items():
                if v == register:
                    del self.registrations[k]
        else:
            self.registrations[len(self.registrations)] = register
        return register

    async def cog_check(self, ctx: commands.Context) -> bool:
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
        # not sure if it'd be best to do an elif or an `or` operation here.
        if ctx.author.id in Settings.OWNERS:
            return True
        elif await self.bot.is_owner(ctx.author) and not Settings.OWNERS:
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")
