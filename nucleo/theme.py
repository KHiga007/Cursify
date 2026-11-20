"""Carga de imágenes, armado del tema Xcursor y aplicación en el escritorio
(Cinnamon, MATE y Xfce: todas las ediciones de Linux Mint; también GNOME)."""

import json
import os
import re
import shutil
import subprocess
import tempfile

import gi

gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gio, GdkPixbuf, GLib  # noqa: E402

from formatos import wincursor, xcursor  # noqa: E402
from nucleo import roles  # noqa: E402
from nucleo.i18n import T  # noqa: E402

SIZES = (24, 32, 48, 64)
MARKER = ".cursify.json"
LEGACY_MARKERS = (".punterofacil.json",)   # temas creados cuando la app se llamaba PunteroFácil
ICONS_DIR = os.path.expanduser("~/.local/share/icons")
LEGACY_ICONS_DIR = os.path.expanduser("~/.icons")
STATE_FILE = os.path.expanduser("~/.config/cursify/state.json")
MAX_SOURCE = 256


# --------------------------------------------------------------------------
# Conversión entre Pixbuf y RGBA
# --------------------------------------------------------------------------

def pixbuf_to_rgba(pb):
    if not pb.get_has_alpha():
        pb = pb.add_alpha(False, 0, 0, 0)
    w, h, rs = pb.get_width(), pb.get_height(), pb.get_rowstride()
    pixels = pb.get_pixels()
    if rs == w * 4:
        return w, h, bytes(pixels[:w * h * 4])
    return w, h, b"".join(pixels[y * rs:y * rs + w * 4] for y in range(h))


def rgba_to_pixbuf(w, h, rgba):
    return GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes.new(rgba),
                                           GdkPixbuf.Colorspace.RGB, True, 8, w, h, w * 4)


def _png_decoder(data):
    loader = GdkPixbuf.PixbufLoader()
    loader.write(data)
    loader.close()
    return pixbuf_to_rgba(loader.get_pixbuf())


# --------------------------------------------------------------------------
# Fuente de un cursor (archivo elegido para una situación)
# --------------------------------------------------------------------------

def readable_name(name):
    """Arregla nombres japoneses que se rompen al descomprimir zips de Windows."""
    if all(ord(c) < 128 for c in name):
        return name
    for enc in ("cp850", "cp437"):
        try:
            fixed = name.encode(enc).decode("cp932", errors="replace")
        except UnicodeEncodeError:
            continue
        cjk = sum(1 for c in fixed if "぀" <= c <= "鿿")
        if cjk >= 3:
            return fixed.replace("�+", "").replace("�-", "").replace("�", "")
    return name


class Source:
    def __init__(self, path, frames):
        self.path = path
        self.frames = frames
        self.hotspot = None  # (x, y) elegido a mano, en píxeles del primer cuadro

    @property
    def name(self):
        return readable_name(os.path.basename(self.path))

    @property
    def animated(self):
        return len(self.frames) > 1

    def effective_frames(self):
        if self.hotspot is None:
            return self.frames
        base = self.frames[0]
        hx, hy = self.hotspot
        out = []
        for f in self.frames:
            x = min(hx * f.width // base.width, f.width - 1)
            y = min(hy * f.height // base.height, f.height - 1)
            out.append(f.copy(xhot=x, yhot=y))
        return out

    def snapshot(self):
        """Copia independiente (para armar el tema en otro hilo sin carreras)."""
        copy = Source(self.path, list(self.frames))
        copy.hotspot = tuple(self.hotspot) if self.hotspot is not None else None
        return copy

    def current_hotspot(self):
        if self.hotspot is not None:
            return self.hotspot
        f = self.frames[0]
        return f.xhot, f.yhot


# Situaciones donde el punto activo va en el centro del símbolo.
_CENTERED = {"busy", "precision", "text", "unavailable", "vertical", "horizontal",
             "diagonal1", "diagonal2", "move"}


def _symbol_box(frame):
    """Caja del símbolo más cercano a la esquina superior izquierda.

    Muchos packs dibujan un símbolo chico arriba a la izquierda y un personaje
    al lado, a veces pegados. Si la mancha encontrada es grande, se limita la
    búsqueda a la zona superior izquierda.
    """
    box = _flood_box(frame, frame.width, frame.height)
    if box is None:
        return None
    limit = max(8, round(0.4 * max(frame.width, frame.height)))
    if box[2] - box[0] >= limit or box[3] - box[1] >= limit:
        box = _flood_box(frame, limit, limit) or box
    return box


def _flood_box(frame, max_w, max_h):
    w, h, px = frame.width, frame.height, frame.rgba
    max_w, max_h = min(w, max_w), min(h, max_h)
    opaque = [px[i * 4 + 3] > 64 for i in range(w * h)]
    start = None
    for s in range(max_w + max_h - 1):  # recorre diagonales desde (0, 0)
        for x in range(max(0, s - max_h + 1), min(s, max_w - 1) + 1):
            if opaque[(s - x) * w + x]:
                start = (x, s - x)
                break
        if start:
            break
    if start is None:
        return None
    seen = {start}
    stack = [start]
    x0 = x1 = start[0]
    y0 = y1 = start[1]
    while stack:
        x, y = stack.pop()
        x0, x1, y0, y1 = min(x0, x), max(x1, x), min(y0, y), max(y1, y)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if (0 <= nx < max_w and 0 <= ny < max_h and (nx, ny) not in seen
                        and opaque[ny * w + nx]):
                    seen.add((nx, ny))
                    stack.append((nx, ny))
    return x0, y0, x1, y1


def suggest_hotspot(source, role_key):
    """Si el archivo trae el punto activo en (0,0), propone uno según la situación."""
    first = source.frames[0]
    if (first.xhot, first.yhot) != (0, 0) or source.hotspot is not None:
        return False
    if role_key not in _CENTERED and role_key != "alternate":
        return False
    box = _symbol_box(first)
    if box is None:
        return False
    x0, y0, x1, y1 = box
    if role_key == "alternate":
        source.hotspot = ((x0 + x1) // 2, y0)
    else:
        source.hotspot = ((x0 + x1) // 2, (y0 + y1) // 2)
    return source.hotspot != (0, 0)


def load_source(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".cur", ".ico", ".ani"):
        frames = wincursor.load(path, _png_decoder)
    else:
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file(path)
        except GLib.Error as exc:
            raise wincursor.CursorError(exc.message) from exc
        w, h = pb.get_width(), pb.get_height()
        if max(w, h) > MAX_SOURCE:
            f = MAX_SOURCE / max(w, h)
            pb = pb.scale_simple(max(1, round(w * f)), max(1, round(h * f)),
                                 GdkPixbuf.InterpType.HYPER)
        w, h, rgba = pixbuf_to_rgba(pb)
        frames = [wincursor.Frame(w, h, rgba, 0, 0, 0)]
    return Source(path, frames)


# --------------------------------------------------------------------------
# Escalado
# --------------------------------------------------------------------------

def scale_frame(frame, factor):
    if abs(factor - 1.0) < 1e-6:
        return frame
    nw = max(1, round(frame.width * factor))
    nh = max(1, round(frame.height * factor))
    if factor >= 2 and abs(factor - round(factor)) < 1e-6:
        interp = GdkPixbuf.InterpType.NEAREST       # aumento exacto: nítido
    elif factor < 1:
        interp = GdkPixbuf.InterpType.HYPER         # reducción: mejor calidad
    else:
        interp = GdkPixbuf.InterpType.BILINEAR
    pb = rgba_to_pixbuf(frame.width, frame.height, frame.rgba).scale_simple(nw, nh, interp)
    _, _, rgba = pixbuf_to_rgba(pb)
    return wincursor.Frame(nw, nh, rgba,
                           min(int(frame.xhot * factor), nw - 1),
                           min(int(frame.yhot * factor), nh - 1),
                           frame.delay)


def frame_for_size(frame, base, target):
    """Cuadro escalado para que ``base`` (tamaño original) pase a ``target``."""
    return scale_frame(frame, target / base)


# --------------------------------------------------------------------------
# Tema
# --------------------------------------------------------------------------

def safe_name(name):
    name = re.sub(r"\s+", "-", name.strip())
    name = re.sub(r"[^\w.\-]", "", name)
    return name.strip(".-") or "MiCursor"


def theme_dir(name):
    return os.path.join(ICONS_DIR, safe_name(name))


def _marker_path(path):
    for name in (MARKER,) + LEGACY_MARKERS:
        candidate = os.path.join(path, name)
        if os.path.isfile(candidate):
            return candidate
    return None


def is_ours(path):
    return _marker_path(path) is not None


def theme_exists_foreign(name):
    for root in (ICONS_DIR, LEGACY_ICONS_DIR):
        path = os.path.join(root, safe_name(name))
        if os.path.lexists(path) and not os.path.islink(path) and not is_ours(path):
            return True
    return False


def build_theme(name, assignments, inherits="Adwaita", progress=None):
    """Crea el tema en ~/.local/share/icons/<nombre>. Devuelve la ruta."""
    name = safe_name(name)
    final = theme_dir(name)
    if theme_exists_foreign(name):
        raise FileExistsError(T("Ya existe un tema «{name}» que no fue creado con esta app.", name=name))
    os.makedirs(ICONS_DIR, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=f".{name}-", dir=ICONS_DIR)
    try:
        cursors = os.path.join(tmp, "cursors")
        os.makedirs(cursors)
        written = set()
        total = sum(1 for r in roles.ROLES if r.key in assignments)
        done = 0
        for role in roles.ROLES:
            source = assignments.get(role.key)
            if source is None:
                continue
            frames = source.effective_frames()
            base = max(frames[0].width, frames[0].height)
            images = []
            for target in SIZES:
                for f in frames:
                    sf = frame_for_size(f, base, target)
                    images.append((target, sf.width, sf.height, sf.xhot, sf.yhot,
                                   f.delay, sf.rgba))
            primary = role.xnames[0]
            xcursor.write(os.path.join(cursors, primary), images)
            written.add(primary)
            for alias in role.xnames[1:]:
                if alias not in written:
                    os.symlink(primary, os.path.join(cursors, alias))
                    written.add(alias)
            done += 1
            if progress:
                progress(done, total)

        index = (f"[Icon Theme]\nName={name}\nComment=Creado con Cursify\n"
                 f"Inherits={inherits}\n")
        for fname in ("index.theme", "cursor.theme"):
            with open(os.path.join(tmp, fname), "w", encoding="utf-8") as fh:
                fh.write(index)
        with open(os.path.join(tmp, MARKER), "w", encoding="utf-8") as fh:
            json.dump({"name": name, "inherits": inherits,
                       "roles": {k: s.path for k, s in assignments.items()}},
                      fh, ensure_ascii=False, indent=2)
        os.chmod(tmp, 0o755)

        if os.path.islink(final):
            os.unlink(final)            # la carpeta del tema era un enlace: se reemplaza el enlace
        elif os.path.lexists(final):
            shutil.rmtree(final)
        os.rename(tmp, final)
    except BaseException:
        shutil.rmtree(tmp, ignore_errors=True)
        raise

    # Enlace en ~/.icons para programas viejos que solo buscan ahí.
    legacy = os.path.join(LEGACY_ICONS_DIR, name)
    if not os.path.lexists(legacy):
        os.makedirs(LEGACY_ICONS_DIR, exist_ok=True)
        os.symlink(final, legacy)
    return final


def list_own_themes():
    if not os.path.isdir(ICONS_DIR):
        return []
    return sorted(n for n in os.listdir(ICONS_DIR)
                  if not n.startswith(".") and is_ours(os.path.join(ICONS_DIR, n)))


def delete_theme(name):
    path = theme_dir(name)
    if not is_ours(path):  # is_ours sigue el enlace si la carpeta es un enlace
        raise PermissionError(T("Solo se pueden borrar temas creados con esta app."))
    shutil.rmtree(path)
    legacy = os.path.join(LEGACY_ICONS_DIR, safe_name(name))
    if os.path.islink(legacy) and os.path.realpath(legacy) == os.path.realpath(path):
        os.unlink(legacy)


# --------------------------------------------------------------------------
# Configuración del escritorio
# --------------------------------------------------------------------------

_SCHEMAS = ("org.cinnamon.desktop.interface", "org.gnome.desktop.interface",
            "org.mate.peripherals-mouse")


def _desktop():
    """Escritorio de la sesión actual, en minúsculas (p. ej. «x-cinnamon», «mate», «xfce»)."""
    return (os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "").lower()


def _schemas_in_order():
    """Los esquemas, empezando por el del escritorio actual (es el que manda al leer)."""
    desktop = _desktop()
    first = None
    if "cinnamon" in desktop:
        first = "org.cinnamon.desktop.interface"
    elif "mate" in desktop:
        first = "org.mate.peripherals-mouse"
    elif "gnome" in desktop or "unity" in desktop or "budgie" in desktop:
        first = "org.gnome.desktop.interface"
    return ((first,) if first else ()) + tuple(s for s in _SCHEMAS if s != first)


def _settings_list():
    source = Gio.SettingsSchemaSource.get_default()
    found = []
    for schema_id in _schemas_in_order():
        schema = source.lookup(schema_id, True) if source else None
        if schema is None:
            continue
        theme_key = "cursor-theme" if schema.has_key("cursor-theme") else None
        size_key = "cursor-size" if schema.has_key("cursor-size") else None
        if theme_key:
            found.append((Gio.Settings.new(schema_id), theme_key, size_key))
    return found


# Xfce (Linux Mint Xfce) guarda el cursor en xfconf, no en gsettings.
_XFCONF_THEME = "/Gtk/CursorThemeName"
_XFCONF_SIZE = "/Gtk/CursorThemeSize"


def _xfconf(*args):
    """Corre xfconf-query sobre el canal xsettings. Devuelve la salida, o None si falla."""
    exe = shutil.which("xfconf-query")
    if not exe:
        return None
    try:
        done = subprocess.run([exe, "-c", "xsettings", *args], capture_output=True,
                              text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def _xfce_current():
    theme = _xfconf("-p", _XFCONF_THEME)
    if not theme:
        return None
    size = _xfconf("-p", _XFCONF_SIZE)
    return theme, int(size) if size and size.isdigit() and int(size) > 0 else 24


def _xfce_set(theme, size):
    # -n crea la propiedad si todavía no existe (Xfce recién instalado).
    if _xfconf("-p", _XFCONF_THEME, "-s", theme) is None:
        _xfconf("-p", _XFCONF_THEME, "-n", "-t", "string", "-s", theme)
    if size:
        if _xfconf("-p", _XFCONF_SIZE, "-s", str(int(size))) is None:
            _xfconf("-p", _XFCONF_SIZE, "-n", "-t", "int", "-s", str(int(size)))


def current_cursor():
    if "xfce" in _desktop():
        found = _xfce_current()
        if found:
            return found
    for settings, theme_key, size_key in _settings_list():
        size = settings.get_int(size_key) if size_key else 24
        return settings.get_string(theme_key), size
    return "", 24


def _load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)


def previous_cursor():
    """Tema que había antes de usar la app (para heredar y para restaurar)."""
    state = _load_state()
    if state.get("previous_theme"):
        return state["previous_theme"], state.get("previous_size", 24)
    theme, size = current_cursor()
    if theme and not is_ours(theme_dir(theme)):
        return theme, size
    return "Adwaita", 24


def _set_cursor(theme, size):
    for settings, theme_key, size_key in _settings_list():
        settings.set_string(theme_key, theme)
        if size_key and size:
            settings.set_int(size_key, int(size))
    Gio.Settings.sync()
    if shutil.which("xfconf-query"):
        _xfce_set(theme, size)


def apply_theme(name, size):
    name = safe_name(name)
    current, current_size = current_cursor()
    state = _load_state()
    # El «anterior» es el último cursor que no fue creado con la app: si lo cambiaste a mano
    # en Configuración, se actualiza la próxima vez que apliques.
    if current and not is_ours(theme_dir(current)):
        state["previous_theme"] = current
        state["previous_size"] = current_size
        _save_state(state)
    _set_cursor(name, size)


def restore_previous():
    state = _load_state()
    theme = state.get("previous_theme")
    if not theme:
        return None
    _set_cursor(theme, state.get("previous_size", 24))
    return theme


def has_previous():
    """True si hay un cursor anterior guardado para poder restaurarlo."""
    return bool(_load_state().get("previous_theme"))


def set_cursor(theme_name, size):
    """Activa un tema de cursor y su tamaño en Cinnamon, MATE, Xfce y GNOME."""
    _set_cursor(theme_name, size)


def theme_inherits(name):
    """Primer tema de la línea Inherits= de un tema creado con la app."""
    try:
        with open(os.path.join(theme_dir(name), "index.theme"), encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("Inherits="):
                    value = line.split("=", 1)[1].split(",")[0].strip()
                    return value or None
    except OSError:
        pass
    return None


def list_own_themes_info():
    """Temas creados con la app: lista de dicts {name, count, mtime}."""
    found = []
    for name in list_own_themes():
        path = os.path.join(ICONS_DIR, name)
        count = 0
        try:
            with open(_marker_path(path) or os.path.join(path, MARKER), encoding="utf-8") as fh:
                count = len(json.load(fh).get("roles", {}))
        except (OSError, ValueError):
            pass
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            mtime = 0
        found.append({"name": name, "count": count, "mtime": mtime})
    return found


# --------------------------------------------------------------------------
# Cursor del sistema (para las tarjetas vacías)
# --------------------------------------------------------------------------

_ICON_ROOTS = (ICONS_DIR, LEGACY_ICONS_DIR, "/usr/share/icons", "/usr/local/share/icons")


def _find_theme_dir(name):
    for root in _ICON_ROOTS:
        path = os.path.join(root, name)
        if os.path.isdir(path):
            return path
    return None


def _inherits_of(theme_path):
    for fname in ("index.theme", "cursor.theme"):
        try:
            with open(os.path.join(theme_path, fname), encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("Inherits="):
                        return [v.strip() for v in line.split("=", 1)[1].split(",") if v.strip()]
        except OSError:
            continue
    return []


def system_cursor_image(xname, size=40):
    """Imagen (ancho, alto, rgba) del cursor ``xname`` en el tema que usa el sistema cuando
    una situación queda vacía: el cursor anterior (no el tema creado con la app)."""
    base, _ = previous_cursor()
    queue, seen = [base, "default", "Adwaita", "DMZ-White"], set()
    while queue:
        name = queue.pop(0)
        if not name or name in seen:
            continue
        seen.add(name)
        path = _find_theme_dir(name)
        if path is None:
            continue
        cursor = os.path.join(path, "cursors", xname)
        if os.path.exists(cursor):
            try:
                found = xcursor.read_image(cursor, size)
            except (OSError, ValueError):
                found = None
            if found:
                return found
        queue[0:0] = _inherits_of(path)
    return None
