# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic classes that will be used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Optional,
    List,
    Literal,
    Tuple,
    Type,
    TypeVar,
    Union
)

from discord.ext import commands
from discord.utils import MISSING

from dev.registrations import BaseCommandRegistration, CommandRegistration, SettingRegistration
from dev.types import AnyCommand, BotT, Callback, CommandT, CommandObj, GroupT


__all__ = (
    "Command",
    "GlobalLocals",
    "Group",
    "GroupMixin",
    "Root",
    "root"
)

CST = TypeVar("CST", CommandRegistration, SettingRegistration)


class GlobalLocals:
    """This allows variables to be stored within a class instance, instead of a global scope or dictionary.

    All parameters are positional-only.

    Parameters
    ----------
    __globals: Optional[Dict[:class:`str`, Any]]
        Global scope variables. Acts the same way as :meth:`globals()`.
        Defaults to ``None``.
    __locals: Optional[Dict[:class:`str`, Any]]
        Local scope variables. Acts the same way as :meth:`locals()`.
        Defaults to ``None``.
    """

    def __init__(self, __globals: Optional[Dict[str, Any]] = None, __locals: Optional[Dict[str, Any]] = None, /):
        self.globals: Dict[str, Any] = __globals or {}
        self.locals: Dict[str, Any] = __locals or {}

    def __bool__(self) -> bool:
        return bool(self.globals or self.locals)

    def __delitem__(self, key: Any):
        glob_exc, loc_exc = False, False
        try:
            del self.globals[key]
        except KeyError:
            glob_exc = True
        try:
            del self.locals[key]
        except KeyError:
            loc_exc = True

        if glob_exc and loc_exc:
            raise KeyError(key)

    def __getitem__(self, item: Any) -> Tuple[Any, Any]:
        glob, loc = None, None
        glob_exc, loc_exc = False, False
        try:
            glob = self.globals[item]
        except KeyError:
            glob_exc = True
        try:
            loc = self.locals[item]
        except KeyError:
            loc_exc = True

        if glob_exc and loc_exc:
            raise KeyError(item)
        return glob, loc

    def __len__(self) -> int:
        return len(self.globals) + len(self.locals)

    def items(self) -> Tuple[List[str], List[Any]]:
        """Returns a list of all global and local scopes with their respective key-value pairs.

        Returns
        -------
        Tuple[List[:class:`str`], List[Any]]
            A joined list of global and local variables from the current scope.
        """
        return [*self.globals.items()], [*self.locals.items()]

    def keys(self) -> Tuple[List[str], List[str]]:
        """Returns a list of keys of all global and local scopes.

        Returns
        -------
        Tuple[List[:class:`str`], List[:class:`str`]]
            A list of a global and local's keys from the current scope.
        """
        return [*list(self.globals.keys())], [*list(self.locals.keys())]

    def values(self) -> Tuple[List[Any], List[Any]]:
        """Returns a list of values of all global and local scopes.

        Returns
        -------
        Tuple[List[Any], List[Any]]
            A list of a global and local's values from the current scope.
        """
        return [*list(self.globals.values())], [*list(self.locals.values())]

    def get(self, item: str, default: Any = None) -> Any:
        """Get an item from either the global scope or the locals scope.

        Items found in the global scope will be returned before checking locals.
        It's best to use this when you are just trying to get a value without worrying about the scope.

        Parameters
        ----------
        item: :class:`str`
            The item that should be searched for in the scopes.
        default: Any
            An argument that should be returned if no value was found. Defaults to ``None``

        Returns
        -------
        Any
            The value of the item that was found, if it was found.
        """

        return self.globals.get(item) or self.locals.get(item, default)

    def update(self, __new_globals: Optional[Dict[str, Any]] = None, __new_locals: Optional[Dict[str, Any]] = None, /):
        """Update the current instance of variables with new ones.

        All parameters are positional-only.

        Parameters
        ----------
        __new_globals: Optional[Dict[:class:`str`, Any]]
            New instances of global variables.
        __new_locals: Optional[Dict[:class:`str`, Any]]
            New instances of local variables.
        """
        if __new_globals:
            self.globals.update(__new_globals)
        if __new_locals:
            self.locals.update(__new_locals)


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
        self.all_commands: Dict[str, AnyCommand] = {}
        self._add_parent: Dict[AnyCommand, str] = {}

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
        def decorator(func: Callback) -> Command:
            parent: str = kwargs.get("parent", MISSING)
            kwargs.setdefault('parent', self)
            result = group(name=name, **kwargs)(func)
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
            result = command(name=name, **kwargs)(func)
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
        def decorator(func: Callback) -> Command:
            kwargs.setdefault('parent', self)
            result = group(name=name, **kwargs)(func)
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
            result = command(name=name, **kwargs)(func)
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
            raise TypeError("Cannot toggle global use value for a command that didn't have it enabled in the first place")
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
    command_uses: Dict[:class:`str`, :class:`int`]
        A dictionary that keeps track of the amount of times a command has been used.
    """

    scope: GlobalLocals = GlobalLocals()

    def __init__(self, bot: BotT):
        from dev.utils.functs import all_commands  # circular import

        self.bot: BotT = bot
        self.root_command: Optional[Group] = root.all_commands.get("dev")
        self.command_uses: Dict[str, int] = {}
        self.registrations: Dict[int, CST] = {}
        self._base_registrations: Tuple[BaseCommandRegistration, ...] = tuple([BaseCommandRegistration(cmd) for cmd in all_commands(self.bot.commands)])

        for kls in type(self).__mro__:
            for key, cmd in kls.__dict__.items():
                if isinstance(cmd, (Command, Group)):
                    cmd.cog = self

    def get_base_command(self, command_name: str, /) -> BaseCommandRegistration:
        return [cmd for cmd in self._base_registrations if cmd.qualified_name == command_name][0]

    def filter_register_type(self, predicate: str, /) -> List[CST]:
        return [register for register in self.registrations.values() if register.register_type == predicate]

    def filter_over_type(self, predicate: str, /) -> List[CST]:
        return [register for register in self.registrations.values() if register.over_type == predicate]

    def to_register(self, command_string: str, /) -> List[CommandObj]:
        return [register for register in self.registrations.values() if register.command.qualified_name == command_string] or [cmd for cmd in self._base_registrations if cmd.qualified_name == command_string]

    def update_register(self, register: CST, mode: Literal["add", "del"], /) -> CST:
        if mode not in ("add", "del"):
            raise ValueError(f"Invalid mode submitted: {mode!r}")
        values = []
        if mode == "del" and register not in self.registrations.values():
            raise IndexError("Registration cannot be deleted because it does not exist")
        for k, v in self.registrations.items():
            if mode == "del":
                if v == register:
                    continue
            values.append(v)
        if mode == "add":
            values.append(register)
        registrations: Dict[int, Union[CommandRegistration, SettingRegistration]] = {}
        for index, rgs in enumerate(values, start=1):
            registrations[index] = rgs
        self.registrations.clear()
        self.registrations.update(registrations)
        return register

    def cog_load(self) -> None:
        from dev.utils.functs import all_commands  # circular import

        self._base_registrations: Tuple[BaseCommandRegistration, ...] = tuple([BaseCommandRegistration(cmd) for cmd in all_commands(self.bot.commands)])

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


def group(name: str = MISSING, **attrs: Any):
    return command(name=name, cls=Group, **attrs)


def command(name: str = MISSING, cls: Type[CommandT] = MISSING, **attrs):
    if cls is MISSING:
        cls = Command

    def decorator(func: Callback):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)
    return decorator
