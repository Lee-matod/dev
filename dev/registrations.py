# -*- coding: utf-8 -*-

"""
dev.registrations
~~~~~~~~~~~~~~~~~

Custom classes used to keep track of overrides and overwrites.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


import inspect
from typing import Any, Dict, Literal
from datetime import datetime

from discord.ext import commands

from dev.types import AnyCommand, Callback


__all__ = (
    "BaseCommandRegistration",
    "BaseRegistration",
    "CommandRegistration",
    "SettingRegistration"
)


class BaseCommandRegistration(commands.Command):
    def __init__(self, __command: AnyCommand, /):
        super().__init__(__command.callback, **__command.__original_kwargs__)
        self.source: str = inspect.getsource(__command.callback)

    def __repr__(self):
        return f"<BaseCommandRegistration command={self} qualified_name={self.qualified_name}>"


class BaseRegistration:
    def __init__(self, register_type: Literal["override", "overwrite"], /, *, over_type: Literal["command", "setting"]):
        if register_type.lower() not in ("override", "overwrite"):
            raise ValueError(f"Invalid register type submitted: {register_type!r}")
        if over_type.lower() not in ("command", "setting"):
            raise ValueError(f"Invalid over type submitted: {over_type!r}")
        self.register_type: str = register_type.lower()
        self.over_type: str = over_type.lower()
        self.created_at: str = datetime.utcnow().strftime("%b %d, %Y at %H:%M:%S UTC")

    def __repr__(self):
        return f"<BaseRegistration register_type={self.register_type} created_at={self.created_at} over_type={self.over_type}>"


class CommandRegistration(BaseRegistration):
    def __init__(self, __command: AnyCommand, register_type: Literal["override", "overwrite"], /, **kwargs):
        super().__init__(register_type, over_type="command")
        self.command: AnyCommand = __command
        self.callback: Callback = __command.callback
        self.qualified_name: str = __command.qualified_name
        self.source: str = kwargs.get("source") or inspect.getsource(__command.callback)

    def __repr__(self) -> str:
        return f"<CommandRegistration qualified_name={self.qualified_name} {repr(super())}>"

    def __str__(self):
        return f"Command name: {self.qualified_name}"


class SettingRegistration(BaseRegistration):
    def __init__(self, default_settings: Dict[str, Any], new_settings: Dict[str, Any], /):
        super().__init__("overwrite", over_type="setting")
        self.defaults: Dict[str, Any] = default_settings
        self.changed: Dict[str, Any] = new_settings

    def __repr__(self):
        return f"<SettingRegistration> defaults={self.defaults} changed={self.changed}"

    def __str__(self):
        return f"Changed settings: {', '.join(self.changed.keys())}"
