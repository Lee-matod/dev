# -*- coding: utf-8 -*-

"""
dev.utils.to_dict
~~~~~~~~~~~~~~~~~

Discord objects and their respective payload types.

:copyright: Copyright 2022-present Lee (Lee-matod)
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

if TYPE_CHECKING:

    from dev import types

__all__ = ("REQUIRES_CTX", "TYPE_MAPPING", "attachment", "channel", "member", "role", "thread", "user")


def attachment(_attachment: discord.Attachment, /) -> dict[str, Any]:
    return {
        "id": _attachment.id,
        "filename": _attachment.filename,
        "description": _attachment.description,
        "content_type": _attachment.content_type,
        "size": _attachment.size,
        "url": _attachment.url,
        "proxy_url": _attachment.proxy_url,
        "height": _attachment.height,
        "width": _attachment.width,
        "ephemeral": _attachment.ephemeral,
    }


def user(_user: discord.User, /) -> dict[str, Any]:
    return {
        "username": _user.name,
        "public_flags": _user._public_flags,  # type: ignore
        "id": str(_user.id),
        "display_name": getattr(_user, "nick", None),
        "discriminator": _user.discriminator,
        "bot": _user.bot,
        "avatar": _user._avatar,  # type: ignore
        "avatar_decoration": None,
    }


def role(_role: discord.Role, /) -> dict[str, Any]:
    return {
        "unicode_emoji": _role.unicode_emoji,
        "position": _role.position,
        "permissions": str(_role._permissions),  # type: ignore
        "name": _role.name,
        "mentionable": _role.mentionable,
        "managed": _role.managed,
        "id": str(_role.id),
        "icon": _role._icon,  # type: ignore
        "hoist": _role.hoist,
        "flags": 0,
        "description": None,
        "color": _role._colour,  # type: ignore
    }


def member(_member: discord.Member, /) -> dict[str, Any]:
    payload = {
        "roles": list(map(lambda r: str(r.id), _member._roles)),  # type: ignore
        "premium_since": str(_member.premium_since) if _member.premium_since else None,
        "pending": _member.pending,
        "nick": _member.nick,
        "joined_at": str(_member.joined_at),
        "is_pending": False,
        "flags": _member._flags,  # type: ignore
        "communication_disabled_until": str(_member.timed_out_until) if _member.timed_out_until else None,
        "avatar": _member._avatar,  # type: ignore
        "user": user(_member._user),  # type: ignore
    }
    if _member._permissions is not None:  # type: ignore
        payload["permissions"] = str(_member._permissions)  # type: ignore
    return payload


def channel(_channel: discord.abc.GuildChannel, /, context: commands.Context[types.Bot]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "type": _channel.type.value,
        "permissions": str(context.permissions.value),
        "parent_id": str(_channel.category_id) if _channel.category_id else None,
        "name": _channel.name,
        "id": str(_channel.id),
        "nsfw": _channel.nsfw,  # type: ignore
        "position": _channel.position,
        "permission_overwrites": [overwrite._asdict() for overwrite in _channel._overwrites],  # type: ignore
    }
    metadata: dict[str, Any] = {}
    if isinstance(_channel, discord.TextChannel):
        metadata.update(
            {
                "topic": _channel.topic,
                "rate_limit_per_user": _channel.slowmode_delay,
                "default_auto_archive_duration": _channel.default_auto_archive_duration,
                "last_message_id": _channel.last_message_id,
            }
        )
    elif isinstance(_channel, discord.ForumChannel):
        metadata.update(
            {
                "topic": _channel.topic,
                "rate_limit_per_user": _channel.slowmode_delay,
                "default_auto_archive_duration": _channel.default_auto_archive_duration,
                "last_message_id": _channel.last_message_id,
                "default_thread_rate_limit_per_user": _channel.default_thread_slowmode_delay,
                "default_forum_layout": _channel.default_layout.value,
                "available_tags": [tag.to_dict() for tag in _channel.available_tags],
                "default_reaction_emoji": _channel.default_reaction_emoji.to_dict()
                if _channel.default_reaction_emoji
                else None,
                "flags": _channel._flags,  # type: ignore
            }
        )
    elif isinstance(_channel, (discord.VoiceChannel, discord.StageChannel)):
        metadata.update(
            {
                "rtc_region": _channel.rtc_region,
                "video_quality_mode": _channel.video_quality_mode.value,
                "last_message_id": _channel.last_message_id,
                "rate_limit_per_user": _channel.slowmode_delay,
                "bitrate": _channel.bitrate,
                "user_limit": _channel.user_limit,
            }
        )
        if isinstance(_channel, discord.StageChannel):
            metadata["topic"] = _channel.topic
    payload.update(metadata)
    return payload


def thread(_thread: discord.Thread, /, context: commands.Context[types.Bot]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": str(_thread.id),
        "parent_id": str(_thread.parent_id),
        "owner_id": str(_thread.owner_id),
        "name": _thread.name,
        "type": _thread._type.value,  # type: ignore
        "last_message_id": _thread.last_message_id,
        "rate_limit_per_user": _thread.slowmode_delay,
        "message_count": _thread.message_count,
        "member_count": _thread.member_count,
        "flags": _thread._flags,  # type: ignore
        "thread_metadata": {
            "archiver_id": _thread.archiver_id,
            "invitable": _thread.invitable,
            "locked": _thread.locked,
            "create_timestamp": str(_thread.created_at),
            "auto_archive_duration": _thread.auto_archive_duration,
            "archived": _thread.archived,
            "archive_timestamp": str(_thread.archive_timestamp),
        },
    }
    me = context.me
    if isinstance(me, discord.Member):
        payload["member"] = {
            "id": me.id,
            "thread_id": payload["id"],
            "join_timestamp": str(me.joined_at),
            "flags": me._flags,  # type: ignore
        }
    return payload


TYPE_MAPPING = {
    discord.Attachment: attachment,
    discord.TextChannel: channel,
    discord.CategoryChannel: channel,
    discord.ForumChannel: channel,
    discord.StageChannel: channel,
    discord.VoiceChannel: channel,
    discord.Member: member,
    discord.Role: role,
    discord.Thread: thread,
    discord.User: user,
}

REQUIRES_CTX = (
    discord.TextChannel,
    discord.CategoryChannel,
    discord.ForumChannel,
    discord.StageChannel,
    discord.VoiceChannel,
    discord.Thread,
)
