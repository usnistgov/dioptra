# How to Check Published Versions

Use this guide to list Dioptra's Git version tags, published Python package versions, and container release tags. Before preparing a release, check that the proposed version is absent from all three.

-   [Prerequisites](#prerequisites)
-   [Step 1: List the Git Tags](#step-1-list-the-git-tags)
-   [Step 2: List the Python Package Versions](#step-2-list-the-python-package-versions)
-   [Step 3: List the Container Release Tags](#step-3-list-the-container-release-tags)

## Prerequisites

-   A Dioptra clone with `origin` pointing to `usnistgov/dioptra`
-   `curl`, [jq](https://jqlang.org/), and the [GitHub CLI](https://cli.github.com/) installed
-   The GitHub CLI authenticated with permission to read GitHub Packages, which requires `read:packages` for its OAuth login or a classic personal access token

For an existing GitHub CLI login, add the package scope if needed with `gh auth refresh --hostname github.com --scopes read:packages`.

Run the commands from the clone root. If any query fails, resolve the error before treating an empty result as an unused version.

## Step 1: List the Git Tags

Query the remote tags:

```sh
git ls-remote --tags --refs origin
```

Each line contains a commit or tag object ID and a tag name such as `refs/tags/1.2.1`. Find the proposed version in this list. To query only that tag, append `"refs/tags/$RELEASE_VERSION"`, with `RELEASE_VERSION` set to the version you are preparing.

## Step 2: List the Python Package Versions

Query the [PyPI JSON API](https://docs.pypi.org/api/json/) and print the published versions:

```sh
curl --fail --silent --show-error \
    https://pypi.org/pypi/dioptra-platform/json |
    jq -r '.releases | keys[]'
```

For a development release, replace `https://pypi.org` with `https://test.pypi.org`. Match the normalized package version; for example, Git tag `1.3.0dev1` corresponds to package version `1.3.0.dev1`. See [Version Format Variations](about-versioned-releases.md#version-format-variations).

## Step 3: List the Container Release Tags

Use the [GitHub Packages API](https://docs.github.com/en/rest/packages/packages#list-package-versions-for-a-package-owned-by-an-organization) to list release tags for all seven images:

```sh
for IMAGE in nginx mlflow-tracking restapi pytorch-cpu tensorflow2-cpu \
    pytorch-gpu tensorflow2-gpu; do
    echo "$IMAGE"
    GH_PAGER=cat gh api --paginate \
        "/orgs/usnistgov/packages/container/dioptra%2F$IMAGE/versions?per_page=100" \
        --jq '.[].metadata.container.tags[] | select(test("^[0-9]+[.][0-9]+[.][0-9]+"))' || break
done
```

`GH_PAGER=cat` prints the results directly in the terminal for this command. The output groups version tags under each image name. The filter omits branch, pull request, and signature tags. Check every image for the proposed version. If the command reports an error, the listing is incomplete; correct the error and rerun it.

If the version appears as a Git tag, a Python package version, or a tag on any image, select another version before preparing the release.
