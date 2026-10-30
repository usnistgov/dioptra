# Release Workflow and Metadata Reference

<a id="implementation-status"></a>

This reference describes the GitHub Actions workflows, container image tags, and version metadata files used to prepare and publish Dioptra releases. The [release and maintenance policy](release-and-maintenance-policy.md) states the governing rules, and the [implementation status](release-policy-implementation-status.md) tracks which rules are currently active.

## Published artifacts

| Artifact | Destination | Identity |
| --- | --- | --- |
| Stable Python wheel and source distribution | [PyPI](https://pypi.org/project/dioptra-platform/) | Normalized project version. |
| Development Python wheel and source distribution | [TestPyPI](https://test.pypi.org/project/dioptra-platform/) | Normalized project version. |
| Service container images | [GHCR](https://github.com/orgs/usnistgov/packages?repo_name=dioptra) | Tags listed in the [image tag inventory](#image-tag-inventory). |
| Sphinx documentation site | [NIST Pages](https://pages.nist.gov/dioptra/) (`nist-pages` branch) | Documentation built from `main`. |

Container images are built from the repository source tree and `uv.lock`, not from the PyPI wheel. The source distribution includes `uv.lock`, while the wheel and source metadata publish the version ranges declared in `pyproject.toml`.

## Service images and platforms

| Image (`ghcr.io/usnistgov/dioptra/<service>`) | `linux/amd64` | `linux/arm64` |
| --- | :---: | :---: |
| `nginx` | Yes | Yes |
| `mlflow-tracking` | Yes | Yes |
| `restapi` | Yes | Yes |
| `pytorch-cpu` | Yes | Yes |
| `tensorflow2-cpu` | Yes | Yes |
| `pytorch-gpu` | Yes | No |
| `tensorflow2-gpu` | Yes | No |

[docker-images.yml](../../.github/workflows/docker-images.yml) builds each platform image, pushes it by digest, and assembles a multi-architecture image index (manifest list) for each service.

## Workflow triggers and outcomes

| Workflow | Triggers | Actions | Failure behavior |
| --- | --- | --- | --- |
| [release.yml](../../.github/workflows/release.yml) | Tag push matching `*.*.*`. | Runs unit tests, validates the tag against `pyproject.toml`, builds distributions, and publishes to PyPI or TestPyPI via OIDC trusted publishing. | A failed test or version mismatch blocks the package upload. Does not stop `docker-images.yml`. |
| [docker-images.yml](../../.github/workflows/docker-images.yml) | Pushes to `main` and `dev`, PRs targeting them, tags matching `*.*.*`, and Sundays at 03:00 UTC (`0 3 * * 0`). | Builds and pushes platform images, assembles image indexes, and signs and verifies them. | Images are pushed to GHCR before the signing and verification jobs run. |
| [tox-tests.yml](../../.github/workflows/tox-tests.yml) | Branch pushes, tag pushes, and manual dispatch. | Runs linting, type checks, unit tests, and deployment template tests (`pytest-cookiecutter`). | Reports a failed check on the commit or PR. |
| [sphinx-docs.yml](../../.github/workflows/sphinx-docs.yml) | Branch pushes, tag pushes, and manual dispatch. | Builds the Sphinx documentation and OpenAPI spec. Builds on `main` deploy `docs/build` to `nist-pages`. | Deploys on `main` push without waiting for tag workflows. |
| [refresh-uv-lock.yml](../../.github/workflows/refresh-uv-lock.yml) | Mondays at 08:37 UTC (`37 8 * * 1`) and manual dispatch (`target_branch`, `dry_run`). | Runs `uv lock --upgrade`, opens or updates a PR (defaulting to `dev`), and dispatches `tox-tests.yml` and `sphinx-docs.yml`. | Reports check results on the PR; merging requires human review. |

`refresh-uv-lock.yml` uses the branch and concurrency group name `refresh-uv-lock-dev` regardless of the selected `target_branch`.

<a id="release-review-and-main-adoption"></a>

## Release review and adoption

| Event | Behavior |
| --- | --- |
| Push of `release-<version>` branch | Runs `tox-tests.yml` and `sphinx-docs.yml` on the branch head. |
| Pull request into `main` | Runs `docker-images.yml` and `frontend-e2e.yml`, plus `frontend-checks.yml` when frontend paths change. PR workflows run against GitHub's temporary merge ref (`refs/pull/<number>/merge`). |
| Pull request with merge conflicts | GitHub skips `pull_request` workflows until conflicts are resolved. |
| Fast-forward of `main` to `release-<version>` | Marks the release PR as **Merged** at the exact reviewed commit. |

Stable releases assemble a local `--no-ff` merge commit (`Merge branch 'release-<version>'`) with `main` as the first parent and the release preparation commit as the tip of the second parent, push it to `origin` as `release-<version>`, then fast-forward `main` to that merge commit after PR checks pass. This preserves the reviewed commit hash and individual fix commits, unlike the squash-merge workflow used for ordinary feature PRs in [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Image tag inventory

`docker-images.yml` generates tags using [docker/metadata-action](https://github.com/docker/metadata-action/tree/v6#tags-input):

| Trigger | Generated tags |
| --- | --- |
| Version tag (`*.*.*`) | The raw Git tag. Stable versions also receive `X.Y.Z`, `X.Y`, and `X` (`X` is omitted for `0.x`). |
| Stable version tag | `latest` (excluded for prerelease tags). |
| Branch push | The branch name (`main` or `dev`). |
| Pull request | `pr-<number>`. |
| Weekly schedule | `weekly`, `weekly-YYYYMMDD`, `main`, and the commit SHA (scheduled runs execute on the default branch, `main`). |
| Every build | The full 40-character commit SHA. |

## Version validation

The [validate-release-tag](../../.github/actions/validate-release-tag/action.yml) action in `release.yml` checks that the pushed Git tag matches `version` in `pyproject.toml`. Tags containing `dev`, `rc`, `a` (alpha), or `b` (beta) route to TestPyPI; stable versions route to PyPI. Release tags do not use a leading `v`.

## Version spellings

| Location | Development example | Stable example |
| --- | --- | --- |
| `pyproject.toml` (`project.version`), `__version__.py` files, Git tag | `1.3.0dev0` | `1.2.1` |
| `uv.lock`, built package metadata, TestPyPI | `1.3.0.dev0` | `1.2.1` |
| `pyproject.toml` (`tool.bumpver.current_version`), `README.md` heading, `docs/source/conf.py` | `1.3.0-dev` | `1.2.1` |
| Same display fields when `N > 0` | `1.3.0-dev2` | Not applicable |

## Version reference locations

Running `uvx tox run -e bumpver` updates `pyproject.toml`, `src/dioptra/{client,pyplugs,restapi,rq,sdk,task_engine,worker}/__version__.py`, the `README.md` version heading, and `docs/source/conf.py`.

The following files are outside bumpver and are updated explicitly during release preparation. `X.Y.Z` is the version being released:

| Location | Stable release value | `dev` branch value |
| --- | --- | --- |
| `uv.lock` (`name = "dioptra-platform"` version) | `X.Y.Z` | `X.Y.Z.devN` |
| `cookiecutter-templates/cookiecutter-dioptra-deployment/cookiecutter.json` (`container_tag`) | `X.Y.Z` | `dev` |
| `tests/cookiecutter_dioptra_deployment/test_cruft_no_prompt.py` (`EXPECTED_DEFAULTS["container_tag"]`) | `X.Y.Z` | `dev` |
| `docs/source/how-to/setup-dioptra/prepare-deployment.rst` (`container_tag` default) | `X.Y.Z` | `dev` |
| `docs/source/how-to/setup-dioptra/reference/deployment-template-reference.rst` (`container_tag` default and prompt) | `X.Y.Z` | `dev` |
| `README.md` (`docker pull` examples) | Latest published stable version | Latest published stable version |
| `examples/examples-setup-requirements.txt` (`dioptra-platform` pin) | `dioptra-platform==X.Y.Z` | Unbounded `dioptra-platform` |

> [!IMPORTANT]
> `tests/cookiecutter_dioptra_deployment/test_cruft_no_prompt.py` runs `cruft create` against the local Git repository's **committed** tree and checks that rendered service images match `EXPECTED_DEFAULTS["container_tag"]`. Always update `test_cruft_no_prompt.py` alongside `cookiecutter.json` and commit the version changes before running `uvx tox run -e pytest-cookiecutter`.

Third-party container tags in the deployment template (`postgres`, `redis`, `minio`, `minio/mc`, `pgadmin4`) are independent of the Dioptra release version and remain unchanged unless an update is explicitly planned.

## Image signing

`docker-images.yml` signs each multi-architecture image index in five steps:

1.  Generate the signing payload (`cosign generate`).
2.  Sign the payload with OpenSSL via [sign-payload-fips](../../.github/actions/sign-payload-fips/action.yml).
3.  Attach the signature to the image in GHCR (`cosign attach signature`).
4.  Upload and verify the [Rekor](https://docs.sigstore.dev/logging/overview/) transparency log entry.
5.  Verify the attached signature against the public key.

## Maintainer procedures

-   [How to Merge Dev into Main](how-to-merge-dev-into-main.md)
-   [How to Create a Patch Release](how-to-create-a-patch-release.md)
-   [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md)
-   [How to Create a Release](how-to-create-a-release.md)
-   [How to Check Published Versions](how-to-check-published-versions.md)
