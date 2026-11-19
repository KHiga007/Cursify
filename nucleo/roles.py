"""Situaciones del cursor (como en Windows) y su equivalencia en Linux.

También adivina qué archivo corresponde a cada situación a partir de una
carpeta: primero con el install.inf del pack, después por nombre de archivo y,
por último, por el número de orden de Windows (01 = Normal, 02 = Ayuda, ...).
"""

import os
import re
import unicodedata

SUPPORTED_EXT = (".ani", ".cur", ".ico", ".png", ".svg")


class Role:
    def __init__(self, key, label, hint, win_name, xnames, keywords, tokens=()):
        self.key = key
        self.label = label          # nombre que ve el usuario
        self.hint = hint            # cuándo aparece
        self.win_name = win_name    # nombre en el registro de Windows
        self.xnames = xnames        # nombres Xcursor (el primero es el archivo real)
        self.keywords = keywords    # subcadenas que lo identifican en un nombre
        self.tokens = tokens        # palabras sueltas cortas


# Orden idéntico al de Windows (Panel de control > Mouse > Punteros).
ROLES = [
    Role("normal", "Selección normal", "La flecha de siempre", "Arrow",
         ["left_ptr", "default", "arrow", "top_left_arrow", "left_arrow",
          "context-menu", "copy", "dnd-copy", "dnd-none", "dnd-ask", "zoom-in", "zoom-out",
          "right_ptr"],
         ["arrow", "normal", "default", "通常"], ("ptr",)),
    Role("help", "Selección de ayuda", "Flecha con signo de pregunta", "Help",
         ["help", "question_arrow", "whats_this", "left_ptr_help",
          "5c6cd98b3f3ebcb1f9c7f1c204630408", "d9ce0ab605698f320427677b458ad60b"],
         ["help", "ayuda", "question", "pregunta", "ヘルプ"]),
    Role("working", "Trabajando en segundo plano", "Flecha con reloj: cargando", "AppStarting",
         ["left_ptr_watch", "progress", "half-busy",
          "3ecb610c1bf2410f44200f48c40d3599", "00000000000000020006000e7e9ffc3f",
          "08e8e1c95fe2fc01f976f1e063a24ccd"],
         ["working", "appstarting", "background", "segundo", "progress", "progreso",
          "cargando", "バックグラウンド"]),
    Role("busy", "Ocupado", "Reloj de espera", "Wait",
         ["watch", "wait"],
         ["busy", "wait", "ocupado", "espera", "hourglass", "待ち"]),
    Role("precision", "Selección de precisión", "Cruz para apuntar", "Crosshair",
         ["crosshair", "cross", "tcross", "cross_reverse", "diamond_cross", "cell", "plus"],
         ["precision", "precisión", "cross", "cruz", "領域"]),
    Role("text", "Selección de texto", "La barrita para escribir", "IBeam",
         ["xterm", "text", "ibeam", "vertical-text"],
         ["text", "texto", "ibeam", "beam", "テキスト"]),
    Role("handwriting", "Escritura a mano", "Lápiz", "NWPen",
         ["pencil", "draft"],
         ["handwriting", "escritura", "pencil", "lapiz", "lápiz", "手書き"], ("pen",)),
    Role("unavailable", "No disponible", "Prohibido", "No",
         ["not-allowed", "no-drop", "forbidden", "circle", "crossed_circle", "dnd-no-drop",
          "pirate", "X_cursor", "03b6e0fcb3499374a867c041f52298f0"],
         ["unavailable", "unavail", "disponible", "forbidden", "prohibido", "not-allowed",
          "notallowed", "利用不可"], ("no",)),
    Role("vertical", "Cambiar tamaño vertical", "Flecha ↕", "SizeNS",
         ["ns-resize", "size_ver", "v_double_arrow", "sb_v_double_arrow", "n-resize",
          "s-resize", "top_side", "bottom_side", "row-resize", "split_v",
          "00008160000006810000408080010102", "2870a09082c103050810ffdffffe0204"],
         ["vertical", "sizens", "上下"], ("ns", "vert")),
    Role("horizontal", "Cambiar tamaño horizontal", "Flecha ↔", "SizeWE",
         ["ew-resize", "size_hor", "h_double_arrow", "sb_h_double_arrow", "e-resize",
          "w-resize", "left_side", "right_side", "col-resize", "split_h",
          "028006030e0e7ebffc7f7070c0600140", "14fef782d02440884392942c11205230"],
         ["horizontal", "sizewe", "左右"], ("ew", "horz", "hor")),
    Role("diagonal1", "Cambiar tamaño en diagonal 1", "Flecha ↖↘", "SizeNWSE",
         ["nwse-resize", "size_fdiag", "fd_double_arrow", "nw-resize", "se-resize",
          "top_left_corner", "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000"],
         ["nwse", "fdiag"]),
    Role("diagonal2", "Cambiar tamaño en diagonal 2", "Flecha ↗↙", "SizeNESW",
         ["nesw-resize", "size_bdiag", "bd_double_arrow", "ne-resize", "sw-resize",
          "top_right_corner", "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000"],
         ["nesw", "bdiag"]),
    Role("move", "Mover", "Cruz con flechas", "SizeAll",
         ["fleur", "move", "all-scroll", "size_all", "dnd-move", "all-resize",
          "4498f0e0c1937ffe01fd06f973665830", "9081237383d90e509aa00f00170e968f"],
         ["move", "mover", "sizeall", "fleur", "移動"]),
    Role("alternate", "Selección alternativa", "Flecha hacia arriba", "UpArrow",
         ["up_arrow", "center_ptr", "sb_up_arrow"],
         ["alternate", "alternativ", "uparrow", "代替"], ("up",)),
    Role("link", "Selección de vínculo", "La manito de los enlaces", "Hand",
         ["pointer", "hand", "hand1", "hand2", "pointing_hand", "grab", "openhand",
          "grabbing", "closedhand", "fist", "link", "alias", "dnd-link",
          "e29285e634086352946a0e7090d73106", "9d800788f1b08800ae810202380a0822",
          "3085a0e285430894940527032f8b26df", "640fb0e74195791501fd1ed57b41487f",
          "a2a266d0498c3104214a47bd64ab0fc8"],
         ["link", "enlace", "vinculo", "vínculo", "hand", "mano", "pointing", "リンク"]),
]

ROLE_BY_KEY = {r.key: r for r in ROLES}
ROLE_BY_WIN = {r.win_name.lower(): r for r in ROLES}

# Orden de prueba por nombre: lo más específico primero, "normal" al final
# (porque "uparrow" contiene "arrow").
_MATCH_ORDER = ["help", "working", "busy", "precision", "text", "handwriting",
                "unavailable", "vertical", "horizontal", "move", "alternate", "link",
                "normal"]


def _normalize(name):
    name = unicodedata.normalize("NFKC", name).lower()
    base = os.path.splitext(name)[0]
    tokens = [t for t in re.split(r"[^0-9a-záéíóúñ぀-ヿ一-鿿]+", base) if t]
    return base, tokens


def guess_role_by_name(filename):
    base, tokens = _normalize(filename)
    # Diagonales: deciden entre 1 y 2.
    if any(k in base for k in ("diag", "dgn", "nwse", "nesw", "斜め")):
        if any(k in base for k in ("nesw", "bdiag")):
            return "diagonal2"
        if any(k in base for k in ("nwse", "fdiag")):
            return "diagonal1"
        tail = re.findall(r"(?:diag\w*|dgn|斜め\w*)\D*([12])", base)
        if tail:
            return "diagonal1" if tail[0] == "1" else "diagonal2"
    for key in _MATCH_ORDER:
        role = ROLE_BY_KEY[key]
        if any(_keyword_matches(k, base, tokens) for k in role.keywords):
            return key
        if any(t in tokens for t in role.tokens):
            return key
    return None


def _keyword_matches(keyword, base, tokens):
    """Palabras simples: tienen que empezar una palabra del nombre («helpsel» sí, pero
    «context» no cuenta como «text» ni «remove» como «move»). Palabras con guiones o en
    japonés: alcanza con que aparezcan en el nombre."""
    if not keyword.isascii() or not keyword.isalpha():
        return keyword in base
    return any(t.startswith(keyword) for t in tokens)


def guess_role_by_number(filename):
    base, _ = _normalize(filename)
    for match in re.finditer(r"(?<!\d)(\d{1,2})(?!\d)", base):
        n = int(match.group(1))
        if 1 <= n <= len(ROLES):
            return ROLES[n - 1].key
    return None


# --------------------------------------------------------------------------
# install.inf de Windows
# --------------------------------------------------------------------------

def _read_text(path):
    raw = open(path, "rb").read()
    for enc in ("utf-8-sig", "utf-16", "cp932", "latin-1"):
        try:
            text = raw.decode(enc)
            if "\x00" not in text:
                return text
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", "replace")


def parse_inf(inf_path, files):
    """Asignaciones a partir de un install.inf. ``files``: rutas disponibles."""
    text = _read_text(inf_path)
    strings = {}
    section = ""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and "]" in line:
            section = line[1:line.index("]")].strip().lower()
            continue
        lines.append((section, line))
        if section == "strings" and "=" in line:
            k, v = line.split("=", 1)
            strings[k.strip().lower()] = v.strip().strip('"')

    def expand(value):
        return re.sub(r"%([^%]+)%", lambda m: strings.get(m.group(1).lower(), ""), value)

    by_name = {os.path.basename(f).lower(): f for f in files}

    def find(entry):
        name = expand(entry).replace("/", "\\").split("\\")[-1].strip().strip('"').lower()
        return by_name.get(name)

    result = {}
    for _section, line in lines:
        low = line.lower()
        if "cursors\\schemes" in low:
            quoted = re.findall(r'"([^"]*)"', line)
            if quoted:
                items = expand(quoted[-1]).split(",")
                if len(items) >= 2:
                    for role, item in zip(ROLES, items):
                        path = find(item)
                        if path:
                            result[role.key] = path
        elif "control panel\\cursors" in low:
            parts = [p.strip().strip('"') for p in line.split(",")]
            if len(parts) >= 5:
                role = ROLE_BY_WIN.get(parts[2].lower())
                path = find(parts[-1])
                if role and path and role.key not in result:
                    result[role.key] = path
    return result


# --------------------------------------------------------------------------
# Asignación automática de una carpeta
# --------------------------------------------------------------------------

def _cursor_files(folder):
    found = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.isfile(path) and name.lower().endswith(SUPPORTED_EXT):
            found.append(path)
    return found


def collect_files(folder, depth=2):
    """Archivos de cursor de la carpeta; si no hay, busca en subcarpetas."""
    files = _cursor_files(folder)
    if files or depth == 0:
        return files, folder
    for name in sorted(os.listdir(folder)):
        sub = os.path.join(folder, name)
        if os.path.isdir(sub) and not name.startswith("."):
            files, where = collect_files(sub, depth - 1)
            if files:
                return files, where
    return [], folder


def auto_assign(folder):
    """Devuelve (asignaciones {rol: ruta}, archivos sin asignar, carpeta usada)."""
    files, where = collect_files(folder)
    result = {}

    for name in sorted(os.listdir(where)):
        if name.lower().endswith(".inf"):
            try:
                result.update(parse_inf(os.path.join(where, name), files))
            except OSError:
                pass

    used = set(result.values())
    # 1) por nombre
    for path in files:
        if path in used:
            continue
        key = guess_role_by_name(os.path.basename(path))
        if key and key not in result:
            result[key] = path
            used.add(path)
    # 2) por número de orden de Windows
    for path in files:
        if path in used:
            continue
        key = guess_role_by_number(os.path.basename(path))
        if key and key not in result:
            result[key] = path
            used.add(path)

    leftovers = [p for p in files if p not in used]
    return result, leftovers, where
