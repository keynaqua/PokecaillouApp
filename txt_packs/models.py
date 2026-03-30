from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InstalledPack:
    file_name: str
    file_path: Path
    sha256: str


@dataclass
class DetectionReport:
    packs: list[InstalledPack] = field(default_factory=list)


@dataclass
class DesiredPack:
    file_name: str
    download_url: str
    sha256: str


@dataclass
class CompareResult:
    actions: list = field(default_factory=list)
    up_to_date: list[str] = field(default_factory=list)
