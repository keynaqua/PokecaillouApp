from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from .models import DetectionReport, InstalledMod


class ModDetectError(RuntimeError):
    pass


class FabricMetaError(ModDetectError):
    pass


def _escape_newlines_inside_strings(text: str) -> str:
    """
    Remplace les retours à la ligne bruts trouvés *à l'intérieur* des chaînes JSON
    par \\n, pour tolérer certains fabric.mod.json mal formés.
    """
    result: list[str] = []
    in_string = False
    escaped = False

    for char in text:
        if escaped:
            result.append(char)
            escaped = False
            continue

        if char == "\\":
            result.append(char)
            escaped = True
            continue

        if char == '"':
            result.append(char)
            in_string = not in_string
            continue

        if in_string and char in ("\n", "\r"):
            # On normalise les vrais retours à la ligne présents dans une string JSON
            result.append("\\n")
            continue

        result.append(char)

    return "".join(result)


def _load_json_tolerant(raw_text: str, jar_name: str) -> dict[str, Any] | list[Any]:
    """
    Essaie d'abord le parseur JSON standard.
    Si ça échoue, tente une réparation des sauts de ligne bruts dans les strings.
    """
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        repaired = _escape_newlines_inside_strings(raw_text)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise FabricMetaError(f"{jar_name}: invalid fabric.mod.json") from exc


def _read_fabric_meta(jar_path: Path) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(jar_path) as jar:
            with jar.open("fabric.mod.json") as file:
                raw_text = file.read().decode("utf-8")
    except KeyError as exc:
        raise FabricMetaError(f"{jar_path.name}: missing fabric.mod.json") from exc
    except zipfile.BadZipFile as exc:
        raise FabricMetaError(f"{jar_path.name}: invalid JAR") from exc
    except UnicodeDecodeError as exc:
        raise FabricMetaError(f"{jar_path.name}: unreadable fabric.mod.json") from exc

    data = _load_json_tolerant(raw_text, jar_path.name)

    if isinstance(data, list):
        data = next((item for item in data if isinstance(item, dict) and item.get("id")), None)
        if data is None:
            raise FabricMetaError(f"{jar_path.name}: unusable fabric.mod.json list")

    if not isinstance(data, dict):
        raise FabricMetaError(f"{jar_path.name}: fabric.mod.json must be an object")

    return data


def detect_mods(mods_dir: str | Path) -> DetectionReport:
    mods_path = Path(mods_dir)
    if not mods_path.exists():
        raise FileNotFoundError(f"Mods directory not found: {mods_path}")
    if not mods_path.is_dir():
        raise NotADirectoryError(f"Invalid mods directory: {mods_path}")

    report = DetectionReport()

    for jar_path in sorted(mods_path.glob("*.jar")):
        try:
            meta = _read_fabric_meta(jar_path)
            mod_id = meta.get("id")
            version = meta.get("version")
            name = meta.get("name")

            if not isinstance(mod_id, str) or not mod_id.strip():
                raise FabricMetaError(f"{jar_path.name}: missing id")
            if not isinstance(version, str) or not version.strip():
                raise FabricMetaError(f"{jar_path.name}: missing version")

            report.mods.append(
                InstalledMod(
                    mod_id=mod_id.strip(),
                    version=version.strip(),
                    name=name.strip() if isinstance(name, str) and name.strip() else None,
                    file_path=jar_path,
                )
            )
        except FabricMetaError as exc:
            report.broken_files.append((jar_path, str(exc)))
        except Exception as exc:
            report.broken_files.append((jar_path, f"{jar_path.name}: unexpected error: {exc}"))

    return report