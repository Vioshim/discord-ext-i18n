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


from logging import getLogger

from discord import Locale

from .exceptions import (
    InvalidFallbackError,
    InvalidLocaleError,
    InvalidTranslationKeyError,
)
from .language import Language

log = getLogger(__name__)


class I18n:
    __slots__ = ("_languages", "_fallback")

    def __init__(self, languages: list[Language], fallback: str | int | Locale) -> None:
        self._languages = {language.code: language for language in languages}

        if isinstance(fallback, (str, Locale)):
            self._fallback = str(fallback)
        elif isinstance(fallback, int):
            self._fallback = languages[fallback].code
        else:
            raise InvalidFallbackError(fallback)

        if self._fallback not in self._languages:
            raise InvalidLocaleError(self._fallback)

    def get_text(
        self,
        key: str,
        locale: int | str | Locale,
        list_formatter: bool = None,
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
        locale : int | str | Locale
            The locale to search in
        list_formatter : bool, optional
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
        language = self._languages.get(locale)

        if language is None:
            if not should_fallback:
                raise InvalidLocaleError(locale)
            locale = self._fallback
            language = self._languages[locale]

        try:
            base_string = language.get_text(
                key,
                list_formatter=list_formatter,
                use_translations=use_translations,
                raise_on_empty=raise_on_empty,
                **kwargs,
            )
            if isinstance(base_string, str):
                formatted_args = {
                    k: list_formatter(v)
                    if list_formatter and isinstance(v, list)
                    else v
                    for k, v in kwargs.items()
                }
                mapping = (
                    {**language.translations, **formatted_args}
                    if use_translations
                    else formatted_args
                )
                return base_string.format(**mapping)
            return base_string
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
