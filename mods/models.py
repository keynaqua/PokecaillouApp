from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InstalledMod:
    mod_id: str
    version: str
    name: str | None
    file_path: Path


@dataclass
class DetectionReport:
    mods: list[InstalledMod] = field(default_factory=list)
    broken_files: list[tuple[Path, str]] = field(default_factory=list)


@dataclass
class DesiredMod:
    mod_id: str
    version: str
    download_url: str
    file_name: str | None = None


@dataclass
class ModAction:
    kind: str
    mod_id: str
    from_version: str | None
    to_version: str
    download_url: str | None = None
    target_file: Path | None = None
    remove_files: list[Path] = field(default_factory=list)


@dataclass
class CompareResult:
    actions: list[ModAction] = field(default_factory=list)
    up_to_date: list[InstalledMod] = field(default_factory=list)
    extra_mods: list[InstalledMod] = field(default_factory=list)
