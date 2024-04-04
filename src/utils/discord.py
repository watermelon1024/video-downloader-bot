"""
Discord-related utilities functions for the bot.
"""

import discord


def get_user_name(user: discord.User) -> str:
    """
    Get the name of a user.

    :param user: The user to get the name of.
    :type user: discord.User

    :return: The name of the user.
    :rtype: str
    """
    if user.discriminator == "0":
        return f"@{user.name}"
    return f"{user.name}#{user.discriminator}"
