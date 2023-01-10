# -*- coding: utf-8 -*-

"""
dev.components.buttons
~~~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.Button` related classes.

:copyright: Copyright 2023 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import discord

from dev.types import InteractionResponseType
from dev.components.modals import SettingEditor
from dev.components.views import AuthoredView

from dev.utils.functs import interaction_response
from dev.utils.startup import Settings

__all__ = (
    "SettingsToggler",
)


class SettingsToggler(discord.ui.Button[AuthoredView]):
    def __init__(self, setting: str, author: int, *, label: str) -> None:
        super().__init__(label=label)
        self.author: int = author
        self.setting: str = setting
        if label in ("Allow Global Uses", "Invoke on Edit"):
            self.style = discord.ButtonStyle.green if getattr(Settings, setting) else discord.ButtonStyle.red
        else:
            self.style = discord.ButtonStyle.blurple

    @classmethod
    def add_buttons(cls, view: AuthoredView, /) -> None:
        for setting in [setting for setting in Settings.kwargs.keys()]:
            fmt = " ".join(word.lower() if len(word) <= 2 else word.title() for word in setting.split("_"))
            view.add_item(cls(setting, view.author, label=fmt))

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.setting not in [sett for sett, ann in Settings.mapping.items() if ann == bool]:
            label = self.label
            if label is not None:
                return await interaction.response.send_modal(
                    SettingEditor(label.replace(" ", "_").lower())
                )
            return await interaction_response(
                interaction,
                InteractionResponseType.SEND,
                "Something broke, this should not have happened.",
                ephemeral=True
            )
        setting = self.setting.lower().replace(" ", "_")
        if self.style == discord.ButtonStyle.green:
            setattr(Settings, setting, False)
            self.style = discord.ButtonStyle.red
        else:
            setattr(Settings, setting, True)
            self.style = discord.ButtonStyle.green
        view = AuthoredView(self.author)
        self.add_buttons(view)
        await interaction_response(
            interaction,
            InteractionResponseType.EDIT,
            view
        )
