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
Extract task plugin function signature information from Python source code.
"""
import ast as ast_module  # how many variables named "ast" might we have...
import itertools
import re
import sys
from pathlib import Path
from typing import Any, Container, Iterator, Optional, Union

import structlog
from structlog.stdlib import BoundLogger

from dioptra.task_engine import type_registry

_PYTHON_TO_DIOPTRA_TYPE_NAME = {
    "str": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "None": "null",
}

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def _is_constant(ast: ast_module.AST, value: Any) -> bool:
    """
    Determine whether the given AST node represents a constant (literal) of
    the given value.

    Args:
        ast: An AST node
        value: A value to compare to

    Returns:
        True if the AST node is a constant of the given value; False if not
    """
    return isinstance(ast, ast_module.Constant) and ast.value == value


def _is_simple_dotted_name(node: ast_module.AST) -> bool:
    """
    Determine whether the given AST node represents a simple name or dotted
    name, like "foo", "foo.bar", "foo.bar.baz", etc.

    Args:
        node: The AST node

    Returns:
        True if the node represents a simple dotted name; False if not
    """
    return isinstance(node, ast_module.Name) or (
        isinstance(node, ast_module.Attribute) and _is_simple_dotted_name(node.value)
    )


def _update_symbols(symbol_tree: dict[str, Any], name: str) -> dict[str, Any]:
    """
    Update/modify the given symbol tree such that it includes the given
    name.

    The symbol tree is conceptually roughly a symbol hierarchy.  This is how
    modules and other types of values are naturally arranged in Python.  An
    import statement (assuming it is correct, and in the absence of any way or
    desire to check, we assume they are all correct) reflects this hierarchy,
    and the hierarchy may be inferred from it.

    It is implemented as a nested dict of dicts.  The dicts map a symbol name
    to other dicts which may have other symbol names, which map to other dicts,
    etc.  One can look up a symbol to get a "value", but we don't actually have
    access to any runtime values.  A symbol's "value" in this tree will be
    whatever dict it maps to (which may be empty).

    Importantly, aliasing present in import statements ("as" clauses) is
    reflected in the symbol tree by referring to the same dict in multiple
    places.  This means the structure is not technically a tree, since nodes
    can have in-degree greater than one.  But it makes aliasing trivial to
    deal with: you can use the "is" operator to check whether two symbols'
    "values" are the same.

    Args:
        symbol_tree: A symbol tree structure to update
        name: The name to update the tree with

    Returns:
        The resulting "value" of the symbol after the tree has been updated
    """
    names = name.split(".")

    curr_mod = symbol_tree
    for symbol_name in names:
        curr_mod = curr_mod.setdefault(symbol_name, {})

    return curr_mod


def _look_up_symbol(
    symbol_tree: Optional[dict[str, Any]], name: str
) -> Optional[dict[str, Any]]:
    """
    Look up a symbol in the given symbol tree and return its "value".  The
    symbol tree data structure is comprised of nested dicts, so the value
    returned (if the symbol is found) is always a dict.

    Args:
        symbol_tree: A symbol tree structure
        name: The name to look up, as a string.  E.g. "foo", "foo.bar", etc.

    Returns:
        The value of the given symbol, or None if it was not found in the
            symbol tree
    """
    if not name:
        # Just in case...
        raise ValueError("Symbol name must not be null/empty")

    if not symbol_tree:
        result = None
    else:
        dot_idx = name.find(".")
        if dot_idx == -1:
            result = symbol_tree.get(name)
        else:
            result = _look_up_symbol(
                symbol_tree.get(name[:dot_idx]), name[dot_idx + 1 :]
            )

    return result


def _are_aliases(symbol_tree: dict[str, Any], name1: str, name2: str) -> bool:
    """
    Determine whether two symbol names refer to the same value.

    Args:
        symbol_tree: A symbol tree structure
        name1: A symbol name
        name2: A symbol name

    Returns:
        True if both symbol names are defined and resolve to the same value;
        False if not
    """
    name1_value = _look_up_symbol(symbol_tree, name1)
    name2_value = _look_up_symbol(symbol_tree, name2)

    return (
        name1_value is not None
        and name2_value is not None
        and name1_value is name2_value
    )


def _process_import(stmt: ast_module.AST, symbol_tree: dict[str, Any]) -> None:
    """
    Update the given symbol tree according to the given import statement.  This
    can add new symbols to the tree, or change what existing symbols refer to.

    Args:
        stmt: A stmt AST node.  Node types other than Import and ImportFrom
            are ignored.
        symbol_tree: A symbol tree structure to update.
    """
    if isinstance(stmt, ast_module.Import):
        # For a normal import, update the hierarchy according to the
        # imported name.  If aliased, also introduce an alias symbol at
        # the top level.
        for alias in stmt.names:
            value = _update_symbols(symbol_tree, alias.name)

            if alias.asname:
                symbol_tree[alias.asname] = value

    elif isinstance(stmt, ast_module.ImportFrom):
        # for mypy: how can a "from <module> import ...", import from nothing?
        # But module is apparently optional...
        assert stmt.module

        # Can't hope to interpret relative imports by themselves, because
        # we don't know what they're relative to.  So just ignore those.
        # E.g. "from ...foo import bar".
        if stmt.level == 0:
            # Update the symbol hierarchy with the module name
            # (from "...").  This identifies a module to import from.
            mod_value = _update_symbols(symbol_tree, stmt.module)

            # Each imported symbol is introduced at the sub-module level
            # (from ... import "..."), since the statement implies that
            # symbol exists there.  If the symbol is not aliased, it is
            # also introduced at the top level.  If it is aliased, only the
            # alias is introduced at the top level.
            for alias in stmt.names:
                value = mod_value.setdefault(alias.name, {})
                if alias.asname:
                    symbol_tree[alias.asname] = value
                else:
                    symbol_tree[alias.name] = value


def _is_register_decorator(decorator_symbol: str, symbol_tree: dict[str, Any]) -> bool:
    """
    Try to detect a pyplugs registration decorator symbol.  In dioptra, the
    "register" symbol is defined in the "dioptra.pyplugs" module.  So one could
    import the dioptra.pyplugs module and just access the "register" symbol
    from there, or import the "register" symbol directly.  E.g.

        import dioptra.pyplugs

        @dioptra.pyplugs.register
        def foo():
            pass

    Or:

        from dioptra import pyplugs

        @pyplugs.register
        def foo():
            pass

    Or:

        from dioptra.pyplugs import register

        @register
        def foo():
            pass

    In the first two cases, our symbol tree would contain "dioptra.pyplugs"
    but not "register" since the latter was never mentioned in an import
    statement.  In the last case, the whole "dioptra.pyplugs.register" symbol
    would be present.  We need to handle both cases.  This should also be
    transparent to aliasing, e.g.

        from dioptra import pyplugs as bar

        @bar.register
        def foo():
            pass

    must also work.

    Args:
        decorator_symbol: A decorator symbol used on a function, as a string,
            e.g. "foo", "foo.bar", etc
        symbol_tree: A data structure representing symbol hierarchy inferred
            from import statements

    Returns:
        True if the decorator symbol represents a task plugin registration
        decorator; False if not
    """

    if _are_aliases(symbol_tree, "dioptra.pyplugs.register", decorator_symbol):
        result = True

    elif decorator_symbol.endswith(".register"):
        deco_prefix = decorator_symbol[:-9]
        result = _are_aliases(symbol_tree, "dioptra.pyplugs", deco_prefix)

    else:
        result = False

    return result


def _is_task_plugin(
    func_def: ast_module.FunctionDef, symbol_tree: dict[str, Any]
) -> bool:
    """
    Determine whether the given function definition is defining a task plugin.

    Args:
        func_def: A function definition AST node
        symbol_tree: A data structure representing symbol hierarchy inferred
            from import statements

    Returns:
        True if the function definition is for a task plugin; False if not
    """
    for decorator_expr in func_def.decorator_list:

        # we will only handle simple decorator expressions: simple dotted
        # names, optionally with a function call.
        if _is_simple_dotted_name(decorator_expr):
            decorator_symbol = ast_module.unparse(decorator_expr)

        elif isinstance(decorator_expr, ast_module.Call) and _is_simple_dotted_name(
            decorator_expr.func
        ):
            decorator_symbol = ast_module.unparse(decorator_expr.func)

        else:
            decorator_symbol = None

        if decorator_symbol and _is_register_decorator(decorator_symbol, symbol_tree):
            result = True
            break
    else:
        result = False

    return result


def _find_plugins(ast: ast_module.Module) -> Iterator[ast_module.FunctionDef]:
    """
    Find AST nodes corresponding to task plugin functions.

    Args:
        ast: An AST node.  Plugin functions will only be found inside Module
            nodes

    Yields:
        AST nodes corresponding to task plugin function definitions
    """
    if isinstance(ast, ast_module.Module):
        symbol_tree: dict[str, Any] = {}
        for stmt in ast.body:

            if isinstance(stmt, (ast_module.Import, ast_module.ImportFrom)):
                _process_import(stmt, symbol_tree)

            elif isinstance(stmt, ast_module.FunctionDef) and _is_task_plugin(
                stmt, symbol_tree
            ):
                yield stmt


def _derive_type_name_from_annotation(annotation_ast: ast_module.AST) -> Optional[str]:
    """
    Try to derive a suitable Dioptra type name from a type annotation AST.
    Annotations can be arbitrarily complex and even nonsensical (not all
    kind of errors are caught at parse time), so derivation may fail depending
    on the AST.

    Args:
        annotation_ast: An AST used as an argument or return type annotation

    Returns:
        A type name if one could be derived, or None if one could not be
        derived from the given annotation
    """

    # "None" isn't a type, but is used to mean the type of None
    if _is_constant(annotation_ast, None):
        type_name_suggestion = "null"

    # A name, e.g. int
    elif isinstance(annotation_ast, ast_module.Name):
        type_name_suggestion = annotation_ast.id

    # A string literal, e.g. "foo".  Can be used in Python code to defer
    # evaluation of an annotation.
    elif isinstance(annotation_ast, ast_module.Constant) and isinstance(
        annotation_ast.value, str
    ):
        type_name_suggestion = annotation_ast.value

    # Frequently used annotation expressions, e.g. list[str] is a "Subscript",
    # and str | int is a "BinOp".
    elif isinstance(
        annotation_ast, (ast_module.Subscript, ast_module.BinOp)
    ) or _is_simple_dotted_name(annotation_ast):
        type_name_suggestion = ast_module.unparse(annotation_ast)

    else:
        type_name_suggestion = None

    # normalize the suggestion, if we were able to derive one
    if type_name_suggestion:
        type_name_suggestion = type_name_suggestion.strip()
        type_name_suggestion = type_name_suggestion.lower()
        type_name_suggestion = type_name_suggestion.replace(" ", "")
        # Replace non-alphanumerics with underscores
        type_name_suggestion = re.sub(r"\W+", "_", type_name_suggestion)
        # Condense multiple underscores to one
        type_name_suggestion = re.sub("_+", "_", type_name_suggestion)
        type_name_suggestion = type_name_suggestion.strip("_")

        # Try to map to a Dioptra builtin type name.
        type_name_suggestion = _PYTHON_TO_DIOPTRA_TYPE_NAME.get(
            type_name_suggestion, type_name_suggestion
        )

        # After all this, if we wound up with an empty string, we failed.
        # If the name doesn't begin with a letter (like all good identifiers
        # should), we also failed.
        if not type_name_suggestion or not type_name_suggestion[0].isalpha():
            type_name_suggestion = None

    return type_name_suggestion


def _make_unique_type_name(existing_types: Container[str]) -> str:
    """
    Make a unique type name, i.e. one which doesn't exist in existing_types.
    One never knows if a user's type annotation actually resulted in a derived
    type name which matches our chosen unique name syntax.  So it is not
    sufficient to maintain a counter elsewhere which is incremented every time
    we need a new unique name.  That might result in name collisions.  So this
    is done conservatively (if inefficiently) by concatenating a base name with
    an incrementing integer counter starting at 1, until we obtain a name which
    has not previously been seen.

    :param existing_types: A container of existing type names
    :return: A new type name which is not in the container
    """
    counter = 1
    type_name = f"type{counter}"
    while type_name in existing_types:
        counter += 1
        type_name = f"type{counter}"

    return type_name


def _pos_args_defaults(
    args: ast_module.arguments,
) -> Iterator[tuple[ast_module.arg, Optional[ast_module.expr]]]:
    """
    Generate the positional argument AST nodes paired with their defined
    default AST nodes (if any), contained within the given AST arguments value.
    This requires a bit of coding since pos args/defaults aren't stored in a
    way you can straightforwardly just zip them up.  This includes all
    positional-only and "regular" (non-keyword-only) arguments, in the order
    they appear in the function signature.

    Args:
        args: An AST arguments value

    Yields:
        positional arg, arg default pairs.  If an arg does not have a default
            defined in the signature, it is generated as None.
    """
    num_pos_args = len(args.posonlyargs) + len(args.args)
    idx_first_defaulted_arg = num_pos_args - len(args.defaults)

    for arg_idx, arg in enumerate(itertools.chain(args.posonlyargs, args.args)):
        if arg_idx >= idx_first_defaulted_arg:
            arg_default = args.defaults[arg_idx - idx_first_defaulted_arg]
        else:
            arg_default = None

        yield arg, arg_default


def _func_args_defaults(
    func: ast_module.FunctionDef,
) -> Iterator[tuple[ast_module.arg, Optional[ast_module.expr]]]:
    """
    Generate all argument AST nodes paired with their defined default AST nodes
    (if any).  This includes positional-only and keyword-only arguments, in the
    order they appear in the function signature.

    Args:
        func: A FunctionDef AST node representing a function definition

    Yields:
        arg, arg default pairs.  If an arg does not have a default defined in
            the signature, it is generated as None.
    """
    yield from _pos_args_defaults(func.args)
    yield from zip(func.args.kwonlyargs, func.args.kw_defaults)


def _func_args(func: ast_module.FunctionDef) -> Iterator[ast_module.arg]:
    """
    Generate all argument AST nodes.  This does not include any of their
    defaults.  They are generated in the order they appear in the function
    signature.

    Args:
        func: A FunctionDef AST node representing a function definition

    Returns:
        An iterator which produces all function argument AST nodes
    """
    # Must use same iteration order as _func_args_defaults()!
    return itertools.chain(func.args.posonlyargs, func.args.args, func.args.kwonlyargs)


def _get_function_signature_via_derivation(
    func: ast_module.FunctionDef,
) -> dict[str, Any]:
    """
    Create a dict structure which reflects the signature of the given function,
    including where possible, argument and return type names suitable for use
    with the Dioptra type system.  This function tries to derive type names
    from argument/return type annotations.  This derivation may or may not
    produce a suitable type name.  Where it is unable to derive a type name,
    None is used in the data structure.  The end result is a structure which
    accounts for all arguments and the return type, although some type names
    may be None.

    Args:
        func: A FunctionDef AST node representing a function definition

    Returns:
        A function signature data structure as a dict
    """
    inputs = []
    outputs = []
    suggested_types = []
    used_type_names = set()

    for arg, arg_default in _func_args_defaults(func):
        if arg.annotation:
            type_name_suggestion = _derive_type_name_from_annotation(arg.annotation)
            type_structure_suggestion = _build_type_dictionary_from_AST(arg.annotation)
        else:
            type_name_suggestion = None
            type_structure_suggestion = None

        inputs.append(
            {
                "name": arg.arg,
                "type": type_name_suggestion,  # might be None
                "required": arg_default is None,
            }
        )

        # Add suggestions for non-Dioptra-builtin types only, which we have not
        # already created a suggestion for
        if (
            type_name_suggestion
            and type_name_suggestion not in type_registry.BUILTIN_TYPES
            and type_name_suggestion not in used_type_names
        ):
            # For mypy: we would not have a type name suggestion here if we did
            # not have an annotation.
            assert arg.annotation
            suggested_types.append(
                {
                    "suggestion": type_name_suggestion,
                    "type_annotation": ast_module.unparse(arg.annotation),
                    "structure": type_structure_suggestion,
                }
            )

            used_type_names.add(type_name_suggestion)

    # Also address any return annotation other than None.  If it is None,
    # skip the output.  None means the plugin produces no output.
    if func.returns and not _is_constant(func.returns, None):
        type_name_suggestion = _derive_type_name_from_annotation(func.returns)
        type_structure_suggestion = _build_type_dictionary_from_AST(func.returns)

        outputs.append(
            {
                "name": "output",
                "type": type_name_suggestion,  # might be None
                "structure": type_structure_suggestion,
            }
        )

        if (
            type_name_suggestion
            and type_name_suggestion not in type_registry.BUILTIN_TYPES
            and type_name_suggestion not in used_type_names
        ):
            suggested_types.append(
                {
                    "suggestion": type_name_suggestion,
                    "type_annotation": ast_module.unparse(func.returns),
                    "structure": type_structure_suggestion,
                }
            )

            used_type_names.add(type_name_suggestion)

    signature = {
        "name": func.name,
        "inputs": inputs,
        "outputs": outputs,
        "suggested_types": suggested_types,
    }

    return signature


def _complete_function_signature_via_generation(
    func: ast_module.FunctionDef, signature: dict[str, Any]
) -> None:
    """
    Search through the given signature structure for missing (None) type names,
    and use name generation to generate unique names.  The signature structure
    is updated such that all arguments and return type should have a type name.

    Args:
        func: A FunctionDef AST node representing a function definition
        signature: A function signature structure to update
    """

    # Gather used types; use this to ensure uniqueness of generated types.
    used_type_names = {
        input_["type"] for input_ in signature["inputs"] if input_["type"]
    }

    used_type_names.update(
        output["type"] for output in signature["outputs"] if output["type"]
    )

    # For annotations for which we could not derive a type name, we must
    # nevertheless recognize annotation reuse, and reuse the same
    # generated unique type name.  I don't think AST's have any support
    # for equality checks, hashing, etc.  The only way I can think of to
    # compare one AST to another is via their unparsed Python code (as
    # strings).  So this mapping maps unparsed Python to a generated unique
    # name.
    ann_to_unique: dict[str, str] = {}
    unparsed_ann: Optional[str]

    for input_, arg in zip(signature["inputs"], _func_args(func)):
        if not input_["type"]:
            if arg.annotation:
                unparsed_ann = ast_module.unparse(arg.annotation)
                type_name_suggestion = ann_to_unique.get(unparsed_ann)
            else:
                unparsed_ann = type_name_suggestion = None

            if not type_name_suggestion:
                type_name_suggestion = _make_unique_type_name(used_type_names)
                if unparsed_ann:
                    ann_to_unique[unparsed_ann] = type_name_suggestion

            input_["type"] = type_name_suggestion

            if unparsed_ann and type_name_suggestion not in used_type_names:
                signature["suggested_types"].append(
                    {
                        "suggestion": type_name_suggestion,
                        "type_annotation": unparsed_ann,
                    }
                )

            used_type_names.add(type_name_suggestion)

    # generate a type name for output if necessary
    if signature["outputs"]:
        output = signature["outputs"][0]
        if not output["type"]:
            # For mypy: we would not have a defined output if the function did
            # not have a return type annotation.
            assert func.returns
            unparsed_ann = ast_module.unparse(func.returns)
            type_name_suggestion = ann_to_unique.get(unparsed_ann)
            if not type_name_suggestion:
                type_name_suggestion = _make_unique_type_name(used_type_names)
                ann_to_unique[unparsed_ann] = type_name_suggestion

            output["type"] = type_name_suggestion

            if type_name_suggestion not in used_type_names:
                signature["suggested_types"].append(
                    {
                        "suggestion": type_name_suggestion,
                        "type_annotation": unparsed_ann,
                    }
                )

            used_type_names.add(type_name_suggestion)


def get_plugin_signatures(
    python_source: str, filepath: Optional[Union[str, Path]] = None
) -> Iterator[dict[str, Any]]:
    """
    Extract plugin signatures and build signature information structures from
    all task plugins defined in the given source code.

    Args:
        python_source: Some Python source code; should be complete with
            supporting import statements to assist in understanding what
            symbols mean
        filepath: A value representative of where the python source came from.
            This is an optional arg passed on to the underlying compile()
            function, which documents it as:  "The filename argument should
            give the file from which the code was read; pass some recognizable
            value if it wasn't read from a file ('<string>' is commonly used)."

    Yields:
        Function signature information data structures, as dicts
    """
    if filepath:
        ast = ast_module.parse(
            python_source, filename=filepath, feature_version=sys.version_info[0:2]
        )
    else:
        ast = ast_module.parse(python_source, feature_version=sys.version_info[0:2])

    for plugin_func in _find_plugins(ast):

        # We need to come up with a syntax for unique type names.  But no
        # matter what syntax we choose, a user's type annotations might collide
        # with it.  So we can't easily do this in one pass where we generate a
        # name whenever we fail to derive one from a type annotation.  If a
        # subsequent type name derived from a user type annotation collides
        # with a unique name we already generated, the user's name must take
        # precedence.
        #
        # A better way is to make two passes: the first pass derives type names
        # from type annotations where possible, and determines what the
        # user-annotation-derived type names are.  The second pass uses unique
        # name generation to generate all type names we could not derive in the
        # first pass, where the generation can use the names derived in the
        # first pass to ensure there are no naming collisions.

        # Pass #1
        signature = _get_function_signature_via_derivation(plugin_func)

        # Pass #2
        _complete_function_signature_via_generation(plugin_func, signature)

        yield signature


def get_plugin_signatures_from_file(
    filepath: Union[str, Path], encoding: str = "utf-8"
) -> Iterator[dict[str, Any]]:
    """
    Extract plugin signatures and build signature information structures from
    all task plugins defined in the given Python source file.

    Args:
        filepath: A path to a file with Python source code; should be complete
            with supporting import statements to assist in understanding what
            symbols mean
        encoding: A text encoding used to read the given source file

    Returns:
        An iterator of function signature information data structures, as dicts
    """
    filepath = Path(filepath)
    python_source = filepath.read_text(encoding=encoding)

    return get_plugin_signatures(python_source, filepath)


def _build_type_dictionary_from_AST(
    annotation: ast_module.AST, 
    top_level: bool = True
):
    structure = None
    potential_name = None
    if isinstance(annotation, ast_module.Subscript):
        substructure = _build_type_dictionary_from_AST(
            annotation.slice, top_level=False
        )
        LOGGER.debug(f"Substructure generated from slice: {substructure}")

        if annotation.value.id in ["List", "list"]:
            structure = {"list": substructure}
        if annotation.value.id in ["Union"]:
            structure = {"union": substructure}
        if annotation.value.id in ["Optional"]:
            structure = {"union": [substructure, "null"]}
        if annotation.value.id in ["Dict", "dict"]:
            structure = {"mapping": substructure}
        if annotation.value.id in ["Tuple", "tuple"]:
            structure = {"tuple": substructure}
    elif isinstance(annotation, ast_module.Tuple):
        structure = [
            _build_type_dictionary_from_AST(m, top_level=False) for m in annotation.elts
        ]
    elif isinstance(annotation, ast_module.BinOp):
        if isinstance(annotation.op, ast_module.BitOr):
            structure = {
                "union": [
                    _build_type_dictionary_from_AST(annotation.left, top_level=False),
                    _build_type_dictionary_from_AST(annotation.right, top_level=False),
                ]
            }
    elif isinstance(annotation, ast_module.Name):
        if top_level:
            return None  # only keep the name if part of another structure
        else:
            potential_name = _derive_type_name_from_annotation(annotation)

    structure = resolve_structure(structure, potential_name)
    return structure


def resolve_structure(structure, potential_name):
    if structure is None and potential_name is not None:
        return potential_name

    # if we ever want to suggest structures, we can query restapi
    # here to make them more brief (potentially replace substructures
    # with already registered structures)

    return structure
