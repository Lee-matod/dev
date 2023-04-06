# -*- coding: utf-8 -*-

"""
dev.plugins.environment
~~~~~~~~~~~~~~~~~~~~~~~

A virtual environment variable manager directly implemented to this extension.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from discord.ext import commands

from dev import root
from dev.components import ModalSender, EnvValueSubmitter
from dev.utils.functs import send

if TYPE_CHECKING:
    from dev import types


class RootEnvironment(root.Plugin):
    """Environment variables manager"""

    @root.command("environment", parent="dev", aliases=["env"])
    async def root_environment(
        self,
        ctx: commands.Context[types.Bot],
        mode: Literal["all", "content", "create", "delete", "edit", "exists", "new", "remove", "replace", "value",],
        *,
        name: str | None = None,
    ):
        """A virtual environment variable manager.

        This allows you to create temporary variables that can later be used as placeholder texts.
        Note that all variables created using this manager will later be destroyed.

        Parameters
        ----------
        mode: Literal["all", "content", "delete", "edit", "exists", "new", "remove", "replace", "value"]
            What should be done with the given variable name, if any.
        name: Optional[:class:`str`]
            The name of the variable to edit. `all` does not require this parameter to be given.
        """
        if mode in ["new", "create"]:
            if name is None:
                raise commands.MissingRequiredArgument(ctx.command.clean_params["name"])  # type: ignore
            if name in self.scope:
                return await send(ctx, f"A variable called `{name}` already exists.")
            await send(ctx, ModalSender(EnvValueSubmitter(name, True), ctx.author, label="Submit Variable Value"))

        elif mode in ["delete", "remove"]:
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
                    EnvValueSubmitter(name, False, self.scope[name]), ctx.author, label="Submit Variable Value"
                ),
            )

        elif mode in ["all"]:
            variables = self.scope.keys()
            if not variables:
                return await send(ctx, "No variables have been created yet.")
            await send(ctx, f"\n".join(variables))

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
