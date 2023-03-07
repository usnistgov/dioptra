# Code Review Guide

Prior to submitting a merge request be sure the code follows the guides indicated below. The automated formatting and linting tools are strongly recommended to be sure the code conforms and has been vetted.

## Python Code Style Guides

-   [Google Comments and Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)

-   [PEP 8 – Style Guide for Python Code](https://peps.python.org/pep-0008/)

-   Line width 88 Characters - SHOULD not a MUST

## Automated Code Formatters and Linters

-   [Black code formatter](https://black.readthedocs.io/en/stable/)

-   [isort import sorter](https://pycqa.github.io/isort/)

-   [flake8 code linter](https://flake8.pycqa.org/en/latest/) with the [flake8-bugbear plugin](https://github.com/PyCQA/flake8-bugbear)

-   [mypy static type checker](https://mypy.readthedocs.io/en/stable/)

## Performing Code Reviews

For in-depth description of the process we are following please see the referenced documents below, but a quick summary of what is being examined (this list has been extracted from the referenced documentation):

-   The code is well-designed.

-   The functionality is good for the users of the code.

-   Any UI changes are sensible and look good.

-   Any parallel programming is done safely.

-   The code isn’t more complex than it needs to be.

-   The developer isn’t implementing things they _might_ need in the future but don’t know they need now.

-   Code has appropriate unit tests.

-   Tests are well-designed.

-   The developer used clear names for everything.

-   Comments are clear and useful, and mostly explain _why_ instead of _what_.

-   Code is appropriately documented.

-   The code conforms to the style guides (see the section above).

<!-- -->

-   [Google Engineering Practices Documentation](https://google.github.io/eng-practices/) - Top-level document that links out to a Code Review Developer Guide. In this guide, CL = “changelist”.

-   [Google’s *How to do a code review*](https://google.github.io/eng-practices/review/reviewer/) - This is a detailed guide on the various aspects and considerations of a code review. This is a good starting point for our team. Note that any references to a style guide point to Google’s style guides, those should be substituted for our team’s styles.

-   [Google’s CL author’s guide to getting through code review](https://google.github.io/eng-practices/review/developer/) - A guide with tips and suggestions for structuring and documenting your pull requests. Again, these are good general ideas for how to make pull requests manageable. The concept of making changes small is particularly important, as it can be very time consuming to review a large number of changes.
