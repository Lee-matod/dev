# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
import io
import ast
import inspect
import contextlib

import discord
from discord.ext import commands
from typing import Dict, Any, AsyncGenerator, Optional

from dev.converters import __previous__
from dev.handlers import ExceptionHandler, replace_vars

from dev.utils.startup import Settings
from dev.utils.functs import clean_code, send
from dev.utils.baseclass import root, Root, GlobalLocals

# TODO: I have to reword this
# cause omg was it annoying to eval stuff

class RootPython(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)


