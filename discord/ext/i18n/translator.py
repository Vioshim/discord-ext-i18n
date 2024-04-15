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

from logging import getLogger
from typing import Any

import regex as re
from discord.app_commands import (
    TranslationContext,
    TranslationContextLocation,
    locale_str,
)
from discord.utils import _from_json

from discord import Locale, app_commands
from discord.ext import commands

from .extension import I18nExtension

CHECKER = re.compile(r"^[-_\p{L}\p{N}\p{sc=Deva}\p{sc=Thai}]{1,32}$")

log = getLogger(__name__)

__all__ = ("I18nTranslator",)


class I18nTranslator(app_commands.Translator):
    path: str = "locale"
    fallback: Locale = Locale.american_english
    pattern: str = "*.json"
    delimiter: str = "."

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get_locale(self, ctx: commands.Context) -> Locale:
        if ctx.interaction:
            return ctx.interaction.locale
        if ctx.guild:
            return ctx.guild.preferred_locale
        return self.fallback

    def process(self, text: str) -> dict[str, Any]:
        return _from_json(text)

    async def load(self) -> None:
        self.i18n = I18nExtension.load_files(
            bot=self.bot,
            path=self.path,
            fallback=self.fallback,
            pattern=self.pattern,
            method=self.process,
            delimiter=self.delimiter,
            get_locale_func=self.get_locale,
        )

    async def unload(self) -> None:
        self.i18n.unload()

    async def translate(
        self, string: locale_str, locale: Locale, context: TranslationContext
    ) -> str:
        should_lower = False

        match context.location:
            case (
                TranslationContextLocation.command_name
                | TranslationContextLocation.group_name
                | TranslationContextLocation.command_description
                | TranslationContextLocation.group_description
            ):
                _, info = context.location.name.split("_")
                if isinstance(context.data, app_commands.ContextMenu):
                    key = f"interactions.{string.message}.{info}"
                else:
                    should_lower = info == "name"
                    ref = string.message if should_lower else context.data.name
                    *data, _ = str(context.data.qualified_name).split()
                    data.append(ref)
                    text = ".group.".join(data)
                    key = f"commands.{text}.{info}"
            case TranslationContextLocation.parameter_name | TranslationContextLocation.parameter_description:
                _, info = context.location.name.split("_")
                text = ".group.".join(str(context.data.command.qualified_name).split())
                should_lower = info == "name"
                ref = string.message if should_lower else context.data.name
                key = f"commands.{text}.params.{ref}.{info}"

            case TranslationContextLocation.choice_name:  # Choice
                if route := string.extras.get("locale", ""):
                    *items, command = route.split(".")
                    text = ".group.".join(items)
                    key = f"commands.{text}.params.{command}.choices.{string.message}"
                else:
                    return string.message
            case _:
                key = f"{context.location.name}.{string.message}"

        item = I18nExtension.contextual_get_text(
            key=key,
            locale=str(locale),
            raise_on_empty=False,
            **string.extras,
        )
        item = item.lower() if should_lower else item
        if not item or (should_lower and not CHECKER.match(item)):
            log.warning("Value %r is not a valid name with key %r", item, key)
            return string.message

        return item
