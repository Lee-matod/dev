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
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union, cast

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
        ApplicationCommandInteractionData as InteractionPayloadData,
        ApplicationCommandInteractionDataOption as OptionsData,
        ChatInputApplicationCommandInteractionData as ApplicationCommandData,
        ResolvedData,
    )

    from dev import types

    PartialMessageableChannel = Union[
        discord.TextChannel,
        discord.VoiceChannel,
        discord.StageChannel,
        discord.Thread,
        discord.DMChannel,
        discord.PartialMessageable,
    ]

__all__ = ("SyntheticInteraction", "get_app_command", "get_parameters")

T = TypeVar("T")
ClientT = TypeVar("ClientT", bound=discord.Client)
ChoiceT = TypeVar("ChoiceT", str, int, float, Union[str, int, float])


def get_app_command(
    content: str, app_command_list: List[app_commands.Command[Any, ..., Any]]
) -> Optional[app_commands.Command[Any, ..., Any]]:
    possible_subcommands = content.split()
    app_command_name = possible_subcommands[0]
    possible_subcommands = possible_subcommands[1:]
    app_command: Optional[Union[app_commands.Command[Any, ..., Any], app_commands.Group]] = discord.utils.get(
        app_command_list, name=app_command_name
    )
    while isinstance(app_command, discord.app_commands.Group):
        app_command_name = f"{app_command_name} {possible_subcommands[0]}"
        possible_subcommands = possible_subcommands[1:]
        app_command: Optional[Union[app_commands.Command[Any, ..., Any], app_commands.Group]] = discord.utils.get(
            app_command.commands, qualified_name=app_command_name
        )
    if app_command is not None and possible_subcommands:
        raise commands.TooManyArguments(f"Too many arguments passed to {app_command.name}")
    return app_command


async def get_parameters(
    context: commands.Context[types.Bot], command: app_commands.Command[Any, ..., Any]
) -> Dict[app_commands.Parameter, Any]:
    required_arguments = [param for param in command.parameters if param.required]
    optional_arguments = [param for param in command.parameters if not param.required]
    _, *arguments = context.message.content.split("\n")
    parameters: Dict[str, str] = {
        (name := param.split(Settings.FLAG_DELIMITER, 1)[0].strip()): param[len(f"{name}{Settings.FLAG_DELIMITER}") :]
        for param in arguments
    }
    mapped: Dict[app_commands.Parameter, Any] = {}
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
        choice = discord.utils.get(parameter.choices, name=argument)
        if choice is None:
            raise InvalidChoice(argument, parameter.choices)
        return choice.value

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
        converters: Dict[commands.Converter[Any], Type[commands.BadArgument]] = {
            commands.MemberConverter(): commands.MemberNotFound,
            commands.UserConverter(): commands.UserNotFound,
        }
        value = await _multiple_converters(context, argument, converters)
    elif parameter.type is discord.AppCommandOptionType.channel:
        converters: Dict[commands.Converter[Any], Type[commands.BadArgument]] = {
            commands.GuildChannelConverter(): commands.ChannelNotFound,
            commands.ThreadConverter(): commands.ThreadNotFound,
        }
        value = await _multiple_converters(context, argument, converters)
    elif parameter.type is discord.AppCommandOptionType.role:
        value = await commands.RoleConverter().convert(context, argument)
    elif parameter.type is discord.AppCommandOptionType.mentionable:
        converters: Dict[commands.Converter[Any], Type[commands.BadArgument]] = {
            commands.RoleConverter(): commands.RoleNotFound,
            commands.MemberConverter(): commands.MemberNotFound,
            commands.UserConverter(): commands.UserNotFound,
        }
        value = await _multiple_converters(context, argument, converters)
    return value


async def _multiple_converters(
    ctx: commands.Context[types.Bot],
    argument: str,
    converters: Dict[commands.Converter[T], Type[commands.BadArgument]],
    /,
) -> T:
    exception = Exception
    for converter, exception in converters.items():
        try:
            converted = await converter.convert(ctx, argument)
        except exception:
            continue
        return converted
    raise exception(argument)


def _append_snowflake(
    dictionary: ResolvedData, name: str, snowflake: to_dict.PayloadTypes, as_dict: to_dict.Payloads, /
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
    def __init__(self, argument: str, choices: List[app_commands.Choice[Union[str, int, float]]], /) -> None:
        self.argument: str = argument
        self.choices: List[app_commands.Choice[Union[str, int, float]]] = choices
        super().__init__(
            f"Chosen value {argument!r} is not a valid choice " f"{', '.join([choice.name for choice in choices])}"
        )


class SyntheticInteraction(discord.Interaction[ClientT]):
    #  I really don't like setting new attributes/methods, but I don't see any
    #  other way to do this without making everything a lot more complicated than
    #  what it has to be.
    __slots__: Tuple[str, ...] = (
        "id",
        "type",
        "guild_id",
        "channel_id",
        "data",
        "application_id",
        "message",
        "user",
        "token",
        "version",
        "locale",
        "guild_locale",
        "extras",
        "command_failed",
        "_permissions",
        "_app_permissions",
        "_app_command",
        "_state",
        "_client",
        "_context",
        "_session",
        "_baton",
        "_original_response",
        "_unknown_interaction",
        "_cs_response",
        "_cs_followup",
        "_cs_channel",
        "_cs_namespace",
        "_cs_command",
    )

    def __init__(
        self,
        context: commands.Context[types.Bot],
        command: app_commands.Command[Any, ..., Any],
        parameters: Dict[app_commands.Parameter, Any],
    ) -> None:
        assert not isinstance(context.channel, discord.PartialMessageable)
        #  Application command synthetic payload
        data: ApplicationCommandData = {"type": 1, "name": getattr(command.root_parent, "name", command.name), "id": 0}
        resolved: ResolvedData = {}
        command_parameters: List[OptionsData] = []
        #  Populate resolved data and command options
        for param, obj in parameters.items():
            value = obj
            converter: Optional[Callable[[to_dict.PayloadTypes], to_dict.Payloads]] = to_dict.TYPE_MAPPING.get(type(obj))  # type: ignore
            if converter is not None:
                name = converter.__name__ + "s"
                _append_snowflake(resolved, name, obj, converter(obj))
                if name == "members":
                    _append_snowflake(resolved, "users", obj, to_dict.user(obj._user))
            command_parameters.append(
                {"type": param.type.value, "name": param.display_name, "value": value}  # type: ignore
            )
        data["resolved"] = resolved
        #  Add application command options
        if command.root_parent is None:
            data["options"] = command_parameters
        else:
            #  Either 1 or 2 level deep command
            subcommand_options: List[OptionsData] = [{"type": 1, "options": command_parameters, "name": command.name}]
            if command.parent is command.root_parent:
                data["options"] = subcommand_options
            else:
                data["options"] = [{"type": 2, "options": subcommand_options, "name": command.root_parent.name}]
        # DMChannel causes problems here, because it's techincally InteractionDMChannel
        channel: Union[
            to_dict.GuildChannelPayload, to_dict.InteractionDMChannelPayload, to_dict.GroupDMChannelPayload
        ] = to_dict.channel(
            context.channel
        )  # type: ignore
        payload: InteractionPayload = {
            "version": 1,
            "type": 2,
            "token": "",
            "locale": Settings.LOCALE,
            "id": 0,
            "guild_locale": Settings.LOCALE,
            "channel_id": context.channel.id,
            "application_id": context.me.id,
            "data": data,
            "channel": channel,
            "app_permissions": str(context.me.guild_permissions.value)
            if isinstance(context.me, discord.Member)
            else "0",
        }
        if context.guild is not None:
            payload["guild_id"] = context.guild.id
            payload["member"] = to_dict.member(context.author)  # type: ignore
        else:
            user = context.author if isinstance(context.author, discord.User) else context.author._user
            payload["user"] = to_dict.user(user)  # type: ignore

        self._unknown_interaction: bool = False
        self._context = context
        self._app_command = command
        super().__init__(data=payload, state=context._state)  # type: ignore

    async def invoke(
        self, context: commands.Context[types.Bot], /  # Match signature of commands.Command.invoke
    ) -> None:
        app_commands.Command
        if not await self._app_command._check_can_run(self):
            raise app_commands.CheckFailure(f"The check functions for command {self._app_command.name!r} failed.")
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
        transformed_values = await self._app_command._transform_arguments(self, self.namespace)
        return await self._app_command._do_call(self, transformed_values)

    async def __wait_for_response(self, ctx: commands.Context[types.Bot]) -> None:
        await asyncio.sleep(3)  # simulate maximum of 3 seconds for a response
        if self.response._response_type is None:
            # The bot did not respond to the interaction, so we have to somehow tell the user that
            # it took too long.
            # By this time, the interaction would become unknown, so we have to simulate that too
            self._unknown_interaction = True
            await ctx.message.add_reaction("\N{HEAVY EXCLAMATION MARK SYMBOL}")

    @discord.utils.cached_slot_property("_cs_response")
    def response(self) -> InteractionResponse[ClientT]:
        return InteractionResponse(self)

    @discord.utils.cached_slot_property("_cs_followup")
    def followup(self) -> SyntheticWebhook:  # type: ignore
        return SyntheticWebhook(self)

    @discord.utils.cached_slot_property("_cs_namespace")
    def namespace(self) -> app_commands.Namespace:
        if self.type not in (discord.InteractionType.application_command, discord.InteractionType.autocomplete):
            return app_commands.Namespace(self, {}, [])

        tree = self._state._command_tree
        if tree is None:
            return app_commands.Namespace(self, {}, [])

        # The type checker does not understand this narrowing
        data: InteractionPayloadData = self.data  # type: ignore

        try:
            _, options = tree._get_app_command_options(data)
        except discord.DiscordException:
            options = []

        return app_commands.Namespace(self, data.get("resolved", {}), options)

    async def original_response(self) -> discord.InteractionMessage:
        if self._original_response is not None:
            return self._original_response
        channel = self.channel
        if channel is None:
            raise discord.ClientException("Channel for message could not be resolved")
        self._original_response = cast(discord.InteractionMessage, self._context.message)
        return self._original_response

    async def edit_original_response(
        self,
        *,
        content: Optional[str] = MISSING,
        embeds: Sequence[discord.Embed] = MISSING,
        embed: Optional[discord.Embed] = MISSING,
        attachments: Sequence[Union[discord.Attachment, discord.File]] = MISSING,
        view: Optional[discord.ui.View] = MISSING,
        allowed_mentions: Optional[discord.AllowedMentions] = None,
    ) -> discord.InteractionMessage:
        kwargs: Dict[str, Any] = {
            "content": content,
            "attachments": attachments,
            "view": view,
            "allowed_mentions": allowed_mentions,
        }
        if embeds is not MISSING:
            kwargs["embeds"] = embeds
        elif embed is not MISSING:
            kwargs["embed"] = embed
        message = await self._context.message.edit(**kwargs)
        return cast(discord.InteractionMessage, message)

    async def delete_original_response(self) -> None:
        return await self._context.message.delete()

    async def translate(self, string: Union[str, app_commands.locale_str], **kwargs: Any) -> Optional[str]:
        if isinstance(string, app_commands.locale_str):
            return string.message
        return string


class SyntheticWebhook:
    # We can't really create a webhook, so I just resolved to creating a class that
    # mimics common functionality of an actual webhook. Just like with SyntheticInteraction,
    # there are a few attributes and methods that I cannot synthesize given the command
    # invocation context, which is why most of these features do nothing.
    def __init__(self, interaction: SyntheticInteraction[ClientT], /) -> None:
        ctx: commands.Context[types.Bot] = interaction._context
        http: HTTPClient = ctx.bot.http
        self.id: int = discord.utils.time_snowflake(discord.utils.utcnow())
        self.type: discord.WebhookType = discord.WebhookType.application
        self.channel_id: Optional[int] = ctx.channel.id
        self.guild_id: Optional[int] = getattr(ctx.guild, "id", None)
        self.name: Optional[str] = ctx.me.name
        self.auth_token: Optional[str] = ""
        self.session: aiohttp.ClientSession = http._HTTPClient__session  # type: ignore
        self.proxy: Optional[str] = http.proxy
        self.proxy_url: Optional[aiohttp.BasicAuth] = http.proxy_auth
        self.token: Optional[str] = ""
        self.user: Optional[discord.User] = None
        self.source_channel: Optional[discord.PartialWebhookChannel] = None
        self.source_guild: Optional[discord.PartialWebhookGuild] = None

        self._state: ConnectionState = ctx._state
        self._avatar: Optional[str] = ctx.me._avatar

        self.__context: commands.Context[types.Bot] = ctx
        self.__interaction: SyntheticInteraction[ClientT] = interaction

    def is_partial(self) -> bool:
        return self.channel_id is None

    def is_authenticated(self) -> bool:
        return self.auth_token is not None

    @property
    def guild(self) -> Optional[discord.Guild]:
        return self.__context.guild

    @property
    def channel(self) -> Optional[Union[discord.ForumChannel, discord.VoiceChannel, discord.TextChannel]]:
        guild = self.guild
        return guild and guild.get_channel(self.channel_id)  # type: ignore

    @property
    def created_at(self) -> datetime.datetime:
        return discord.utils.snowflake_time(self.id)

    @property
    def avatar(self) -> Optional[discord.Asset]:
        if self._avatar is not None:
            return discord.Asset._from_avatar(self._state, self.__context.me.id, self._avatar)
        return None

    @property
    def default_avatar(self) -> discord.Asset:
        return discord.Asset._from_default_avatar(self._state, 0)

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

    async def delete(self, *, reason: Optional[str] = None, prefer_auth: bool = True) -> None:
        return

    async def edit(self, **kwargs: Any) -> SyntheticWebhook:
        name = kwargs.get("name", MISSING)
        if name is not MISSING:
            self.name = name
        avatar = kwargs.get("avatar", MISSING)
        if avatar is not MISSING:
            self._avatar = discord.utils._bytes_to_base64_data(avatar) if avatar is not None else None
        channel_id: Optional[discord.abc.Snowflake] = kwargs.get("channel")
        if channel_id is not None:
            self.channel_id = channel_id.id
        return self

    async def send(self, *args: Any, **kwargs: Any) -> discord.Message:
        if self.__interaction.response.is_done():
            return await self.__context.send(*args, **kwargs)
        raise discord.NotFound(UnknownError, {"code": 10015, "message": "Unknown Webhook"})  # type: ignore

    async def fetch_message(self, _id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> discord.Message:
        if thread is not MISSING and self.__context.guild is not None:
            channel = self.__context.guild.get_thread(thread.id)
            if channel is not None:
                return await channel.fetch_message(_id)
        return await self.__context.channel.fetch_message(_id)

    async def edit_message(self, message_id: int, **kwargs: Any) -> discord.Message:
        thread: discord.abc.Snowflake = kwargs.pop("thread", MISSING)
        if thread is not MISSING and self.__context.guild is not None:
            channel = self.__context.guild.get_thread(thread.id)
            if channel is not None:
                message = channel.get_partial_message(message_id)
                return await message.edit(**kwargs)
        partial_channel: PartialMessageableChannel = self.__context.channel  # type: ignore
        message = partial_channel.get_partial_message(message_id)
        return await message.edit(**kwargs)

    async def delete_message(self, message_id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> None:
        if thread is not MISSING and self.__context.guild is not None:
            channel = self.__context.guild.get_thread(thread.id)
            if channel is not None:
                return await channel.get_partial_message(message_id).delete()
        partial_channel: PartialMessageableChannel = self.__context.channel  # type: ignore
        message = partial_channel.get_partial_message(message_id)
        await message.delete()


class InteractionResponse(discord.InteractionResponse[ClientT]):
    _parent: SyntheticInteraction[ClientT]

    async def defer(self, *, ephemeral: bool = False, thinking: bool = False) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.deferred_channel_message

    async def pong(self) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.pong

    async def send_message(self, content: Optional[str] = None, **kwargs: Any) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        kwargs.pop("ephemeral", None)
        message = await self._parent._context.send(content, **kwargs)
        self._parent._original_response = message  # type: ignore
        self._response_type = discord.InteractionResponseType.channel_message

    async def edit_message(self, **kwargs: Any) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        await self._parent._context.message.edit(**kwargs)
        self._response_type = discord.InteractionResponseType.message_update

    async def send_modal(self, _: discord.ui.Modal, /) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.modal

    async def autocomplete(self, choices: Sequence[app_commands.Choice[ChoiceT]]) -> None:
        if self._response_type:
            raise discord.InteractionResponded(self._parent)
        if self._parent._unknown_interaction:
            raise discord.NotFound(UnknownError, {"code": 10062, "message": "Unknown interaction"})  # type: ignore
        self._response_type = discord.InteractionResponseType.autocomplete_result
