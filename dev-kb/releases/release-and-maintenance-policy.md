# Release and Maintenance Policy

This reference states Dioptra's rules for package versions, branches, dependency maintenance, container builds, and release documentation. [About Versioned Releases](about-versioned-releases.md) explains the reasoning behind them. The [implementation status](release-policy-implementation-status.md) tracks which rules are currently in effect.

## Version changes

[Version increments](about-versioned-releases.md#version-increments) explains the reasoning behind these criteria.

Stable package versions use `X.Y.Z`. A package version identifies the backend source, the frontend built for that release, and the dependency requirements published in `pyproject.toml`. Every major, minor, and patch release publishes a new Python package and its container images.

| Increment | Criteria |
| --- | --- |
| Major | A planned architectural break with the current major series, or a fundamental change to a primary user workflow or file format. |
| Minor | New capability, streamlined existing capability, or consolidation of features within the current architecture. May include incompatible changes to features outside primary user workflows. |
| Patch | A correction without new user-facing capability. May narrow behavior for security or correctness, and may include a bug-fix database migration. |

Classification rules:

-   The content of the release determines the increment, not the branch it originates from.
-   A `BREAKING CHANGE` commit footer records that a change could interrupt an existing workflow; it does not determine the version increment.
-   Removing a feature or refactoring internals with no user-facing improvement is a patch when released alone, or ships as part of the next minor release when bundled with new features.
-   The REST API path version (`api/v1`) is independent of the package version.

Publication requirements by change type:

| Change | Required publication |
| --- | --- |
| Backend application fix | Package patch and container images. |
| Frontend application fix | Package patch and container images, even when Python code is unchanged. |
| npm dependency update on `main` for a security or bug fix | Rebuilt frontend in a package patch and container images. |
| Routine npm dependency refresh on `dev` | Included in the next minor release. |
| Correction to published Python requirements in `pyproject.toml`, such as excluding a vulnerable version | Package patch and container images. |
| `uv.lock` refresh within unchanged `pyproject.toml` requirements | Container maintenance build of the existing package version; PyPI package is unchanged. |
| OS or base-image refresh | Container maintenance build of the existing package version. |
| Repository-only tooling change or correction to released documentation | No package release or container build. |

## Deprecation

Dioptra 1.x does not enforce a deprecation notice period before removing or replacing features. A formal deprecation policy and schedule will be established no later than the 2.0 release. [Deprecation](about-versioned-releases.md#deprecation) explains when one will be needed.

<a id="approval-and-maintenance-triggers"></a>

## Release timing and approval

[Release timing](about-versioned-releases.md#release-timing) explains how releases are planned.

| Release | Trigger | Approval |
| --- | --- | --- |
| Major | A planned set of breaking changes is complete. | Planned by the team and approved by the release owner. |
| Minor | A planned roadmap milestone is complete, or accumulated work on `dev` warrants a release. | Approved by the release owner. |
| Patch | Any one of these: a security update; a material bug fix that does not depend on `dev`-only changes; a large internal refactoring released early to limit branch drift. | Approved by the release owner. |

A stable release requires one complete tested candidate and human approval. Adopting the candidate on `main` authorizes tagging and publishing that exact commit. Automation never substitutes a newer commit or tags a failed candidate. Maintenance commits on `main` do not trigger package releases.

If a container maintenance build runs while `main` holds an adopted candidate whose release publication has not yet finished, the maintenance build must check the released application and dependency declarations rather than publishing unreleased candidate content under the previous version.

<a id="branch-and-candidate-responsibilities"></a>

## Branch responsibilities

[Branch life cycles](about-versioned-releases.md#branch-life-cycles) explains why the branches are reconciled during release preparation.

| Branch | Contents |
| --- | --- |
| `main` | The latest stable release, plus reviewed lockfile maintenance, workflow updates, bug fixes, and corrections to released documentation. |
| `dev` | Integration of the next release. Feature branches start from `dev` and merge back into it. |
| `release-<version>` | Temporary branch for preparing and reviewing one stable release. |

Fixes may start on either `main` or `dev`. The fix owner ensures that applicable stable fixes also reach `dev` without introducing separate implementations on the two branches. When reconciling dependency constraints between `main` and `dev`, preserve active security restrictions from both branches.

## Candidate preparation

Every stable release is prepared on a temporary branch created from `main`. For a major or minor release, the intended `dev` changes are merged into that branch. After review, `main` is fast-forwarded to the checked release commit.

| Candidate dependency declarations (`pyproject.toml`) | Lockfile handling (`uv.lock`) |
| --- | --- |
| Differ from `main` | Run `uv lock --upgrade` and review the full lockfile diff. |
| Match `main` | Update only the local `dioptra-platform` version entry in `uv.lock`. |

If `main` advances before the candidate is adopted, reconcile the candidate with the updated `main` branch and re-run validation before fast-forwarding `main`.

## Dependency maintenance

[Dependency lockfiles](about-versioned-releases.md#dependency-lockfiles) explains why the two lockfiles are maintained differently.

| Lockfile | `main` | `dev` |
| --- | --- | --- |
| `uv.lock` | Reviewed refresh PRs; each merge triggers a container maintenance build. | Reviewed refresh PRs. |
| `src/frontend/package-lock.json` | Updated only for security or bug fixes released as a patch. | Routine reviewed refresh PRs shipped in the next minor release. |

Validate each branch's lockfile against that branch's code and dependency declarations. Do not copy lockfiles across branches or hand-edit dependency entries, apart from the local `dioptra-platform` version in `uv.lock`. Reconcile differences during release candidate preparation.

<a id="development-publication"></a>

## Development versions

Development versions use `X.Y.ZdevN` (see [Version spellings](release-workflow-reference.md#version-spellings) for tool-specific formats). After a major or minor release, advance `dev` to the next minor target with the counter reset to `dev0`, unless a new major version is planned.

Development snapshots are published at the team's discretion for testing or evaluation. Carrying a stable fix to `dev`, refreshing lockfiles, or updating README image tags does not require a snapshot or a counter increment. If the current `dev` version string has never been published (including `dev0`), it can be tagged and published directly; if it has already been published, increment the `devN` counter first. Never republish changed contents under an existing version tag.

## Maintenance scope

Only the latest stable package version receives container maintenance builds and security fixes. Each stable release supersedes earlier releases, including previous patches in the same minor series. Published development snapshots receive no maintenance builds.

## Upgrades and downgrades

-   Database migrations apply sequentially, supporting forward upgrades across the 1.x series.
-   When a release changes data outside the database (such as MLflow artifacts), the project provides a forward migration script.
-   Alembic migrations define downgrade steps, but reversing a schema migration can drop tables or columns, so a downgrade can lose data. To return to an earlier version, restore a pre-upgrade backup and pin the earlier package version and image tags.
-   Deployments running superseded versions receive no maintenance builds or security updates.

## Container maintenance builds

A container maintenance build refreshes the operating system, base images, and locked Python packages for the latest stable release without changing the package version. Maintenance builds run on two triggers:

-   A weekly scheduled build using the latest committed `uv.lock` on `main`.
-   Merging a reviewed `uv.lock` refresh PR into `main`.

Once a maintenance build passes validation, signing, and verification, it is published automatically without requiring an additional approval step.

## Image identities and completed builds

[Container builds](about-versioned-releases.md#container-builds) explains why images carry build numbers.

Every versioned container image publication receives an immutable `<package-version>-build<N>` tag (starting at `build1` for each package version).

| Tag example | Meaning |
| --- | --- |
| `restapi:1.2.1-build1` | Initial image build for package `1.2.1`. |
| `restapi:1.2.1-build3` | Subsequent maintenance build for `1.2.1` (for example, after a failed `build2`). |
| `restapi:1.2.1` | Moving tag pointing to the highest completed build of `1.2.1`. |
| `restapi:1.2.2-build1` | Initial image build for package `1.2.2`. |

Build numbering rules:

-   All seven service images and target architectures in a build share the same `<package-version>-build<N>` tag.
-   Build numbers are reserved when a build starts and are never reused after a failed or cancelled run.
-   A numbered tag is immutable. Rebuilding images allocates a new build number; retrying signing or publication on already-built images retains the same build number.
-   Build numbers are compared numerically (`build10` is newer than `build9`) and do not create Git tags or PyPI releases.
-   Cross-version tags (`latest`, `1`, `1.2`) and branch or PR tags are not release build identities.

A build is complete only when all seven service images pass build, image index assembly, signing, transparency logging, and verification. Only a completed build updates the moving `<package-version>` tag and publishes a completed-build record containing the package version, build number, source commit, and image digests.

## Completed-build discovery

Completed-build records are published independently to the NIST documentation site (<https://pages.nist.gov/dioptra/>) and to GitHub Releases. A publication failure on one host does not block the other, and missing records can be republished from retained build metadata without rebuilding images.

Discovery and deployment rules:

-   Deployment tooling queries the published records without requiring authentication, preferring the NIST site when both hosts are reachable, and selects the highest completed build number for the installed `dioptra-platform` package version.
-   All services in a deployment must use the image digests from the same completed-build record.
-   Tooling must reject records with conflicting digests for the same build identity, must never downgrade a deployment to an older build number or change the package version automatically, and must leave an existing deployment untouched if discovery or image pulls fail.

## Documentation publication

Corrections to released documentation and workflow updates on `main` may republish the documentation site without a package release, Git tag, or container build number.

Documentation for unreleased features stays on `dev` or a release preparation branch. During a release, updated documentation is deployed after the release's package and images are published, and every documentation deployment preserves existing completed-build records.

## Ownership and recovery

Each release has an assigned release owner (typically the maintainer preparing it) who coordinates review, validation, publication recovery, and post-release `dev` follow-up. A designated maintenance owner handles dependency refresh PRs and failed maintenance builds.

Publication workflows report the status of each stage and retry transient failures a limited number of times before notifying the release owner. When a publication workflow fails:

-   Transient network or registry errors may be retried on the unchanged commit and build inputs.
-   If the PyPI upload succeeds but image publication fails, keep the published package version and recover the missing image stages under the build numbering rules.
-   If fixing the failure requires changing application code or `pyproject.toml` requirements, prepare and review a new package version.
-   Never delete or move a tag after artifacts have been published under it.
