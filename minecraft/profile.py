import json
from datetime import datetime, timezone
from utils.system import build_java_args
from config import (get_minecraft_dir, ICON)

def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def create_launcher_profile(name, game_dir, version_id):
    launcher_file = get_minecraft_dir() / "launcher_profiles.json"

    if launcher_file.exists():
        data = json.loads(launcher_file.read_text(encoding="utf-8"))
    else:
        data = {"profiles": {}}

    profiles = data.setdefault("profiles", {})

    profile = {
        "name": name,
        "type": "custom",
        "created": now_iso(),
        "lastUsed": now_iso(),
        "lastVersionId": version_id,
        "gameDir": str(game_dir),
        "icon": ICON,
        "javaArgs": build_java_args()
    }

    profiles[name] = profile

    launcher_file.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )