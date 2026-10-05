# About Versioned Releases

This document explains the versioning philosophy and release model used in the Dioptra repository. It covers why releases happen, when they happen, and how version numbers flow between branches.

- [Semantic Versioning](#semantic-versioning)
- [The Two-Branch Model](#the-two-branch-model)
  - [The `main` Branch](#the-main-branch)
  - [The `dev` Branch](#the-dev-branch)
- [When Releases Happen](#when-releases-happen)
  - [Main Branch Releases](#main-branch-releases)
  - [Dev Branch Releases](#dev-branch-releases)
    - [Scenario 1 - After a minor or major release to main](#scenario-1---after-a-minor-or-major-release-to-main)
    - [Scenario 2 - After a patch release to main with corresponding changes to dev](#scenario-2---after-a-patch-release-to-main-with-corresponding-changes-to-dev)
    - [Scenario 3 - When substantial new content warrants a dev release](#scenario-3---when-substantial-new-content-warrants-a-dev-release)
- [How Version Numbers Flow](#how-version-numbers-flow)
- [Branch-Specific Release References](#branch-specific-release-references)
- [Downstream Artifacts](#downstream-artifacts)
- [Version Format Variations](#version-format-variations)

## Semantic Versioning

Dioptra follows [Semantic Versioning](https://semver.org/) (semver) conventions. Version numbers take the form `X.Y.Z` where:

- **X (Major)**: Incremented for incompatible API changes
- **Y (Minor)**: Incremented for new functionality that is backwards-compatible
- **Z (Patch)**: Incremented for backwards-compatible bug fixes

Development versions append a dev tag: `X.Y.ZdevN`, where N is incremented for each development release.

## The Two-Branch Model

The repository maintains two primary branches with distinct purposes:

### The `main` Branch

The `main` branch contains stable, released code. Every release to `main` is tagged with a version number (e.g., `1.0.0`) and represents code that has been tested and deemed ready for production use.

Not every commit to `main` constitutes a release. Releases are deliberate: a release commit is created and tagged, which triggers the release process. This includes [publishing to PyPI](https://pypi.org/project/dioptra-platform) and building container images that are pushed to [GitHub Packages](https://github.com/orgs/usnistgov/packages?repo_name=dioptra).

### The `dev` Branch

The `dev` branch contains bleeding-edge development work. It uses development version tags (`X.Y.ZdevN`) to distinguish pre-release builds from stable releases. After the post-release version bump, dev targets the next minor version beyond the stable release on `main`, unless a new major version has been selected for upcoming work.

For Dioptra developers, `dev` is the branch from which feature branches are created and merged back into as part of the development workflow. For users, the dev branch provides access to the latest features and fixes before they land in a stable release.

As with `main`, not every commit to `dev` constitutes a release. Development releases are deliberate and follow the same pattern: a release commit is created and tagged, triggering TestPyPI and container builds that are made available for testing and evaluation.

## When Releases Happen

### Main Branch Releases

A stable release brings the selected dev changes into main with stable package versions, deployment defaults, and example requirements. Preparation creates one integration merge locally, which is reviewed and checked through a release PR before main is advanced to it. Tagging and publication follow successful main CI.

See [How to Merge Dev into Main](how-to-merge-dev-into-main.md) for preparation and integration, then [How to Create a Release](how-to-create-a-release.md) for tagging and publication.

### Dev Branch Releases

Dev branch releases happen under three circumstances:

#### Scenario 1 - After a minor or major release to main

When a new minor version is released to `main` (e.g., `1.0.0` → `1.1.0`), the `dev` branch must be updated to stay one minor version ahead. The minor version on `dev` is incremented, and the dev tag is reset to zero.

For example, if `main` releases `1.1.0`, then `dev` (which was at `1.1.0dev3`) becomes `1.2.0dev0`.

Major releases follow the same mechanical pattern. When a major version is released to `main` (e.g., `1.2.0` → `2.0.0`), `dev` bumps to the next minor version of that new major. For example, if `main` releases `2.0.0`, then `dev` becomes `2.1.0dev0`.

This keeps `dev` one minor version ahead of the latest stable release, clearly indicating that it contains work targeted at the *next* release.

**A note on pre-emptive major version bumps on dev**

The scenarios above describe what happens *after* a release occurs on `main`. There is a separate question of whether to bump `dev` to a new major version *before* `main` has released that major. Unlike minor version increments, which follow a mechanical rule, the decision to target a new major version on `dev` is a planning decision. It requires determining that upcoming work represents breaking changes significant enough to warrant a new major version. This is not governed by a fixed rule but by judgment about the nature of the planned changes.

#### Scenario 2 - After a patch release to main with corresponding changes to dev

When a bug fix is important enough to be released as a patch to `main`, it is typically also cherry-picked into `dev`. Note that not every cherry-pick or merge to `main` triggers a release, as multiple patches may be batched together before making a release.

A dev tag increment happens when both of the following conditions are met:

1. A patch version release occurs on `main` (i.e., a release commit is created and tagged)
2. Corresponding cherry-picks for the same fixes were also made to `dev`

If patches were only applied to `main` and `dev` was left untouched, there is no new content on `dev` and therefore no reason to increment its tag. When both conditions are met, the dev tag is incremented (e.g., `1.2.0dev0` → `1.2.0dev1`) to indicate that new content is available and to trigger fresh builds.

#### Scenario 3 - When substantial new content warrants a dev release

Even without a corresponding main branch release, there are times when significant work has landed on `dev` that should be made available to users tracking the bleeding edge. Incrementing the dev tag triggers new TestPyPI and container builds, making this work accessible.

## How Version Numbers Flow

The relationship between `main` and `dev` versions follows a predictable pattern, with dev advancing to the next minor version after a stable release:

```text
main: 1.0.0 ──────────────────────────────> 1.1.0 ────────────────> 1.1.1 ────> 2.0.0
                                              │                       │           │
dev:  1.1.0dev0 → 1.1.0dev1 → 1.1.0dev2 → 1.2.0dev0 → 1.2.0dev1 → 1.2.0dev2 → 2.1.0dev0
                                              ↑                       ↑           ↑
                                    minor release to main      patch to main  major release
                                    triggers minor bump        triggers dev   triggers bump to
                                    and dev tag reset          tag increment  next minor of
                                                                              new major
```

The dev branch version always indicates what the *next* release will be. When `dev` shows `1.2.0dev3`, it means the next minor release will be `1.2.0` (or the version will increment further if scope changes).

## Branch-Specific Release References

Bumpver updates the package and module versions, README version, and Sphinx release value according to the patterns in `pyproject.toml`. It does not update `uv.lock`, deployment template defaults, deployment documentation examples, README installation image tags, or the example platform requirement. Stable preparation includes those references in the same version commit, while a development bump changes only the configured versions and local package lock entry.

The stable release uses its version number for the deployment template's `container_tag` and pins `dioptra-platform` to that version in `examples/examples-setup-requirements.txt`. Dev retains the literal `dev` container tag and an unbounded platform requirement. README installation instructions select main, so their image tags follow the published stable release even when the README is viewed on dev. The README's package version can therefore differ from its installation image tags.

Most third-party image defaults use `latest`, including pgAdmin, MinIO, and Redis. PostgreSQL stays on a selected major version to avoid unexpected database migrations, and `minio/mc` retains a specific release pin because newer client versions have caused compatibility problems. Stable preparation reviews these defaults without replacing every `latest` tag or upgrading dependencies as a release prerequisite.

## Downstream Artifacts

Version releases trigger automated builds of downstream artifacts:

- **Python packages**: Stable releases are [published to PyPI](https://pypi.org/project/dioptra-platform), and development releases are [published to TestPyPI](https://test.pypi.org/project/dioptra-platform)
- **Container images**: Docker images are built, tagged with the corresponding version numbers, and published to [GitHub Packages](https://github.com/orgs/usnistgov/packages?repo_name=dioptra)

These automated builds are one of the primary reasons for creating dev releases, as they make in-progress work available for testing in realistic deployment scenarios.

## Version Format Variations

Due to tooling differences, the dev version format varies slightly depending on where it appears:

| Location                                                                          | Format       | Example      |
| --------------------------------------------------------------------------------- | ------------ | ------------ |
| Most files                                                                        | `X.Y.ZdevN`  | `1.1.0dev5`  |
| `uv.lock`                                                                         | `X.Y.Z.devN` | `1.1.0.dev5` |
| `README.md`, `docs/source/conf.py`, bumpver `current_version` in `pyproject.toml` | `X.Y.Z-devN` | `1.1.0-dev5` |

When `N=0`, the numeric counter is omitted in `README.md`, `docs/source/conf.py`, and the bumpver `current_version` field; the `-dev` suffix remains. For example, these fields use `1.3.0-dev`, while the project version and Git tag use `1.3.0dev0` and the lockfile uses `1.3.0.dev0`. TestPyPI and distribution filenames also use the normalized form `1.3.0.dev0`. Package metadata can retain the equivalent spelling `1.3.0dev0`.

These variations exist due to a combination of tooling requirements (different tools expect different version string formats) and readability considerations for user-facing documents (such as spelling out "beta" instead of using the abbreviated "b").
