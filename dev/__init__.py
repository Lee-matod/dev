# -*- coding: utf-8 -*-

"""
dev
~~~

A simple debugging, editing and testing extension for discord.py.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from dev.__main__ import *
from dev.handlers import *

from dev.utils.utils import *
from dev.utils.functs import *
from dev.utils.startup import *
from dev.utils.baseclass import *


__all__ = (
    "Command",
    "Group",
    "StringCodeblockConverter",
    "VirtualVarReplacer",
    "is_owner",
    "local_globals",
    "Root",
    "root",
    "send",
    "settings"
)