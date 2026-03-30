import json
from pathlib import Path
from urllib.request import urlopen

from .detect import detect_packs
from .compare import compare_packs
from .install import apply_actions
from .models import DesiredPack

from logger import txtp, success


def _load_manifest(url):
    from urllib.request import urlopen
    import json

    with urlopen(url) as r:
        data = json.loads(r.read().decode("utf-8"))

    return [
        DesiredPack(
            file_name=p["file_name"],
            download_url=p["download_url"],
            sha256=p["sha256"],
        )
        for p in data.get("packs", [])
    ]


def update_txt_packs(resourcepacks_dir, manifest_url, apply=True):
    txtp("Load Resourcepacks manifest")
    desired = _load_manifest(manifest_url)

    txtp("Detect local packs installation")
    detected = detect_packs(resourcepacks_dir)

    txtp("Comparing local with online installation")
    result = compare_packs(detected, desired, resourcepacks_dir)

    if not apply:
        txtp("Dry run mode activated")
        return result

    txtp("Apply changes...")
    apply_actions(result, resourcepacks_dir)

    success("Resourcepacks synchronisés avec succes !")
    return result
