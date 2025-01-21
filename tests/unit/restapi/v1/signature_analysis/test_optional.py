from dioptra import pyplugs
@pyplugs.register()
def do_things(arg1: Optional[str], arg2: int = 123):
    pass