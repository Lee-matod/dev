# -*- coding: utf-8 -*-

"""
dev.config.variables
~~~~~~~~~~~~~~~~~~~~

A virtual variable manager directly implemented to the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""

import discord

from typing import Optional
from discord.ext import commands

from dev.utils.functs import send
from dev.utils.utils import local_globals
from dev.utils.baseclass import root, Root


class ValueSubmitter(discord.ui.Modal):
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph)

    def __init__(self, name: str, new: bool, default: str):
        super().__init__(title="Value Submitter")
        self.name = name
        self.new = new
        self.value.default = default

    async def on_submit(self, interaction: discord.Interaction):
        local_globals[self.name] = self.value.value
        await interaction.response.send_message(f"Successfully {'created a new variable called' if self.new else 'edited'} `{self.name}`")


class ModalSubmitter(discord.ui.View):
    def __init__(self, name: str, new: bool, author: discord.Member, default: str = None):
        super().__init__()
        self.name = name
        self.new = new
        self.author = author
        self.default = default

    @discord.ui.button(label="Submit Variable Value", style=discord.ButtonStyle.gray)
    async def submit_value(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.user.id != self.author.id:
            return
        await interaction.response.send_modal(ValueSubmitter(self.name, self.new, self.default))
        button.disabled = True
        await interaction.message.edit(view=self)


class RootVariables(Root):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @root.command(name="variable", parent="dev", version=1, aliases=["variables", "vars", "var"])
    async def root_variable(self, ctx: commands.Context, mode: str, name: Optional[str]):
        """A virtual variable manager.
        This allows you to create temporary variables that can later be used as placeholder texts if you want to hide certain things from the public.
        Note that all variables created using this manager will later be destroyed once the bot restarts.
        **Modes:**
        `content` = Sends the content of the variable to ctx.author.
        `exists` = Check if a variable with the given name exists. The bot reacts with a checkmark if it does, else with an X.
        `all`|`~` = Sends a list of all currently existing tags.
        `edit`|`replace` = Edit the contents of an already existing variable.
        `delete`|`del` = Delete an already existing variable.
        `new`|`create` = Create a new variable.
        """
        if mode in ["new", "create"]:
            if name in local_globals:
                return await send(ctx, f"A variable called `{name}` already exists.")
            await send(ctx, "\u200b", view=ModalSubmitter(name, True, ctx.author))

        elif mode in ["delete", "del"]:
            if local_globals.get(name, False):
                del local_globals[name]
                return await send(ctx, f"Successfully deleted the variable `{name}`.")
            await send(ctx, f"No variable called `{name}` found.")

        elif mode in ["edit", "replace"]:
            if name not in local_globals:
                return await send(ctx, f"No variable called `{name}` found.")
            await send(ctx, "\u200b", view=ModalSubmitter(name, False, ctx.author, local_globals[name]))

        elif mode in ["all", "~"]:
            variables = '\n'.join(f"+ {var}" for var in local_globals) if local_globals else "- No variables found."
            await send(ctx, f"```diff\n{variables}\n```")

        elif mode == "exists":
            if name not in local_globals:
                return await ctx.message.add_reaction("❌")
            await ctx.message.add_reaction("☑")

        elif mode == "content":
            if name not in local_globals:
                return await send(ctx, f"No variable called `{name}` found.")
            await ctx.author.send(f"**{name}:** {local_globals[name]}")

        else:
            await ctx.message.add_reaction("❓")