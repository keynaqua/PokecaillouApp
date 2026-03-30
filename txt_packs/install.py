from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from logger import txtp

def _download(url, target: Path):
    target.parent.mkdir(parents=True, exist_ok=True)

    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
        },
    )

    try:
        with urlopen(request) as r, target.open("wb") as f:
            f.write(r.read())
    except HTTPError as e:
        raise RuntimeError(f"Download refused ({e.code}) for URL: {url}") from e
    except URLError as e:
        raise RuntimeError(f"Unable to reach URL: {url}") from e



def apply_actions(result, resourcepacks_dir):
    for action in result.actions:
        kind = action[0]

        if kind == "install":
            pack = action[1]
            txtp(f"Install {pack.file_name}")
            _download(pack.download_url, Path(resourcepacks_dir) / pack.file_name)

        elif kind == "update":
            pack, old_file = action[1], action[2]
            if old_file.exists():
                txtp(f"Remove {old_file.name}")
                old_file.unlink()

            txtp(f"Update {pack.file_name}")
            _download(pack.download_url, Path(resourcepacks_dir) / pack.file_name)
