# -*- coding: utf-8 -*-

"""
dev.config.variables
~~~~~~~~~~~~~~~~~~~~

A virtual variable manager directly implemented to the dev extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from discord.ext import commands

from dev import root
from dev.components import ModalSender, VariableValueSubmitter
from dev.converters import LiteralModes
from dev.types import Annotated
from dev.utils.functs import send

if TYPE_CHECKING:
    from dev import types


class RootVariables(root.Container):
    """Virtual variables manager"""

    @root.command(name="variable", parent="dev", aliases=["variables", "vars", "var"])
    async def root_variable(
        self,
        ctx: commands.Context[types.Bot],
        mode: Annotated[
            str | None,
            LiteralModes[
                Literal["~", "all", "content", "create", "del", "delete", "edit", "exists", "new", "replace", "value",]
            ],
        ],
        *,
        name: str | None = None,
    ):
        """A virtual scope manager.
        This allows you to create temporary variables that can later be used as placeholder texts.
        Note that all variables created using this manager will later be destroyed.
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
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params["name"])  # type: ignore
            if name in self.scope:
                return await send(ctx, f"A variable called `{name}` already exists.")
            await send(ctx, ModalSender(VariableValueSubmitter(name, True), ctx.author, label="Submit Variable Value"))

        elif mode in ["delete", "del"]:
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params["name"])  # type: ignore
            if self.scope.get(name, False):
                del self.scope[name]
                return await send(ctx, f"Successfully deleted the variable `{name}`.")
            await send(ctx, f"No variable called `{name}` found.")

        elif mode in ["edit", "replace"]:
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params["name"])  # type: ignore
            if name not in self.scope:
                return await send(ctx, f"No variable called `{name}` found.")
            await send(
                ctx,
                ModalSender(
                    VariableValueSubmitter(name, False, self.scope[name]), ctx.author, label="Submit Variable Value"
                ),
            )

        elif mode in ["all", "~"]:
            variables = "\n".join(f"+ {var}" for var in self.scope.keys()) if self.scope else "- No variables found."
            await send(ctx, f"```diff\n{variables}\n```")

        elif mode == "exists":
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params["name"])  # type: ignore
            if name not in self.scope:
                return await ctx.message.add_reaction("\u274c")
            await ctx.message.add_reaction("\u2611")

        elif mode in ["content", "value"]:
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params["name"])  # type: ignore
            if name not in self.scope:
                return await send(ctx, f"No variable called `{name}` found.")
            await ctx.author.send(f"**{name}:** {self.scope[name]}")
