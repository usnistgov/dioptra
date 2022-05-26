.. This Software (Dioptra) is being made available as a public service by the
.. National Institute of Standards and Technology (NIST), an Agency of the United
.. States Department of Commerce. This software was developed in part by employees of
.. NIST and in part by NIST contractors. Copyright in portions of this software that
.. were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
.. to Title 17 United States Code Section 105, works of NIST employees are not
.. subject to copyright protection in the United States. However, NIST may hold
.. international copyright in software created by its employees and domestic
.. copyright (or licensing rights) in portions of software that were assigned or
.. licensed to NIST. To the extent that NIST holds copyright in this software, it is
.. being made available under the Creative Commons Attribution 4.0 International
.. license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
.. of the software developed or licensed by NIST.
..
.. ACCESS THE FULL CC BY 4.0 LICENSE HERE:
.. https://creativecommons.org/licenses/by/4.0/legalcode

.. _dev-guide-commit-styleguide:

Commit Styleguide
-----------------

.. include:: /_glossary_note.rst

This project follows precise rules over how git commit messages should be formatted.
This leads to more readable messages that are easy to follow when looking through the project history.

General Rules
~~~~~~~~~~~~~

1. Separate subject from body with a blank line

2. Limit the subject line to 70 characters

3. Do not capitalize the subject line

4. Do not end the subject line with a period

5. Use the imperative mood in the subject line

6. Use the body to explain what and why vs. how

7. Each commit should be a single, stable change

Merge vs Rebase
~~~~~~~~~~~~~~~

This project uses a rebase workflow.
That means that every commit on its own should be a clear, functional, and stable change.
This means then when you’re building a new feature, you should try to pare it down into functional steps, and when that’s not reasonable, the end patch should be a single commit.
This is counter to having a Merge Request which may include commit messages like “fix [unmerged] behavior”.
Those commits should get squashed, and the final patch when landed should be rebased.

Remember: each commit should follow the commit message format and be stable.

Squashing
^^^^^^^^^

If you are squashing your branch, it’s important to make sure you update the commit message.
If you’re using GitHub’s UI it will by default create a new commit message which is a combination of all commits and **does not follow the commit guidelines**.

If you’re working locally, it often can be useful to ``--amend`` a commit, or utilize ``rebase -i`` to reorder, squash, and reword your commits.

Commit Message Format
~~~~~~~~~~~~~~~~~~~~~

Each commit message consists of a **header**, a **body** and a **footer**.

The header has a special format that includes a type, a scope and a subject:

::

   <type>(<scope>): <subject>
   <BLANK LINE>
   <body>
   <BLANK LINE>
   <footer>

The **header** is mandatory and the **scope** of the header is optional.
Both are written in *camelCase*.

Any line of the commit message cannot be longer 100 characters!
This allows the message to be easier to read on GitHub as well as in various git tools.

The footer should contain a closing reference to an issue as well as a relevant GitHub issue (if any):

::

   examples: fix url joining for endpoints in lab api client on windows

   Replace the platform-specific `os.path.join()` with the platform-independent `posixpath.join()` so
   that joining behavior is consistent on both Windows and POSIX systems.

   Closes #1

Revert
~~~~~~

If the commit reverts a previous commit, it should begin with ``revert:``, followed by the header of the reverted commit.
In the body it should say: ``This reverts commit <hash>.``, where the hash is the SHA of the commit being reverted.

Type
~~~~

Must be one of the following:

-  **build**: Changes that affect the build system or external dependencies

-  **ci**: Changes to our CI configuration files and scripts

-  **chore**: Miscellaneous changes that do not fall under any of the other types, such as changes to meta information in the repo (owner files, editor config, etc) or licensing

-  **docs**: Documentation only changes

-  **examples**: Additions or changes to the examples provided in the project’s ``examples/`` folder

-  **feat**: A new feature

-  **fix**: A bug fix

-  **perf**: A code change that improves performance

-  **refactor**: A code change that neither fixes a bug nor adds a feature

-  **revert**: A change that reverses the change in earlier commit

-  **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)

-  **test**: Adding missing tests or correcting existing tests

Scope
~~~~~

The scope should be the name of the core component affected as perceived by person reading changelog generated from commit messages, not the name of the literal file changed.
For example, if the code primarily affects configuration, you’d use the *config* scope, even if the changes are made to a utility file.

The following is the list of supported scopes:

-  **docker**: used for updates related to the development and maintenance of the project’s Docker images

-  **mlflow**: used for updates related to the development and maintenance of plugins that extend the functionality of the MLFlow library

-  **pyplugs**: used for updates related to the development and maintenance of the Testbed’s `PyPlugs <https://pypi.org/project/pyplugs>`__ fork

-  **restapi**: used for updates related to the development and maintenance of the Testbed’s :term:`REST` :term:`API`

-  **rq**: used for updates related to the development and maintenance of the Testbed’s Redis-based job tracking and management system

-  **sdk**: used for updates related to the development and maintenance of the Testbed’s software development kit

Ad-hoc scopes are permitted for the ``examples`` change type to indicate which example was updated provided the scope names remain consistent.
The special scopes **github** and **tox** are also permitted when combined with the ``ci`` change type.

Note that not all commits should have a scope.
Cases where a commit should not specify a scope typically fall into one of two categories:

1. Changes impacting more than one scope: This is common with the ``examples``, ``style``, ``test``, and ``refactor`` change types.
   Examples include restructuring the project layout or running a code beautifier across the entire codebase.

2. ``chore`` and ``build`` changes: There is a broad range of tools and libraries out there related to changes in the project’s configuration files and the build system (examples: conda, flake8, makefile, mypy, pre-commit, etc).
   The use of scopes for these kinds of changes is optional and it is generally recommended that you omit them in the interest of keeping the list of scopes simple.

Subject
~~~~~~~

The subject contains a succinct description of the change:

-  Use the imperative, present tense: “change” not “changed” nor “changes”
-  Don’t capitalize the first letter
-  No dot (.) at the end

Body
~~~~

Just as in the **subject**, use the imperative, present tense: “change” not “changed” nor “changes”.
The body should include the motivation for the change and contrast this with previous behavior.

Footer
~~~~~~

The footer should contain any information about **Breaking Changes** and is also the place to reference GitHub issues that this commit **Closes**.

**Breaking Changes** should start with the word ``BREAKING CHANGE:`` with a space or two newlines. The rest of the commit message is then used for this.

.. _references-1:

References
~~~~~~~~~~

-  https://chris.beams.io/posts/git-commit/
-  https://conventionalcommits.org/
-  https://github.com/angular/angular/blob/master/CONTRIBUTING.md
-  https://docs.sentry.io/development/contribute/contributing
