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
Common search functionality
"""
from collections.abc import Callable, Iterable

import sqlalchemy as sa
import sqlalchemy.sql.expression as sae

import dioptra.restapi.errors as e

# Type alias for search field callbacks
SearchFieldCallback = Callable[[str], sae.ColumnElement[bool]]


def _construct_sql_search_value(search_term: str) -> str:
    """
    Constructs a search value for a SQL query by replacing wildcards,
    escaping and un-escaping.  The escape character is assumed to be "/".

    Args:
        search_term: A search term

    Returns:
        A string to be used as the value in the WHERE clause of a SQL query.
    """
    if search_term == "*":
        search_term = "%"
    elif search_term == "?":
        search_term = "_"
    else:
        search_term = search_term.replace("/", r"//")
        search_term = search_term.replace("%", r"/%")
        search_term = search_term.replace("_", r"/_")
        search_term = search_term.replace(r"\\", "\\")
        search_term = search_term.replace(r"\*", "*")
        search_term = search_term.replace(r"\?", "?")
        search_term = search_term.replace(r"\"", '"')
        search_term = search_term.replace(r"\'", "'")
        search_term = search_term.replace(r"\n", "\n")

    return search_term


def construct_sql_query_filters(
    parsed_search_terms: list[dict], searchable_fields: dict[str, SearchFieldCallback]
) -> sae.ColumnElement[bool] | None:
    """
    Constructs a search filter to be used by sqlalchemy.

    Args:
        parsed_search_terms: A data structure describing a search; see
            parse_search_text()
        searchable_fields: A dict which maps from a search field name to a
            function of one argument which transforms a query string to an
            SQLAlchemy expression usable in the WHERE clause of a SELECT
            statement, i.e. to filter table rows.  The query string will be
            an SQL "LIKE" pattern.

    Returns:
        A filter that can be used in a sqlalchemy query, or None if no search
        terms were given.

    Raises:
        SearchParseError: if parsed_search_terms includes a field which is
            not supported (i.e. not None and not in searchable_fields)
    """
    filter_fns: Iterable[SearchFieldCallback]

    query_filters = []
    for search_term in parsed_search_terms:
        field = search_term["field"]
        values = search_term["value"]

        sql_search_values = (_construct_sql_search_value(value) for value in values)

        if field is None:
            # if no field, create a "fuzzier" combined search pattern
            combined_search_value = "%" + "%".join(sql_search_values) + "%"
            filter_fns = searchable_fields.values()
        else:
            combined_search_value = "".join(sql_search_values)
            filter_fn = searchable_fields.get(field)
            if filter_fn:
                filter_fns = (filter_fn,)
            else:
                # The "context" arg was originally the whole search string, but
                # that is not known here (only the results of parsing it).
                # The parsing has already succeeded at this point, so the
                # exception class name doesn't make any sense.  Need to rethink
                # the error class?
                raise e.SearchParseError(field, f"'{field}' is not a valid field")

        search_exprs = [filter_fn(combined_search_value) for filter_fn in filter_fns]

        if len(search_exprs) == 1:
            # avoid useless 1-arg OR
            combined_search_expr = search_exprs[0]
        else:
            combined_search_expr = sa.or_(*search_exprs)

        query_filters.append(combined_search_expr)

    if not query_filters:
        result = None
    elif len(query_filters) == 1:
        # avoid useless 1-arg AND
        result = query_filters[0]
    else:
        result = sa.and_(*query_filters)

    return result


__all__ = [
    "SearchFieldCallback",
    "construct_sql_query_filters",
]
