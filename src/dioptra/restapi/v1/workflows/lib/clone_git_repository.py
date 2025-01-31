import subprocess
from pathlib import Path
from urllib.parse import urlparse


def clone_git_repository(url: str, dir: Path) -> str:
    parsed_url = urlparse(url)
    git_branch = parsed_url.fragment or None
    git_paths = parsed_url.params or None
    git_url = parsed_url._replace(fragment="", params="").geturl()

    git_env = ["GIT_TERMINAL_PROMPT=0"]
    git_sparse_args = ["--filter=blob:none", "--no-checkout", "--depth=1"]
    git_branch_args = ["-b", git_branch] if git_branch else []
    clone_cmd = ["git", "clone", *git_sparse_args, *git_branch_args, git_url, str(dir)]
    clone_result = subprocess.run(git_env + clone_cmd, capture_output=True, text=True)

    if clone_result.returncode != 0:
        raise subprocess.CalledProcessError(
            clone_result.returncode, clone_result.stderr
        )

    if git_paths is not None:
        paths = git_paths.split(",")
        sparse_checkout_cmd = ["git", "sparse-checkout", "set", "--cone", *paths]
        sparse_checkout_result = subprocess.run(
            sparse_checkout_cmd, cwd=dir, capture_output=True, text=True
        )

        if sparse_checkout_result.returncode != 0:
            raise subprocess.CalledProcessError(
                sparse_checkout_result.returncode, sparse_checkout_result.stderr
            )

    checkout_cmd = ["git", "checkout"]
    checkout_result = subprocess.run(
        checkout_cmd, cwd=dir, capture_output=True, text=True
    )

    if checkout_result.returncode != 0:
        raise subprocess.CalledProcessError(
            checkout_result.returncode, checkout_result.stderr
        )

    hash_cmd = ["git", "rev-parse", "HEAD"]
    hash_result = subprocess.run(hash_cmd, cwd=dir, capture_output=True, text=True)

    if hash_result.returncode != 0:
        raise subprocess.CalledProcessError(hash_result.returncode, hash_result.stderr)

    return str(hash)


if __name__ == "__main__":
    clone_git_repository(
        "https://github.com/usnistgov/dioptra.git;plugins#dev", Path("dioptra-plugins")
    )
