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