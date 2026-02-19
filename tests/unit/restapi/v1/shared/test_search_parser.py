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
"""Test suite for search parser operations.

This module contains a set of tests that validates the module responsible for defining
the query language used for search queries.
"""

import pytest

from dioptra.restapi.errors import SearchParseError
from dioptra.restapi.v1.shared.search_parser import (
    DIOPTRA_QUERY_GRAMMAR,
    construct_sql_query_filters,
    construct_sql_search_value,
    parse_search_text,
)


def test_grammar() -> None:
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
        # invalid multi word field search -- needs to be quoted
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


def test_parse_search_text() -> None:
    assert parse_search_text(search_text="") == []
    assert parse_search_text(
        search_text='description:"my value",tag:something,name:else,extra'
    ) == [
        {"field": "description", "value": ["my value"]},
        {"field": "tag", "value": ["something"]},
        {"field": "name", "value": ["else"]},
        {"field": None, "value": ["extra"]},
    ]


@pytest.mark.parametrize(
    "term_list, fuzzy, expected",
    [
        (["te/st"], False, "te//st"),
        (["tes%t"], False, "tes/%t"),
        (["tes_t"], False, "tes/_t"),
        (["*"], False, "%"),
        (["?"], False, "_"),
        (["value", "?"], False, "value_"),
        (["value", "*"], False, "value%"),
        (["tes\\\\t"], False, "tes\\t"),
        (["tes\\*t"], False, "tes*t"),
        (["tes\\?t"], False, "tes?t"),
        (['tes\\"t'], False, 'tes"t'),
        (["tes't"], False, "tes't"),
        (["tes\\nt"], False, "tes\nt"),
        (["tes't"], True, "%tes't%"),
        (["test", "value"], False, "testvalue"),
        (["test", "value"], True, "%test%value%"),
    ],
)
def test_construct_sql_search_value(
    term_list: list[str], fuzzy: bool, expected: str
) -> None:
    assert construct_sql_search_value(search_term=term_list, fuzzy=fuzzy) == expected


def test_construct_sql_query_filters() -> None:
    # using queues for testing this functionality since it is relatively simple
    from dioptra.restapi.db.repository.queues import QueueRepository

    assert construct_sql_query_filters(
        search_string="",
        searchable_fields=QueueRepository.SEARCHABLE_FIELDS,
    )
    # just test that it works
    construct_sql_query_filters(
        search_string='description:"my value",tag:something,name:else,extra',
        searchable_fields=QueueRepository.SEARCHABLE_FIELDS,
    )

    # invalid -- no quotes around multi word query
    with pytest.raises(SearchParseError):
        construct_sql_query_filters(
            search_string="description:my value",
            searchable_fields=QueueRepository.SEARCHABLE_FIELDS,
        )

    # invalid - unknown field
    with pytest.raises(SearchParseError):
        construct_sql_query_filters(
            search_string="test:some_value",
            searchable_fields=QueueRepository.SEARCHABLE_FIELDS,
        )
