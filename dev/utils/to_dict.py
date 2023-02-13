# -*- coding: utf-8 -*-

"""
dev.to_dict
~~~~~~~~~~~

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

__all__ = (
    "REQUIRES_CTX",
    "TYPE_MAPPING",
    "attachment",
    "channel",
    "member",
    "role",
    "thread",
    "user",
)


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
        "flags": 0,
        "communication_disabled_until": str(_member.timed_out_until) if _member.timed_out_until else None,
        "avatar": _member._avatar,  # type: ignore
        "user": user(_member._user),  # type: ignore
    }
    if _member._permissions is not None:  # type: ignore
        payload["permissions"] = str(_member._permissions)  # type: ignore
    return payload


def channel(_channel: discord.abc.GuildChannel, /, context: commands.Context[types.Bot]) -> dict[str, Any]:
    if _channel.category_id is not None:
        parent_id = str(_channel.category_id)
    else:
        parent_id = None
    _channel.permissions_for
    return {
        "type": _channel.type.value,
        "permissions": str(context.permissions.value),
        "parent_id": parent_id,
        "name": _channel.name,
        "id": str(_channel.id),
    }


def thread(_thread: discord.Thread, /, context: commands.Context[types.Bot]) -> dict[str, Any]:
    channel_data = channel(_thread, context)  # type: ignore
    channel_data["type"] = 11
    channel_data["thread_metadata"] = {
        "locked": _thread.locked,
        "create_timestamp": str(_thread.created_at),
        "auto_archive_duration": _thread.auto_archive_duration,
        "archived": _thread.archived,
        "archive_timestamp": str(_thread.archive_timestamp),
    }
    return channel_data


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
