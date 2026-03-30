from pathlib import Path

from .detect import has_any_shader
from .install import install_shader

from logger import shader, success

def ensure_shaders_installed(shaders_dir, shader_url, file_name=None):
    shaders_path = Path(shaders_dir)
    shaders_path.mkdir(parents=True, exist_ok=True)

    shader(f"Checking shaders folder...")

    if has_any_shader(shaders_path):
        shader("Shader already present, skip.")
        success("Configuration des shaderpacks terminée !")
        return None

    shader("No shader found, install Complementary Unbound...")
    installed_file = install_shader(shaders_path, shader_url, file_name)
    success("Configuration des shaderpacks terminée !")

    return installed_file
