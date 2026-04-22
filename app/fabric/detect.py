import json
from pathlib import Path


def _parse_version_tuple(version: str) -> tuple[int, ...]:
    """
    Transforme une version du type '0.18.6' en tuple comparable: (0, 18, 6).
    Si jamais un segment n'est pas numérique, on le traite en 0.
    """
    parts = []

    for part in version.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)

    return tuple(parts)


def _extract_loader_version(version_id: str, mc_version: str) -> str | None:
    """
    Extrait la version du loader depuis un id du type:
        fabric-loader-0.18.6-1.21.1
    Retourne:
        0.18.6
    """
    prefix = "fabric-loader-"
    suffix = f"-{mc_version}"

    if not version_id.startswith(prefix):
        return None

    if not version_id.endswith(suffix):
        return None

    return version_id[len(prefix):-len(suffix)]


def find_installed_fabric_loader(mc_dir: Path, mc_version: str):
    """
    Cherche toutes les installations Fabric correspondant à mc_version
    et retourne la version du loader la plus récente.
    Exemple:
        '0.18.6'
    """
    versions_dir = mc_dir / "versions"

    if not versions_dir.exists():
        return None

    found_versions = []

    for version_json in versions_dir.glob("*/*.json"):
        try:
            content = json.loads(version_json.read_text(encoding="utf-8"))
        except Exception:
            continue

        version_id = content.get("id", "")
        inherits_from = content.get("inheritsFrom", "")

        if "fabric-loader-" not in version_id:
            continue

        loader_version = _extract_loader_version(version_id, mc_version)
        if loader_version is None:
            continue

        # On valide bien qu'il s'agit de la bonne version MC.
        # La plupart du temps inheritsFrom == mc_version.
        # On garde aussi le cas où l'id est déjà parfaitement suffixé.
        if inherits_from != mc_version and not version_id.endswith(f"-{mc_version}"):
            continue

        found_versions.append(loader_version)

    if not found_versions:
        return None

    return max(found_versions, key=_parse_version_tuple)


def get_installed_fabric_version_id(mc_dir: Path, mc_version: str):
    """
    Cherche la version Fabric installée la plus récente correspondant
    à la version Minecraft demandée.

    Exemple de retour:
        fabric-loader-0.18.6-1.21.1
    """
    versions_dir = mc_dir / "versions"

    if not versions_dir.exists():
        raise FileNotFoundError("Le dossier versions de Minecraft est introuvable.")

    candidates = []

    for entry in versions_dir.iterdir():
        if not entry.is_dir():
            continue

        version_id = entry.name
        loader_version = _extract_loader_version(version_id, mc_version)

        if loader_version is None:
            continue

        candidates.append((loader_version, version_id))

    if not candidates:
        raise RuntimeError(
            f"Aucune version Fabric installée trouvée pour Minecraft {mc_version}."
        )

    candidates.sort(key=lambda item: _parse_version_tuple(item[0]))
    return candidates[-1][1]
