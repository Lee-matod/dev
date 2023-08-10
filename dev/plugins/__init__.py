# -*- coding: utf-8 -*-

"""
dev.plugins
~~~~~~~~~~~

Where all containers are united to a single master cog.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""

from dev.plugins.__main__ import RootCommand
from dev.plugins.environment import RootEnvironment
from dev.plugins.files import RootFiles
from dev.plugins.http import RootHTTP
from dev.plugins.information import RootInformation
from dev.plugins.invoke import RootInvoke
from dev.plugins.management import RootManagement
from dev.plugins.override import RootOverride
from dev.plugins.python import RootPython
from dev.plugins.search import RootSearch
from dev.plugins.shell import RootShell

__all__ = (
    "Dev",
    "RootCommand",
    "RootEnvironment",
    "RootFiles",
    "RootHTTP",
    "RootInformation",
    "RootInvoke",
    "RootManagement",
    "RootOverride",
    "RootPython",
    "RootSearch",
    "RootShell",
)


class Dev(
    RootCommand,
    RootEnvironment,
    RootFiles,
    RootHTTP,
    RootInformation,
    RootInvoke,
    RootManagement,
    RootOverride,
    RootPython,
    RootSearch,
    RootShell,
):
    """The frontend root cog of the dev extension that implements all features."""
