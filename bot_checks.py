from discord.ext import commands


def check_for(bot: commands.Bot, check: str, specific: str = None):
    __checks__ = {

        "~": {
            "intents": {intent: dict(bot.intents)[intent] for intent in dict(bot.intents)},
            "self": bot.user.mention,
            "desc": bot.description,
            "id": bot.user.id,
            "guilds": len(bot.guilds),
            "channels": len([guild.channels for guild in bot.guilds]),
            "users": len(bot.users),
            "prefix": bot.command_prefix,
            "commands": len(bot.commands),
            "extensions": len(bot.extensions),
            "owners": ', '.join(f"<@!{owner}>" for owner in bot.owner_ids or bot.owner_id),
            "latency": bot.latency,
            "activity": bot.activity,
            "flags": {flag: dict(bot.application_flags)[flag] for flag in dict(bot.application_flags)}
        },

        "self": {
            "name": bot.user.name,
            "discrim": bot.user.discriminator,
            "mention": bot.user.mention,
            "avatar_url": bot.user.avatar.url,
            "created_at": bot.user.created_at,
            "is_verified": bot.user.verified
        },

        "commands": {},

        "owners": {},

        "guilds": {}

    }
    if specific:
        return __checks__[check][specific]
    return __checks__[check]