import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse


def clone_git_repository(url: str, dir: Path) -> str:
    """
    Clones a git repository by calling the git command line tool as a subprocess. It
    attempts to pull the minimal amount of data needed.

    As an example, providing 'https://github.com/usnistgov/dioptra.git#dev;extras' as
    the url would clone the dioptra repository and perform a sparse checkout of the dev
    branch for the extras directory.

    Args:
        url: The url to the git repository. A branch can be specified as the url
            fragment and paths for sparse checkout can be specified in a comma
            separated list in the url params.
        dir: The directory to clone the git repository into.

    Returns:
        The git commit hash of the cloned repository.
    """

    parsed_url = urlparse(url)
    git_branch = parsed_url.fragment or None
    git_paths = parsed_url.params or None
    git_url = parsed_url._replace(fragment="", params="").geturl()

    cmd = shutil.which("git")
    if cmd is None:
        raise RuntimeError("Git command not found.")

    git_env = {"GIT_TERMINAL_PROMPT": "0"}
    git_sparse_args = ["--filter=blob:none", "--no-checkout", "--depth=1"]
    git_branch_args = ["-b", git_branch] if git_branch else []
    clone_cmd = [cmd, "clone", *git_sparse_args, *git_branch_args, git_url, str(dir)]
    clone_result = subprocess.run(
        clone_cmd, env=git_env, capture_output=True, text=True
    )

    if clone_result.returncode != 0:
        raise subprocess.CalledProcessError(
            clone_result.returncode, clone_result.stderr
        )

    if git_paths is not None:
        paths = git_paths.split(",")
        sparse_checkout_cmd = [cmd, "sparse-checkout", "set", "--cone", *paths]
        sparse_checkout_result = subprocess.run(
            sparse_checkout_cmd, cwd=dir, capture_output=True, text=True
        )

        if sparse_checkout_result.returncode != 0:
            raise subprocess.CalledProcessError(
                sparse_checkout_result.returncode, sparse_checkout_result.stderr
            )

    checkout_cmd = [cmd, "checkout"]
    checkout_result = subprocess.run(
        checkout_cmd, cwd=dir, capture_output=True, text=True
    )

    if checkout_result.returncode != 0:
        raise subprocess.CalledProcessError(
            checkout_result.returncode, checkout_result.stderr
        )

    hash_cmd = [cmd, "rev-parse", "HEAD"]
    hash_result = subprocess.run(hash_cmd, cwd=dir, capture_output=True, text=True)

    if hash_result.returncode != 0:
        raise subprocess.CalledProcessError(hash_result.returncode, hash_result.stderr)

    return str(hash_result.stdout.strip())


if __name__ == "__main__":
    clone_git_repository(
        "https://github.com/usnistgov/dioptra.git;plugins#dev", Path("dioptra-plugins")
    )
