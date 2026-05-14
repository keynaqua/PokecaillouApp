from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from config import JAR_GLOB, MOD_HASH_CHUNK_SIZE


@dataclass
class InstalledMod:
    mod_id: str
    version: str
    file_path: Path
    sha1: str | None = None
    git_blob_sha: str | None = None


@dataclass
class DetectionReport:
    mods: list[InstalledMod] = field(default_factory=list)
    broken_files: list[tuple[Path, str]] = field(default_factory=list)


def sha1_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as file:
        while chunk := file.read(MOD_HASH_CHUNK_SIZE):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()


def ensure_sha1(mod: InstalledMod) -> str:
    if mod.sha1 is None:
        mod.sha1 = sha1_file(mod.file_path)
    return mod.sha1


def ensure_git_blob_sha(mod: InstalledMod) -> str:
    if mod.git_blob_sha is None:
        mod.git_blob_sha = git_blob_sha(mod.file_path)
    return mod.git_blob_sha


def _escape_control_chars(text: str) -> str:
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
        if in_string and char in ("\n", "\r", "\t"):
            result.append({"\n": "\\n", "\r": "\\r", "\t": "\\t"}[char])
            continue
        result.append(char)

    return "".join(result)


def _load_json_tolerant(text: str) -> dict[str, Any] | list[Any]:
    text = text.replace("\ufeff", "")
    for candidate in (text, _escape_control_chars(text)):
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            pass
    return json.loads(_escape_control_chars(text))


def _read_fabric_meta(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as jar:
        with jar.open("fabric.mod.json") as file:
            data = _load_json_tolerant(file.read().decode("utf-8-sig", errors="replace"))

    if isinstance(data, list):
        data = next((item for item in data if isinstance(item, dict) and item.get("id")), {})
    if not isinstance(data, dict):
        raise RuntimeError("fabric.mod.json inexploitable")
    return data


def detect_mods(mods_dir: str | Path) -> DetectionReport:
    mods_path = Path(mods_dir)
    report = DetectionReport()

    if not mods_path.exists():
        return report
    if not mods_path.is_dir():
        raise NotADirectoryError(f"Dossier mods invalide: {mods_path}")

    for jar_path in sorted(mods_path.glob(JAR_GLOB)):
        try:
            meta = _read_fabric_meta(jar_path)
            mod_id = meta.get("id")
            version = meta.get("version")
            if not isinstance(mod_id, str) or not mod_id.strip():
                raise RuntimeError("id manquant")
            if not isinstance(version, str) or not version.strip():
                raise RuntimeError("version manquante")
            report.mods.append(
                InstalledMod(
                    mod_id=mod_id.strip(),
                    version=version.strip(),
                    file_path=jar_path,
                )
            )
        except Exception as exc:
            report.broken_files.append((jar_path, str(exc)))

    return report
