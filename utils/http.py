import json
import time
import shutil
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Connection": "close",
}


class DownloadError(RuntimeError):
    pass


def _make_request(url: str, headers: dict | None = None) -> Request:
    merged_headers = dict(DEFAULT_HEADERS)
    if headers:
        merged_headers.update(headers)
    return Request(url, headers=merged_headers)


def get_json(
    url: str,
    timeout: int = 20,
    retries: int = 3,
    retry_delay: float = 1.5,
) -> dict | list:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            req = _make_request(url, {"Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                raw = response.read()
                encoding = response.headers.get_content_charset() or "utf-8"
                return json.loads(raw.decode(encoding))

        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(retry_delay * attempt)
            else:
                raise DownloadError(
                    f"Échec récupération JSON: {url} ({e})"
                ) from e

    raise DownloadError(f"Échec récupération JSON: {url} ({last_error})")


def download_file(
    url: str,
    dest: Path,
    timeout: int = 60,
    retries: int = 4,
    retry_delay: float = 2.0,
    chunk_size: int = 1024 * 64,
) -> Path:
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp_dest = dest.with_suffix(dest.suffix + ".part")
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            req = _make_request(url)

            with urlopen(req, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                if status >= 400:
                    raise DownloadError(f"HTTP {status} sur {url}")

                with open(tmp_dest, "wb") as f:
                    shutil.copyfileobj(response, f, length=chunk_size)

            if not tmp_dest.exists() or tmp_dest.stat().st_size == 0:
                raise DownloadError(f"Fichier vide téléchargé depuis {url}")

            tmp_dest.replace(dest)
            return dest

        except (HTTPError, URLError, TimeoutError, OSError, DownloadError) as e:
            last_error = e

            if tmp_dest.exists():
                try:
                    tmp_dest.unlink()
                except OSError:
                    pass

            if attempt < retries:
                time.sleep(retry_delay * attempt)
            else:
                raise DownloadError(
                    f"Échec téléchargement fichier: {url} -> {dest} ({e})"
                ) from e

    raise DownloadError(f"Échec téléchargement fichier: {url} ({last_error})")
