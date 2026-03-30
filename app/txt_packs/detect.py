import hashlib
from pathlib import Path

from .models import DetectionReport, InstalledPack


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_packs(resourcepacks_dir):
    path = Path(resourcepacks_dir)
    report = DetectionReport()

    if not path.exists():
        path.mkdir(parents=True)

    for file in path.glob("*.zip"):
        report.packs.append(
            InstalledPack(
                file_name=file.name,
                file_path=file,
                sha256=_sha256(file),
            )
        )

    return report
