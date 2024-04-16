# Copyright (C) 2024 Vioshim (original author: Avery)
#
# This file is part of discord-ext-i18n.
#
# discord-ext-i18n is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# discord-ext-i18n is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with discord-ext-i18n.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import annotations

import contextvars
import re
from functools import partial
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from discord.utils import _from_json, maybe_coroutine
from yaml import safe_load as yaml_load

from discord import Locale
from discord.ext import commands

from .exceptions import NoDefaultI18nInstanceError
from .i18n import I18n
from .language import Language

PARSER = re.compile(r"\{\{([^{}]+)\}\}", re.MULTILINE)

__all__ = (
    "I18nExtension",
    "load_files",
    "flatten_dict",
    "unload",
    "_",
)

L = TypeVar("L", Locale, str)


def flatten_dict(data: dict[str, Any] | list, delimiter: str = "."):
    def _flatten(current_dict: dict[str, Any] | list, key_prefix: str = ""):
        if isinstance(current_dict, list):
            pairs = enumerate(current_dict)
        else:
            pairs = current_dict.items()

        items = {}
        for k, v in pairs:
            key = f"{key_prefix}{delimiter}{k}" if key_prefix else f"{k}"
            if isinstance(v, (dict, list)):
                items.update(_flatten(v, key))
            else:
                items[key] = v
        return items

    return dict(_flatten(data))


class I18nExtension(I18n[L]):
    default_instance: Optional[I18nExtension] = None

    def __init__(
        self,
        languages: list[Language[L]],
        fallback: L = Locale.american_english,
        bot: Optional[commands.Bot] = None,
        get_locale_func: Optional[Callable[[commands.Context], L]] = None,
        default: bool = True,
    ) -> None:
        super(I18nExtension, self).__init__(languages, fallback)
        self._current_locale = contextvars.ContextVar("_current_locale")
        self._bot = None

        if default or I18nExtension[L].default_instance is None:
            I18nExtension[L].default_instance = self

        if bot:
            self.init_bot(bot, get_locale_func)

    @classmethod
    def get_locale_or_fallback(cls, fallback: L):
        """Get the locale from the context or fallback to the given locale.

        Parameters
        ----------
        fallback : Locale | str
            The locale to fallback to if no locale is found.
        """

        def inner(ctx: commands.Context):
            if ctx.interaction:
                return ctx.interaction.locale
            if ctx.guild:
                return ctx.guild.preferred_locale
            return fallback

        return inner

    def init_bot(
        self,
        bot: commands.Bot,
        get_locale_func: Optional[Callable[[commands.Context], L]] = None,
    ):
        """Initialize the bot with this extension.

        Parameters
        ----------
        bot : commands.Bot
            The bot to initialize with.
        get_locale_func : Callable[[commands.Context], Locale | str], optional
            A function to get the locale from the context, by default None.
        """
        self._bot = bot

        if get_locale_func is None:
            method = self.get_locale_or_fallback(self._fallback)
        else:
            method = get_locale_func

        async def pre(ctx: commands.Context):
            locale = await maybe_coroutine(method, ctx)
            self.set_current_locale(locale)

        self._bot.before_invoke(pre)

    def set_current_locale(self, locale: Locale | str):
        self._current_locale.set(locale)

    def get_current_locale(self) -> Locale | str:
        return self._current_locale.get(self._fallback)

    @classmethod
    def contextual_get_text(
        cls,
        key: str,
        locale: Optional[L] = None,
        list_formatter: Optional[Callable[[list[str]], str]] = None,
        use_translations: bool = True,
        should_fallback: bool = True,
        raise_on_empty: bool = False,
        **kwargs,
    ) -> str:
        i18n = cls.default_instance

        if i18n is None:
            raise NoDefaultI18nInstanceError()

        if locale is None:
            current_locale = i18n.get_current_locale()
        else:
            current_locale = locale

        return i18n.get_text(
            key=key,
            locale=current_locale,
            list_formatter=list_formatter,
            use_translations=use_translations,
            should_fallback=should_fallback,
            raise_on_empty=raise_on_empty,
            **kwargs,
        )

    @staticmethod
    def parser(
        route: Path,
        method: Callable[[str], dict[str, str]] = _from_json,
        delimiter: str = ".",
    ) -> tuple[str, Locale | str, dict[str, str]]:
        """Get the name and code from the filename, popular i18n file naming convention.

        Parameters
        ----------
        filename : str
            The filename to parse.

        Returns
        -------
        tuple[str, Locale | str, dict]
            The name and code.
        """
        name = route.stem

        if "_" in name:
            lang_name, *_, lang_code = name.split("_")
        else:
            lang_name, lang_code = name, ""

        info = flatten_dict(
            method(PARSER.sub(r"{\1}", route.read_text(encoding="utf-8"))),
            delimiter=delimiter,
        )

        try:
            item = Locale(lang_code or lang_name)
            return lang_name or item.name, item, info
        except ValueError:
            pass

        try:
            item = Locale[(lang_code or lang_name).lower()]
            return lang_name or item.name, item, info
        except ValueError:
            pass

        return lang_name, lang_code, info

    @classmethod
    def load_files(
        cls,
        bot: Optional[commands.Bot] = None,
        path: str = ".",
        fallback: Optional[L] = None,
        pattern: str = "*.json",
        method: Callable[[str], dict[str, str]] = _from_json,
        delimiter: str = ".",
        get_locale_func: Optional[Callable[[commands.Context], L]] = None,
    ):
        """Load the languages from a glob pattern.

        Parameters
        ----------
        bot : commands.Bot
            The bot to initialize with.
        path : str, optional
            The path to the directory. By default current directory.
        fallback : Locale | str, optional
            The locale to fallback to if no locale is found. By default american_english.
        pattern : str, optional
            The glob pattern to search for, by default "**/*.json".
        method : Optional[Callable[[str], dict]], optional
            The method to use to parse the file, by default discord.utils._from_json.
        delimiter : str, optional
            The delimiter to use for the translations, by default ".".
        get_locale_func : Callable[[commands.Context], str], optional
            A function to get the locale from the context, by default None.
        """

        route = Path(path)
        name_code_method = partial(cls.parser, method=method, delimiter=delimiter)
        return cls(
            languages=[
                Language[L](
                    name=name,
                    code=code,  # type: ignore
                    translations=info,
                )
                for name, code, info in map(name_code_method, route.glob(pattern))
            ],
            fallback=fallback or Locale.american_english,
            bot=bot,
            get_locale_func=get_locale_func,
        )

    @classmethod
    def yaml_load(
        cls,
        bot: Optional[commands.Bot] = None,
        path: str = ".",
        fallback: Optional[L] = None,
        pattern: str = "**/*.yaml",
        method: Callable[[str], dict[str, str]] = yaml_load,
        delimiter: str = ".",
        get_locale_func: Optional[Callable[[commands.Context], str]] = None,
    ):
        """Shortcut to load yaml files."""
        cls.load_files(
            bot=bot,
            path=path,
            fallback=fallback,
            pattern=pattern,
            method=method,
            delimiter=delimiter,
            get_locale_func=get_locale_func,
        )

    @classmethod
    def unload(
        cls,
        bot: Optional[commands.Bot] = None,
        remove_before_invoke: bool = False,
    ):
        """Unload the languages from the class"""

        i18n = cls.default_instance
        if i18n is None:
            raise NoDefaultI18nInstanceError()

        if bot and remove_before_invoke:
            bot._before_invoke = None

        cls.default_instance = None
        i18n._bot = None
        i18n._current_locale = contextvars.ContextVar("_current_locale")


load_files = I18nExtension.load_files
unload = I18nExtension.unload
_ = I18nExtension.contextual_get_text
