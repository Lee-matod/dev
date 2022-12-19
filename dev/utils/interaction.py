# -*- coding: utf-8 -*-

"""
dev.utils.interaction
~~~~~~~~~~~~~~~~~~~~~

Discord interaction wrappers.

:copyright: Copyright 2022 Lee (Lee-matod)
:license: Licensed under the Apache License, Version 2.0; see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import datetime
import inspect
import shlex
import time
from typing import TYPE_CHECKING, Any, NamedTuple, Union

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING

from dev.converters import str_bool

if TYPE_CHECKING:
    from collections.abc import Sequence

    from discord import (
        VoiceChannel,
        StageChannel,
        TextChannel,
        ForumChannel,
        CategoryChannel,
        Thread,
        PartialMessageable
    )

    from dev import types

    InteractionChannel = Union[
        VoiceChannel,
        StageChannel,
        TextChannel,
        ForumChannel,
        CategoryChannel,
        Thread,
        PartialMessageable
    ]

else:
    InteractionChannel = (
        discord.VoiceChannel,
        discord.StageChannel,
        discord.TextChannel,
        discord.ForumChannel,
        discord.CategoryChannel,
        discord.Thread,
        discord.PartialMessageable
    )

__all__ = (
    "SyntheticInteraction",
    "get_app_command"
)

# I'm not too sure if all of these type hint converters are actually available in app command type hinting, but I
# couldn't be bothered to check
CONVERSIONS = {
    discord.Role: commands.RoleConverter(),
    discord.Member: commands.MemberConverter(),
    discord.User: commands.UserConverter(),
    discord.Color: commands.ColorConverter(),
    discord.Colour: commands.ColourConverter(),
    discord.TextChannel: commands.TextChannelConverter(),
    discord.CategoryChannel: commands.CategoryChannelConverter(),
    discord.Emoji: commands.EmojiConverter(),
    discord.ForumChannel: commands.ForumChannelConverter(),
    discord.abc.GuildChannel: commands.GuildChannelConverter(),
    discord.Guild: commands.GuildConverter(),
    discord.GuildSticker: commands.GuildStickerConverter(),
    discord.Invite: commands.InviteConverter(),
    discord.Message: commands.MessageConverter(),
    discord.PartialEmoji: commands.PartialEmojiConverter(),
    discord.PartialMessage: commands.PartialMessageConverter(),
    discord.ScheduledEvent: commands.ScheduledEventConverter(),
    discord.StageChannel: commands.StageChannelConverter(),
    discord.VoiceChannel: commands.VoiceChannelConverter(),
    discord.Thread: commands.ThreadConverter()
}


def get_app_command(
        content: str,
        app_command_list: list[app_commands.Command[Any, ..., Any]]
) -> app_commands.Command[Any, ..., Any] | None:
    possible_subcommands = content.split()
    app_command_name = possible_subcommands[0]
    possible_subcommands = possible_subcommands[1:]
    app_command = discord.utils.get(app_command_list, name=app_command_name)  # type: ignore
    while isinstance(app_command, discord.app_commands.Group):
        app_command_name = f"{app_command_name} {possible_subcommands[0]}"
        possible_subcommands = possible_subcommands[1:]
        app_command = discord.utils.get(app_command.commands, qualified_name=app_command_name)  # type: ignore
    return app_command


class UnknownInteraction:
    status: int = 404
    reason: str = "Not Found"


class Parameter(NamedTuple):
    name: str
    default: Any
    annotation: Any
    argument: str


class InvalidChoice(app_commands.AppCommandError):
    def __init__(self, parameter: Parameter, choices: list[app_commands.Choice[str | int | float]]) -> None:
        super().__init__(
            f"Choice value {parameter.argument!r} "
            f"passed to {parameter.name} "
            f"not found as a valid choice: {', '.join([choice.name for choice in choices])}"
        )


class SyntheticInteraction:
    def __init__(self, context: commands.Context[types.Bot], command: app_commands.Command[Any, ..., Any]) -> None:
        self._context: commands.Context[types.Bot] = context
        self._command: app_commands.Command[Any, ..., Any] = command
        self._created_at: int = round(time.time())
        self._interaction_response: InteractionResponse = InteractionResponse(self)
        self._unknown_interaction: bool = False

        # There are a few attributes that just cannot be obtained using the Context,
        # so I'll just leave them with a static value.
        # These attributes might be the case for some nasty errors.
        self.id: int = 0
        self.type: discord.InteractionType = discord.InteractionType.application_command
        self.data: dict[str, Any] | None = None
        self.token: str = ""
        self.version: int = 1
        self.channel_id: int = context.channel.id
        self.guild_id: int | None = context.guild.id if context.guild is not None else None
        self.application_id: int | None = self._context.bot.application_id
        self.locale: discord.Locale = discord.Locale("en-US")
        self.guild_locale: discord.Locale | None = None
        self.message: discord.Message = context.message
        self.user: types.User = context.author
        self.extras: dict[str, Any] = {}
        self.command_failed: bool = False

        # Protected attributes won't be defined, but we still need to keep track of the original response regardless
        self._original_response: discord.Message | None = None

    async def get_parameters(self, arguments: list[str], ignore_params: int) -> dict[str, Any]:
        signature = inspect.signature(self._command.callback)
        parameters = [
            Parameter(name=name, annotation=param.annotation, argument=argument, default=param.default)
            for argument, (name, param) in zip(arguments, list(signature.parameters.items())[ignore_params:])
        ]
        kwargs: dict[str, Any] = {}
        for param in parameters:
            if base_converter := CONVERSIONS.get(param.annotation, False):
                kwargs[param.name] = await base_converter.convert(self._context, param.argument)  # type: ignore
            elif choices := self._command.get_parameter(param.name).choices:  # type: ignore
                for choice in choices:
                    if choice.name == param.argument:
                        kwargs[param.name] = choice.value
                        break
                else:
                    raise InvalidChoice(param, choices)
            elif inspect.isclass(param.annotation):
                if issubclass(param.annotation, app_commands.Transformer):
                    kwargs[param.name] = await param.annotation().transform(self, param.argument)  # type: ignore
                try:
                    kwargs[param.name] = param.annotation(param.argument)  # type: ignore
                except TypeError:
                    kwargs[param.name] = param.argument
            elif not inspect.isclass(param.annotation):
                if isinstance(param.annotation, app_commands.Transformer):
                    kwargs[param.name] = await param.annotation.transform(self, param.argument)  # type: ignore
            elif param.annotation is None and param.default not in (inspect.Parameter.empty, None):
                # We should never run into this section, but might as well deal with it
                kwargs[param.name] = type(param.default)(param.argument)
            elif param.annotation == bool:
                kwargs[param.name] = str_bool(param.argument)
            else:
                kwargs[param.name] = param.argument
        return kwargs

    async def invoke(
            self,
            context: commands.Context[types.Bot],
            /
    ) -> None:  # Match signature of commands.Command.invoke
        if not await self._command._check_can_run(self):  # type: ignore  # pyright: ignore [reportPrivateUsage]
            raise app_commands.CheckFailure(f"The check functions for command {self._command.qualified_name!r} failed.")
        arguments = context.message.content.removeprefix(f"/{self._command.qualified_name} ")
        if len(self._command.parameters) == 1:
            arguments = [arguments]
        else:
            arguments = shlex.split(arguments)
        # Pass in interaction and check if the command is inside a cog/group
        required = (self,) if self._command.binding is None else (self._command.binding, self)
        parameters = await self.get_parameters(arguments, len(required))
        context.bot.loop.create_task(self._wait_for_response())
        await self._command.callback(*required, **parameters)  # type: ignore

    async def reinvoke(
            self,
            context: commands.Context[types.Bot],
            /,
            *,
            call_hooks: bool = False
    ) -> None:  # Match signature of commands.Command.reinvoke
        arguments = context.message.content.removeprefix(f"/{self._command.qualified_name}")
        if len(self._command.parameters) == 1:
            arguments = [arguments]
        else:
            arguments = shlex.split(arguments)
        # Pass in interaction and check if the command is inside a cog/group
        required = (self,) if self._command.binding is None else (self._command.binding, self)
        parameters = await self.get_parameters(arguments, len(required))
        context.bot.loop.create_task(self._wait_for_response())
        await self._command.callback(*required, **parameters)  # type: ignore

    async def _wait_for_response(self) -> None:
        await asyncio.sleep(3)  # simulate maximum of 3 seconds for a response
        if self._interaction_response._response_type is None:  # pyright: ignore [reportPrivateUsage]
            # The bot did not respond to the interaction, so we have to somehow tell the user that it took too long.
            # By this time, the interaction would become unknown, so we have to simulate that too
            self._unknown_interaction = True
            await self._context.message.add_reaction("\u2757")

    @property  # type: ignore
    def __class__(self) -> type[discord.Interaction]:
        return discord.Interaction

    def __instancecheck__(self, instance: Any) -> bool:
        return type(instance) is self.__class__

    def __subclasscheck__(self, subclass: Any) -> bool:
        return subclass == self.__class__

    @property
    def client(self) -> types.Bot:
        return self._context.bot

    @property
    def guild(self) -> discord.Guild | None:
        return self._context.guild

    @discord.utils.cached_slot_property("_cs_channel")
    def channel(self) -> InteractionChannel | None:
        if isinstance(self._context.channel, InteractionChannel):
            return self._context.channel  # type: ignore

    @property
    def permissions(self) -> discord.Permissions:
        return self._context.author.guild_permissions  # type: ignore

    @property
    def app_permissions(self) -> discord.Permissions:
        return self._context.guild.me.guild_permissions  # type: ignore

    @discord.utils.cached_slot_property("_cs_namespace")
    def namespace(self) -> app_commands.Namespace:
        return app_commands.Namespace(self, {}, [])  # type: ignore

    @discord.utils.cached_slot_property("_cs_command")
    def command(self) -> app_commands.Command[Any, ..., Any] | app_commands.ContextMenu | None:
        return self._command

    @discord.utils.cached_slot_property("_cs_response")
    def response(self) -> InteractionResponse:
        return self._interaction_response

    @discord.utils.cached_slot_property("_cs_followup")
    def followup(self) -> SyntheticWebhook:
        return SyntheticWebhook(self._context)

    @property
    def created_at(self) -> datetime.datetime:
        return discord.utils.snowflake_time(self._created_at)

    @property
    def expires_at(self) -> datetime.datetime:
        return self.created_at + datetime.timedelta(minutes=15)

    def is_expired(self) -> bool:
        return discord.utils.utcnow() >= self.expires_at

    async def original_response(self) -> discord.Message:
        if self._original_response is None:
            return self._context.message
        return self._original_response

    async def edit_original_response(self, **kwargs: Any) -> discord.Message:
        return await self._context.message.edit(**kwargs)

    async def delete_original_response(self) -> None:
        return await self._context.message.delete()

    async def translate(
            self,
            string: str | app_commands.locale_str,
            **kwargs: Any
    ) -> str | app_commands.locale_str:  # noqa
        return string


class SyntheticWebhook:
    # We can't really create a webhook, so I just resolved to creating a class that mimics common functionality
    # of an actual webhook. Just like with SyntheticInteraction, there are a few attributes and methods that I cannot
    # synthesize given the command invocation context, which is why most of these features do nothing.
    def __init__(self, ctx: commands.Context[types.Bot]) -> None:
        self.ctx: commands.Context[types.Bot] = ctx

    @property
    def url(self) -> str:
        return ""

    async def fetch(self, **kwargs: Any) -> SyntheticWebhook:  # noqa
        return self

    async def delete(self, **kwargs: Any) -> None:
        return

    async def edit(self, **kwargs: Any) -> SyntheticWebhook:  # noqa
        return self

    async def send(self, *args: Any, **kwargs: Any) -> discord.Message:
        return await self.ctx.send(*args, **kwargs)

    async def fetch_message(self, _id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> discord.Message:
        if thread is not MISSING:
            return await self.ctx.guild.get_thread(thread.id).fetch_message(_id)  # type: ignore
        return await self.ctx.channel.fetch_message(_id)

    async def edit_message(self, message_id: int, **kwargs: Any) -> discord.Message:
        thread: discord.abc.Snowflake = kwargs.pop("thread", MISSING)
        if thread is not MISSING:
            message = await self.ctx.guild.get_thread(thread.id).fetch_message(message_id)  # type: ignore
            return await message.edit(**kwargs)
        message = await self.ctx.channel.fetch_message(message_id)
        return await message.edit(**kwargs)

    async def delete_message(self, message_id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> None:
        if thread is not MISSING:
            return await self.ctx.guild.get_thread(thread.id).delete_messages(  # type: ignore
                [discord.Object(id=message_id)]
            )
        if not isinstance(self.ctx.channel, (discord.GroupChannel, discord.PartialMessageable, discord.DMChannel)):
            return await self.ctx.channel.delete_messages([discord.Object(id=message_id)])


class InteractionResponse(discord.InteractionResponse):
    def __init__(self, parent: SyntheticInteraction) -> None:
        self.__parent = parent
        self._response_type: discord.InteractionResponseType | None = None

    def is_done(self) -> bool:
        return self._response_type is not None

    @property
    def type(self) -> discord.InteractionResponseType | None:
        return self._response_type

    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # pyright: ignore [reportPrivateUsage]
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.deferred_channel_message

    async def pong(self) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # pyright: ignore [reportPrivateUsage]
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.pong

    async def send_message(self, content: str | None = None, **kwargs: Any) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # pyright: ignore [reportPrivateUsage]
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        kwargs.pop("ephemeral", None)
        message = await self.__parent._context.send(  # type: ignore  # pyright: ignore [reportPrivateUsage]
            content,
            **kwargs
        )
        self.__parent._original_response = message  # pyright: ignore [reportPrivateUsage]
        self._response_type = discord.InteractionResponseType.channel_message

    async def edit_message(self, **kwargs: Any) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # pyright: ignore [reportPrivateUsage]
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        # noinspection PyProtectedMember
        await self.__parent._context.message.edit(**kwargs)  # type: ignore
        self._response_type = discord.InteractionResponseType.message_update

    async def send_modal(self, modal: discord.ui.Modal, /) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # pyright: ignore [reportPrivateUsage]
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.modal

    async def autocomplete(self, choices: Sequence[app_commands.Choice]) -> None:  # type: ignore
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # pyright: ignore [reportPrivateUsage]
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.autocomplete_result
