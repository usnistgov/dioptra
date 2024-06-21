# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
"""
A module for Dioptra's REST API query language.

This module is responsible for defining the query language and providing a parser.
It parses syntactically correct search queries into a list of search terms. It also
provides support for constructing sqlalchemy WHERE clauses from a parsed query.
"""
from typing import Any

import pyparsing as pp
from sqlalchemy import and_, or_

from dioptra.restapi.errors import SearchParseError


def _define_query_grammar() -> pp.ParserElement:
    """
    Defines the grammar for the Dioptra query language. The value of the REST
    API's `search` query parameter conforms to this grammar.

    The grammar supports a comma separated list of search terms.

    Returns:
        The pyparsing grammar.
    """

    # A wildcard is a '*' (multi) or a '?' (single) that is not escaped with a '\'
    wildcard = ~pp.Literal("\\") + (pp.Literal("*") | pp.Literal("?"))

    # An escaped character is a '\' followed by a character that needs to be escaped
    escape = pp.Literal("\\") + pp.Word("\\?*\"'n", exact=1)

    # Spaces are allowed in unquoted searches, but not when a field is specified
    space = pp.Literal(" ")

    # Unquoted searches are limited to words containing alphanumerics and underscores
    unquoted_word = pp.Combine((escape | pp.Word(pp.alphanums + "_") + ~space)[1, ...])
    unquoted_words = (
        pp.Combine((escape | pp.Word(pp.alphanums + "_"))[1, ...]) | space
    )[1, ...]
    # quoted searches can include any printable characters
    sgl_quoted_words = pp.Combine(
        (escape | pp.Word(pp.printables + " ", exclude_chars="\\?*'\n"))[1, ...]
    )
    dbl_quoted_words = pp.Combine(
        (escape | pp.Word(pp.printables + " ", exclude_chars='\\?*"\n'))[1, ...]
    )

    # The search strings are a sequence of one ore more valid characters and wildcards
    unquoted_search_word = (unquoted_word | wildcard)[1, ...]
    unquoted_search_string = (unquoted_words | wildcard)[1, ...]
    sgl_quoted_search_string = (
        pp.Suppress("'") + (sgl_quoted_words | wildcard)[1, ...] + pp.Suppress("'")
    )
    dbl_quoted_search_string = (
        pp.Suppress('"') + (dbl_quoted_words | wildcard)[1, ...] + pp.Suppress('"')
    )
    quoted_search_string = sgl_quoted_search_string | dbl_quoted_search_string
    search_string = pp.Group(quoted_search_string | unquoted_search_string)
    field_search_value = pp.Group(quoted_search_string | unquoted_search_word)

    # A field name can contain alphabetical characters and underscores.
    field_name = pp.Word(pp.alphas + "_")
    # A colon is used as the separator between search fields and search strings.
    assign = pp.Suppress(pp.Literal(":"))
    # A field search string is a field name and search string separated by a colon.
    field_search_string = pp.Group(field_name + assign + field_search_value)

    # A search term is either a single search string or a search field:string pair.
    search_term = field_search_string | search_string

    # The full grammar is a comma-delimited list of search terms.
    grammar = pp.delimitedList(search_term, delim=",")

    return grammar


DIOPTRA_QUERY_GRAMMAR = _define_query_grammar()


def parse_search_text(search_text: str) -> list[dict]:
    """
    Parses the search text into a tokenized list of search terms.

    Args:
        search_text: the raw search text provided by the user.

    Returns:
        A list of dictionaries containing the tokenized search terms. Each dictionary
            contains a 'field' and 'value' key. The field is the name of the field to
            be searched or None to indicate the query should not be restricted by
            field. The value is a list of strings that represent the search value.
    """

    parsed_search = DIOPTRA_QUERY_GRAMMAR.parse_string(
        search_text, parse_all=True
    ).as_list()
    formatted_result = []
    for term in parsed_search:
        if len(term) > 1 and isinstance(term[1], list):
            formatted_result.append({"field": term[0], "value": term[1]})
        else:
            formatted_result.append({"field": None, "value": term})
    return formatted_result


def construct_sql_search_value(search_term: list[str], fuzzy: bool = False) -> str:
    """
    Constructs a search value for a SQL query from a tokenized list by replacing
    wildcards and joining the string.

    Args:
        search_value: A tokenized list of strings representing a search term.
        fuzzy: Perform a fuzzy search by placing a wildcard between words.

    Returns:
        A string to be used as the value in the WHERE clause of a SQL query.
    """
    search_term = [text.replace("/", r"//") for text in search_term]
    search_term = [text.replace("%", r"/%") for text in search_term]
    search_term = [text.replace("_", r"/_") for text in search_term]
    search_term = ["%" if text == "*" else text for text in search_term]
    search_term = ["_" if text == "?" else text for text in search_term]
    search_term = [text.replace(r"\\", "\\") for text in search_term]
    search_term = [text.replace(r"\*", "*") for text in search_term]
    search_term = [text.replace(r"\?", "?") for text in search_term]
    search_term = [text.replace(r"\"", '"') for text in search_term]
    search_term = [text.replace(r"'", "'") for text in search_term]
    search_term = [text.replace(r"\n", "\n") for text in search_term]
    if fuzzy:
        return "%" + "%".join(search_term) + "%"
    else:
        return "".join(search_term)


def construct_sql_query_filters(search_string: str, searchable_fields: dict[str, Any]):
    """
    Constructs a search filter to be used by sqlalchemy.

    Args:
        search_string: A string conforming to the search grammar.

    Returns:
        A filter that can be used in a sqlalchemy query.

    Raises:
        SearchParseError: If a search string cannot be parsed.
    """
    if not search_string:
        return True

    try:
        parsed_search_terms = parse_search_text(search_string)
    except pp.ParseException as error:
        raise SearchParseError(error.line, repr(error)) from error

    query_filters: list = []
    for search_term in parsed_search_terms:
        field: str = search_term["field"]
        if field is None:
            value = construct_sql_search_value(search_term["value"], fuzzy=True)
            filter = or_(filter_fn(value) for filter_fn in searchable_fields.values())
        elif field in searchable_fields:
            value = construct_sql_search_value(search_term["value"])
            filter = searchable_fields[field](value)
        else:
            raise SearchParseError(search_string, f"'{field}' is not a valid field")
        query_filters.append(filter)

    return and_(*query_filters)


if __name__ == "__main__":
    """
    A simple demonstration of the query grammar with sample queries.
    """

    DIOPTRA_QUERY_GRAMMAR.run_tests(
        r"""
        # search all text fields matching 'search_*'
        search_*
        # search all text the exactly match 'search_*'
        search_\*
        # a quoted search term can contain spaces and other characters
        "search \"this\", and 'that'"
        # multiple search terms can be provided via a comma-separated list
        "search=this", 'and, how about "this\?"',this_too
        # search tags whose name matches 'classification' exactly
        tag:classification
        # search tags whose name starts with 'class'
        tag:class*
        # search descriptions containing mnist and whose tag name matches 'cv' exactly
        description:*mnist*,tag:cv
        # search for name starting with 'trial_' and ending with two valid characters
        name:trial_??
        # search for literal '*'
        \*
        # multi-word search
        search all for this
        # field multi-word search
        field:"search all for this"
        """,
        full_dump=False,
    )

    DIOPTRA_QUERY_GRAMMAR.run_tests(
        r"""
        # invalid multi word field search
        field:search all for this
        # incorrect assignment character used
        bad=assignment
        # invalid characters in field name
        bad-name:classification
        # invalid delimiter between search terms
        description:bad_delim|tag:cv
        # missing closing quote
        "forgot to close this quote
        # tried to escape an unescapable character
        \q
        """,
        full_dump=False,
    )
