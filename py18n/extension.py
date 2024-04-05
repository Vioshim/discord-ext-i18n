# Copyright (C) 2021 Avery
#
# This file is part of py18n.
#
# py18n is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# py18n is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with py18n.  If not, see <http://www.gnu.org/licenses/>.


import contextvars
import re
from pathlib import Path
from typing import Callable, Optional

from discord import Locale
from discord.ext import commands
from discord.utils import _from_json, maybe_coroutine

from .exceptions import NoDefaultI18nInstanceError
from .i18n import I18n
from .language import Language

PARSER = re.compile(r"\{\{([^{}]+)\}\}", re.MULTILINE)


def get_locale_or_fallback(fallback: str | int | Locale):
    """Get the locale from the context or fallback to the given locale.

    Parameters
    ----------
    fallback : str | int | Locale
        The locale to fallback to if no locale is found.
    """
    fallback = str(fallback) if isinstance(fallback, Locale) else fallback

    def inner(ctx: commands.Context) -> str:
        if ctx.interaction:
            return str(ctx.interaction.locale)
        if ctx.guild:
            return str(ctx.guild.preferred_locale)
        return fallback

    return inner


def flatten_dict(d: dict, sep: str = ".") -> dict:
    def _flatten(current_dict: dict, key_prefix: str = ""):
        items = {}
        for k, v in current_dict.items():
            new_key = f"{key_prefix}{sep}{k}" if key_prefix else k
            
            if isinstance(v, dict):
                items.update(_flatten(v, new_key))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    sub_key = f"{new_key}{sep}{i}"
                    if isinstance(item, dict):
                        items.update(_flatten(item, sub_key))
                    else:
                        items[sub_key] = item
            else:
                items[new_key] = v
                
        return items

    return _flatten(d)


class I18nExtension(I18n):
    default_instance: Optional["I18nExtension"] = None

    def __init__(
        self,
        languages: list[Language],
        fallback: str | int | Locale,
        bot: Optional[commands.Bot] = None,
        get_locale_func: Callable[[commands.Context], str] = None,
        default: bool = True,
    ) -> None:
        fallback = fallback if isinstance(fallback, (str, int)) else str(fallback)
        super(I18nExtension, self).__init__(languages, fallback)
        self._current_locale = contextvars.ContextVar("_current_locale")
        self._bot = None

        if default or I18nExtension.default_instance is None:
            I18nExtension.default_instance = self

        if bot:
            self.init_bot(bot, get_locale_func or get_locale_or_fallback(fallback))

    def init_bot(
        self,
        bot: commands.Bot,
        get_locale_func: Callable[[commands.Context], str] = None,
    ):
        """Initialize the bot with this extension.

        Parameters
        ----------
        bot : commands.Bot
            The bot to initialize with.
        get_locale_func : Callable[[commands.Context], str], optional
            A function to get the locale from the context, by default None.
        """
        self._bot = bot

        if get_locale_func is None:
            get_locale_func = get_locale_or_fallback(self._fallback)

        async def pre(ctx: commands.Context):
            locale = await maybe_coroutine(get_locale_func, ctx)
            self.set_current_locale(locale)

        self._bot.before_invoke(pre)

    def set_current_locale(self, locale: str) -> None:
        self._current_locale.set(locale)

    def get_current_locale(self) -> str:
        return self._current_locale.get(self._fallback)

    @classmethod
    def contextual_get_text(
        cls,
        key: str,
        locale: Optional[str | int | Locale] = None,
        list_formatter: bool = None,
        use_translations: bool = True,
        should_fallback: bool = True,
        raise_on_empty: bool = False,
        **kwargs,
    ) -> str:
        i18n = cls.default_instance
        if i18n is None:
            raise NoDefaultI18nInstanceError()

        if locale is None:
            locale = i18n.get_current_locale()
        else:
            locale = str(locale) if isinstance(locale, Locale) else locale

        return i18n.get_text(
            key,
            locale,
            list_formatter=list_formatter,
            use_translations=use_translations,
            should_fallback=should_fallback,
            raise_on_empty=raise_on_empty,
            **kwargs,
        )

    @staticmethod
    def name_code_method(filename: str) -> tuple[str, str]:
        """Get the name and code from the filename, popular i18n file naming convention.

        Parameters
        ----------
        filename : str
            The filename to parse.

        Returns
        -------
        tuple[str, str]
            The name and code.
        """
        a, *_, b = filename.removesuffix(".json").split("_")
        return a, b

    @classmethod
    def load(
        cls,
        bot: commands.Bot,
        path: str = ".",
        fallback: str | int | Locale = Locale.american_english,
        pattern: str = "**/*.json",
        from_json: Callable[[str], dict] = _from_json,
        method: Optional[Callable[[str], tuple[str, str]]] = None,
        delimiter: str = ".",
        dict_cls: type[dict] = dict,
        get_locale_func: Callable[[commands.Context], str] = None,
    ):
        """Load the languages from a glob pattern.

        Parameters
        ----------
        bot : commands.Bot
            The bot to initialize with.
        path : str, optional
            The path to the directory. By default current directory.
        fallback : str | int | Locale, optional
            The locale to fallback to if no locale is found. By default american_english.
        pattern : str, optional
            The glob pattern to search for, by default "**/*.json".
        method : Optional[Callable[[str], dict]], optional
            The method to use to parse the file, by default discord.utils._from_json.
        delimiter : str, optional
            The delimiter to use for the translations, by default ".".
        dict_cls : type[dict], optional
            The dictionary class to use for the translations, by default dict.
        get_locale_func : Callable[[commands.Context], str], optional
            A function to get the locale from the context, by default None.
        """

        route = Path(path)
        method = method or cls.name_code_method

        return cls(
            languages=[
                Language(name=name, code=code, translations=flatten_dict(item))
                for name, code, item in map(
                    lambda x: (
                        *method(x.name),
                        from_json(PARSER.sub(r"{\1}", x.read_text(encoding="utf-8"))),
                    ),
                    route.glob(pattern),
                )
            ],
            fallback=str(fallback) if isinstance(fallback, Locale) else fallback,
            bot=bot,
            get_locale_func=get_locale_func,
        )

    @classmethod
    def unload(cls, bot: commands.Bot, remove_before_invoke: bool = False):
        """Unload the languages from the class"""

        i18n = cls.default_instance
        if i18n is None:
            raise NoDefaultI18nInstanceError()

        if remove_before_invoke:
            bot._before_invoke = None
        i18n._bot = None
        i18n._current_locale = contextvars.ContextVar("_current_locale")


load = I18nExtension.load
unload = I18nExtension.unload
_ = I18nExtension.contextual_get_text
