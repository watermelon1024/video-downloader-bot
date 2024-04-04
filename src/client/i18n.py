"""
Internationalization and localization utilities.
"""

from typing import Union

import discord
from pyi18n import PyI18n
from pyi18n.loaders import PyI18nYamlLoader


class I18n:
    """
    Internationalization and localization class.
    Provides a simple interface to get translated strings.
    """

    locales = ("en-US", "zh-TW")
    i18n_instance = PyI18n(locales, loader=PyI18nYamlLoader("locales", namespaced=True))
    i18n_get = i18n_instance.gettext

    @classmethod
    def get(
        cls,
        key: str,
        language: Union[str, discord.ApplicationContext, discord.Interaction] = "en-US",
        **kwargs,
    ) -> str:
        """
        Get a translated string.

        :param key: The key of the string.
        :type key: str
        :param language: The language to get the string in.
        :type language: str | discord.ApplicationContext
        :param kwargs: The arguments to format the string with.
        :type kwargs: dict

        :return: The translated string.
        :rtype: str
        """
        if isinstance(language, (discord.ApplicationContext, discord.Interaction)):
            language = language.locale or language.guild_locale
        if not isinstance(language, str) or language not in cls.locales:
            language = "en-US"
        return cls.i18n_get(language, key, **kwargs)

    @classmethod
    def get_all(cls, key: str, **kwargs) -> dict:
        """
        Get all translated strings for a key.

        :param key: The key of the string.
        :type key: str
        :param kwargs: The arguments to format the string with.
        :type kwargs: dict

        :return: The translated strings.
        :rtype: dict
        """
        return {locale: cls.get(key, locale, **kwargs) for locale in cls.locales}


# sourcery skip: require-return-annotation


def slash_command(identifier: str, **kwargs):
    """
    Decorator that registers a slash command.

    :param identifier: The identifier of the locale for the command.
    :type identifier: str
    """
    kwargs["name"] = I18n.get(f"slash.{identifier}.name")
    kwargs["name_localizations"] = I18n.get_all(f"slash.{identifier}.name")
    kwargs["description"] = I18n.get(f"slash.{identifier}.description")
    kwargs["description_localizations"] = I18n.get_all(f"slash.{identifier}.description")
    return discord.application_command(cls=discord.SlashCommand, **kwargs)


def message_command(identifier: str, **kwargs):
    """
    Decorator that registers a message command.

    :param identifier: The identifier of the locale for the command.
    :type identifier: str
    """
    kwargs["name"] = I18n.get(f"message.{identifier}.name")
    kwargs["name_localizations"] = I18n.get_all(f"message.{identifier}.name")
    return discord.application_command(cls=discord.MessageCommand, **kwargs)


def user_command(identifier: str, **kwargs):
    """
    Decorator that registers a user command.

    :param identifier: The identifier of the locale for the command.
    :type identifier: str
    """
    kwargs["name"] = I18n.get(f"user.{identifier}.name")
    kwargs["name_localizations"] = I18n.get_all(f"user.{identifier}.name")
    return discord.application_command(cls=discord.UserCommand, **kwargs)


def option(identifier: str, parameter_name: str, **kwargs):
    """
    Decorator that registers an option for a slash command.

    :param identifier: The identifier of the locale for the option.
    :type identifier: str
    :param parameter_name: The name of the parameter.
    :type parameter_name: str
    """
    kwargs["name"] = I18n.get(f"slash.{identifier}.option.{parameter_name}.name")
    kwargs["name_localizations"] = I18n.get_all(f"slash.{identifier}.option.{parameter_name}.name")
    kwargs["description"] = I18n.get(f"slash.{identifier}.option.{parameter_name}.description")
    kwargs["description_localizations"] = I18n.get_all(
        f"slash.{identifier}.option.{parameter_name}.description"
    )

    def decorator(func: object):
        func.__annotations__[parameter_name] = discord.Option(
            func.__annotations__.get(parameter_name, str), **kwargs
        )
        return func

    return decorator


def bool_option(identifier: str, parameter_name: str, **kwargs):
    """
    Decorator that registers a bool option for a slash command.

    :param identifier: The identifier of the locale for the option.
    :type identifier: str
    :param parameter_name: The name of the parameter.
    :type parameter_name: str
    """
    return option(
        identifier,
        parameter_name,
        choices=[discord.OptionChoice("True", "true"), discord.OptionChoice("False", "false")],
        **kwargs,
    )


class SlashCommandGroup(discord.SlashCommandGroup):
    """
    A subclass of discord.SlashCommandGroup that supports localization.
    """

    def __new__(cls, identifier: str = None, **kwargs) -> "SlashCommandGroup":
        self = super().__new__(cls, **kwargs)
        kwargs["identifier"] = identifier
        self.__original_kwargs__ = kwargs
        return self

    def __init__(self, identifier: str, **kwargs):
        """
        Initializes the SlashCommandGroup.

        :param identifier: The identifier key of the locale for the slash command.
        :type identifier: str
        """
        self.identifier = identifier
        self.prefix = f"slash.group.{identifier}"
        kwargs["name"] = I18n.get(f"{self.prefix}.name")
        kwargs["name_localizations"] = I18n.get_all(f"{self.prefix}.name")
        kwargs["description"] = I18n.get(f"{self.prefix}.description")
        kwargs["description_localizations"] = I18n.get_all(f"{self.prefix}.description")
        return super().__init__(**kwargs)

    def command(self, identifier: str, **kwargs):
        """
        Decorator that registers a slash command for slash command group.

        :param identifier: The identifier of the locale for the command.
        :type identifier: str
        """
        kwargs["name"] = I18n.get(f"{self.prefix}.{identifier}.name")
        kwargs["name_localizations"] = I18n.get_all(f"{self.prefix}.{identifier}.name")
        kwargs["description"] = I18n.get(f"{self.prefix}.{identifier}.description")
        kwargs["description_localizations"] = I18n.get_all(
            f"{self.prefix}.{identifier}.description"
        )
        return super().command(cls=discord.SlashCommand, **kwargs)

    def option(self, identifier: str, parameter_name: str, **kwargs):
        """
        Decorator that registers an option for a slash command.
        This is only available for slash command group.

        :param identifier: The identifier of the locale for the option.
        :type identifier: str
        :param parameter_name: The name of the parameter.
        :type parameter_name: str
        """
        return option(f"group.{self.identifier}.{identifier}", parameter_name, **kwargs)

    def bool_option(self, identifier: str, parameter_name: str, **kwargs):
        """
        Decorator that registers a bool option for a slash command.
        This is only available for slash command group.

        :param identifier: The identifier of the locale for the option.
        :type identifier: str
        :param parameter_name: The name of the parameter.
        :type parameter_name: str
        """
        return bool_option(f"group.{self.identifier}.{identifier}", parameter_name, **kwargs)

    def create_subgroup(
        self,
        identifier: str,
        guild_ids: list[int] | None = None,
        **kwargs,
    ) -> "SlashCommandGroup":
        if self.parent is not None:
            # TODO: Improve this error message
            raise Exception("a subgroup cannot have a subgroup")

        sub_command_group = SlashCommandGroup(
            f"{self.identifier}.{identifier}", guild_ids, parent=self, **kwargs
        )
        self.subcommands.append(sub_command_group)
        return sub_command_group
