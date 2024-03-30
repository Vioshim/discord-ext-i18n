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


from dataclasses import InitVar, dataclass, field
from typing import Callable, Optional

from flatdict import FlatterDict

from .exceptions import TranslationKeyEmptyError


class SafeDict(dict):
    def __missing__(self, key: str):
        return f"{{{key}}}"


@dataclass(slots=True, unsafe_hash=True)
class Language:
    name: str
    code: str
    translations: FlatterDict[str, str] = field(default=None, hash=False)
    delimiter: InitVar[str] = "."
    dict_class: InitVar[type[dict]] = dict

    def __post_init__(self, delimiter: str = ".", dict_class: type[dict] = dict):
        if self.translations is None:
            self.translations = FlatterDict(
                self.translations,
                delimiter=delimiter,
                dict_class=dict_class,
            )

    def _get_translation_from_key(self, key: str, raise_on_empty: bool = True) -> str:
        """
        Get the translation string from a given key. The default behaviour
        supports simple key-translation access and dotted nesting.

        Parameters
        ----------
        key : str
            The key to parse
        raise_on_empty : bool, optional
            Whether to raise a KeyError when the returned value is an empty string, by default True

        Returns
        -------
        str
            The translation listed under the given key

        Raises
        ------
        TranslationKeyEmptyError
            The translation was empty and `raise_on_empty` was set to True

        Examples
        --------
        >>> language = Language("English", "en", {
            "hello": "Hello",
            "nested": {
                "key": "Nested key",
            },
        })
        >>> language._get_translation_from_key("nested.hello")
        "Nested key"
        """
        result = self.translations.get(key, "")
        if raise_on_empty and isinstance(result, str) and not result:
            raise TranslationKeyEmptyError(key, self.code)
        return result

    def join_list(self, value: list[str], connector: str) -> str:
        """
        Sensibly join list elements together

        Parameters
        ----------
        value : list
            The list of values to combine. Automatically converted to strings
        connector : str
            The text that goes either between two items when the list is 2
            items long, or between all but the last item of the list
            and the last item of the list when the list has more than 2
            items

        Returns
        -------
        str
            The list as a "sensible" string
        """
        return connector.join(value)

    def and_(self, value: list[str], *args, **kwargs) -> str:
        """
        Wraps :func:`join_list` but uses the translation key ``and_``

        Parameters
        ----------
        value : list
            The list of values to combine. Automatically converted to strings

        Returns
        -------
        str
            The list as a "sensible" string
        """
        return self.join_list(
            value, f" {self._get_translation_from_key('and_', *args, **kwargs)} "
        )

    def or_(self, value: list[str], *args, **kwargs) -> str:
        """
        Wraps :func:`join_list` but uses the translation key ``or_``

        Parameters
        ----------
        value : list
            The list of values to combine. Automatically converted to strings

        Returns
        -------
        str
            The list as a "sensible" string
        """
        return self.join_list(
            value, f" {self._get_translation_from_key('or_', *args, **kwargs)} "
        )

    def get_text(
        self,
        key: str,
        list_formatter: Optional[Callable[[list[str]], str]] = None,
        use_translations: bool = True,
        safedict: type[dict] = SafeDict,
        raise_on_empty: bool = True,
        **kwargs,
    ) -> str:
        """
        Get the formatted translation string

        Parameters
        ----------
        key : str
            The key to search for
        list_formatter : Optional[Callable[[list[str]], str]], optional
            Function to format lists, by default None

            .. seealso :: functions :func:`and_`, :func:`or_`, :func:`join_list`
        use_translations : bool, optional
            Whether to use translations in formatting, by default True

            For example, any missing parameters for the string (wrapped
            in curly braces) can be replaced by translations in the current
            language. This could be used to mix translation entries.

                >>> language = Language("English", "en", {
                    "you_lost": "You lost the {game}",
                    "game": "game",
                })

                >>> language.get_text("you_lost")
                "You lost the game"
        safedict : type[dict], optional
            Class to use as a "Safe dict", by default :cls:`SafeDict`
        raise_on_empty : bool, optional
            Raise errors if the key is not found, by default True
        **kwargs :  dict[str, Any], optional
            Parameters to pass to translation

        Returns
        -------
        str
            The translated string

        Raises
        ------
        TranslationKeyEmptyError
            The translation was not found (raised through `_get_translation_from_key`)
        """
        base_string = self._get_translation_from_key(key, raise_on_empty=raise_on_empty)

        if isinstance(base_string, str):
            formatted_args = {
                k: list_formatter(v) if list_formatter and isinstance(v, list) else v
                for k, v in kwargs.items()
            }
            mapping = (
                {**self.translations, **formatted_args}
                if use_translations
                else formatted_args
            )
            return base_string.format_map(safedict(**mapping))
        return base_string
