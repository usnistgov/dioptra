# How to Check Published Versions

Use this guide to list Dioptra's Git version tags, published Python package versions, and container release tags. Before preparing a release, verify that the target version is absent from all three.

-   [Prerequisites](#prerequisites)
-   [Step 1: List the Git Tags](#step-1-list-the-git-tags)
-   [Step 2: List the Python Package Versions](#step-2-list-the-python-package-versions)
-   [Step 3: List the Container Release Tags](#step-3-list-the-container-release-tags)

## Prerequisites

-   A Dioptra clone with `origin` pointing to `usnistgov/dioptra`
-   `curl`, [jq](https://jqlang.org/), and the [GitHub CLI](https://cli.github.com/) installed
-   The GitHub CLI authenticated with `read:packages` scope (`gh auth refresh --hostname github.com --scopes read:packages`)

Run the commands from the clone root.

<a id="step-1-list-the-git-tags"></a>

## Step 1: List the Git Tags

Query the remote tags:

```sh
git ls-remote --tags --refs origin
```

Each line prints a commit or tag object ID and a tag ref such as `refs/tags/1.2.1`. To check a single tag directly, append `"refs/tags/$RELEASE_VERSION"`.

<a id="step-2-list-the-python-package-versions"></a>

## Step 2: List the Python Package Versions

Query the [PyPI JSON API](https://docs.pypi.org/api/json/) to list published package versions:

```sh
curl --fail --silent --show-error \
    https://pypi.org/pypi/dioptra-platform/json |
    jq -r '.releases | keys[]'
```

For a development release, replace `https://pypi.org` with `https://test.pypi.org`. Note that PEP 440 normalizes development tags on TestPyPI (`1.3.0dev1` appears as `1.3.0.dev1`); see [Version spellings](release-workflow-reference.md#version-spellings).

<a id="step-3-list-the-container-release-tags"></a>

## Step 3: List the Container Release Tags

Query the [GitHub Packages API](https://docs.github.com/en/rest/packages/packages#list-package-versions-for-a-package-owned-by-an-organization) across all seven service images:

```sh
for IMAGE in nginx mlflow-tracking restapi pytorch-cpu tensorflow2-cpu \
    pytorch-gpu tensorflow2-gpu; do
    echo "$IMAGE"
    GH_PAGER=cat gh api --paginate \
        "/orgs/usnistgov/packages/container/dioptra%2F$IMAGE/versions?per_page=100" \
        --jq '.[].metadata.container.tags[] | select(test("^[0-9]+[.][0-9]+[.][0-9]+"))' || break
done
```

The `select(...)` filter prints only version tags (`X.Y.Z` and `X.Y.ZdevN`), omitting branch, PR, SHA, and signature tags. Confirm that the proposed version does not appear under any of the seven images.
