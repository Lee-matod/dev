# -*- coding: utf-8 -*-

"""
dev.registrations
~~~~~~~~~~~~~~~~~

Custom classes used to keep track attributes and operations.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from datetime import datetime
import inspect
from typing import Any, Dict, Optional

from dev import types
from dev.types import Callback, ManagementOperation, Over, OverType


__all__ = (
    "BaseCommandRegistration",
    "BaseRegistration",
    "CommandRegistration",
    "ManagementRegistration",
    "SettingRegistration"
)


class BaseCommandRegistration:
    def __init__(self, __command: types.Command, /):
        self.command: types.Command = __command
        self.callback: Callback = __command.callback
        self.qualified_name: str = __command.qualified_name
        try:
            lines, line_no = inspect.getsourcelines(__command.callback)
        except OSError:
            pass
        else:
            self.source: str = "".join(lines)
            self.line_no: int = line_no - 1


class BaseRegistration:
    def __init__(self):
        self.created_at: str = datetime.utcnow().strftime("%b %d, %Y at %H:%M:%S UTC")
        self.timestamp: int = round(datetime.utcnow().timestamp())

    def __repr__(self):
        return f"<{self.__class__.__name__} created_at={self.created_at} timestamp={self.timestamp}>"


class ManagementRegistration(BaseRegistration):
    def __init__(self, directory: str, operation_type: ManagementOperation, other: Optional[str] = None):
        super().__init__()
        self.directory: str = directory
        self.operation_type: ManagementOperation = operation_type
        if operation_type is ManagementOperation.RENAME and other is None:
            raise TypeError("other is a required positional or keyword argument that is missing")
        self.other: Optional[str] = other

    def __str__(self) -> str:
        if self.operation_type is ManagementOperation.RENAME:
            return f"Renamed `{self.directory}` to `{self.other}`"
        return f"{self.operation_type.name}".title() + f"ed `{self.directory}`"

    @property
    def name(self) -> str:
        return "/" + self.directory.split("/")[-1]


class CommandRegistration(BaseRegistration):
    def __init__(self, __command: types.Command, register_type: Over, /, *, source: str = ""):
        super().__init__()
        self.command: types.Command = __command
        self.register_type: Over = register_type
        self.over_type: OverType = OverType.COMMAND
        self.callback: Callback = __command.callback
        self.qualified_name: str = __command.qualified_name
        self.source: str = source or inspect.getsource(__command.callback)

    def __str__(self):
        return f"Command name: {self.qualified_name}"


class SettingRegistration(BaseRegistration):
    def __init__(self, default_settings: Dict[str, Any], new_settings: Dict[str, Any], /):
        super().__init__()
        self.defaults: Dict[str, Any] = default_settings
        self.changed: Dict[str, Any] = new_settings
        self.register_type: Over = Over.OVERWRITE
        self.over_type: OverType = OverType.SETTING

    def __str__(self):
        return f"Changed settings: {', '.join(self.changed.keys())}"
