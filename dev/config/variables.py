# -*- coding: utf-8 -*-

"""
dev.config.variables
~~~~~~~~~~~~~~~~~~~~

A virtual variable manager directly implemented to the dev extension.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from discord.ext import commands

from dev.converters import LiteralModes
from dev.components import VariableModalSender

from dev.utils.functs import send
from dev.utils.baseclass import Root, root

if TYPE_CHECKING:
    from dev import types


class RootVariables(Root):

    @root.command(name="variable", parent="dev", aliases=["variables", "vars", "var"])
    async def root_variable(
            self,
            ctx: commands.Context[types.Bot],
            mode: LiteralModes[
                Literal["~", "all", "content", "create", "del", "delete", "edit", "exists", "new", "replace", "value"]
            ],
            *,
            name: str | None = None
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
        if mode in ["new", "create"]:  # pyright: ignore [reportUnnecessaryContains]
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params.get("name"))  # type: ignore
            glob, loc = Root.scope.keys()
            if name in [*glob, *loc]:
                return await send(ctx, f"A variable called `{name}` already exists.")
            await send(ctx, VariableModalSender(name, True, ctx.author))

        elif mode in ["delete", "del"]:  # pyright: ignore [reportUnnecessaryContains]
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params.get("name"))  # type: ignore
            if Root.scope.get(name, False):
                del Root.scope[name]
                return await send(ctx, f"Successfully deleted the variable `{name}`.")
            await send(ctx, f"No variable called `{name}` found.")

        elif mode in ["edit", "replace"]:  # pyright: ignore [reportUnnecessaryContains]
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params.get("name"))  # type: ignore
            glob, loc = Root.scope.keys()
            if name not in [*glob, *loc]:
                return await send(ctx, f"No variable called `{name}` found.")
            glob, loc = Root.scope[name]
            await send(ctx, VariableModalSender(name, False, ctx.author, glob or loc))

        elif mode in ["all", "~"]:  # pyright: ignore [reportUnnecessaryContains]
            variables = '\n'.join(f"+ {var}" for var in Root.scope.keys()) if Root.scope else "- No variables found."
            await send(ctx, f"```diff\n{variables}\n```")

        elif mode == "exists":  # pyright: ignore [reportUnnecessaryContains, reportUnnecessaryComparison]
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params.get("name"))  # type: ignore
            glob, loc = Root.scope.keys()
            if name not in [*glob, *loc]:
                return await ctx.message.add_reaction("\u274c")
            await ctx.message.add_reaction("\u2611")

        elif mode in ["content", "value"]:  # pyright: ignore [reportUnnecessaryContains]
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params.get("name"))  # type: ignore
            glob, loc = Root.scope.keys()
            if name not in [*glob, *loc]:
                return await send(ctx, f"No variable called `{name}` found.")
            glob, loc = Root.scope[name]
            await ctx.author.send(f"**{name}:** {glob or loc}")
