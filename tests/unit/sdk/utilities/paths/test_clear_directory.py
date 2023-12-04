from dioptra.sdk.utilities.paths import clear_directory


def test_clear_directory(tmp_path):
    files = ["file1", "dir1/file2", "dir1/dir2/file3"]

    # Make some files
    for f in files:
        # Ensure we're not trying to create files in the root directory!
        f = f.lstrip("/")
        pathobj = tmp_path / f
        pathobj.parent.mkdir(parents=True, exist_ok=True)
        pathobj.touch()

    # Test the function
    clear_directory(tmp_path)

    # Ensure the directory is now clear!
    test_files = list(tmp_path.iterdir())
    assert len(test_files) == 0
