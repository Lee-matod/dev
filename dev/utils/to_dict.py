# -*- coding: utf-8 -*-

"""
dev.utils.to_dict
~~~~~~~~~~~~~~~~~

Discord objects and their respective payload types.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Union, cast, overload

import discord

if TYPE_CHECKING:
    from discord.types.channel import (
        CategoryChannel as CategoryChannelPayload,
        DMChannel as DMChannelPayload,
        ForumChannel as ForumChannelPayload,
        ForumTag as ForumTagPayload,
        GroupDMChannel as GroupDMChannelPayload,
        InteractionDMChannel as InteractionDMChannelPayload,
        NewsChannel as NewsChannelPayload,
        StageChannel as StageChannelPayload,
        TextChannel as TextChannelPayload,
        ThreadChannel as ThreadChannelPayload,
        VoiceChannel as VoiceChannelPayload,
        _BaseGuildChannel,
        _BaseTextChannel,
    )
    from discord.types.member import Member as MemberPayload
    from discord.types.message import Attachment as AttachmentPayload
    from discord.types.role import Role as RolePayload, RoleTags as RoleTagsPayload
    from discord.types.threads import Thread as ThreadPayload, ThreadMetadata
    from discord.types.user import PartialUser as PartialUserPayload, User as UserPayload

    GuildChannels = Union[
        discord.CategoryChannel,
        discord.ForumChannel,
        discord.StageChannel,
        discord.TextChannel,
        discord.Thread,
        discord.VoiceChannel,
    ]
    PrivateChannels = Union[discord.DMChannel, discord.GroupChannel]
    GuildChannelPayload = Union[
        CategoryChannelPayload,
        ForumChannelPayload,
        NewsChannelPayload,
        StageChannelPayload,
        TextChannelPayload,
        ThreadChannelPayload,
        VoiceChannelPayload,
    ]
    PrivateChannelPayload = Union[DMChannelPayload, GroupDMChannelPayload, InteractionDMChannelPayload]

    PayloadTypes = Union[discord.Attachment, GuildChannels, discord.Member, PrivateChannels, discord.Role, discord.User]
    Payloads = Union[
        AttachmentPayload,
        GuildChannelPayload,
        MemberPayload,
        PrivateChannelPayload,
        RolePayload,
        ThreadPayload,
        UserPayload,
    ]
else:
    GuildChannels = (
        discord.CategoryChannel,
        discord.ForumChannel,
        discord.StageChannel,
        discord.TextChannel,
        discord.Thread,
        discord.VoiceChannel,
    )
    PrivateChannels = (discord.DMChannel, discord.GroupChannel)

__all__ = ("TYPE_MAPPING", "attachment", "channel", "member", "role", "thread", "user")


def attachment(_attachment: discord.Attachment, /) -> AttachmentPayload:
    payload: AttachmentPayload = {
        "id": _attachment.id,
        "filename": _attachment.filename,
        "size": _attachment.size,
        "url": _attachment.url,
        "proxy_url": _attachment.proxy_url,
        "height": _attachment.height,
        "width": _attachment.width,
        "spoiler": _attachment.is_spoiler(),
        "ephemeral": _attachment.ephemeral,
    }
    if (description := _attachment.description) is not None:
        payload["description"] = description
    if (content_type := _attachment.content_type) is not None:
        payload["content_type"] = content_type
    if (duration_secs := _attachment.duration) is not None:
        payload["duration_secs"] = duration_secs
    if (waveform := _attachment.waveform) is not None:
        payload["waveform"] = discord.utils._bytes_to_base64_data(waveform)
    return payload


def user(_user: discord.User, /) -> UserPayload:
    return {
        "id": _user.id,
        "username": _user.name,
        "discriminator": str(_user.discriminator),
        "avatar": _user._avatar,
        "global_name": _user.global_name,
        "bot": _user.bot,
        "system": _user.system,
        "public_flags": _user._public_flags,
    }


def role(_role: discord.Role, /) -> RolePayload:
    payload: RolePayload = {
        "id": _role.id,
        "name": _role.name,
        "color": _role._colour,
        "hoist": _role.hoist,
        "position": _role.position,
        "permissions": str(_role._permissions),
        "managed": _role.managed,
        "mentionable": _role.mentionable,
        "icon": _role._icon,
        "unicode_emoji": _role.unicode_emoji,
    }
    tags = _role.tags
    if tags is not None:
        assert tags.bot_id and tags.integration_id and tags.subscription_listing_id
        tags_payload: RoleTagsPayload = {
            "bot_id": tags.bot_id,
            "integration_id": tags.integration_id,
            "subscription_listing_id": tags.subscription_listing_id,
        }
        if tags.is_premium_subscriber():
            tags_payload["premium_subscriber"] = None
        if tags.is_available_for_purchase():
            tags_payload["available_for_purchase"] = None
        if tags.is_guild_connection():
            tags_payload["guild_connections"] = None
        payload["tags"] = tags_payload
    return payload


def member(_member: discord.Member, /) -> MemberPayload:
    assert _member.joined_at is not None
    premium_since = _member.premium_since
    payload: MemberPayload = {
        "roles": list(map(str, _member._roles)),
        "joined_at": _member.joined_at.isoformat(),
        "deaf": getattr(_member.voice, "deaf", False),
        "mute": getattr(_member.voice, "mute", False),
        "flags": _member._flags,
        "user": user(_member._user),
        "premium_since": premium_since and premium_since.isoformat(),
        "pending": _member.pending,
    }
    if (avatar := _member._avatar) is not None:
        payload["avatar"] = avatar
    if (nick := _member.nick) is not None:
        payload["nick"] = nick
    if (permissions := _member._permissions) is not None:
        payload["permissions"] = str(permissions)
    if (communication_disabled_until := _member.timed_out_until) is not None:
        payload["communication_disabled_until"] = communication_disabled_until.isoformat()
    return payload


@overload
def channel(_channel: discord.CategoryChannel, /) -> CategoryChannelPayload:
    ...


@overload
def channel(_channel: discord.DMChannel, /) -> Union[DMChannelPayload, InteractionDMChannelPayload]:
    ...


@overload
def channel(_channel: discord.ForumChannel, /) -> ForumChannelPayload:
    ...


@overload
def channel(_channel: discord.GroupChannel, /) -> GroupDMChannelPayload:
    ...


@overload
def channel(_channel: discord.StageChannel, /) -> StageChannelPayload:
    ...


@overload
def channel(_channel: discord.TextChannel, /) -> TextChannelPayload:
    ...


@overload
def channel(_channel: discord.Thread, /) -> ThreadChannelPayload:
    ...


@overload
def channel(_channel: discord.VoiceChannel, /) -> VoiceChannelPayload:
    ...


def channel(
    _channel: Union[GuildChannels, PrivateChannels, discord.Thread], /
) -> Union[GuildChannelPayload, PrivateChannelPayload, ThreadChannelPayload]:
    if not isinstance(_channel, (*GuildChannels, *PrivateChannels, discord.Thread)):  # type: ignore
        raise TypeError("Invalid channel type provided")

    if isinstance(_channel, discord.Thread):
        thread_metadata: ThreadMetadata = {
            "archived": _channel.archived,
            "auto_archive_duration": _channel.auto_archive_duration,  # type: ignore
            "archive_timestamp": _channel.archive_timestamp.isoformat(),
            "locked": _channel.locked,
            "invitable": _channel.invitable,
        }
        if (archiver_id := _channel.archiver_id) is not None:
            thread_metadata["archiver_id"] = archiver_id
        if (created_timestamp := _channel._created_at) is not None:
            thread_metadata["create_timestamp"] = created_timestamp.isoformat()
        thread_payload: ThreadChannelPayload = {
            "id": _channel.id,
            "name": _channel.name,
            "type": _channel._type.value,
            "guild_id": _channel.guild.id,
            "parent_id": _channel.parent_id,
            "owner_id": _channel.owner_id,
            "nsfw": _channel.is_nsfw(),
            "last_message_id": _channel.last_message_id,
            "rate_limit_per_user": _channel.slowmode_delay,
            "message_count": _channel.message_count,
            "member_count": _channel.member_count,
            "thread_metadata": thread_metadata,
            "flags": _channel._flags,
            "applied_tags": list(_channel._applied_tags),
        }
        return thread_payload

    if isinstance(_channel, discord.abc.GuildChannel):
        base_guild_channel: _BaseGuildChannel = {
            "id": _channel.id,
            "name": _channel.name,
            "guild_id": _channel.guild.id,
            "position": _channel.position,
            "permission_overwrites": [overwrite._asdict() for overwrite in _channel._overwrites],
            "nsfw": _channel.nsfw,
            "parent_id": _channel.category_id,
        }
        if isinstance(_channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel)):
            base_text_channel: _BaseTextChannel = {
                **base_guild_channel,
                "last_message_id": _channel.last_message_id,
                "rate_limit_per_user": _channel.slowmode_delay,
            }
            if isinstance(_channel, discord.TextChannel):
                text_payload: TextChannelPayload = {
                    **base_text_channel,
                    "type": 0,
                    "default_thread_rate_limit_per_user": _channel.default_thread_slowmode_delay,
                    "default_auto_archive_duration": _channel.default_auto_archive_duration,
                }
                if (topic := _channel.topic) is not None:
                    text_payload["topic"] = topic
                return text_payload
            elif isinstance(_channel, discord.VoiceChannel):
                voice_payload: VoiceChannelPayload = {
                    **base_guild_channel,
                    "type": 2,
                    "bitrate": _channel.bitrate,
                    "user_limit": _channel.user_limit,
                    "video_quality_mode": _channel.video_quality_mode.value,
                }
                if (rtc_regoin := _channel.rtc_region) is not None:
                    voice_payload["rtc_region"] = rtc_regoin
                return voice_payload
            elif isinstance(_channel, discord.ForumChannel):
                reaction_emoji = _channel.default_reaction_emoji
                available_tags: List[ForumTagPayload] = [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "moderated": tag.moderated,
                        "emoji_id": tag.emoji and tag.emoji.id,
                        "emoji_name": tag.emoji and tag.emoji.name,
                    }
                    for tag in _channel._available_tags.values()
                ]
                forum_payload: ForumChannelPayload = {
                    **base_text_channel,
                    "type": 15,
                    "available_tags": available_tags,
                    "default_reaction_emoji": reaction_emoji
                    and {"emoji_id": reaction_emoji.id, "emoji_name": reaction_emoji.name},
                    "default_sort_order": _channel.default_sort_order and _channel.default_sort_order.value,
                    "default_forum_layout": _channel.default_layout.value,
                    "flags": _channel._flags,
                }
                return forum_payload
        elif isinstance(_channel, discord.CategoryChannel):
            category_payload: CategoryChannelPayload = {**base_guild_channel, "type": 4}
            return category_payload
        elif isinstance(_channel, discord.StageChannel):
            stage_payload: StageChannelPayload = {
                **base_guild_channel,
                "type": 13,
                "bitrate": _channel.bitrate,
                "user_limit": _channel.user_limit,
            }
            if (rtc_regoin := _channel.rtc_region) is not None:
                stage_payload["rtc_region"] = rtc_regoin
            if (topic := _channel.topic) is not None:
                stage_payload["topic"] = topic
            return stage_payload
    elif isinstance(_channel, discord.DMChannel):
        dm_payload: Union[DMChannelPayload, InteractionDMChannelPayload] = {
            "type": 1,
            "id": _channel.id,
            # TypeDict wants these attributes, but they are not stored
            "last_message_id": 0,
            "name": "",
            "recipients": [],
        }
        if _channel.recipient is not None:
            dm_payload["recipients"] = [user(_channel.recipient)]
        return dm_payload
    elif isinstance(_channel, discord.GroupChannel):
        recipients: List[PartialUserPayload] = [
            {
                "id": user.id,
                "username": user.name,
                "discriminator": user.discriminator,
                "avatar": user._avatar,
                "global_name": user.global_name,
            }
            for user in _channel.recipients
        ]
        group_payload: GroupDMChannelPayload = {
            "id": _channel.id,
            "type": 3,
            # Type checker doesn't allow me to simply leave these as None
            "name": cast(str, _channel.name),
            "icon": cast(str, _channel._icon),
            "owner_id": cast(str, _channel.owner_id),
            "recipients": recipients,
        }
        return group_payload


def thread(_thread: discord.Thread, /) -> ThreadPayload:
    thread_metadata: ThreadMetadata = {
        "archived": _thread.archived,
        "auto_archive_duration": _thread.auto_archive_duration,  # type: ignore
        "archive_timestamp": _thread.archive_timestamp.isoformat(),
        "locked": _thread.locked,
        "invitable": _thread.invitable,
    }
    if (archiver_id := _thread.archiver_id) is not None:
        thread_metadata["archiver_id"] = archiver_id
    if (created_timestamp := _thread._created_at) is not None:
        thread_metadata["create_timestamp"] = created_timestamp.isoformat()

    payload: ThreadPayload = {
        "id": _thread.id,
        "guild_id": _thread.guild.id,
        "parent_id": _thread.parent_id,
        "owner_id": _thread.owner_id,
        "name": _thread.name,
        "type": _thread._type.value,
        "member_count": _thread.member_count,
        "message_count": _thread.message_count,
        "rate_limit_per_user": _thread.slowmode_delay,
        "thread_metadata": thread_metadata,
        "last_message_id": _thread.last_message_id,
        "flags": _thread._flags,
        "applied_tags": list(_thread._applied_tags),
    }
    if (me := _thread.me) is not None:
        payload["member"] = {
            "id": me.thread_id,
            "user_id": me.id,
            "join_timestamp": me.joined_at.isoformat(),
            "flags": me.flags,
        }
    return payload


TYPE_MAPPING = {
    discord.Attachment: attachment,
    discord.TextChannel: channel,
    discord.CategoryChannel: channel,
    discord.CategoryChannel: channel,
    discord.DMChannel: channel,
    discord.ForumChannel: channel,
    discord.GroupChannel: channel,
    discord.StageChannel: channel,
    discord.TextChannel: channel,
    discord.VoiceChannel: channel,
    discord.Member: member,
    discord.Role: role,
    discord.Thread: thread,
    discord.User: user,
}
