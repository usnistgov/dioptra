# Commit Style Guide

This project follows precise rules over how git commit messages should be formatted. This leads to more readable messages that are easy to follow when looking through the project history.

## General Rules

1.  Separate subject from body with a blank line

2.  Limit the subject line to 70 characters

3.  Do not capitalize the subject line

4.  Do not end the subject line with a period

5.  Use the imperative mood in the subject line

6.  Use the body to explain what and why vs. how

7.  Each commit should be a single, stable change

## Commit Message Format

Each commit message consists of a **header**, a **body** and a **footer**.

The header has a special format that includes a type, a scope and a subject:

    <type>(<scope>): <subject>
    <BLANK LINE>
    <body>
    <BLANK LINE>
    <footer>

The **header** is mandatory and the **scope** of the header is optional. Both are written in *camelCase*.

Any line of the commit message cannot be longer 100 characters! This allows the message to be easier to read in various git tools.

The footer should contain a closing reference to an issue as well as a relevant issue (if any):

    examples: fix url joining for endpoints in lab api client on windows

    Replace the platform-specific `os.path.join()` with the platform-independent `posixpath.join()` so
    that joining behavior is consistent on both Windows and POSIX systems.

    Closes #1

## Revert

If the commit reverts a previous commit, it should begin with `revert:`, followed by the header of the reverted commit. In the body it should say: This reverts commit \<hash\>., where the hash is the SHA of the commit being reverted.

## Type

Must be one of the following:

-   **build**: Changes that affect the build system or external dependencies

-   **ci**: Changes to our CI configuration files and scripts

-   **chore**: Miscellaneous changes that do not fall under any of the other types, such as changes to meta information in the repo (owner files, editor config, etc) or licensing

-   **docs**: Documentation only changes

-   **feat**: A new feature (can include adding a new library into a container to enable new functionality)

-   **fix**: A bug fix

-   **refactor**: A code change that neither fixes a bug nor adds a feature, can include stylistic changes to the code base (white-space, formatting, etc.)

-   **tests**: Adding missing tests or correcting existing tests

## Scope

The scope should be the name of the core component affected as perceived by a person reading a changelog generated from the commit messages, not the name of the literal file changed. For example, if the code primarily affects configuration, you’d use the *container*, even if the changes are made to a utility file.

The following is the list of supported scopes:

-   **container**: used for updates related to the development and maintenance of the project’s containers

-   **examples**: additions or changes to the examples provided in the project’s examples/ folder

-   **restapi**: used for updates related to the development and maintenance of the Testbed’s RESTful API

-   **sdk**: used for updates related to the development and maintenance of the Testbed’s software development kit

-   **ui**: used for updates related to the development and maintenance of the frontend web UI

The special scopes **github** and **tox** are permitted when combined with the ci change type.

Note that not all commits should have a scope. Cases where a commit should not specify a scope typically fall into one of two categories:

1.  Changes impacting more than one scope: This is common with the tests, and refactor change types. Examples include restructuring the project layout or running a code beautifier across the entire codebase.

2.  chore and build changes: There is a broad range of tools and libraries out there related to changes in the project’s configuration files and the build system (examples: conda, flake8, makefile, mypy, pre-commit, etc). The use of scopes for these kinds of changes is optional and it is generally recommended that you omit them in the interest of keeping the list of scopes simple.

## Subject

The subject contains a succinct description of the change:

-   Use the imperative, present tense: “change” not “changed” nor “changes”

-   Don’t capitalize the first letter

-   No dot (.) at the end

## Body

Just as in the **subject**, use the imperative, present tense: “change” not “changed” nor “changes”. The body should include the motivation for the change and contrast this with previous behavior.

## Footer

The footer should contain any information about **Breaking Changes** and is also the place to reference GitLab issues that this commit **Closes**.

**Breaking Changes** should start with the word BREAKING CHANGE: with a space or two newlines. The rest of the commit message is then used for this.

## References

-   <https://chris.beams.io/posts/git-commit/>

-   <https://conventionalcommits.org/>

-   <https://github.com/angular/angular/blob/master/CONTRIBUTING.md>

-   <https://docs.sentry.io/development/contribute/contributing>
