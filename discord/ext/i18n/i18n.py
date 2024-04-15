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


from logging import getLogger
from typing import Callable, Optional, TypeVar, Generic, Iterable

from discord import Locale

from exceptions import (
    InvalidFallbackError,
    InvalidLocaleError,
    InvalidTranslationKeyError,
)
from language import Language

__all__ = ("I18n", "Language")


log = getLogger(__name__)

L = TypeVar("L", Locale, str)


class I18n(Generic[L]):
    
    __slots__ = ("_languages", "_fallback")

    def __init__(
        self,
        languages: Iterable[Language[L]],
        fallback: L,
    ):
        self._languages = {language.code: language for language in languages}

        if not (isinstance(fallback, (str, Locale)) and fallback in self._languages):
            raise InvalidFallbackError(fallback)

        self._fallback: L = fallback

    def get_text(
        self,
        key: str,
        locale: Optional[L] = None,
        list_formatter: Optional[Callable[[list[str]], str]] = None,
        use_translations: bool = True,
        should_fallback: bool = True,
        raise_on_empty: bool = True,
        **kwargs,
    ) -> str:
        """
        Wraps :func:`Language.get_text` to get translation based on the given locale

        .. seealso: documentation for :func:`Language.get_text`

        Parameters
        ----------
        key : str
            The key to search for
        locale : Locale | str
            The locale to search in
        list_formatter : Optional[Callable[[list[str]], str]], optional
            Function to format lists, by default None
        use_translations : bool, optional
            Whether to use translations in formatting, by default True
        should_fallback : bool, optional
            Should fallback to default locale, by default True
        raise_on_empty : bool, optional
            Raise errors if the key is not found, by default True

        Returns
        -------
        str
            Translated and formatted string

        Raises
        ------
        InvalidLocaleError
            If the locale does not exist on this instance
        InvalidTranslationKeyError
            If the key could not be found in the locale, nor in the fallback
            if `should_fallback` is `True`
        """
        locale = locale or self._fallback
        language = self._languages.get(locale)

        if language is None:
            if not should_fallback:
                raise InvalidLocaleError(locale)
            locale = self._fallback
            language = self._languages[locale]

        try:
            return language.get_text(
                key,
                list_formatter=list_formatter,
                use_translations=use_translations,
                raise_on_empty=raise_on_empty,
                **kwargs,
            )
        except KeyError:
            pass

        if should_fallback and locale != self._fallback:
            try:
                return self._languages[self._fallback].get_text(
                    key,
                    list_formatter=list_formatter,
                    use_translations=use_translations,
                    raise_on_empty=raise_on_empty,
                    **kwargs,
                )
            except KeyError:
                pass

        if raise_on_empty:
            raise InvalidTranslationKeyError(key, locale, self._fallback)

        log.warn(
            "Translation key %r not found in locale %r nor in fallback %r",
            key,
            locale,
            self._fallback,
        )

        return ""
