# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Base command classes used within the dev extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar

from discord.ext import commands

from dev.types import CogT

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from dev import types
    from dev.types import Coro

    P = ParamSpec("P")
else:
    P = TypeVar("P")

T = TypeVar("T")

__all__ = ("Command", "DiscordCommand", "DiscordGroup", "Group")


def copy_commands_to(group: commands.Group[Any, ..., Any], cmds: set[commands.Command[Any, ..., Any]], /) -> None:
    for child in cmds:
        try:
            group.add_command(child)
        except commands.CommandRegistrationError:
            pass


class _DiscordMixin:
    __global_use__: bool | None
    __virtual_vars__: bool
    __root_placeholder__: bool

    @property
    def global_use(self) -> bool | None:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.__global_use__

    @global_use.setter
    def global_use(self, value: bool) -> None:
        if self.__global_use__ is None:
            raise TypeError("Cannot toggle global use value for a command that didn't have it enabled")
        if not isinstance(value, bool):
            raise TypeError(f"Expected type bool but received {type(value).__name__}")
        self.__global_use__ = value

    @property
    def virtual_vars(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the use of out-of-scope variables.
        """
        return self.__virtual_vars__

    @property
    def root_placeholder(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the `|root|` placeholder text.
        """
        return self.__root_placeholder__


class DiscordCommand(commands.Command[CogT, ..., Any], _DiscordMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__global_use__: bool | None = kwargs.pop("global_use", None)
        self.__virtual_vars__: bool = kwargs.pop("virtual_vars", False)
        self.__root_placeholder__: bool = kwargs.pop("root_placeholder", False)
        super().__init__(*args, **kwargs)


class DiscordGroup(commands.Group[CogT, ..., Any], _DiscordMixin):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.__global_use__: bool | None = kwargs.pop("global_use", None)
        self.__virtual_vars__: bool = kwargs.pop("virtual_vars", False)
        self.__root_placeholder__: bool = kwargs.pop("root_placeholder", False)
        super().__init__(*args, **kwargs)


class BaseCommand(Generic[CogT, P, T]):
    def __init__(
        self, func: Callable[Concatenate[CogT, commands.Context[types.Bot], P], Coro[T]], **kwargs: Any
    ) -> None:
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("Callback must be a coroutine.")
        name: str = kwargs.pop("name", None) or func.__name__
        if not isinstance(name, str):
            raise TypeError("Name of a command must be a string.")
        self.name: str = name
        self.callback: Callable[Concatenate[CogT, commands.Context[types.Bot], P], Coro[T]] = func
        self.parent: str | None = kwargs.pop("parent", None)
        self.kwargs: dict[str, Any] = kwargs

        self.level: int = 0
        if self.parent:
            self.level = len(self.parent.split())

        self.on_error: Callable[[CogT, commands.Context[types.Bot], commands.CommandError], Coro[Any],] | None = None
        self.cog: CogT | None = None

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

    def to_instance(self, bot: types.Bot, command_mapping: dict[str, types.Command] | None = None, /) -> types.Command:
        raise NotImplementedError

    def error(
        self, func: Callable[[CogT, commands.Context[types.Bot], commands.CommandError], Coro[Any],]
    ) -> Callable[[CogT, commands.Context[types.Bot], commands.CommandError], Coro[Any],]:
        """Set a local error handler"""
        self.on_error = func
        return func


class Command(BaseCommand[CogT, ..., Any]):
    """A class that simulates :class:`discord.ext.commands.Command`.

    This class is used to keep track of which functions should be commands,
    and it shouldn't get called manually.
    Instead, consider using :meth:`root.command` to instantiate this class.
    """

    def to_instance(self, bot: types.Bot, command_mapping: dict[str, types.Command] | None = None, /) -> commands.Command[CogT, ..., Any]:
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
        if command_mapping is None:
            command_mapping = {c.qualified_name: c for c in bot.commands}
        if self.parent:
            command = command_mapping.get(self.parent)
            if not command:
                raise RuntimeError(f"Could not find parent {self.parent!r} for {self.name!r}")
            if not isinstance(command, commands.Group):
                raise RuntimeError(f"Parent {self.parent!r} of {self.name!r} is not commands.Group instance")
            command.remove_command(self.name)
            deco = command.command
        else:
            bot.remove_command(self.name)
            deco = commands.command
        cmd: commands.Command[CogT, ..., Any] = deco(name=self.name, cls=DiscordCommand, **self.kwargs)(self.callback)
        if self.on_error:
            cmd.error(self.on_error)
        return cmd


class Group(BaseCommand[CogT, ..., Any]):
    """A class that simulates :class:`discord.ext.commands.Group`.

    This class is used to keep track of which functions be groups,
    and it shouldn't get called manually.
    Instead, consider using :meth:`root.group` to instantiate this class.
    """

    def to_instance(self, bot: types.Bot, command_mapping: dict[str, types.Command] | None = None, /) -> commands.Group[CogT, ..., Any]:
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
        if command_mapping is None:
            command_mapping = {c.qualified_name: c for c in bot.commands}
        children: set[commands.Command[Any, ..., Any]] = set()
        if self.parent:
            command = command_mapping.get(self.parent)
            if not command:
                raise RuntimeError(f"Could not find a parent {self.parent!r} for {self.name!r}")
            if not isinstance(command, commands.Group):
                raise RuntimeError(f"Parent {self.parent!r} of {self.name!r} is not commands.Group instance")
            old_command = command.remove_command(self.name)
            if old_command is not None and isinstance(old_command, commands.Group):
                children.update(old_command.commands)
            deco = command.group
        else:
            old_command = bot.remove_command(self.name)
            if old_command is not None and isinstance(old_command, commands.Group):
                children.update(old_command.commands)
            deco = commands.group
        cmd: commands.Group[CogT, ..., Any] = deco(name=self.name, cls=DiscordGroup, **self.kwargs)(self.callback)
        copy_commands_to(cmd, children)
        if self.on_error:
            cmd.error(self.on_error)
        return cmd
