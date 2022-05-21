# -*- coding: utf-8 -*-

"""
dev.experimental.python
~~~~~~~~~~~~~~~~~~~~~~~

Direct evaluation or execution of Python code.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""


from discord.ext import commands

from dev.utils.baseclass import root, Root

# TODO: I have to reword this
# cause omg was it annoying to eval stuff

class RootPython(Root):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        
