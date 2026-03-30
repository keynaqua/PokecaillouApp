import json
from pathlib import Path


def find_installed_fabric_loader(mc_dir: Path, mc_version: str):
    versions_dir = mc_dir / "versions"

    if not versions_dir.exists():
        return None

    for version_json in versions_dir.glob("*/*.json"):
        try:
            content = json.loads(version_json.read_text(encoding="utf-8"))
        except Exception:
            continue

        version_id = content.get("id", "")
        inherits_from = content.get("inheritsFrom", "")

        if "fabric-loader-" not in version_id:
            continue

        if inherits_from != mc_version and not version_id.endswith(f"-{mc_version}"):
            continue

        prefix = "fabric-loader-"
        tail = version_id.split(prefix, 1)[1]

        suffix = f"-{mc_version}"
        if not tail.endswith(suffix):
            continue

        return tail[:-len(suffix)]

    return None

def get_installed_fabric_version_id(mc_dir: Path, mc_version: str):
    """
    Cherche une version Fabric installée correspondant à la version Minecraft demandée.
    Exemple de retour:
        fabric-loader-0.16.10-1.21.1
    """
    versions_dir = mc_dir / "versions"

    if not versions_dir.exists():
        raise FileNotFoundError("Le dossier versions de Minecraft est introuvable.")

    candidates = []

    for entry in versions_dir.iterdir():
        if not entry.is_dir():
            continue

        name = entry.name
        if name.startswith("fabric-loader-") and name.endswith(f"-{mc_version}"):
            candidates.append(name)

    if not candidates:
        raise RuntimeError(f"Aucune version Fabric installée trouvée pour Minecraft {mc_version}.")

    candidates.sort()
    return candidates[-1]
