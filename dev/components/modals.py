# -*- coding: utf-8 -*-

"""
dev.components.modals
~~~~~~~~~~~~~~~~~~~~~

All :class:`discord.ui.Modal` related classes.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import discord

from dev.converters import str_ints
from dev.root import Plugin
from dev.utils.functs import interaction_response
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from dev.components.views import ModalSender

__all__ = ("SettingsEditor", "VariableValueSubmitter")


class VariableValueSubmitter(discord.ui.Modal):
    value: discord.ui.TextInput[ModalSender] = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph)

    def __init__(self, name: str, new: bool, default: str | None = None) -> None:
        self.value.default = default
        super().__init__(title="Value Submitter")
        self.name: str = name
        self.new: bool = new

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        Plugin.scope.update({self.name: self.value.value})
        fmt = "created new variable" if self.new else "edited"
        await interaction.response.edit_message(content=f"Successfully {fmt} `{self.name}`", view=None)


class SettingsEditor(discord.ui.Modal):
    def __init__(self, setting: str) -> None:
        self.setting: str = setting
        self.setting_obj: set[int] | str = getattr(Settings, setting)
        self.item: discord.ui.TextInput[ModalSender] = discord.ui.TextInput(
            label=setting.replace("_", " ").title(),
            default=(", ".join(map(str, self.setting_obj)) if isinstance(self.setting_obj, set) else self.setting_obj),
        )
        super().__init__(title=f"{setting.replace('_', ' ').title()} Editor")
        self.add_item(self.item)

    async def on_submit(self, interaction: discord.Interaction, /) -> None:
        if isinstance(self.setting_obj, set):
            setattr(Settings, self.setting, set(str_ints(self.item.value)))
        #  bool instances are toggleable buttons
        else:
            setattr(Settings, self.setting, self.item.value)
        await interaction_response(interaction, discord.InteractionResponseType.message_update)
