# -*- coding: utf-8 -*-

"""
dev.utils.utils
~~~~~~~~~~~~~~~

Basic utilities that will be used with the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

from typing import Any, Dict

__all__ = (
    "MISSING",
    "local_globals"
)

MISSING = ...

local_globals: Dict[Any, Any] = {}
