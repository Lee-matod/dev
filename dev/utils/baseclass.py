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
from typing import Callable, Dict, Optional, List, Tuple, TypeVar, Union, overload

from discord.ext import commands
from discord.utils import MISSING

from dev import types
from dev.handlers import GlobalLocals
from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import Callback, Over


__all__ = (
    "Command",
    "Group",
    "Root",
    "root"
)

CST = TypeVar("CST", CommandRegistration, SettingRegistration)

class root:  # noqa E302

    @staticmethod
    def command(name: str = MISSING, **kwargs) -> Callable[[Callback], Command]:
        def decorator(func: Callback) -> Command:
            if isinstance(func, Command):
                raise TypeError("Callback is already a command.")
            return Command(func, name=name, **kwargs)
        return decorator

    @staticmethod
    def group(name: str = MISSING, **kwargs) -> Callable[[Callback], Group]:
        def decorator(func: Callback) -> Group:
            if isinstance(func, Group):
                raise TypeError("Callback is already a group.")
            return Group(func, name=name, **kwargs)
        return decorator


class BaseCommand:
    """Class that implements common functionality within both :class:`Command` and :class:`Group`"""
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

        self.extras: Dict[str, bool] = {
            "global_use": kwargs.pop("global_use", None),
            "virtual_vars": kwargs.pop("virtual_vars", False),
            "root_placeholder": kwargs.pop("root_placeholder", False)
        }
        extras = self.kwargs.setdefault("extras", self.extras)
        if extras:
            extras.update(self.extras)

    @property
    def global_use(self) -> bool:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.extras.get("global_use")

    @global_use.setter
    def global_use(self, value: bool):
        if self.extras.get("global_use") is None:
            raise TypeError("Cannot toggle global use value for a group that didn't have it enabled in the first place")
        if not isinstance(value, bool):
            raise TypeError(f"Expected type bool but received {type(value).__name__}")
        self.extras["global_use"] = value

    @property
    def virtual_vars(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the use of out-of-scope variables.
        """
        return self.extras.get("virtual_vars")

    @property
    def root_placeholder(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the `|root|` placeholder text.
        """
        return self.extras.get("root_placeholder")


class Group(BaseCommand):
    """A class that simulates a :class:`commands.Group` class"""

    def to_instance(self, command_mapping: Dict[str, types.Command], /) -> commands.Group:
        if self.parent:
            command = command_mapping.get(self.parent)
            if not command:
                raise RuntimeError("Couldn't find group command's parent")
            if not isinstance(command, commands.Group):
                raise RuntimeError("Group's parent command is not commands.Group instance")
            deco = command.group
        else:
            deco = commands.group
        return deco(name=self.name, **self.kwargs)(self.callback)


class Command(BaseCommand):
    """A class that simulates a :class:`commands.Command` class"""

    def to_instance(self, command_mapping: Dict[str, types.Command], /) -> commands.Group:
        if self.parent:
            command = command_mapping.get(self.parent)
            if not command:
                raise RuntimeError("Couldn't find command command's parent")
            if not isinstance(command, commands.Group):
                raise RuntimeError("Command's parent command is not commands.Group instance")
            deco = command.command
        else:
            deco = commands.command
        return deco(name=self.name, **self.kwargs)(self.callback)


class Root(commands.Cog):
    """A cog base subclass that implements a global check and some default functionality that the dev
    extension should have.

    Command uses and override callbacks are stored in here for quick access between different cogs.

    Parameters
    ----------
    bot: :class:`commands.Bot`
        The bot instance that gets passed to :meth:`commands.Bot.add_cog`.

    Attributes
    ----------
    bot: :class:`commands.Bot`
        The bot instance that was passed to :meth:`baseclass.Root`
    """

    scope: GlobalLocals = GlobalLocals()

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

    def update_register(self, register: CST, mode: Union[Over, Over], /) -> CST:
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
        """A cog check that is called every time a dev command is invoked.
        This check is called internally, and shouldn't be called elsewhere.

        It first checks if the command is allowed for global use.
        If that check fails, it checks if the author of the invoked command is specified
        in :attr:`Settings.OWNERS` or if they own the bot.

        If all checks fail, :class:`commands.NotOwner` is raised. This is done so that you can
        customize the message that is sent by the bot through an error handler.

        Raises
        ------
        NotOwner
            All checks failed. The user who invoked the command is not the owner of the bot.
        """
        from dev.utils.startup import Settings  # circular import

        if isinstance(ctx.command, (Command, Group)):
            if ctx.command.global_use and Settings.ALLOW_GLOBAL_USES:
                return True
        # not sure if it'd be best to do an elif or an `or` operation here.
        if ctx.author.id in Settings.OWNERS or await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")
