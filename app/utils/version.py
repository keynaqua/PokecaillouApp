import re


def parse_java_major(version_output: str):
    match = re.search(r'version "([^"]+)"', version_output)
    if not match:
        return None

    raw = match.group(1)

    if raw.startswith("1."):
        parts = raw.split(".")
        if len(parts) > 1 and parts[1].isdigit():
            return int(parts[1])
        return None

    major = raw.split(".", 1)[0]
    return int(major) if major.isdigit() else None