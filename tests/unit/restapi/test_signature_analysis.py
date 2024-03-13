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
from dioptra.restapi.v1.shared.signature_analysis import get_plugin_signatures


def test_plugin_recognition_1():
    source = """\
import dioptra.pyplugs

@dioptra.pyplugs.register
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_2():
    source = """\
from dioptra import pyplugs

@pyplugs.register
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_3():
    source = """\
from dioptra.pyplugs import register

@register
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_alias_1():
    source = """\
import dioptra.pyplugs as foo

@foo.register
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_alias_2():
    source = """\
from dioptra import pyplugs as foo

@foo.register
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_alias_3():
    source = """\
from dioptra.pyplugs import register as foo

@foo
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_call():
    source = """\
from dioptra.pyplugs import register

@register()
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_alias_call():
    source = """\
from dioptra.pyplugs import register as foo

@foo()
def test_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 1


def test_plugin_recognition_none():
    source = """\
import dioptra.pyplugs

# missing the decorator
def not_a_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert not signatures


def test_plugin_recognition_complex():
    source = """\
from dioptra.pyplugs import register
import aaa

@register()
def test_plugin():
    pass

@aaa.register
def not_a_plugin():
    pass

class SomeClass:
    pass

def some_other_func():
    pass

x = 1

@register
def test_plugin2():
    pass

# re-definition of the "register" symbol
from bbb import ccc as register

@register
def also_not_a_plugin():
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert len(signatures) == 2


def test_dioptra_builtin_types():
    source = """\
from dioptra.pyplugs import register

@register
def test_plugin(
    arg1: str,
    arg2: int,
    arg3: float,
    arg4: bool,
    arg5: None
):
    pass
"""

    signatures = list(get_plugin_signatures(source))

    assert signatures == [
        {
            "name": "test_plugin",
            "inputs": [
                {"name": "arg1", "required": True, "type": "string"},
                {"name": "arg2", "required": True, "type": "integer"},
                {"name": "arg3", "required": True, "type": "number"},
                {"name": "arg4", "required": True, "type": "boolean"},
                {"name": "arg5", "required": True, "type": "null"},
            ],
            "outputs": [],
            "suggested_types": [],
        }
    ]


def test_return_none():
    source = """\
from dioptra.pyplugs import register

# None is same as not having a return type annotation
@register
def my_plugin() -> None:
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert signatures == [
        {"name": "my_plugin", "inputs": [], "outputs": [], "suggested_types": []}
    ]


def test_derive_type_simple():
    source = """\
import dioptra.pyplugs

@dioptra.pyplugs.register()
def the_plugin(arg1: SomeType) -> SomeType:
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert signatures == [
        {
            "name": "the_plugin",
            "inputs": [{"name": "arg1", "required": True, "type": "sometype"}],
            "outputs": [{"name": "output", "type": "sometype"}],
            "suggested_types": [
                {"suggestion": "sometype", "type_annotation": "SomeType"}
            ],
        }
    ]


def test_derive_type_complex():
    source = """\
import dioptra.pyplugs

@dioptra.pyplugs.register()
def the_plugin(arg1: Optional[str]) -> Union[int, bool]:
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert signatures == [
        {
            "name": "the_plugin",
            "inputs": [{"name": "arg1", "required": True, "type": "optional_str"}],
            "outputs": [{"name": "output", "type": "union_int_bool"}],
            "suggested_types": [
                {"suggestion": "optional_str", "type_annotation": "Optional[str]"},
                {"suggestion": "union_int_bool", "type_annotation": "Union[int, bool]"},
            ],
        }
    ]


def test_generate_type():
    source = """\
import dioptra.pyplugs

# annotation is a function call; we don't attempt a type derivation for
# that kind of annotation.
@dioptra.pyplugs.register
def plugin_func(arg1: foo(2)) -> foo(2):
    pass
"""
    signatures = list(get_plugin_signatures(source))
    assert signatures == [
        {
            "name": "plugin_func",
            "inputs": [{"name": "arg1", "required": True, "type": "type1"}],
            "outputs": [{"name": "output", "type": "type1"}],
            "suggested_types": [{"suggestion": "type1", "type_annotation": "foo(2)"}],
        }
    ]


def test_generate_type_conflict():
    source = """\
import dioptra.pyplugs

# annotation is a function call; we don't attempt a type derivation for
# that kind of annotation.  Our first generated type would normally be "type1",
# but we can't use that either because the code author already used that!  So
# our generated type will have to be "type2".
@dioptra.pyplugs.register
def plugin_func(arg1: foo(2), arg2: Type1) -> foo(2):
    pass
"""
    signatures = list(get_plugin_signatures(source))
    assert signatures == [
        {
            "name": "plugin_func",
            "inputs": [
                {"name": "arg1", "required": True, "type": "type2"},
                {"name": "arg2", "required": True, "type": "type1"},
            ],
            "outputs": [{"name": "output", "type": "type2"}],
            "suggested_types": [
                {"suggestion": "type1", "type_annotation": "Type1"},
                {"suggestion": "type2", "type_annotation": "foo(2)"},
            ],
        }
    ]


def test_optional_arg():
    source = """\
from dioptra import pyplugs

@pyplugs.register()
def do_things(arg1: Optional[str], arg2: int = 123):
    pass
"""

    signatures = list(get_plugin_signatures(source))
    assert signatures == [
        {
            "name": "do_things",
            "inputs": [
                {"name": "arg1", "required": True, "type": "optional_str"},
                {"name": "arg2", "required": False, "type": "integer"},
            ],
            "outputs": [],
            "suggested_types": [
                {"suggestion": "optional_str", "type_annotation": "Optional[str]"}
            ],
        }
    ]
