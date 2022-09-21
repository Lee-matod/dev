# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic classes used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional, List, Tuple, TypeVar, Union, overload

from discord.ext import commands
from discord.utils import MISSING

from dev import types
from dev.handlers import GlobalLocals
from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import Callback, CommandT, GroupT, Over


__all__ = (
    "Command",
    "Group",
    "GroupMixin",
    "Root",
    "root"
)

CST = TypeVar("CST", CommandRegistration, SettingRegistration)


class GroupMixin(commands.GroupMixin):
    """A subclasses of :class:`commands.GroupMixin` that overrides command registering functionality.

    You would usually want to create an instance of this class and start registering your commands from there.

    Attributes
    ----------
    all_commands: Dict[:class:`str`, Union[:class:`Command`, :class:`Group`]]
        A dictionary of all registered commands and their qualified names.
    """

    def __init__(self):
        super().__init__()
        self.all_commands: Dict[str, types.Command] = {}
        self._add_parent: Dict[types.Command, str] = {}

    def group(
            self,
            name: str = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callback
        ],
        GroupT
    ]:
        def decorator(func: Callback) -> Group:
            parent: str = kwargs.get("parent", MISSING)
            kwargs.setdefault('parent', self)
            if isinstance(func, Group):
                raise TypeError('Callback is already a command.')
            result = Group(func, name=name, **kwargs)
            self.all_commands[name] = result
            if parent:
                self._add_parent[result] = parent
            return result
        return decorator

    def command(
            self,
            name: str = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callback,
        ],
        CommandT
    ]:
        def decorator(func: Callback) -> Command:
            parent: str = kwargs.get("parent", MISSING)
            kwargs.setdefault('parent', self)
            if isinstance(func, Command):
                raise TypeError('Callback is already a command.')
            result = Command(func, name=name, **kwargs)
            self.all_commands[name] = result
            if parent:
                self._add_parent[result] = parent
            return result

        return decorator


root = GroupMixin()


class Group(commands.Group):
    """A subclasses of :class:`commands.Group` which adds a few extra properties for commands."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs

    @property
    def global_use(self) -> bool:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.kwargs.get("global_use", False)

    @global_use.setter
    def global_use(self, value: bool):
        if self.kwargs.get("global_use") is None:
            raise TypeError("Cannot toggle global use value for a group that didn't have it enabled in the first place")
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool type but received {type(value).__name__}")
        self.kwargs["global_use"] = value

    @property
    def supports_virtual_vars(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the use of out-of-scope variables.
        """
        return self.kwargs.get("virtual_vars", False)

    @property
    def supports_root_placeholder(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the `|root|` placeholder text.
        """
        return self.kwargs.get("root_placeholder", False)

    def group(
            self,
            name: str = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callback,
        ],
        CommandT
    ]:
        def decorator(func: Callback) -> Group:
            kwargs.setdefault('parent', self)
            if isinstance(func, Group):
                raise TypeError('Callback is already a command.')
            result = Group(func, name=name, **kwargs)
            self.add_command(result)
            root.all_commands[result.qualified_name] = result
            return result
        return decorator

    def command(
            self,
            name: str = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callback,
        ],
        CommandT
    ]:
        def decorator(func: Callback) -> Command:
            kwargs.setdefault('parent', self)
            if isinstance(func, Command):
                raise TypeError('Callback is already a command.')
            result = Command(func, name=name, **kwargs)
            self.add_command(result)
            root.all_commands[result.qualified_name] = result
            return result

        return decorator


class Command(commands.Command):
    """A subclasses of :class:`commands.Command` which adds a few extra properties for commands."""

    def __init__(self, func, *args, **kwargs):
        super().__init__(func, **kwargs)
        list(args).append(func)
        self.args = tuple(args)
        self.kwargs = kwargs

    @property
    def global_use(self) -> bool:
        """:class:`bool`:
        Check whether this command is allowed to be invoked by any user.
        """
        return self.kwargs.get("global_use", False)

    @global_use.setter
    def global_use(self, value: bool):
        if self.kwargs.get("global_use") is None:
            raise TypeError(
                "Cannot toggle global use value for a command that didn't have it enabled in the first place"
            )
        if not isinstance(value, bool):
            raise ValueError(f"Expected bool type but received {type(value).__name__}")
        self.kwargs["global_use"] = value

    @property
    def supports_virtual_vars(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the use of out-of-scope variables.
        """
        return self.kwargs.get("virtual_vars", False)

    @property
    def supports_root_placeholder(self) -> bool:
        """:class:`bool`:
        Check whether this command is compatible with the `|root|` placeholder text.
        """
        return self.kwargs.get("root_placeholder", False)


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
    root_command: Optional[Group]
        The root command (`dev`) of the extension.
    """

    scope: GlobalLocals = GlobalLocals()

    def __init__(self, bot: types.Bot):
        from dev.utils.functs import all_commands  # circular import

        self.bot: types.Bot = bot
        self.root_command: Optional[Group] = root.all_commands.get("dev")
        self.registrations: Dict[int, Union[CommandRegistration, SettingRegistration]] = {}
        self._base_registrations: Tuple[BaseCommandRegistration, ...] = tuple(
            [BaseCommandRegistration(cmd) for cmd in all_commands(self.bot.commands)]
        )

        for kls in type(self).__mro__:
            for key, cmd in kls.__dict__.items():
                if isinstance(cmd, (Command, Group)):
                    cmd.cog = self

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
