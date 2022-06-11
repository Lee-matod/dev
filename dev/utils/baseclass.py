# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic classes that will be used within the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from discord.ext import commands
from discord.utils import MISSING


CogT = TypeVar("CogT", bound="Optional[Cog]")
CommandT = TypeVar("CommandT", bound="Command")
ContextT = TypeVar("ContextT", bound="Context")
GroupT = TypeVar("GroupT", bound="Group")


__all__ = (
    "Command",
    "GlobalLocals",
    "Group",
    "Root",
    "root"
)


class GlobalLocals:
    def __init__(self, __globals: Optional[Dict[str, Any]] = None, __locals: Optional[Dict[str, Any]] = None):
        self.globals: Dict[str, Any] = __globals or {}
        self.locals: Dict[str, Any] = __locals or {}

    def update(self, __new_globals: Optional[Dict[str, Any]] = None, __new_locals: Optional[Dict[str, Any]] = None):
        if __new_globals:
            self.globals.update(__new_globals)
        if __new_locals:
            self.locals.update(__new_locals)
        return self


class GroupMixin(commands.GroupMixin):
    def __init__(self):
        super().__init__()
        self.all_commands: Dict[str, Union[Command, Group]] = {}
        self._add_parent: Dict[Union[Command, Group], str] = {}

    def group(
            self,
            name: str = MISSING,
            cls: Type[GroupT] = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callable[[CogT, ContextT, Any], Coroutine[Any, Any, Any]],
        ],
        CommandT
    ]:
        def decorator(func) -> Command:
            parent = kwargs.get("parent", MISSING)
            kwargs.setdefault('parent', self)
            result = group(name=name, cls=cls, **kwargs)(func)
            self.all_commands[name] = result
            if parent:
                self._add_parent[result] = parent
            return result
        return decorator

    def command(
            self,
            name: str = MISSING,
            cls: Type[CommandT] = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callable[[CogT, ContextT, Any], Coroutine[Any, Any, Any]],
        ],
        CommandT
    ]:
        def decorator(func) -> Command:
            parent = kwargs.get("parent", MISSING)
            kwargs.setdefault('parent', self)
            result = command(name=name, cls=cls, **kwargs)(func)
            self.all_commands[name] = result
            if parent:
                self._add_parent[result] = parent
            return result

        return decorator


root = GroupMixin()


class Group(commands.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs

    @property
    def global_use(self) -> bool:
        return self.kwargs.get("global_use", False)

    @global_use.setter
    def global_use(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool type but received {type(value).__name__}")
        self.kwargs["global_use"] = value

    @property
    def supports_virtual_vars(self) -> bool:
        return self.kwargs.get("virtual_vars", False)

    @property
    def supports_root_placeholder(self):
        return self.kwargs.get("root_placeholder", False)

    def group(
            self,
            name: str = MISSING,
            cls: Type[CommandT] = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callable[[CogT, ContextT, Any], Coroutine[Any, Any, Any]],
        ],
        CommandT
    ]:
        def decorator(func) -> Command:
            kwargs.setdefault('parent', self)
            result = group(name=name, cls=cls, **kwargs)(func)
            self.add_command(result)
            root.all_commands[result.qualified_name] = result
            return result
        return decorator

    def command(
            self,
            name: str = MISSING,
            cls: Type[CommandT] = MISSING,
            *args: Any,
            **kwargs: Any) -> Callable[
        [
            Callable[[CogT, ContextT, Any], Coroutine[Any, Any, Any]],
        ],
        CommandT
    ]:
        def decorator(func) -> Command:
            kwargs.setdefault('parent', self)
            result = command(name=name, cls=cls, **kwargs)(func)
            self.add_command(result)
            root.all_commands[result.qualified_name] = result
            return result

        return decorator


class Command(commands.Command):
    def __init__(self, func, *args, **kwargs):
        super().__init__(func, **kwargs)
        list(args).append(func)
        self.args = args
        self.kwargs = kwargs

    @property
    def global_use(self) -> bool:
        return self.kwargs.get("global_use", False)

    @global_use.setter
    def global_use(self, value: bool):
        if not isinstance(value, bool):
            raise TypeError(f"Expected bool type but received {type(value).__name__}")
        self.kwargs["global_use"] = value

    @property
    def supports_virtual_vars(self) -> bool:
        return self.kwargs.get("virtual_vars", False)

    @property
    def supports_root_placeholder(self):
        return self.kwargs.get("root_placeholder", False)


class Root(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.root_command = root.all_commands.get("dev", None)
        self.command_uses: Dict[str, int] = {}
        self.CALLBACKS: Dict[
            int,  # ID
            Tuple[
                str,  # command name
                Callable[[CogT, ContextT, Any], Coroutine[Any, Any, Any]],  # original callback
                str  # new source code
            ]
        ] = {}

        for kls in type(self).__mro__:
            for key, cmd in kls.__dict__.items():
                if isinstance(cmd, (Command, Group)):
                    cmd.cog = self

    def cog_check(self, ctx) -> bool:
        from dev.utils.startup import Settings  # circular import

        if isinstance(ctx.command, (Command, Group)):
            if ctx.command.global_use and Settings.ALLOW_GLOBAL_USES:
                return True
        if ctx.author.id in Settings.OWNERS or ctx.bot.is_owner(ctx.author):
            return True
        raise commands.NotOwner("You have to own this bot to be able to use this command")


def group(name: str = MISSING, cls=MISSING, **attrs: Any):
    if cls is MISSING:
        cls = Group
    return command(name=name, cls=cls, **attrs)


def command(name: str = MISSING, cls=MISSING, **attrs):
    if cls is MISSING:
        cls = Command

    def decorator(func):
        if isinstance(func, Command):
            raise TypeError('Callback is already a command.')
        return cls(func, name=name, **attrs)
    return decorator
