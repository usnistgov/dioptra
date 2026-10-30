# Release Policy Implementation Status

This temporary table tracks which rules of the [release and maintenance policy](release-and-maintenance-policy.md) are currently in effect. Remove this document once every row applies.

| Policy rule | Applies now (manual) | Applies now (automated) | Waiting on prerequisite | Current mechanism or prerequisite |
| --- | :---: | :---: | :---: | --- |
| [Version classification](release-and-maintenance-policy.md#version-changes) | ✓ | | | Applied by the release owner during preparation. |
| [Stable approval and exact-commit tagging](release-and-maintenance-policy.md#release-timing-and-approval) | ✓ | | | Tagged manually after `main` adoption ([How to Create a Release](how-to-create-a-release.md)). Automated tagging requires release workflow updates. |
| [Branch responsibilities and fix propagation](release-and-maintenance-policy.md#branch-responsibilities) | ✓ | | | Fix owners carry changes between `main` and `dev`. |
| [Patch preparation from `main`](release-and-maintenance-policy.md#candidate-preparation) | ✓ | | | [How to Create a Patch Release](how-to-create-a-patch-release.md). |
| [Major and minor preparation](release-and-maintenance-policy.md#candidate-preparation) | ✓ | | | [How to Merge Dev into Main](how-to-merge-dev-into-main.md). |
| [`uv.lock` refresh PRs on `dev`](release-and-maintenance-policy.md#dependency-maintenance) | | ✓ | | [refresh-uv-lock.yml](../../.github/workflows/refresh-uv-lock.yml) opens a weekly PR targeting `dev`. |
| [`uv.lock` refresh PRs on `main`](release-and-maintenance-policy.md#dependency-maintenance) | ✓ | | | Dispatched manually via `refresh-uv-lock.yml` (`target_branch=main`). Scheduled `main` runs need separate branch and concurrency names. |
| [npm refresh PRs on `dev`, `main` patches only](release-and-maintenance-policy.md#dependency-maintenance) | ✓ | | | Opened manually by maintainers; Dependabot currently covers only GitHub Actions. |
| [Development targets and snapshots](release-and-maintenance-policy.md#development-versions) | ✓ | | | [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md). |
| [Release and maintenance owners](release-and-maintenance-policy.md#ownership-and-recovery) | ✓ | | | Assigned per release and for ongoing maintenance. |
| [Forward database migrations](release-and-maintenance-policy.md#upgrades-and-downgrades) | | ✓ | | The REST API container runs `dioptra-db autoupgrade` on startup. |
| [Routine documentation republication from `main`](release-and-maintenance-policy.md#documentation-publication) | | ✓ | | [sphinx-docs.yml](../../.github/workflows/sphinx-docs.yml) deploys `main` builds to `nist-pages`. |
| [Frontend packaged with the Python distribution](release-and-maintenance-policy.md#version-changes) | | | ✓ | Requires building and packaging the frontend into the wheel/sdist. Deployments currently build the frontend from the branch during initialization. |
| [Numbered build tags (`-buildN`) and moving version tag](release-and-maintenance-policy.md#image-identities-and-completed-builds) | | | ✓ | Requires `docker-images.yml` changes to allocate build numbers and move the version tag after completion. |
| [Container maintenance builds](release-and-maintenance-policy.md#container-maintenance-builds) | | | ✓ | Requires numbered builds, a released-content check on `main`, and lockfile-merge triggers. Current weekly builds tag the tip of `main` as `weekly`. |
| [Completed-build records and discovery](release-and-maintenance-policy.md#completed-build-discovery) | | | ✓ | Requires a completed-build record producer, publication to NIST Pages and GitHub Releases, and discovery tooling. |
| [Release documentation timing and record preservation](release-and-maintenance-policy.md#documentation-publication) | | | ✓ | Requires `sphinx-docs.yml` to wait for release artifact publication and preserve completed-build records. |
| [Per-stage status reporting and bounded retries](release-and-maintenance-policy.md#ownership-and-recovery) | | | ✓ | Requires updates to `release.yml` and `docker-images.yml`. |
