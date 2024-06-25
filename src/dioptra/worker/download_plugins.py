from pathlib import Path
import requests

USER = "string"
PASS = "string"

HOST = "http://localhost:5000"

OUTPUT = Path("./plugins")


def download_plugins(s, hostname, output_path):
    """
    Download all plugins

    """

    for plugin in page_iter(s, hostname, "/api/v1/plugins", page_length=2):
        plugin_name = plugin["name"]
        plugin_id = plugin["id"]
        (OUTPUT / plugin_name).mkdir(parents=True, exist_ok=True)

        print(f"creating plugin {plugin_name}")

        for plugin_file in page_iter(
            s, hostname, f"/api/v1/plugins/{plugin_id}/files", page_length=1
        ):
            filename = plugin_file["filename"]
            contents = plugin_file["contents"]
            (OUTPUT / plugin_name / filename).write_text(contents)


def download_plugins_by_id(s, hostname: str, output_path: Path, plugin_ids: list[int]):
    """
    Download list of plugins.
    """

    for plugin_id in plugin_ids:
        plugin = s.get(f"{hostname}/api/v1/plugins/{plugin_id}").json()
        plugin_name = plugin["name"]
        plugin_id = plugin["id"]
        (OUTPUT / plugin_name).mkdir(parents=True, exist_ok=True)

        print(f"creating plugin {plugin_name}")

        for plugin_file in page_iter(s, hostname, f"/api/v1/plugins/{plugin_id}/files"):
            filename = plugin_file["filename"]
            contents = plugin_file["contents"]
            (OUTPUT / plugin_name / filename).write_text(contents)


def page_iter(
    s: requests.Session,
    hostname: str,
    route: str,
    page_index: int = 0,
    page_length: int = 10,
):
    """
    Generator for iterating over paged responses.
    """

    page = s.get(
        f"{hostname}/{route}?pageIndex={page_index}&pageLength={page_length}"
    ).json()
    while page is not None:
        for element in page["data"]:
            yield element

        next = page.get("next", None)
        page = s.get(f"{hostname}/{next}").json() if next is not None else None


if __name__ == "__main__":
    s = requests.Session()

    s.post(f"{HOST}/api/v1/auth/login", json={"username": USER, "password": PASS})
    user_info = s.get(f"{HOST}/api/v1/users/current").json()
    username = user_info["username"]

    print(f"logged in as {username}")

    download_plugins(s, HOST, OUTPUT)

    plugins = s.get(f"{HOST}/api/v1/plugins").json()
    plugin_ids = [plugin["id"] for plugin in plugins["data"]]
    download_plugins_by_id(s, HOST, OUTPUT, plugin_ids)
