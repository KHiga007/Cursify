"""Presets: combinaciones de cursores guardadas para usar (o aplicar) después.

Cada preset es una carpeta en ~/.config/cursify/presets/<nombre>/ con una
copia de cada archivo de cursor y un preset.json con los puntos activos, así
sigue funcionando aunque borres o muevas el pack original.
"""

import json
import os
import shutil
import tempfile

from formatos import cursave
from nucleo import roles
from nucleo.theme import safe_name

PRESETS_DIR = os.path.expanduser("~/.config/cursify/presets")
INFO = "preset.json"


def preset_dir(name):
    return os.path.join(PRESETS_DIR, safe_name(name))


def exists(name):
    return os.path.isfile(os.path.join(preset_dir(name), INFO))


def list_presets():
    if not os.path.isdir(PRESETS_DIR):
        return []
    found = []
    for entry in sorted(os.listdir(PRESETS_DIR), key=str.lower):
        info = os.path.join(PRESETS_DIR, entry, INFO)
        if not entry.startswith(".") and os.path.isfile(info):
            try:
                with open(info, encoding="utf-8") as fh:
                    data = json.load(fh)
                found.append((data.get("name", entry), len(data.get("roles", {}))))
            except (OSError, ValueError):
                continue
    return found


def save_preset(name, size, sources):
    """Guarda un preset. ``sources``: {clave_de_rol: theme.Source}."""
    name = safe_name(name)
    final = preset_dir(name)
    os.makedirs(PRESETS_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=f".{name}-", dir=PRESETS_DIR)
    try:
        data = {"name": name, "size": int(size), "roles": {}}
        for role in roles.ROLES:
            source = sources.get(role.key)
            if source is None:
                continue
            ext = os.path.splitext(source.path)[1].lower()
            if os.path.isfile(source.path):
                filename = role.key + ext
                shutil.copy2(source.path, os.path.join(tmp, filename))
            else:
                # El archivo original se borró o se movió: se guarda desde la memoria.
                written = cursave.write(os.path.join(tmp, role.key), source.frames)
                filename = os.path.basename(written)
            data["roles"][role.key] = {
                "file": filename,
                "original": source.path,
                "hotspot": list(source.hotspot) if source.hotspot is not None else None,
            }
        with open(os.path.join(tmp, INFO), "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
        if os.path.lexists(final):
            shutil.rmtree(final)
        os.rename(tmp, final)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return name


def load_preset(name):
    """Devuelve (nombre, tamaño, {rol: (ruta, hotspot o None)})."""
    folder = preset_dir(name)
    with open(os.path.join(folder, INFO), encoding="utf-8") as fh:
        data = json.load(fh)
    entries = {}
    for key, item in data.get("roles", {}).items():
        if key not in roles.ROLE_BY_KEY:
            continue
        hotspot = item.get("hotspot")
        entries[key] = (os.path.join(folder, item["file"]),
                        tuple(hotspot) if hotspot is not None else None)
    return data.get("name", name), int(data.get("size", 32)), entries


def delete_preset(name):
    folder = preset_dir(name)
    if os.path.isfile(os.path.join(folder, INFO)):
        shutil.rmtree(folder)


def list_presets_info():
    """Lista de dicts {name, count, size} de los presets guardados."""
    if not os.path.isdir(PRESETS_DIR):
        return []
    found = []
    for entry in sorted(os.listdir(PRESETS_DIR), key=str.lower):
        info = os.path.join(PRESETS_DIR, entry, INFO)
        if entry.startswith(".") or not os.path.isfile(info):
            continue
        try:
            with open(info, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        count = sum(1 for item in data.get("roles", {}).values() if item.get("file"))
        found.append({"name": data.get("name", entry), "count": count,
                      "size": int(data.get("size", 32))})
    return found
