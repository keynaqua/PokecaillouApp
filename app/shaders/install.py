from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from logger import shader

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
        with urlopen(request) as response, target.open("wb") as file:
            file.write(response.read())
    except HTTPError as exc:
        raise RuntimeError(f"Download refused ({exc.code}) for URL: {url}") from exc
    except URLError as exc:
        raise RuntimeError(f"Unable to reach URL: {url}") from exc


def install_shader(shaders_dir, shader_url, file_name=None):
    shaders_path = Path(shaders_dir)
    shaders_path.mkdir(parents=True, exist_ok=True)

    if file_name is None:
        file_name = shader_url.rstrip("/").split("/")[-1]
        if not file_name:
            file_name = "shaderpack.zip"

    target = shaders_path / file_name

    shader(f"Download {file_name}")
    _download(shader_url, target)

    return target
