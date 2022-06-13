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
    Dict,
    Optional,
    Tuple,
    Type
)

from discord.ext import commands
from discord.utils import MISSING

from dev.types import BotT, Callback, CommandT, GroupT, GroupMixinT


__all__ = (
    "Command",
    "GlobalLocals",
    "Group",
    "GroupMixin",
    "Root",
    "root"
)


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
    def __init__(self):
        super().__init__()
        self.all_commands: Dict[str, GroupMixinT] = {}
        self._add_parent: Dict[GroupMixinT, str] = {}

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
        The bot instance that was passed to :meth:`baseclass.Root.__init__`
    root_command: Optional[Group]
        The root command (`dev`) of the extension.
    command_uses: Dict[:class:`str`, :class:`int`]
        A dictionary that keeps track of the amount of times a command has been used.
    CALLBACKS: Dict[:class:`int`, Tuple[:class:`str`, Callable[[:class:`Cog`, :class:`Context`, Any], Coroutine[Any, Any, Any]], :class:`str`]]
        Saved callbacks and source codes from command overrides or overwrites.
    """

    def __init__(self, bot: BotT):
        self.bot = bot
        self.root_command: Optional[Group] = root.all_commands.get("dev")
        self.command_uses: Dict[str, int] = {}
        self.CALLBACKS: Dict[
            int,  # ID
            Tuple[
                str,  # command name
                Callback,  # original callback
                str  # new source code
            ]
        ] = {}

        for kls in type(self).__mro__:
            for key, cmd in kls.__dict__.items():
                if isinstance(cmd, (Command, Group)):
                    cmd.cog = self

    def cog_check(self, ctx) -> bool:
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
        if ctx.author.id in Settings.OWNERS or ctx.bot.is_owner(ctx.author):
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
