# Contributing

Thank you for taking an interest in contributing. This documentation contains some general guidelines for contributions to this project. These guidelines describe and govern NIST’s management of this repository and contributors’ responsibilities. NIST reserves the right to modify this policy at any time.

## Criteria for Contributions and Feedback

This is a moderated platform. NIST will only accept contributions that are contributed per the terms of the license file. All contributors must add their name to the [CONTRIBUTORS.md](./CONTRIBUTORS.md) file to affirmatively indicate acceptance of the license terms. Contributions cannot be accepted from user accounts for which this acceptance has not been done. Upon submission, materials will be public and considered publicly available information, unless noted in the license file.

NIST reserves the right to reject, remove, or edit any contribution or feedback, including anything that:

-   states or implies NIST endorsement of any entities, services, or products;

-   is inaccurate;

-   contains abusive or vulgar content, spam, hate speech, personal attacks, or similar content;

-   is clearly "off topic";

-   makes unsupported accusations;

-   includes personally identifiable or business identifiable information according to Department of Commerce Office of Privacy and Open Government [guidelines](https://www.osec.doc.gov/opog/privacy/PII_BII.html)

## Contributor Responsibilities

NIST also reserves the right to reject or remove contributions from the repository if the contributor fails to carry out any of the following responsibilities:

-   following the contribution instructions;

-   responding to feedback from other repository users in a timely manner;

-   responding to NIST representatives in a timely manner;

-   keeping contributions and contributor GitHub username up to date

## Question or Problem?

If you have any questions or problems with the software please try posting in [Q&A](https://github.com/usnistgov/dioptra/discussions/categories/q-a).

If you have general questions, please contact [dioptra@nist.gov](mailto:dioptra@nist.gov). Please allow a few business days for a response.

## Submitting Issues

Prior to submitting any issue please try a brief search to see if an issue similar to yours already exists. Avoiding duplicate submissions helps to limit time needed to triage issues. Each issue card should be focused and describe a single bug, feature, etc… Please try to use the [provided templates](https://github.com/usnistgov/dioptra/issues/new/choose) if they align with the issue you are submitting.

### Bugs

If you find a bug or unexpected behavior please use the provided [issue template](https://github.com/usnistgov/dioptra/issues/new/choose) and describe the issue along with step-by-step instructions on how to reproduce the issue.

### Feature Requests

Please feel free to suggest new features or capabilities. Try to describe what the desired feature will do and how it will behave and try to avoid implementation details.

## Code Submission Guidelines

This and following sections describe how to participate in the development process if you desire to contribute. Before starting on any large or long-term submission, please give us a heads up by sending an email to dioptra@nist.gov so that we can coordinate and avoid possible duplication of effort.

Create an issue card first to spec out the change and requirements before starting work. - A pull request or update should be tied to at least one issue card (exceptions are **chore** changes like updating copyright year, files to ignore, etc.) - Keep the number of issues covered in a pull request minimal. Multiple issues being resolved in a single pull request should only happen in exceptional circumstances.

Please review the sections below to better understand the code review process to insure a quick and easy acceptance of your submission.

### Development Workflow

Dioptra is following the [Gitflow workflow model](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow).

[Clone](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository) this repository.

Create a [new branch](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging) off the `dev` branch to get started.

### Commit Style Guide

See the [Dioptra Commit Style Guide](./COMMIT_STYLE_GUIDE.md).

#### Squashing

All final commits will be squashed, therefore when squashing your branch, it’s important to make sure you update the commit message. If you’re using GitHub’s UI it will by default create a new commit message which is a combination of all commits and **does not follow the commit guidelines**.

If you’re working locally, it often can be useful to `--amend` a commit, or utilize `rebase -i` to reorder, squash, and reword your commits.

### Code Reviewing Guide

See the [CODEREVIEWERS file](./CODEREVIEWERS.md).

### Testing & User Stories

All new features and submissions require testing to be written and implemented. See the [Testing Guide file](./TESTING_GUIDE.md).