# -*- coding: utf-8 -*-

"""
dev.experimental
~~~~~~~~~~~~~~~~

Testing and debugging commands.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


from dev.experimental.http import *
from dev.experimental.invoke import *
from dev.experimental.python import *


__all__ = (
    "RootExperimental",
    "RootHTTP",
    "RootInvoke",
    "RootPython"
)


class RootExperimental(RootHTTP, RootInvoke, RootPython):
    """The front end experimental cog for the dev extension."""
