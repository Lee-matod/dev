# -*- coding: utf-8 -*-

"""
dev.config.variables
~~~~~~~~~~~~~~~~~~~~

A virtual variable manager directly implemented to the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from typing import Literal, Optional

import discord
from discord.ext import commands

from dev.converters import LiteralModes

from dev.utils.functs import send
from dev.utils.baseclass import Root, root


class ValueSubmitter(discord.ui.Modal):
    value = discord.ui.TextInput(label="Value", style=discord.TextStyle.paragraph)

    def __init__(self, name: str, new: bool, default: str):
        self.value.default = default
        super().__init__(title="Value Submitter")
        self.name = name
        self.new = new

    async def on_submit(self, interaction: discord.Interaction):
        Root.scope.update({self.name: self.value.value})
        await interaction.response.edit_message(
            content=f"Successfully {'created a new variable called' if self.new else 'edited'} `{self.name}`",
            view=None
        )


class ModalSubmitter(discord.ui.View):
    def __init__(self, name: str, new: bool, author: discord.Member, default: str = None):
        super().__init__()
        self.name = name
        self.new = new
        self.author = author
        self.default = default

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return self.author == interaction.user

    @discord.ui.button(label="Submit Variable Value", style=discord.ButtonStyle.gray)
    async def submit_value(self, interaction: discord.Interaction, _):  # 'button' is not being used
        await interaction.response.send_modal(ValueSubmitter(self.name, self.new, self.default))


class RootVariables(Root):

    @root.command(name="variable", parent="dev", aliases=["variables", "vars", "var"])
    async def root_variable(
            self,
            ctx: commands.Context,
            mode: LiteralModes[
                Literal["~", "all", "content", "create", "del", "delete", "edit", "exists", "new", "replace", "value"]
            ],
            *,
            name: Optional[str] = None
    ):
        """A virtual scope manager.
        This allows you to create temporary variables that can later be used as placeholder texts.
        Note that all variables created using this manager will later be destroyed once the bot restarts.
        **Modes:**
        `content|value` = View the value of the given variable.
        `exists` = Check if a variable with the given name exists.
        `all`|`~` = Sends a list of all currently existing variable names.
        `edit`|`replace` = Edit the contents of an already existing variable.
        `delete`|`del` = Delete an already existing variable.
        `new`|`create` = Create a new variable.
        """
        if mode is None:
            return
        if mode in ["new", "create"]:
            glob, loc = Root.scope.keys()
            if name in [*glob, *loc]:
                return await send(ctx, f"A variable called `{name}` already exists.")
            await send(ctx, ModalSubmitter(name, True, ctx.author))

        elif mode in ["delete", "del"]:
            if Root.scope.get(name, False):
                del Root.scope[name]
                return await send(ctx, f"Successfully deleted the variable `{name}`.")
            await send(ctx, f"No variable called `{name}` found.")

        elif mode in ["edit", "replace"]:
            glob, loc = Root.scope.keys()
            if name not in [*glob, *loc]:
                return await send(ctx, f"No variable called `{name}` found.")
            glob, loc = Root.scope[name]
            await send(ctx, ModalSubmitter(name, False, ctx.author, glob or loc))

        elif mode in ["all", "~"]:
            variables = '\n'.join(f"+ {var}" for var in Root.scope.keys()) if Root.scope else "- No variables found."
            await send(ctx, f"```diff\n{variables}\n```")

        elif mode == "exists":
            glob, loc = Root.scope.keys()
            if name not in [*glob, *loc]:
                return await ctx.message.add_reaction("❌")
            await ctx.message.add_reaction("☑")

        elif mode in ["content", "value"]:
            glob, loc = Root.scope.keys()
            if name not in [*glob, *loc]:
                return await send(ctx, f"No variable called `{name}` found.")
            glob, loc = Root.scope[name]
            await ctx.author.send(f"**{name}:** {glob or loc}")
