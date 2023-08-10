# -*- coding: utf-8 -*-

"""
dev.scope
~~~~~~~~~

Python scope-related classes such as configs.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import itertools
import os
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, get_origin

import discord

from dev.converters import str_ints
from dev.types import Annotated

if TYPE_CHECKING:
    from typing_extensions import Self

__all__ = (
    "Option",
    "Scope",
    "Settings",
)

T = TypeVar("T")

def _path_exists(path: str) -> str:
    _dir = pathlib.Path(path)
    if not _dir.exists() or not _dir.is_dir():
        raise NotADirectoryError(path)
    return str(_dir.absolute())  # ensures that the path does not end in a slash


class Scope:
    """Represents a Python scope with global and local variables.

    Parameters
    ----------
    __globals: Optional[Dict[:class:`str`, Any]]
        Global scope variables. Acts the same way as :meth:`globals()`.
        Defaults to ``None``.
    __locals: Optional[Dict[:class:`str`, Any]]
        Local scope variables. Acts the same way as :meth:`locals()`.
        Defaults to ``None``.

    Notes
    -----
    When getting items, the global scope is prioritized over the local scope.
    """

    def __init__(self, __globals: dict[str, Any] | None = None, __locals: dict[str, Any] | None = None, /) -> None:
        self.globals: dict[str, Any] = __globals or {}
        self.locals: dict[str, Any] = __locals or {}

    def __repr__(self) -> str:
        return f"<{type(self).__name__} globals={self.globals} locals={self.locals}"

    def __bool__(self) -> bool:
        """Whether both global and local dictionaries are not empty."""
        return bool(self.globals or self.locals)

    def __delitem__(self, key: Any) -> None:
        """Deletes `y` from the global scope, local scope, or both.  """
        glob_exc, loc_ext = False, False
        try:
            del self.globals[key]
        except KeyError:
            glob_exc = True
        try:
            del self.locals[key]
        except KeyError:
            loc_ext = True
        if glob_exc and loc_ext:
            raise KeyError(key)

    def __getitem__(self, item: Any) -> Any:
        """Gets the global or local value of `y`.  """
        try:
            return self.globals[item]
        except KeyError:
            return self.locals[item]

    def __len__(self) -> int:
        """Returns the added length of both global and local dictionaries."""
        return len(self.globals) + len(self.locals)

    def items(self) -> tuple[tuple[Any, Any], ...]:
        """Returns a tuple of all global and local scopes with their respective key-value pairs.

        Returns
        -------
        Tuple[Tuple[Any, Any], ...]
            A joined tuple of global and local variables from the current scope.
        """
        return tuple(itertools.chain(self.globals.items(), self.locals.items()))

    def keys(self) -> tuple[Any, ...]:
        """Returns a tuple of keys of all global and local scopes.

        Returns
        -------
        Tuple[Any, ...]
            A tuple containing the list of global and local keys from the current scope.
        """
        return tuple(itertools.chain(self.globals.keys(), self.locals.keys()))

    def values(self) -> tuple[Any, ...]:
        """Returns a tuple of values of all global and local scopes.

        Returns
        -------
        Tuple[Any, ...]
            A tuple containing the list of global and local values from the current scope.
        """
        return tuple(itertools.chain(self.globals.values(), self.locals.values()))

    def get(self, item: Any, default: T | None = None) -> Any | None | T:
        """Get an item from either the global or local scope.

        If no item is found, the default will be returned.
        It is best to use this when you are just trying to get a value without worrying about the scope.

        Parameters
        ----------
        item: Any
            The item that should be searched for in the scopes.
        default: Any
            An argument that should be returned if no value was found. Defaults to ``None``.

        Returns
        -------
        Any
            The value of the item that was found, if any.
        """
        try:
            res = self.globals[item]
        except KeyError:
            try:
                res = self.locals[item]
            except KeyError:
                return default
        return res

    def update(
        self, __new_globals: dict[str, Any] | None = None, __new_locals: dict[str, Any] | None = None, /
    ) -> None:
        """Update the current instance of variables with new ones.

        Parameters
        ----------
        __new_globals: Optional[Dict[:class:`str`, Any]]
            New instances of global variables.
        __new_locals: Optional[Dict[:class:`str`, Any]]
            New instances of local variables.
        """
        if __new_globals is not None:
            self.globals.update(__new_globals)
        if __new_locals is not None:
            self.locals.update(__new_locals)


@dataclass
class Option(Generic[T]):
    name: str
    converter: Callable[[Any], T] | None
    value: T | None
    _type: type[T]

    def fetch(self) -> T:
        from_env = os.getenv(f"DEV_{self.name.upper()}", "").strip()

        if from_env:
            if self._type is bool:
                return str(from_env).lower() == "true"  # type: ignore
            return self.convert(from_env)
        if self.value is not None:
            os.environ[f"DEV_{self.name.upper()}"] = str(self.value)
            return self.value
        return self._type()

    def convert(self, argument: Any, /) -> T:
        if self.converter is not None:
            converted = self.converter(str(argument))
        else:
            converted = argument
        if not isinstance(converted, get_origin(self._type) or self._type):
            raise ValueError(f"Expected type {self._type} but received {type(converted)} instead")
        return converted


class _SettingsMeta(type):
    __options__: dict[str, Option[Any]]

    def __new__(cls, name: str, base: tuple[type[Any]], attrs: dict[str, Any]) -> Self:
        attrs["__options__"] = {}

        for name, _annot in attrs["__annotations__"].items():
            annot = discord.utils.resolve_annotation(_annot, globals(), locals(), None)
            default = attrs.pop(name, None)

            if isinstance(annot, Annotated):
                converter = annot.metadata[0]
                annot = annot.typehint
            elif callable(default):
                converter = default
            else:
                converter = None

            attrs["__options__"][name] = Option(name, converter, default, annot)

        return super().__new__(cls, name, base, attrs)

    def __getattr__(cls, __name: str) -> Any:
        if hasattr(cls, "__options__") and __name in cls.__options__:
            return cls.__options__[__name].fetch()

        return super().__getattribute__(__name)

    def __setattr__(cls, __name: str, __value: Any) -> None:
        if __name in cls.__options__:
            option: Option[Any] = cls.__options__[__name]

            converted = option.convert(__value)
            os.environ[f"DEV_{option.name.upper()}"] = str(converted)
        else:
            super().__setattr__(__name, __value)


class Settings(metaclass=_SettingsMeta):
    CWD: Annotated[str, _path_exists] = os.getcwd()

    GLOBAL_USE: bool = False

    FLAG_DELIMITER: str = "="

    INVOKE_ON_EDIT: bool = False

    LOCALE: str = "en-US"

    OWNERS: Annotated[set[int], lambda x: set(str_ints(x))] = set()  # type: ignore

    RETAIN: bool = False

    ROOT_FOLDER: Annotated[str, _path_exists] = os.getcwd()

    VIRTUAL_VARS: str = "|%s|"
