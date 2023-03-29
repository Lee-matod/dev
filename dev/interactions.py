# -*- coding: utf-8 -*-

"""
dev.interaction
~~~~~~~~~~~~~~~

Discord interaction wrappers.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TypeVar

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import MISSING

from dev.converters import str_bool
from dev.scope import Settings
from dev.utils import to_dict

if TYPE_CHECKING:
    import datetime
    from collections.abc import Sequence

    import aiohttp
    from discord.http import HTTPClient
    from discord.state import ConnectionState
    from discord.types.interactions import (
        ApplicationCommandInteraction as InteractionPayload,
        ApplicationCommandInteractionDataOption as OptionsData,
        ChatInputApplicationCommandInteractionData as ApplicationCommandData,
        ResolvedData,
    )

    from dev import types

__all__ = ("SyntheticInteraction", "get_app_command", "get_parameters")

T = TypeVar("T")


def get_app_command(
    content: str, app_command_list: list[app_commands.Command[Any, ..., Any]]
) -> app_commands.Command[Any, ..., Any] | None:
    possible_subcommands = content.split()
    app_command_name = possible_subcommands[0]
    possible_subcommands = possible_subcommands[1:]
    app_command: app_commands.Command[Any, ..., Any] | app_commands.Group | None = discord.utils.get(
        app_command_list, name=app_command_name
    )
    while isinstance(app_command, discord.app_commands.Group):
        app_command_name = f"{app_command_name} {possible_subcommands[0]}"
        possible_subcommands = possible_subcommands[1:]
        app_command: app_commands.Command[Any, ..., Any] | app_commands.Group | None = discord.utils.get(
            app_command.commands, qualified_name=app_command_name
        )
    return app_command


async def get_parameters(
    context: commands.Context[types.Bot], command: app_commands.Command[Any, ..., Any]
) -> dict[app_commands.Parameter, Any]:
    required_arguments = [param for param in command.parameters if param.required]
    optional_arguments = [param for param in command.parameters if not param.required]
    _, *arguments = context.message.content.split("\n")
    parameters: dict[str, str] = {
        (name := param.split(Settings.FLAG_DELIMITER, 1)[0].strip()): param[len(f"{name}{Settings.FLAG_DELIMITER}") :]
        for param in arguments
    }
    mapped: dict[app_commands.Parameter, Any] = {}
    for req in required_arguments:
        if req.display_name not in parameters:
            raise commands.MissingRequiredArgument(req)  # type: ignore
        mapped[req] = await _parameter_type(context, req, parameters[req.display_name])
    for opt in optional_arguments:
        if opt.display_name in parameters:
            mapped[opt] = await _parameter_type(context, opt, parameters[opt.display_name])
        else:
            mapped[opt] = opt.default if opt.default is not MISSING else None
    return mapped


async def _parameter_type(
    context: commands.Context[types.Bot], parameter: app_commands.Parameter, argument: str
) -> Any:
    value = argument
    attachments = context.message.attachments.copy()
    number_mapping = {discord.AppCommandOptionType.integer: int, discord.AppCommandOptionType.number: float}
    datatype = number_mapping.get(parameter.type)
    #  Range
    if parameter.max_value is not None or parameter.min_value is not None:
        min_value = parameter.min_value if parameter.min_value is not None else 0
        param_mapping = {
            discord.AppCommandOptionType.string: len,
            discord.AppCommandOptionType.integer: int,
            discord.AppCommandOptionType.number: float,
        }
        method = param_mapping[parameter.type]
        max_value = parameter.max_value if parameter.max_value is not None else method(argument)
        if method(argument) > max_value or method(argument) < min_value:
            raise commands.RangeError(argument, parameter.min_value, parameter.max_value)
    #  Choices
    if parameter.choices:
        if argument not in [choice.name for choice in parameter.choices]:
            raise InvalidChoice(argument, parameter.choices)
        return discord.utils.get(parameter.choices, name=argument).value  # type: ignore

    if datatype is not None:
        try:
            value = datatype(argument)
        except ValueError:
            raise commands.BadArgument(f"Failed to convert {argument!r} to {datatype}")
    elif parameter.type is discord.AppCommandOptionType.boolean:
        value = str_bool(argument)
    elif parameter.type is discord.AppCommandOptionType.attachment:
        try:
            value = attachments.pop(0)
        except IndexError:
            raise commands.MissingRequiredAttachment(parameter)  # type: ignore
    elif parameter.type is discord.AppCommandOptionType.user:
        converters: dict[commands.Converter[Any], type[commands.BadArgument]] = {
            commands.MemberConverter(): commands.MemberNotFound,
            commands.UserConverter(): commands.UserNotFound,
        }
        value = await _multiple_converters(context, argument, converters)
    elif parameter.type is discord.AppCommandOptionType.channel:
        converters: dict[commands.Converter[Any], type[commands.BadArgument]] = {
            commands.GuildChannelConverter(): commands.ChannelNotFound,
            commands.ThreadConverter(): commands.ThreadNotFound,
        }
        value = await _multiple_converters(context, argument, converters)
    elif parameter.type is discord.AppCommandOptionType.role:
        value = await commands.RoleConverter().convert(context, argument)
    elif parameter.type is discord.AppCommandOptionType.mentionable:
        converters: dict[commands.Converter[Any], type[commands.BadArgument]] = {
            commands.RoleConverter(): commands.RoleNotFound,
            commands.MemberConverter(): commands.MemberNotFound,
            commands.UserConverter(): commands.UserNotFound,
        }
        value = await _multiple_converters(context, argument, converters)
    return value


async def _multiple_converters(
    ctx: commands.Context[types.Bot],
    argument: str,
    converters: dict[commands.Converter[T], type[commands.BadArgument]],
    /,
) -> T:
    for converter, exception in converters.items():
        try:
            converted = await converter.convert(ctx, argument)
        except exception:
            continue
        return converted
    raise exception  # type: ignore


def _append_snowflake(
    dictionary: dict[str, Any], name: str, snowflake: discord.abc.Snowflake, as_dict: dict[str, Any], /
) -> None:
    previous = dictionary.get(name)
    if previous is not None:
        previous[str(snowflake.id)] = as_dict
    else:
        dictionary[name] = {str(snowflake.id): as_dict}


class UnknownError:
    status: int = 404
    reason: str = "Not Found"


class InvalidChoice(app_commands.AppCommandError):
    def __init__(self, argument: str, choices: list[app_commands.Choice[str | int | float]], /) -> None:
        self.argument: str = argument
        self.choices: list[app_commands.Choice[str | int | float]] = choices
        super().__init__(
            f"Chosen value {argument!r} is not a valid choice " f"{', '.join([choice.name for choice in choices])}"
        )


class SyntheticInteraction(discord.Interaction):
    #  I really don't like setting new attributes/methods, but I don't see any
    #  other way to do this without making everything a lot more complicated than
    #  what it has to be.

    def __init__(
        self,
        context: commands.Context[types.Bot],
        command: app_commands.Command[Any, ..., Any],
        parameters: dict[app_commands.Parameter, Any],
    ) -> None:
        #  Top-level synthetic payload
        payload: InteractionPayload = {
            "version": 1,
            "type": 2,
            "token": "",
            "locale": Settings.LOCALE,
            "id": 0,
            "guild_locale": Settings.LOCALE,
            "channel_id": str(getattr(context.channel, "id", None)),
            "application_id": context.bot.user.id,  # type: ignore
        }
        if context.guild is not None:
            payload["guild_id"] = context.guild.id
            payload["member"] = to_dict.member(context.author)  # type: ignore
            payload["app_permissions"] = str(context.me.guild_permissions.value)  # type: ignore
        else:
            payload["user"] = to_dict.user(context.author)  # type: ignore
            payload["app_permissions"] = "0"

        #  Application command synthetic payload
        data: ApplicationCommandData = {"type": 1, "name": getattr(command.root_parent, "name", command.name), "id": 0}
        payload["data"] = data
        resolved: ResolvedData = {}
        command_parameters: list[OptionsData] = []
        #  Populate resolved data and command options
        for param, obj in parameters.items():
            value = obj
            converter = to_dict.TYPE_MAPPING.get(type(obj))
            if converter is not None:
                value = str(obj.id)
                if type(obj) in to_dict.REQUIRES_CTX:
                    _append_snowflake(resolved, "channels", obj, converter(obj, context))  # type: ignore
                else:
                    name = converter.__name__ + "s"
                    _append_snowflake(resolved, name, obj, converter(obj))  # type: ignore
                    if name == "members":
                        assert isinstance(obj, discord.Member)
                        _append_snowflake(resolved, "users", obj, to_dict.user(obj._user))  # type: ignore
            command_parameters.append({"type": param.type.value, "value": value, "name": param.display_name})
        data["resolved"] = resolved
        #  Add application command options
        if command.root_parent is None:
            data["options"] = command_parameters
        else:
            #  Either 1 or 2 level deep command
            subcommand_options: list[OptionsData] = [{"type": 1, "options": command_parameters, "name": command.name}]
            if command.parent is command.root_parent:
                data["options"] = subcommand_options
            else:
                data["options"] = [{"type": 2, "options": subcommand_options, "name": command.root_parent.name}]
        payload["data"] = data

        self._unknown_interaction: bool = False
        self.__context = context
        self.__app_command = command
        super().__init__(data=payload, state=context._state)  # type: ignore

    async def invoke(
        self, context: commands.Context[types.Bot], /  # Match signature of commands.Command.invoke
    ) -> None:
        app_commands.Command
        if not await self.__app_command._check_can_run(self):  # type: ignore
            raise app_commands.CheckFailure(f"The check functions for command {self.__app_command.name!r} failed.")
        #  The only difference between these two methods is that reinvoke
        #  does not call checks, meanwhile invoke does
        await self.reinvoke(context)

    async def reinvoke(
        self,
        context: commands.Context[types.Bot],
        /,
        *,
        call_hooks: bool = False,  # Match signature of commands.Command.reinvoke
    ) -> None:
        context.bot.loop.create_task(self.__wait_for_response(context))
        transformed_values = await self.__app_command._transform_arguments(self, self.namespace)  # type: ignore
        return await self.__app_command._do_call(self, transformed_values)  # type: ignore

    async def __wait_for_response(self, ctx: commands.Context[types.Bot]) -> None:
        await asyncio.sleep(3)  # simulate maximum of 3 seconds for a response
        if self.response._response_type is None:  # type: ignore
            # The bot did not respond to the interaction, so we have to somehow tell the user that
            # it took too long.
            # By this time, the interaction would become unknown, so we have to simulate that too
            self._unknown_interaction = True
            await ctx.message.add_reaction("\u2757")

    @discord.utils.cached_slot_property("_cs_response")
    def response(self) -> InteractionResponse:
        return InteractionResponse(self)

    @discord.utils.cached_slot_property("_cs_followup")
    def followup(self) -> SyntheticWebhook:
        return SyntheticWebhook(self)  # type: ignore

    async def original_response(self) -> discord.Message:  # type: ignore
        if self._original_response is not None:
            return self._original_response
        channel = self.channel  # type: ignore  # For some reason pyright thinks it's not defined
        if channel is None:
            raise discord.ClientException("Channel for message could not be resolved")
        self._original_response = self.__context.message  # type: ignore
        return self._original_response

    async def edit_original_response(self, **kwargs: Any) -> discord.Message:  # type: ignore
        return await self.__context.message.edit(**kwargs)

    async def delete_original_response(self) -> None:
        return await self.__context.message.delete()

    async def translate(self, string: str | app_commands.locale_str, **kwargs: Any) -> str | None:
        if isinstance(string, app_commands.locale_str):
            return string.message
        return string


class SyntheticWebhook:
    # We can't really create a webhook, so I just resolved to creating a class that
    # mimics common functionality of an actual webhook. Just like with SyntheticInteraction,
    # there are a few attributes and methods that I cannot synthesize given the command
    # invocation context, which is why most of these features do nothing.
    def __init__(self, interaction: SyntheticInteraction, /) -> None:
        ctx: commands.Context[types.Bot] = interaction._SyntheticInteraction__context  # type: ignore
        http: HTTPClient = ctx.bot.http
        self.id: int = discord.utils.time_snowflake(discord.utils.utcnow())
        self.type: discord.WebhookType = discord.WebhookType.application
        self.channel_id: int | None = ctx.channel.id
        self.guild_id: int | None = getattr(ctx.guild, "id", None)
        self.name: str | None = ctx.me.name
        self.auth_token: str | None = ""
        self.session: aiohttp.ClientSession = http._HTTPClient__session  # type: ignore
        self.proxy: str | None = http.proxy
        self.proxy_url: aiohttp.BasicAuth | None = http.proxy_auth
        self.token: str | None = ""
        self.user: discord.User | None = None
        self.source_channel: discord.PartialWebhookChannel | None = None
        self.source_guild: discord.PartialWebhookGuild | None = None

        self._state: ConnectionState = ctx._state  # type: ignore
        self._avatar: str | None = ctx.me._avatar  # type: ignore

        self.__context: commands.Context[types.Bot] = ctx
        self.__interaction: SyntheticInteraction = interaction

    def is_partial(self) -> bool:
        return self.channel_id is None

    def is_authenticated(self) -> bool:
        return self.auth_token is not None

    @property
    def guild(self) -> discord.Guild | None:
        return self.__context.guild

    @property
    def channel(self) -> discord.ForumChannel | discord.VoiceChannel | discord.TextChannel | None:
        if self.guild is not None:
            return self.guild.get_channel(self.channel_id)  # type: ignore

    @property
    def created_at(self) -> datetime.datetime:
        return discord.utils.snowflake_time(self.id)

    @property
    def avatar(self) -> discord.Asset | None:
        if self._avatar is not None:
            return discord.Asset._from_avatar(self._state, self.__context.me.id, self._avatar)  # type: ignore
        return None

    @property
    def default_avatar(self) -> discord.Asset:
        return discord.Asset._from_default_avatar(self._state, 0)  # type: ignore

    @property
    def display_avatar(self) -> discord.Asset:
        return self.avatar or self.default_avatar

    @property
    def url(self) -> str:
        return ""

    @classmethod
    def partial(cls, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Cannot synthesize a webhook")

    @classmethod
    def from_url(cls, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Cannot synthesize a webhook")

    @classmethod
    def _as_follower(cls, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Cannot synthesize a webhook")

    @classmethod
    def from_state(cls, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Cannot synthesize a webhook")

    async def fetch(self, *, prefer_auth: bool = True) -> SyntheticWebhook:
        return self

    async def delete(self, *, reason: str | None = None, prefer_auth: bool = True) -> None:
        return

    async def edit(self, **kwargs: Any) -> SyntheticWebhook:
        name = kwargs.get("name", MISSING)
        if name is not MISSING:
            self.name = name
        avatar = kwargs.get("avatar", MISSING)
        if avatar is not MISSING:
            self._avatar = discord.utils._bytes_to_base64_data(avatar) if avatar is not None else None  # type: ignore
        channel_id: discord.abc.Snowflake | None = kwargs.get("channel")
        if channel_id is not None:
            self.channel_id = channel_id.id
        return self

    async def send(self, *args: Any, **kwargs: Any) -> discord.Message:
        if self.__interaction.response.is_done():
            return await self.__context.send(*args, **kwargs)
        raise discord.NotFound(UnknownError, {"code": 10015, "message": "Unknown Webhook"})  # type: ignore

    async def fetch_message(self, _id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> discord.Message:
        if thread is not MISSING:
            return await self.__context.guild.get_thread(thread.id).fetch_message(_id)  # type: ignore
        return await self.__context.channel.fetch_message(_id)

    async def edit_message(self, message_id: int, **kwargs: Any) -> discord.Message:
        thread: discord.abc.Snowflake = kwargs.pop("thread", MISSING)  # type: ignore
        if thread is not MISSING:
            thread: discord.Thread = self.__context.guild.get_thread(thread.id)  # type: ignore
            message = thread.get_partial_message(message_id)
            return await message.edit(**kwargs)
        message: discord.PartialMessage = self.__context.channel.get_partial_message(message_id)  # type: ignore
        return await message.edit(**kwargs)  # type: ignore

    async def delete_message(self, message_id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> None:
        if thread is not MISSING:
            channel: discord.Thread = self.__context.guild.get_thread(thread.id)  # type: ignore
            return await channel.get_partial_message(message_id).delete()
        message: discord.PartialMessage = self.__context.channel.get_partial_message(message_id)  # type: ignore
        await message.delete()  # type: ignore


class InteractionResponse(discord.InteractionResponse):
    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.deferred_channel_message

    async def pong(self) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.pong

    async def send_message(self, content: str | None = None, **kwargs: Any) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        kwargs.pop("ephemeral", None)
        message = await self._parent._SyntheticInteraction__context.send(content, **kwargs)  # type: ignore
        self._parent._original_response = message  # type: ignore
        self._response_type = discord.InteractionResponseType.channel_message

    async def edit_message(self, **kwargs: Any) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        await self._parent._SyntheticInteraction__context.message.edit(**kwargs)  # type: ignore
        self._response_type = discord.InteractionResponseType.message_update

    async def send_modal(self, _: discord.ui.Modal, /) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.modal

    async def autocomplete(self, _: Sequence[app_commands.Choice]) -> None:  # type: ignore
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.autocomplete_result
