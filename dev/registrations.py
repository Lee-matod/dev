# -*- coding: utf-8 -*-

"""
dev.registrations
~~~~~~~~~~~~~~~~~

Custom classes used to keep track attributes and operations.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import inspect
from datetime import datetime
from typing import TYPE_CHECKING, Any, Literal, Callable, Coroutine, overload

from dev.types import ManagementOperation, Over, OverType

if TYPE_CHECKING:
    from typing_extensions import Concatenate, ParamSpec

    from discord.ext import commands

    from dev import types
    from dev.utils.baseclass import Root

    P = ParamSpec("P")


__all__ = (
    "BaseCommandRegistration",
    "BaseRegistration",
    "CommandRegistration",
    "ManagementRegistration",
    "SettingRegistration"
)


class BaseCommandRegistration:
    def __init__(self, __command: types.Command, /) -> None:
        self.command: types.Command = __command
        self.callback: Callable[
            Concatenate[commands.Cog | None, commands.Context[types.Bot], P], Coroutine[Any, Any, Any]
        ] = __command.callback  # type: ignore
        self.qualified_name: str = __command.qualified_name
        try:
            lines, line_no = inspect.getsourcelines(__command.callback)
        except OSError:
            self.source: str = ""
        else:
            self.source: str = "".join(lines)
            self.line_no: int = line_no - 1

    def to_command(self) -> CommandRegistration:
        return CommandRegistration(
            self.command,
            Over.OVERWRITE,  # Technically an overwrite because it's implemented in the source code
            source=self.source
        )


class BaseRegistration:
    def __init__(self) -> None:
        self.created_at: str = datetime.utcnow().strftime("%b %d, %Y at %H:%M:%S UTC")
        self.timestamp: int = round(datetime.utcnow().timestamp())

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} created_at={self.created_at} timestamp={self.timestamp}>"


class ManagementRegistration(BaseRegistration):
    @overload
    def __init__(self, directory: str, operation_type: Literal[ManagementOperation.RENAME], other: str) -> None:
        ...

    @overload
    def __init__(
            self,
            directory: str,
            operation_type: Literal[ManagementOperation.CREATE] |
                            Literal[ManagementOperation.EDIT] |
                            Literal[ManagementOperation.DELETE] |
                            Literal[ManagementOperation.UPLOAD]
    ):
        ...

    def __init__(self, directory: Any, operation_type: Any, other: Any = None) -> None:
        super().__init__()
        self.directory: str = directory
        self.operation_type: ManagementOperation = operation_type
        if operation_type is ManagementOperation.RENAME and other is None:
            raise TypeError("other is a required positional or keyword argument that is missing")
        self.other: str | None = other

    def __str__(self) -> str:
        if self.operation_type is ManagementOperation.RENAME:
            return f"Renamed `{self.directory}` to `{self.other}`"
        return f"{self.operation_type.name}".title() + f"ed `{self.directory}`"

    @property
    def name(self) -> str:
        return "/" + self.directory.split("/")[-1]


class CommandRegistration(BaseRegistration):
    def __init__(self, __command: types.Command, register_type: Over, /, *, source: str = "") -> None:
        super().__init__()
        self.command: commands.Command[Root, ..., Any] | commands.Group[Root, ..., Any] = __command
        self.register_type: Over = register_type
        self.over_type: OverType = OverType.COMMAND
        self.callback: Callable[
            Concatenate[commands.Cog | None, commands.Context[types.Bot], P], Coroutine[Any, Any, Any]  # type: ignore
        ] = __command.callback  # type: ignore
        self.qualified_name: str = __command.qualified_name
        self.source: str = source or inspect.getsource(__command.callback)

    def __str__(self) -> str:
        return f"Command name: {self.qualified_name}"


class SettingRegistration(BaseRegistration):
    def __init__(self, default_settings: dict[str, Any], new_settings: dict[str, Any], /) -> None:
        super().__init__()
        self.defaults: dict[str, Any] = default_settings
        self.changed: dict[str, Any] = new_settings
        self.register_type: Over = Over.OVERWRITE
        self.over_type: OverType = OverType.SETTING

    def __str__(self) -> str:
        return f"Changed settings: {', '.join(self.changed.keys())}"
