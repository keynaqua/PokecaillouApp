from pathlib import Path
from .models import CompareResult


def compare_packs(detected, desired, resourcepacks_dir):
    result = CompareResult()
    installed = {p.file_name: p for p in detected.packs}

    for pack in desired:
        current = installed.get(pack.file_name)

        if not current:
            result.actions.append(("install", pack))
            continue

        if current.sha256 != pack.sha256:
            result.actions.append(("update", pack, current.file_path))
        else:
            result.up_to_date.append(pack.file_name)

    return result
