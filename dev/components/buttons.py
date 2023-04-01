# -*- coding: utf-8 -*-

"""
dev.components.buttons
~~~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.Button` related classes.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import discord

from dev.components.modals import SettingsEditor
from dev.components.views import AuthoredMixin
from dev.scope import Settings
from dev.utils.functs import interaction_response

__all__ = ("SettingsToggler",)


class SettingsToggler(discord.ui.Button[AuthoredMixin]):
    def __init__(self, setting: str, author: int | None, *, label: str) -> None:
        super().__init__(label=label)
        self.author: int | None = author
        self.setting: str = setting.upper().replace(" ", "_")
        self._boolean_options = [option.name for option in Settings.__options__.values() if option._type is bool]  # pyright: ignore [reportPrivateUsage]
        print(self.setting, self._boolean_options)
        if label in self._boolean_options:
            self.style = discord.ButtonStyle.green if getattr(Settings, setting) else discord.ButtonStyle.red
        else:
            self.style = discord.ButtonStyle.blurple

    @classmethod
    def from_view(cls, view: AuthoredMixin, /) -> None:
        for setting in Settings.__options__:
            fmt = " ".join(word.lower() if len(word) <= 2 else word.title() for word in setting.split("_"))
            view.add_item(cls(setting, view.author, label=fmt))

    async def callback(self, interaction: discord.Interaction) -> None:
        if self.setting not in self._boolean_options:
            label = self.label
            if label is not None:
                return await interaction.response.send_modal(SettingsEditor(self.setting))
            return await interaction_response(
                interaction,
                discord.InteractionResponseType.channel_message,
                "Something broke, this should not have happened.",
                ephemeral=True,
            )
        setting = self.setting
        if self.style == discord.ButtonStyle.green:
            setattr(Settings, setting, False)
            self.style = discord.ButtonStyle.red
        else:
            setattr(Settings, setting, True)
            self.style = discord.ButtonStyle.green
        view = AuthoredMixin(self.author)
        self.from_view(view)
        await interaction_response(interaction, discord.InteractionResponseType.message_update, view)
