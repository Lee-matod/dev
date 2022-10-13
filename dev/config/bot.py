# -*- coding: utf-8 -*-

"""
dev.config.bot
~~~~~~~~~~~~~~

Direct bot reconfiguration and attributes manager.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

import discord
from discord.ext import commands

from dev.handlers import optional_raise

from dev.utils.baseclass import Root, root
from dev.utils.functs import all_commands, send
from dev.utils.utils import escape, plural

if TYPE_CHECKING:
    from dev import types


class PermissionsSelector(discord.ui.View):
    options = [
        discord.SelectOption(
            label="General",
            value="general",
            description="All 'General' permissions from the official Discord UI.",
            default=True
        ),
        discord.SelectOption(
            label="All Channel",
            value="all_channel",
            description="All channel-specific permissions."
        ),
        discord.SelectOption(
            label="Membership",
            value="membership",
            description="All 'Membership' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Text",
            value="text",
            description="All 'Text' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Voice",
            value="voice",
            description="All 'Voice' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Stage",
            value="stage",
            description="All 'Stage Channel' permissions from the official Discord UI."
        ),
        discord.SelectOption(
            label="Stage Moderator",
            value="stage_moderator",
            description="All permissions for stage moderators."
        ),
        discord.SelectOption(
            label="Elevated",
            value="elevated",
            description="All permissions that require 2FA (2 Factor Authentication)."
        ),
        discord.SelectOption(
            label="Advanced",
            value="advanced",
            description="All 'Advanced' permissions from the official Discord UI."
        )
    ]

    def __init__(self, target: discord.Member, channel: Optional[types.Channel] = None):
        super().__init__()
        self.user_target: discord.Member = target
        self.channel_target: Optional[types.Channel] = channel

    @discord.ui.select(options=options)
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        for option in select.options:
            if option.value != select.values[0]:
                option.default = False
            else:
                option.default = True
        permissions = ["```ansi", *self.sort_perms(select.values[0]), "```"]
        await interaction.response.edit_message(
            embed=discord.Embed(description="\n".join(permissions), color=discord.Color.blurple()),
            view=self
        )

    def sort_perms(self, permission: str):
        perms = getattr(discord.Permissions, permission)()
        for perm, value in perms:
            if not value:
                continue
            if self.channel_target is not None:
                toggled = dict(self.channel_target.permissions_for(self.user_target)).get(perm)
                yield f"\u001b[1;37m{perm.replace('_', ' ').title():26}\u001b[0;{'32' if toggled else '31'}m{toggled}"
            else:
                toggled = dict(self.user_target.guild_permissions).get(perm)
                yield f"\u001b[1;37m{perm.replace('_', ' ').title():26}\u001b[0;{'32' if toggled else '31'}m{toggled}"


class RootBot(Root):

    @root.group(name="bot", parent="dev", global_use=True, invoke_without_command=True)
    async def root_bot(self, ctx: commands.Context):
        """Get a briefing on some bot information."""
        embed = discord.Embed(
            title=self.bot.user,
            description=self.bot.description or '',
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        mapping = {True: "enabled", False: "disabled", None: "unknown"}
        bot_field = ""
        visibility_field = (f"This bot can see {plural(len(self.bot.guilds), 'guild')}, "
                            f"{plural(len([c for c in self.bot.get_all_channels() if not isinstance(c, discord.CategoryChannel)]), 'channel')} "
                            f"and {plural(len(self.bot.users), 'account')}, "
                            f"{len([user for user in self.bot.users if not user.bot])} of which are users.")
        commands_field = (f"There is a total of {len(all_commands(self.bot.commands))} commands "
                          f"and {len(self.bot.extensions)} loaded {plural(len(self.bot.extensions), 'extension', False)}.")
        information_field = (f"This bot is running with an average websocket latency of {round(self.bot.latency * 1000, 2)}ms. "
                             f"Members intent is {mapping.get(self.bot.intents.members)}, "
                             f"message content intent is {mapping.get(self.bot.intents.message_content)} "
                             f"and presences intent is {mapping.get(self.bot.intents.presences)}.")
        if self.bot.owner_ids:
            bot_field += (f"<@!{'>, <@!'.join(f'{owner}' for owner in self.bot.owner_ids)}> are the owners of this bot. "
                          f"The prefix of this bot is `{escape(ctx.prefix)}` "
                          f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                          f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) ")
        elif self.bot.owner_id:
            bot_field += (f"<@!{self.bot.owner_id}> is the owner of this bot. "
                          f"The prefix of this bot is `{escape(ctx.prefix)}` "
                          f"(case insensitive is {mapping.get(self.bot.case_insensitive)} "
                          f"and strip after prefix is {mapping.get(self.bot.strip_after_prefix)}) ")
        if isinstance(self.bot, commands.AutoShardedBot):
            bot_field += f"and it's automatically sharded: shards {self.bot.shard_id} of {self.bot.shard_count} "
        elif self.bot.shard_count:
            bot_field += f"and it's manually sharded: shards {self.bot.shard_id} of {self.bot.shard_count} "
        else:
            bot_field += "and it's not sharded."
        embed.add_field(name="Bot", value=bot_field, inline=False)
        embed.add_field(name="Visibility", value=visibility_field, inline=False)
        embed.add_field(name="Commands", value=commands_field, inline=False)
        embed.add_field(name="Information", value=information_field, inline=False)
        await send(ctx, embed)

    @root.command(name="perms", parent="dev bot", aliases=["permissions"])
    async def root_bot_here(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        """Show which permissions the bot has.
        A text channel may be optionally passed to check for permissions in the given channel.
        """
        view = PermissionsSelector(ctx.me, channel)
        await send(
            ctx,
            discord.Embed(
                description="\n".join(["```ansi", *view.sort_perms('general'), "```"]),
                color=discord.Color.blurple()
            ),
            view
        )

    @root.command(name="reload", parent="dev bot")
    async def root_bot_reload(self, ctx: commands.Context, *cogs: str):
        """Reload all or a specific set of bot cog(s).
        When adding specific cogs, each extension must be separated but a blank space.
        """
        if not cogs:
            successful = []
            unsuccessful = []
            start = time.perf_counter()
            for ext in list(self.bot.extensions):
                try:
                    await self.bot.reload_extension(ext)
                    successful.append(ext)
                except commands.ExtensionError as e:
                    unsuccessful.append(f"{ext} ‒ {e}")
            end = time.perf_counter()
            reloaded_cogs = ("☑ " + "\n☑ ".join(successful) if successful else "") + \
                            ("\n❌ " + "\n❌ ".join(unsuccessful) if unsuccessful else "")
            embed = discord.Embed(
                title=f"Reloaded {plural(len(successful), 'Cog')}",
                description=reloaded_cogs.strip("\n"),
                color=discord.Color.blurple()
            )
            embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
            return await send(ctx, embed)

        successful = []
        unsuccessful = []
        start = time.perf_counter()
        for cog in cogs:
            try:
                await self.bot.reload_extension(cog)
                successful.append(cog)
            except commands.ExtensionError as e:
                unsuccessful.append(f"{cog} ‒ {e}")
        end = time.perf_counter()
        reloaded_cogs = ("☑ " + "\n☑ ".join(successful) if successful else "") + \
                        ("❌ " + "\n❌ ".join(unsuccessful) if unsuccessful else '')
        embed = discord.Embed(
            title=f"Reloaded {plural(len(successful), 'Cog')}",
            description=reloaded_cogs,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Reloading took {end - start:.3f}s.")
        return await send(ctx, embed)

    @root.command(name="enable", parent="dev bot", require_var_positional=True)
    async def root_bot_enable(self, ctx: commands.Context, *, command_name: str):
        """Enable a command.
        For obvious reasons, it is not recommended to disable this command using `dev bot disable`.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await send(ctx, f"Command `{command_name}` not found.")
        if command.enabled:
            return await send(ctx, f"Command `{command_name}` is already enabled.")
        command.enabled = True
        await ctx.message.add_reaction("☑")

    @root.command(name="disable", parent="dev bot", require_var_positional=True)
    async def root_bot_disable(self, ctx: commands.Context, *, command_name: str):
        """Disable a command.
        For obvious reasons, it is not recommended to disable the `dev bot enable` command.
        """
        command = self.bot.get_command(command_name)
        if not command:
            return await send(ctx, f"Command `{command_name}` not found.")
        elif command.name.startswith("dev"):
            return await send(ctx, "Cannot disable dev commands.")
        elif not command.enabled:
            return await send(ctx, f"Command `{command_name}` is already disabled.")
        command.enabled = False
        await ctx.message.add_reaction("☑")

    @root.command(name="close", parent="dev bot")
    async def root_bot_close(self, ctx: commands.Context):
        """Close the bot."""
        await ctx.message.add_reaction("👋")
        await self.bot.close()

    @root_bot.error
    async def root_bot_error(self, ctx: commands.Context, exception: commands.CommandError):
        if isinstance(exception, commands.TooManyArguments):
            return await send(
                ctx,
                f"`{ctx.invoked_with}` has no subcommand `{ctx.message.content.removeprefix(ctx.prefix + ctx.invoked_with)}`."
            )
        optional_raise(ctx, exception)
