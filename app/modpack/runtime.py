from dataclasses import dataclass
from typing import Any

from config import LATEST_VERSION, get_modpack_info_url, modpack_key
from utils.http import get_json


@dataclass(frozen=True)
class ModpackInfo:
    key: str
    name: str
    minecraft_version: str
    launcher: str
    launcher_version: str
    installation_dir: str


def _first_string(data: dict[str, Any], *fields: str) -> str | None:
    for field in fields:
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _required_string(data: dict[str, Any], label: str, *fields: str) -> str:
    value = _first_string(data, *fields)
    if value is None:
        raise RuntimeError(f"modpack.json: champ '{label}' manquant ou invalide")
    return value


def _loader_data(data: dict[str, Any]) -> tuple[str, str]:
    raw_loader = data.get("loader", data.get("mod_loader"))
    if isinstance(raw_loader, dict):
        launcher = _required_string(raw_loader, "loader.type", "type", "id", "name").lower()
        version = (
            _first_string(raw_loader, "version", "loader_version", f"{launcher}_version")
            or LATEST_VERSION
        )
        return launcher, version

    launcher = _required_string(data, "launcher", "launcher", "mod_loader", "loader").lower()
    version = (
        _first_string(
            data,
            "launcher_version",
            "loader_version",
            f"{launcher}_version",
            "version",
        )
        or LATEST_VERSION
    )
    return launcher, version


def load_modpack_info(name_or_key: str) -> ModpackInfo:
    key = modpack_key(name_or_key)
    data = get_json(get_modpack_info_url(key))
    if not isinstance(data, dict):
        raise RuntimeError("modpack.json doit etre un objet JSON")

    launcher, launcher_version = _loader_data(data)

    return ModpackInfo(
        key=key,
        name=_first_string(data, "name", "display_name") or name_or_key,
        minecraft_version=_required_string(
            data,
            "minecraft_version",
            "minecraft_version",
            "minecraftVersion",
            "mc_version",
        ),
        launcher=launcher,
        launcher_version=launcher_version.lower() if launcher_version.lower() == LATEST_VERSION else launcher_version,
        installation_dir=_required_string(
            data,
            "installation_dir",
            "installation_dir",
            "install_dir",
            "folder",
            "installation_folder",
        ),
    )
