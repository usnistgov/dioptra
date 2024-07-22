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
Try to derive better error messages for jsonschema validation errors.
"""

import collections
from typing import (
    Any,
    Callable,
    Iterable,
    MutableMapping,
    MutableSequence,
    Optional,
    Sequence,
    Union,
    cast,
)

import jsonschema
import jsonschema.exceptions
import jsonschema.protocols
import jsonschema.validators

# Type alias for general JSON schemas
_JsonSchema = Union[dict[str, Any], bool]

# Type alias for non-boolean JSON schemas
_JsonSchemaNonBool = dict[str, Any]

# Controls indentation of sub-parts of error messages
_INDENT_SIZE = 4


def _indent_lines(lines: MutableSequence[str]) -> MutableSequence[str]:
    """
    Add a level of indentation to each of the given lines.  The given
    line sequence is modified in-place, and for convenience also returned.

    Args:
        lines: A mutable sequence of line strings

    Returns:
        The same sequence object as was passed in, but containing indented
        lines.
    """
    for i, line in enumerate(lines):
        lines[i] = " " * _INDENT_SIZE + line

    return lines


def _schema_reference_to_path(ref: str) -> list[str]:
    """
    Convert a JSON-Schema reference to the same sort of path structure used in
    jsonschema ValidationError objects to identify locations in JSON.  This
    makes programmatically "following" the path to find what it refers to,
    much easier.  The general path structure is a list of strings/ints.  This
    implementation returns a list of strings and does not try to convert any
    path components to any other type.  Absent context, all-digits path
    components are ambiguous (keys or list indices?), so we mustn't change them.

    Args:
        ref: A reference value, as a fragment: "#" followed by a
            JSON-Pointer value.  If the fragment is "#" by itself, return an
            empty list.

    Returns:
        A path as a list of strings
    """

    if ref == "#":
        # I think "#" is legal, and refers to the whole document.
        ref_schema_path = []

    else:
        # Else, assume references start with "#/", i.e. are URL fragments
        # containing JSON pointers which start with "/".
        ref = ref[2:]  # strip the "#/"
        ref_schema_path = ref.split("/")

    return ref_schema_path


def _extract_schema_by_schema_path(
    schema_path: Iterable[Union[int, str]],
    full_schema: _JsonSchemaNonBool,
    schema: Optional[Union[dict[str, Any], list[Any]]] = None,
) -> Union[dict[str, Any], list[Any]]:
    """
    Find the schema sub-document referred to by a path.  The path must not
    include any "$ref" elements; references are transparently dereferenced as
    they are encountered.

    Args:
        schema_path: A path relative to "schema" (or if it is None, then
            relative to "full_schema"), as an iterable of strings/ints.
        full_schema: The full schema we are looking inside of.  This is used
            when traversing references, which are always absolute and therefore
            require restarting traversal from the top of the full schema.
        schema: The sub-part of full_schema being examined, or None.  If
            None, examine full_schema.

    Returns:
        The sub-part of schema referred to by the given path
    """

    if schema is None:
        schema = full_schema

    if isinstance(schema, dict) and "$ref" in schema:
        # jsonschema's schema paths don't actually contain "$ref" as an
        # element.  The paths pass through as if the referent was substituted
        # for the reference, and the reference wasn't even there.

        # the cast here is necessary: _schema_reference_to_path() is defined
        # to return list[str].  It never returns anything else, so I think it
        # would be incorrect to define it otherwise.  Mypy regards lists as
        # "invariant", i.e. list[A] and list[B] are considered incompatible
        # types no matter the relationship between A and B.  It is effectively
        # forcing the caller to never add anything other than strings to a
        # list[str] since that's what the called function is declared to
        # return.  In this case, the function may return me a list[str], but I
        # know I will be sole owner of it, and so I should be able to do
        # whatever I want with it, including adding values which are not
        # strings, and use it in contexts where non-string content is expected
        # (ints, in this case).
        ref_schema_path: MutableSequence[Union[int, str]] = cast(
            MutableSequence[Union[int, str]], _schema_reference_to_path(schema["$ref"])
        )
        # Here, schema_path may have integer list indices.  That's okay.
        ref_schema_path.extend(schema_path)

        result_schema = _extract_schema_by_schema_path(ref_schema_path, full_schema)

    else:
        schema_path_it = iter(schema_path)
        next_path_component = next(schema_path_it, None)

        if not next_path_component:
            result_schema = schema

        else:
            if isinstance(schema, list):
                # If current schema is a list, this path step must be
                # interpretable as an integer.  We won't actually know whether
                # a given path step which is a string comprised of all digits
                # refers to an all-digits property name, or a list index, until
                # this point.  This ambiguity occurs when splitting a JSON
                # pointer string to obtain a schema path.
                next_path_component = int(next_path_component)

            # next_path_component is correctly inferred to be Union[int, str],
            # but mypy does not consider that a valid index type.  Since
            # 'schema' can have different values at runtime (sometimes lists,
            # sometimes dicts), the below indexing can't always mean the same
            # thing: sometimes it's a key lookup in a dict, sometimes an index
            # lookup in a list.  As a static type checker, mypy seems to want
            # one meaning, and I couldn't figure out how to make that pass mypy
            # checks.
            subschema = schema[next_path_component]  # type: ignore

            result_schema = _extract_schema_by_schema_path(
                schema_path_it, full_schema, subschema
            )

    return result_schema


def _get_one_of_alternative_names(
    alternative_schemas: Iterable[Any], full_schema: _JsonSchemaNonBool
) -> list[str]:
    """
    Find names for the given alternative schemas.  The names are derived from
    "title" properties of the schemas.  Numeric suffixes may be introduced if
    necessary, to make them unique.

    Args:
        alternative_schemas: An iterable of sub-schemas, relative to
            full_schema
        full_schema: The full schema, of which the alternatives are a part.
            Important for being able to resolve references.

    Returns:
        A list of names
    """

    # It is possible, though unlikely, that more than one alternative has the
    # same name (title).  We will add a numeric counter suffix as necessary to
    # force alternative names to be unique.
    name_counts: MutableMapping[str, int] = collections.defaultdict(int)
    names = []

    for idx, alternative_schema in enumerate(alternative_schemas):
        if isinstance(alternative_schema, dict):
            # dereference if it's just a "$ref" schema
            alternative_schema = _extract_schema_by_schema_path(
                [], full_schema, alternative_schema
            )

            name = alternative_schema.get("title")
            if not name:
                name = "Alternative #" + str(idx + 1)

        else:
            # rare case... would only apply to true/false schemas I think.
            name = "Alternative #" + str(idx + 1)

        # uniquefy names, just in case...
        name_count = name_counts[name]
        name_counts[name] += 1
        if name_count == 0:
            names.append(name)
        else:
            names.append("{}({})".format(name, name_count + 1))

    return names


def _is_valid_for_sub_schema(
    full_schema: _JsonSchemaNonBool, sub_schema: _JsonSchema, sub_instance: Any
) -> bool:
    """
    Run a validation of document sub_instance against sub_schema.

    Args:
        full_schema: The full schema, of which sub_schema is a part.
            Important for being able to resolve references.
        sub_schema: The schema to use for validation
        sub_instance: The instance document to validate

    Returns:
        True if sub_instance is valid; False if not
    """
    validator_class = jsonschema.validators.validator_for(full_schema)

    # Without this type annotation, the is_valid() call below is treated as
    # returning Any, and mypy errors since this function is defined to return
    # bool!  Even with the jsonschema type stubs, mypy gets confused.
    validator: jsonschema.protocols.Validator = validator_class(
        schema=sub_schema,
        # Need to construct a resolver from the full schema, since the
        # sub-schema might contain references relative to the full schema,
        # and we need to be able to resolve them.
        resolver=jsonschema.validators.RefResolver.from_schema(full_schema),
    )

    return cast(bool, validator.is_valid(sub_instance))


def _one_of_too_many_alternatives_satisfied_message_lines(
    error: jsonschema.exceptions.ValidationError, schema: _JsonSchemaNonBool
) -> list[str]:
    """
    Create an error message specifically about the situation where too many
    alternatives in a oneOf schema were valid.

    Args:
        error: The ValidationError object representing the aforementioned
            type of error
        schema: The schema whose validation failed

    Returns:
        An error message, as a list of lines (strings).  Returning a list
        of lines is convenient for callers, who may want to nest this message
        in another, with indented lines.
    """

    alt_names = _get_one_of_alternative_names(error.validator_value, schema)
    error_desc = "Must be exactly one of: {}".format(", ".join(alt_names))

    satisfied_alt_names = []
    for alt_name, alt_schema in zip(alt_names, error.validator_value):
        # Perform a little "mini" validation to determine which alternatives
        # were satisfied, and describe them in the error message.
        if _is_valid_for_sub_schema(schema, alt_schema, error.instance):
            satisfied_alt_names.append(alt_name)

    error_desc += ".  Content satisfied more than one alternative: {}.".format(
        ", ".join(satisfied_alt_names)
    )

    return [error_desc]


def _one_of_no_alternatives_satisfied_message_lines(
    error: jsonschema.exceptions.ValidationError,
    schema: _JsonSchemaNonBool,
    location_desc_callback: Callable[[Sequence[Union[int, str]]], str],
) -> list[str]:
    """
    Create an error message specifically about the situation where none of the
    alternatives in a oneOf schema were valid.

    Args:
        error: The ValidationError object representing the aforementioned
            type of error
        schema: The schema whose validation failed
        location_desc_callback: A callback function used to customize the
            description of the location of errors.  Takes a programmatic "path"
            structure as a sequence of strings/ints, and should return a nice
            one-line string description.

    Returns:
        An error message, as a list of lines (strings).  Returning a list
        of lines is convenient for callers, who may want to nest this message
        in another, with indented lines.
    """

    message_lines = []

    # First error message line describes the error in basic terms.

    alt_names = _get_one_of_alternative_names(error.validator_value, schema)
    basic_desc = (
        "Must be exactly one of: {}; all alternatives failed validation."
    ).format(", ".join(alt_names))

    message_lines.append(basic_desc)

    # Subsequent error lines give additional details about the error: errors
    # associated with each oneOf alternative sub-schema.

    # Maps an alternative name to a list of error objects associated with that
    # alternative.  We organize context errors according to the alternative
    # they apply to.
    errors_by_alt = collections.defaultdict(list)

    one_of_schema_path_len = len(error.absolute_schema_path)

    # required to assure mypy that error.context is non-null.  That is checked
    # before this function is called (in fact it is the exact criteria for the
    # call).  Otherwise, it is treated as a non-iterable Optional type.
    assert error.context
    for ctx_error in error.context:
        # schema paths for errors associated with the alternatives
        # will share a common prefix with the schema path for the
        # "oneOf" error.  The next element after the common portion
        # will be an int which is the index of the alternative.
        error_alt_idx = ctx_error.absolute_schema_path[one_of_schema_path_len]

        # Mypy infers Union[str, int] for error_alt_idx and complains that it
        # is not a valid index type.  As explained above, in this context, this
        # index must be an int.
        assert isinstance(error_alt_idx, int)
        errors_by_alt[alt_names[error_alt_idx]].append(ctx_error)

    for alt_name, alt_errors in errors_by_alt.items():
        message_lines.append(
            'Errors associated with alternative "{}":'.format(alt_name)
        )

        for alt_error in alt_errors:
            sub_message_lines = _validation_error_to_message_lines(
                alt_error, schema, location_desc_callback
            )
            message_lines.extend(_indent_lines(sub_message_lines))

    return message_lines


def _validation_error_to_message_lines(
    error: jsonschema.exceptions.ValidationError,
    schema: _JsonSchema,
    location_desc_callback: Callable[[Sequence[Union[int, str]]], str],
) -> list[str]:
    """
    Create a nice error message for the given error object.

    Args:
        error: A ValidationError object which represents some schema
            validation error
        schema: The schema whose validation failed
        location_desc_callback: A callback function used to customize the
            description of the location of errors.  Takes a programmatic "path"
            structure as a sequence of strings/ints, and should return a nice
            one-line string description.

    Returns:
        An error message, as a list of lines (strings).  Returning a list
        of lines is convenient for callers, who may want to nest this message
        in another, with indented lines.
    """

    # Describe "where" the error occurred
    location_desc = location_desc_callback(error.absolute_path)

    # Describe "what" error(s) occurred
    if error.validator == "oneOf":
        # If a "oneOf" error, the schema can't be a bool schema.  Bool schemas
        # have no subcomponents (it's just true or false), so they can't have a
        # "oneOf" validator.
        assert isinstance(schema, dict)

        if error.context:
            what_lines = _one_of_no_alternatives_satisfied_message_lines(
                error, schema, location_desc_callback
            )

        else:
            what_lines = _one_of_too_many_alternatives_satisfied_message_lines(
                error, schema
            )

    else:
        # fallback if we can't be more clever about our message
        what_lines = [error.message]

    if len(what_lines) == 1:
        message_lines = ["In {}: {}".format(location_desc, what_lines[0])]

    else:
        message_lines = ["In {}:".format(location_desc)]
        message_lines.extend(_indent_lines(what_lines))

    return message_lines


def json_path_to_string(path: Iterable[Any]) -> str:
    """
    Create a string representation of a JSON path as is used in jsonschema
    ValidationError objects.  For now, a filesystem-like syntax is used with
    slash-delimited strings, which I think winds up being the same as
    JSON-Pointer syntax (rfc6901).

    Args:
        path: A "path" into a JSON structure, as an iterable of values
            (strings and ints).

    Returns:
        A string representation of the path
    """
    # Use a filesystem-like syntax?
    return "/" + "/".join(str(elt) for elt in path)


def validation_error_to_message(
    error: jsonschema.exceptions.ValidationError,
    schema: _JsonSchema,
    location_desc_callback: Optional[Callable[[Sequence[Union[int, str]]], str]] = None,
) -> str:
    """
    Create a nice error message for the given error object.

    Args:
        error: A ValidationError object which represents some schema
            validation error
        schema: The schema whose validation failed
        location_desc_callback: A callback function used to customize the
            description of the location of errors.  Takes a programmatic "path"
            structure as a sequence of strings/ints, and should return a nice
            one-line string description.  Defaults to a simple generic
            implementation which produces descriptions which aren't very nice.

    Returns:
        An error message as a string
    """

    if location_desc_callback is None:
        location_desc_callback = json_path_to_string

    message_lines = _validation_error_to_message_lines(
        error, schema, location_desc_callback
    )

    message = "\n".join(message_lines)

    return message


def validation_errors_to_message(
    errors: Iterable[jsonschema.exceptions.ValidationError],
    schema: _JsonSchema,
    location_desc_callback: Optional[Callable[[Sequence[Union[int, str]]], str]] = None,
) -> str:
    """
    Create a nice error message for the given error objects.  This currently
    just creates error messages for each error individually, and then
    concatenates them all together with blank lines in between.

    Args:
        errors: An iterable of ValidationError objects which represent some
            schema validation errors
        schema: The schema whose validation failed
        location_desc_callback: A callback function used to customize the
            description of the location of errors.  Takes a programmatic "path"
            structure as a sequence of strings/ints, and should return a nice
            one-line string description.  Defaults to a simple generic
            implementation which produces descriptions which aren't very nice.

    Returns:
        An error message as a string.
    """
    messages = [
        validation_error_to_message(error, schema, location_desc_callback)
        for error in errors
    ]

    combined_message_str = "\n\n".join(messages)

    return combined_message_str
