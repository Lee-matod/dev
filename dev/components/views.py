# -*- coding: utf-8 -*-

"""
dev.components.views
~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.View` related classes.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from dev.utils.startup import Settings
from dev.types import InteractionResponseType

from dev.utils.functs import interaction_response

if TYPE_CHECKING:
    from dev.interpreters import Process


__all__ = (
    "SigKill",
)


class SigKill(discord.ui.View):
    def __init__(self, process: Process, /):
        super().__init__()
        self.session: ShellSession = process._Process__session  # type: ignore
        self.process: Process = process

    @discord.ui.button(label="Kill", emoji="\u26D4", style=discord.ButtonStyle.danger)
    async def signalkill(self, interaction: discord.Interaction, button: discord.ui.Button[SigKill]):
        self.process.process.kill()
        self.process.process.terminate()
        self.process.force_kill = True
        await interaction_response(
            interaction,
            InteractionResponseType.EDIT,
            self.session.raw.replace(Settings.PATH_TO_FILE, "~"),
            view=None,
            paginator=self.session.paginator
        )