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
from typing import Any, Dict, List, NamedTuple, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING

from dev.converters import convert_str_to_bool


__all__ = (
    "SyntheticInteraction",
    "get_invokable_app_command"
)

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


def get_invokable_app_command(content: str, app_command_list: List[app_commands.Command]) -> app_commands.Command:
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


class SyntheticInteraction:
    def __init__(self, context: commands.Context, command: app_commands.Command):
        self._context: commands.Context = context
        self._command: app_commands.Command = command
        self._created_at: int = round(time.time())
        self._interaction_response: InteractionResponse = InteractionResponse(self)
        self._unknown_interaction: bool = False

        self.id = 0
        self.type = discord.InteractionType.application_command
        self.data = None
        self.token = ""
        self.version = 1
        self.channel_id = context.channel.id
        self.guild_id = context.guild.id
        self.application_id: int = self._context.bot.application_id
        self.locale = discord.Locale("en-US")
        self.guild_locale = None
        self.message = context.message
        self.user = context.author

        # noinspection PyProtectedMember
        self._state = context.bot._connection
        self._client = context.bot
        # noinspection PyProtectedMember
        self._session = self._state.http._HTTPClient__session  # type: ignore
        self._original_response = None
        self._baton = MISSING
        self.extras = {}
        self.command_failed = False

    async def get_namespace(self, arguments: List[str], ignore_params: int) -> Dict[str, Any]:
        signature = inspect.signature(self._command.callback)
        parameters = [
            Parameter(name=name, annotation=param.annotation, argument=argument, default=param.default)
            for argument, (name, param) in zip(arguments, list(signature.parameters.items())[ignore_params:])
        ]
        kwargs = {}
        for param in parameters:
            base_converter = CONVERSIONS.get(param.annotation, None)
            if base_converter is not None:
                kwargs[param.name] = await base_converter.convert(self._context, param.argument)
            elif issubclass(param.annotation, commands.Converter):
                kwargs[param.name] = await param.annotation().convert(self._context, param.argument)
            elif issubclass(param.annotation, app_commands.Transformer):
                kwargs[param.name] = await param.annotation().transform(self, param.argument)  # type: ignore
            elif param.annotation is None and param.default not in (inspect.Parameter.empty, None):
                kwargs[param.name] = type(param.default)(param.argument)
            elif param.annotation == bool:
                kwargs[param.name] = convert_str_to_bool(param.argument)
            else:
                try:
                    kwargs[param.name] = param.annotation(param.argument)  # type: ignore
                except TypeError:
                    kwargs[param.name] = param.argument
        return kwargs

    async def invoke(self):
        # noinspection PyProtectedMember
        if not await self._command._check_can_run(self):  # type: ignore
            raise commands.CheckFailure(f"The check functions for command {self._command.qualified_name!r} failed.")
        arguments = self._context.message.content.removeprefix(f"/{self._command.qualified_name}")
        required = (self,) if self._command.binding is None else (self._command.binding, self)
        parameters = await self.get_namespace(shlex.split(arguments), len(required))
        self._context.bot.loop.create_task(self._wait_for_response())
        await self._command.callback(*required, **parameters)

    async def _wait_for_response(self):
        await asyncio.sleep(3)  # simulate maximum of 3 seconds for a response
        # noinspection PyProtectedMember
        if self._interaction_response._response_type is None:
            self._unknown_interaction = True
            await self._context.message.add_reaction("❗")

    @property
    def __class__(self):
        return discord.Interaction

    def __instancecheck__(self, instance) -> bool:
        return type(instance) is self.__class__

    def __subclasscheck__(self, subclass) -> bool:
        return subclass == self.__class__

    @property
    def client(self) -> commands.Bot:
        return self._context.bot

    @property
    def guild(self) -> discord.Guild:
        return self._context.guild

    @discord.utils.cached_slot_property("_cs_channel")
    def channel(self) -> discord.TextChannel:
        return self._context.channel

    @property
    def permissions(self) -> discord.Permissions:
        return self._context.author.guild_permissions

    @property
    def app_permissions(self) -> discord.Permissions:
        return self._context.me.guild_permissions

    @discord.utils.cached_slot_property("_cs_namespace")
    def namespace(self) -> app_commands.Namespace:
        return app_commands.Namespace(self, {}, [])  # type: ignore

    @discord.utils.cached_slot_property("_cs_command")
    def command(self) -> Optional[Union[app_commands.Command[Any, ..., Any], app_commands.ContextMenu]]:
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

    async def edit_original_response(self, **kwargs) -> discord.Message:
        return await self._context.message.edit(**kwargs)

    async def delete_original_response(self) -> None:
        return await self._context.message.delete()

    async def translate(self, string: Union[str, app_commands.locale_str], **kwargs) -> Optional[str]:  # noqa
        return string


class SyntheticWebhook:
    def __init__(self, ctx: commands.Context):
        self.ctx: commands.Context = ctx

    @property
    def url(self) -> str:
        return ""

    async def fetch(self, **kwargs) -> SyntheticWebhook:  # noqa
        return self

    async def delete(self, **kwargs):
        pass

    async def edit(self, **kwargs) -> SyntheticWebhook:  # noqa
        return self

    async def send(self, *args, **kwargs) -> discord.Message:
        return await self.ctx.send(*args, **kwargs)

    async def fetch_message(self, _id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> discord.Message:
        if thread is not MISSING:
            thread_id = thread.id
            return await self.ctx.guild.get_thread(thread_id).fetch_message(_id)
        return await self.ctx.channel.fetch_message(_id)

    async def edit_message(self, message_id: int, **kwargs) -> discord.Message:
        thread: discord.abc.Snowflake = kwargs.pop("thread", MISSING)
        if thread is not MISSING:
            thread_id = thread.id
            message = await self.ctx.guild.get_thread(thread_id).fetch_message(message_id)
            return await message.edit(**kwargs)
        message = await self.ctx.channel.fetch_message(message_id)
        return await message.edit(**kwargs)

    async def delete_message(self, message_id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> None:
        if thread is not MISSING:
            thread_id = thread.id
            return await self.ctx.guild.get_thread(thread_id).delete_messages([discord.Object(id=message_id)])
        return await self.ctx.channel.delete_messages([discord.Object(id=message_id)])


class InteractionResponse(discord.InteractionResponse):
    def __init__(self, parent: SyntheticInteraction):
        self._parent = parent
        self._response_type: Optional[discord.InteractionResponseType] = None

    def is_done(self) -> bool:
        return self._response_type is not None

    @property
    def type(self) -> Optional[discord.InteractionResponseType]:
        return self._response_type

    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self._parent)  # type: ignore
        # noinspection PyProtectedMember
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownInteraction, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.deferred_channel_message

    async def pong(self) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self._parent)  # type: ignore
        # noinspection PyProtectedMember
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownInteraction, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.pong

    async def send_message(self, content: Optional[Any] = None, **kwargs) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self._parent)  # type: ignore
        # noinspection PyProtectedMember
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownInteraction, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        kwargs.pop("ephemeral", None)
        # noinspection PyProtectedMember
        message = await self._parent._context.send(content, **kwargs)
        self._parent._original_response = message
        self._response_type = discord.InteractionResponseType.channel_message

    async def edit_message(self, **kwargs) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self._parent)  # type: ignore
        # noinspection PyProtectedMember
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownInteraction, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        # noinspection PyProtectedMember
        await self._parent._context.message.edit(**kwargs)
        self._response_type = discord.InteractionResponseType.message_update

    async def send_modal(self, modal: discord.ui.Modal, /) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self._parent)  # type: ignore
        # noinspection PyProtectedMember
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownInteraction, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.modal

    async def autocomplete(self, choices) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self._parent)  # type: ignore
        # noinspection PyProtectedMember
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownInteraction, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.autocomplete_result
