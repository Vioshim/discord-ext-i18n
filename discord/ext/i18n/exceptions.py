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


from discord import Locale

__all__ = (
    "I18nError",
    "InvalidLocaleError",
    "InvalidTranslationKeyError",
    "InvalidFallbackError",
    "NoDefaultI18nInstanceError",
    "TranslationKeyEmptyError",
)


class I18nError(KeyError):
    ...


class InvalidLocaleError(I18nError):
    def __init__(self, locale: Locale | str):
        super().__init__(f"Given locale {locale!r} does not exist!")
        self.locale = locale


class InvalidTranslationKeyError(I18nError):
    def __init__(self, key: str, locale: Locale | str, fallback: Locale | str):
        super().__init__(
            f"Translation {key!r} not found for locale {locale!r}, nor fallback {fallback!r}"
        )
        self.key = key
        self.locale = locale
        self.fallback = fallback


class InvalidFallbackError(I18nError):
    def __init__(self, fallback: Locale | str | int):
        super().__init__(
            f"Invalid fallback: {fallback!r}. Fallback must be a valid locale code."
        )
        self.fallback = fallback


class NoDefaultI18nInstanceError(I18nError):
    def __init__(self):
        super().__init__("No default i18n instance has been initialized!")


class TranslationKeyEmptyError(I18nError):
    def __init__(self, key: str, locale: Locale | str):
        super().__init__(
            f"Translation for key {key!r} in language {locale!r} is empty."
        )
        self.key = key
        self.locale = locale
