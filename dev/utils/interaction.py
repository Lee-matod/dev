# -*- coding: utf-8 -*-

"""
dev.utils.interaction
~~~~~~~~~~~~~~~~~~~~~

Discord interaction wrappers.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import datetime
import time
from typing import TYPE_CHECKING, Any, Union

import discord
from discord import app_commands
from discord.app_commands import transformers
from discord.ext import commands
from discord.utils import MISSING

from dev.converters import str_bool
from dev.utils.startup import Settings

if TYPE_CHECKING:
    from collections.abc import Sequence

    from discord.app_commands.transformers import CommandParameter
    from discord.state import ConnectionState

    from dev import types

    InteractionChannel = Union[
        discord.VoiceChannel,
        discord.StageChannel,
        discord.TextChannel,
        discord.ForumChannel,
        discord.CategoryChannel,
        discord.Thread,
        discord.PartialMessageable,
    ]

else:
    InteractionChannel = (
        discord.VoiceChannel,
        discord.StageChannel,
        discord.TextChannel,
        discord.ForumChannel,
        discord.CategoryChannel,
        discord.Thread,
        discord.PartialMessageable,
    )

__all__ = ("SyntheticInteraction", "get_app_command")


IGNORABLE_TRANSFORMERS: list[type[transformers.Transformer]] = [
    transformers.IdentityTransformer,
    transformers.RangeTransformer,
    transformers.LiteralTransformer,
    transformers.ChoiceTransformer,
    transformers.EnumNameTransformer,
    transformers.EnumValueTransformer,
    transformers.InlineTransformer,
    transformers.MemberTransformer,
    transformers.BaseChannelTransformer,
    transformers.RawChannelTransformer,
    transformers.UnionChannelTransformer,
]


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


class UnknownInteraction:
    status: int = 404
    reason: str = "Not Found"


#  Custom AppCommandError to indicate an invalid choice argument
class InvalidChoice(app_commands.AppCommandError):
    def __init__(self, argument: str, choices: list[app_commands.Choice[str | int | float]], /) -> None:
        self.argument: str = argument
        self.choices: list[app_commands.Choice[str | int | float]] = choices
        super().__init__(
            f"Chosen value {argument!r} is not a valid choice " f"({', '.join([choice.name for choice in choices])})"
        )


#  Copy of commands.MissingRequiredArgument but as AppCommandError
class MissingRequiredArgument(app_commands.AppCommandError):
    def __init__(self, argument: app_commands.Parameter, /) -> None:
        self.parameter: app_commands.Parameter = argument
        super().__init__(f"Missing required argument {argument.display_name!r} ({argument.name})")


#  Copy of commands.MissingRequiredAttachment but as AppCommandError
class MissingRequiredAttachment(app_commands.AppCommandError):
    def __init__(self, parameter: app_commands.Parameter, /) -> None:
        self.parameter: app_commands.Parameter = parameter
        super().__init__(f"{parameter.display_name} ({parameter.name}) is an argument " "that is missing an attachment")


#  Exact copy of commands.RangeError but as AppCommandError
class RangeError(app_commands.AppCommandError):
    def __init__(
        self,
        value: int | float | str,
        /,
        max_size: int | float | None,
        min_size: int | float | None,
    ) -> None:
        self.value: int | float | str = value
        self.max_size: int | float | None = max_size
        self.min_size: int | float | None = min_size

        label: str = ""
        if min_size is None and max_size is not None:
            label = f"no more than {max_size}"
        elif min_size is not None and max_size is None:
            label = f"no less than {min_size}"
        elif max_size is not None and min_size is not None:
            label = f"between {min_size} and {max_size}"

        if isinstance(value, str):
            label += " characters"
            count = len(value)
            if count == 1:
                value = "1 character"
            else:
                value = f"{count} characters"
        super().__init__(f"Value must be {label} but received {value}")


class BadArgument(app_commands.AppCommandError):
    def __init__(self, argument: str, conversion_type: type[Any]) -> None:
        self.argument: str = argument
        self.type: type[Any] = conversion_type
        super().__init__(f"Failed to convert {argument} to {conversion_type.__name__}")


class BadChannel(app_commands.AppCommandError):
    def __init__(self, argument: str, channel_type: str) -> None:
        self.argument: str = argument
        self.channel_type: str = channel_type
        super().__init__(f"Channel {argument} does not meet expected properties: {channel_type}")


class SyntheticInteraction:
    def __init__(
        self,
        context: commands.Context[types.Bot],
        command: app_commands.Command[Any, ..., Any],
    ) -> None:
        self._context: commands.Context[types.Bot] = context
        self._command: app_commands.Command[Any, ..., Any] = command
        self._created_at: int = round(time.time())
        self._interaction_response: InteractionResponse = InteractionResponse(self)
        self._unknown_interaction: bool = False
        self.__attachments: list[discord.Attachment] = context.message.attachments.copy()
        self.__namespace: app_commands.Namespace | None = None

        # There are a few attributes that just cannot be obtained using the Context,
        # so I'll just leave them with a static value.
        # These attributes might be the case for some nasty errors.
        self.id: int = 0
        self.type: discord.InteractionType = discord.InteractionType.application_command
        self.data: dict[str, Any] | None = None
        self.token: str = ""
        self.version: int = 1
        self.channel_id: int = context.channel.id
        self.guild_id: int | None = getattr(context.guild, "id", None)
        self.application_id: int | None = self._context.bot.application_id
        self.locale: discord.Locale = discord.Locale(Settings.locale)
        self.guild_locale: discord.Locale | None = None
        self.message: discord.Message = context.message
        self.user: types.User = context.author
        self.extras: dict[str, Any] = {}
        self.command_failed: bool = False

        # Protected attributes won't be defined,
        # but we still need to keep track of the original response regardless
        self._original_response: discord.Message | None = None
        self._state: ConnectionState = context._state  # type: ignore # Required for namespace

    async def __ensure_correct_argument(self, argument: str, parameter: app_commands.Parameter, /) -> Any:
        #  Check argument type
        value = argument
        if parameter.type is discord.AppCommandOptionType.boolean:
            try:
                value = str_bool(argument)
            except commands.BadBoolArgument as exc:
                raise BadArgument(argument, bool) from exc
        elif parameter.type is discord.AppCommandOptionType.integer:
            try:
                value = int(argument)
            except ValueError as exc:
                raise BadArgument(argument, int) from exc
        elif parameter.type is discord.AppCommandOptionType.number:
            try:
                value = float(argument)
            except ValueError as exc:
                raise BadArgument(argument, float) from exc
        elif parameter.type is discord.AppCommandOptionType.attachment:
            try:
                value = self.__attachments.pop()
            except IndexError as exc:
                raise MissingRequiredAttachment(parameter) from exc
        #  Check range
        if parameter.max_value is not None or parameter.min_value is not None:
            min_value = parameter.min_value if parameter.min_value is not None else 0
            if parameter.type is discord.AppCommandOptionType.string:
                max_value = parameter.max_value if parameter.max_value is not None else len(argument)
                if len(argument) > max_value or len(argument) < min_value:
                    raise RangeError(
                        argument,
                        max_size=parameter.max_value,
                        min_size=parameter.min_value,
                    )
            elif parameter.type is discord.AppCommandOptionType.integer:
                max_value = parameter.max_value if parameter.max_value is not None else int(argument)
                if int(argument) > max_value or int(argument) < min_value:
                    raise RangeError(
                        argument,
                        max_size=parameter.max_value,
                        min_size=parameter.min_value,
                    )
            elif parameter.type is discord.AppCommandOptionType.number:
                max_value = parameter.max_value if parameter.max_value is not None else float(argument)
                if float(argument) > max_value or float(argument) < min_value:
                    raise RangeError(
                        argument,
                        max_size=parameter.max_value,
                        min_size=parameter.min_value,
                    )
        #  Check choices
        elif parameter.choices and argument not in [choice.name for choice in parameter.choices]:
            raise InvalidChoice(argument, parameter.choices)
        #  Check channel type
        elif parameter.channel_types:
            try:
                channel = await commands.GuildChannelConverter().convert(self._context, argument)
            except commands.ChannelNotFound as exc:
                try:
                    thread = await commands.ThreadConverter().convert(self._context, argument)
                except commands.ThreadNotFound as exc1:
                    raise BadArgument(argument, discord.abc.GuildChannel) from exc1
                if thread.is_private() and discord.ChannelType.private_thread not in parameter.channel_types:
                    raise BadChannel(argument, "private thread") from exc
                if thread.is_news() and discord.ChannelType.news_thread not in parameter.channel_types:
                    raise BadChannel(argument, "news thread") from exc
                if not thread.is_private() and discord.ChannelType.public_thread not in parameter.channel_types:
                    raise BadChannel(argument, "public thread") from exc
                value = thread
            else:
                if isinstance(channel, discord.TextChannel) and discord.ChannelType.text not in parameter.channel_types:
                    raise BadChannel(argument, "text channel")
                if (
                    isinstance(channel, discord.DMChannel)
                    and discord.ChannelType.private not in parameter.channel_types
                ):
                    raise BadChannel(argument, "private channel")
                if (
                    isinstance(channel, discord.GroupChannel)
                    and discord.ChannelType.group not in parameter.channel_types
                ):
                    raise BadChannel(argument, "group channel")
                if (
                    isinstance(channel, discord.VoiceChannel)
                    and discord.ChannelType.voice not in parameter.channel_types
                ):
                    raise BadChannel(argument, "voice channel")
                if (
                    isinstance(channel, discord.CategoryChannel)
                    and discord.ChannelType.category not in parameter.channel_types
                ):
                    raise BadChannel(argument, "category channel")
                if (
                    isinstance(channel, discord.StageChannel)
                    and discord.ChannelType.stage_voice not in parameter.channel_types
                ):
                    raise BadChannel(argument, "stage channel")
                if (
                    isinstance(channel, discord.ForumChannel)
                    and discord.ChannelType.forum not in parameter.channel_types
                ):
                    raise BadChannel(argument, "forum channel")
                value = channel
        command_param: CommandParameter = parameter._Parameter__parent  # type: ignore
        ann = command_param._annotation  # type: ignore
        if isinstance(ann, app_commands.Transformer) and type(ann) not in IGNORABLE_TRANSFORMERS:
            value = await command_param.transform(self, value)  # type: ignore
        return value

    async def __validate_parameters(self, initial_arguments: list[str]) -> dict[app_commands.Parameter, Any]:
        required_arguments = [param for param in self._command.parameters if param.required]
        optional_arguments = [param for param in self._command.parameters if not param.required]
        parameters: dict[str, str] = {
            (name := param.split(Settings.flag_delimiter, 1)[0].strip()): param.removeprefix(
                f"{name}{Settings.flag_delimiter}"
            )
            for param in initial_arguments
        }
        mapped: dict[app_commands.Parameter, Any] = {}
        for req in required_arguments:
            if req.display_name not in parameters:
                raise MissingRequiredArgument(req)
            mapped[req] = await self.__ensure_correct_argument(parameters[req.display_name], req)
        for opt in optional_arguments:
            if opt.display_name in parameters:
                mapped[opt] = await self.__ensure_correct_argument(parameters[opt.display_name], opt)
            else:
                mapped[opt] = opt.default if opt.default is not MISSING else None
        return mapped

    def __create_namespace(self, parameters: dict[app_commands.Parameter, Any]) -> app_commands.Namespace:
        options: list[dict[str, Any]] = []
        for param, value in parameters.items():
            if hasattr(value, "id"):
                value = str(value.id)
            options.append({"type": param.type, "name": param.display_name, "value": value})
        #  All the data is already resolved previously, so parsing it again
        #  really just makes everything even more complicated than what it
        #  already is. I can parse it in the future and move to _invoke_with_namespace,
        #  but for now, I don't see any issue in leaving this empty
        return app_commands.Namespace(self, {}, options)  # type: ignore

    async def invoke(
        self, context: commands.Context[types.Bot], /
    ) -> None:  # Match signature of commands.Command.invoke
        if not await self._command._check_can_run(self):  # type: ignore
            raise app_commands.CheckFailure(f"The check functions for command {self._command.qualified_name!r} failed.")
        #  The only difference between these two methods is that reinvoke
        #  does not call checks, meanwhile invoke does
        await self.reinvoke(context)

    async def reinvoke(
        self, context: commands.Context[types.Bot], /, *, call_hooks: bool = False
    ) -> None:  # Match signature of commands.Command.reinvoke
        arguments: list[str]
        _, *arguments = self._context.message.content.split("\n")
        required = (self,) if self._command.binding is None else (self._command.binding, self)
        parameters = await self.__validate_parameters(arguments)
        self.__namespace = self.__create_namespace(parameters)

        kwargs = {param.name: value for param, value in parameters.items()}
        self._context.bot.loop.create_task(self.__wait_for_response())
        await self._command.callback(*required, **kwargs)  # type: ignore

    async def __wait_for_response(self) -> None:
        await asyncio.sleep(3)  # simulate maximum of 3 seconds for a response
        if self._interaction_response._response_type is None:  # type: ignore
            # The bot did not respond to the interaction, so we have to somehow tell the user that
            # it took too long.
            # By this time, the interaction would become unknown, so we have to simulate that too
            self._unknown_interaction = True
            await self._context.message.add_reaction("\u2757")

    @property  # type: ignore
    def __class__(self) -> type[discord.Interaction]:
        return discord.Interaction

    def __instancecheck__(self, instance: Any) -> bool:
        return isinstance(instance, self.__class__)

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
        if isinstance(self._context.channel, InteractionChannel):  # type: ignore
            return self._context.channel
        return None

    @property
    def permissions(self) -> discord.Permissions:
        return self._context.author.guild_permissions  # type: ignore

    @property
    def app_permissions(self) -> discord.Permissions:
        return self._context.guild.me.guild_permissions  # type: ignore

    @discord.utils.cached_slot_property("_cs_namespace")
    def namespace(self) -> app_commands.Namespace:
        return self.__namespace  # type: ignore

    @discord.utils.cached_slot_property("_cs_command")
    def command(
        self,
    ) -> app_commands.Command[Any, ..., Any] | app_commands.ContextMenu | None:
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
        self, string: str | app_commands.locale_str, **kwargs: Any
    ) -> str | app_commands.locale_str:  # noqa
        return string


class SyntheticWebhook:
    # We can't really create a webhook, so I just resolved to creating a class that
    # mimics common functionality of an actual webhook. Just like with SyntheticInteraction,
    # there are a few attributes and methods that I cannot synthesize given the command
    # invocation context, which is why most of these features do nothing.
    def __init__(self, ctx: commands.Context[types.Bot]) -> None:
        self.ctx: commands.Context[types.Bot] = ctx

    @property
    def url(self) -> str:
        return ""

    async def fetch(self, **kwargs: Any) -> SyntheticWebhook:
        return self

    async def delete(self, **kwargs: Any) -> None:
        return

    async def edit(self, **kwargs: Any) -> SyntheticWebhook:
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
            thread = self.ctx.guild.get_thread(thread.id)  # type: ignore
            message = await thread.fetch_message(message_id)  # type: ignore
            return await message.edit(**kwargs)  # type: ignore
        message = await self.ctx.channel.fetch_message(message_id)
        return await message.edit(**kwargs)

    async def delete_message(self, message_id: int, /, *, thread: discord.abc.Snowflake = MISSING) -> None:
        if thread is not MISSING:
            return await self.ctx.guild.get_thread(thread.id).delete_messages(  # type: ignore
                [discord.Object(id=message_id)]
            )
        if not isinstance(
            self.ctx.channel,
            (discord.GroupChannel, discord.PartialMessageable, discord.DMChannel),
        ):
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
        if self.__parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.deferred_channel_message

    async def pong(self) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.pong

    async def send_message(self, content: str | None = None, **kwargs: Any) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        kwargs.pop("ephemeral", None)
        message = await self.__parent._context.send(content, **kwargs)  # type: ignore
        self.__parent._original_response = message  # type: ignore
        self._response_type = discord.InteractionResponseType.channel_message

    async def edit_message(self, **kwargs: Any) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        # noinspection PyProtectedMember
        await self.__parent._context.message.edit(**kwargs)  # type: ignore
        self._response_type = discord.InteractionResponseType.message_update

    async def send_modal(self, modal: discord.ui.Modal, /) -> None:
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.modal

    async def autocomplete(self, choices: Sequence[app_commands.Choice]) -> None:  # type: ignore
        if self._response_type is not None:
            raise discord.InteractionResponded(self.__parent)  # type: ignore
        if self.__parent._unknown_interaction:  # type: ignore
            raise discord.NotFound(
                UnknownInteraction, {"code": 10062, "message": "Unknown interaction"}  # type: ignore
            )
        self._response_type = discord.InteractionResponseType.autocomplete_result
