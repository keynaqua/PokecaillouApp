import json
from datetime import datetime, timezone

from config import ICON, get_minecraft_dir
from utils.system import build_java_args


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def create_launcher_profile(name, game_dir, version_id):
    launcher_file = get_minecraft_dir() / "launcher_profiles.json"

    if launcher_file.exists():
        data = json.loads(launcher_file.read_text(encoding="utf-8"))
    else:
        data = {"profiles": {}}

    profiles = data.setdefault("profiles", {})
    existing = profiles.get(name)

    if existing is not None:
        # Keep user-tuned settings like custom RAM while refreshing
        # the launcher target selected by the installer.
        existing["name"] = name
        existing["type"] = "custom"
        existing["lastUsed"] = now_iso()
        existing["lastVersionId"] = version_id
        existing["gameDir"] = str(game_dir)
        existing["icon"] = ICON
        existing.setdefault("created", now_iso())
        existing.setdefault("javaArgs", build_java_args())
    else:
        profiles[name] = {
            "name": name,
            "type": "custom",
            "created": now_iso(),
            "lastUsed": now_iso(),
            "lastVersionId": version_id,
            "gameDir": str(game_dir),
            "icon": ICON,
            "javaArgs": build_java_args(),
        }

    launcher_file.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
