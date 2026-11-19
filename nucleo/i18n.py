"""Idioma de la interfaz: español o inglés.

Por defecto sigue el idioma del sistema (si es español, español; si no, inglés).
Se puede forzar desde Ajustes; la elección se guarda en
~/.config/cursify/settings.json.

Los textos se escriben en español en el código y ``T()`` los traduce al inglés
cuando corresponde. Los marcadores {nombre} se completan con ``T(texto, nombre=...)``.
"""

import json
import os

SETTINGS_FILE = os.path.expanduser("~/.config/cursify/settings.json")
CHOICES = ("auto", "es", "en")

EN = {
    # Generales
    "Armá y aplicá tu tema de cursores": "Build and apply your cursor theme",
    "Presets": "Presets",
    "Aplicar cursor": "Apply cursor",
    "Más opciones": "More options",
    "Tus combinaciones de cursores guardadas": "Your saved cursor combinations",
    "<b>{n}</b> de {total} asignados": "<b>{n}</b> of {total} assigned",
    "Asigná al menos un cursor para aplicar": "Assign at least one cursor to apply",
    "Cancelar": "Cancel",
    "Cerrar": "Close",
    # Panel
    "Abrir carpeta de cursores…": "Open cursor folder…",
    "Abrir carpeta o arrastrala acá": "Open folder or drag it here",
    "Abrir otra carpeta…": "Open another folder…",
    "También podés arrastrarla a la ventana": "You can also drag it onto the window",
    "Elegí la carpeta de un pack (.ani/.cur) y se ordena solo":
        "Pick a pack folder (.ani/.cur) and it sorts itself",
    "Nombre del tema": "Theme name",
    "Pack de cursores": "Cursor pack",
    "Ej.: Botan": "e.g. Botan",
    "Tamaño": "Size",
    "Pequeño (24 px)": "Small (24 px)",
    "Normal (32 px)": "Normal (32 px)",
    "Grande (48 px)": "Large (48 px)",
    "Muy grande (64 px)": "Extra large (64 px)",
    "Soltá acá la carpeta de tu pack de cursores y se asignan solos":
        "Drop your cursor pack folder here and they're assigned automatically",
    "Hacé clic para elegir la carpeta, o soltala acá": "Click to choose the folder, or drop it here",
    "Hacé clic para elegir la carpeta del pack, o arrastrala y soltala sobre la ventana: los cursores se asignan solos":
        "Click to choose the pack folder, or drag and drop it onto the window: cursors are assigned automatically",
    # Secciones
    "Esenciales": "Essentials",
    "Los que más vas a ver": "The ones you'll see the most",
    "Precisión y edición": "Precision and editing",
    "Apuntar, dibujar y bloquear": "Aim, draw and block",
    "Mover y redimensionar": "Move and resize",
    "Bordes y esquinas de ventanas": "Window edges and corners",
    # Situaciones (roles.py)
    "Selección normal": "Normal select",
    "La flecha de siempre": "The usual arrow",
    "Selección de ayuda": "Help select",
    "Flecha con signo de pregunta": "Arrow with a question mark",
    "Trabajando en segundo plano": "Working in background",
    "Flecha con reloj: cargando": "Arrow with a clock: loading",
    "Ocupado": "Busy",
    "Reloj de espera": "Wait clock",
    "Selección de precisión": "Precision select",
    "Cruz para apuntar": "Crosshair for aiming",
    "Selección de texto": "Text select",
    "La barrita para escribir": "The text bar",
    "Escritura a mano": "Handwriting",
    "Lápiz": "Pen",
    "No disponible": "Unavailable",
    "Prohibido": "Not allowed",
    "Cambiar tamaño vertical": "Vertical resize",
    "Flecha ↕": "Arrow ↕",
    "Cambiar tamaño horizontal": "Horizontal resize",
    "Flecha ↔": "Arrow ↔",
    "Cambiar tamaño en diagonal 1": "Diagonal resize 1",
    "Flecha ↖↘": "Arrow ↖↘",
    "Cambiar tamaño en diagonal 2": "Diagonal resize 2",
    "Flecha ↗↙": "Arrow ↗↙",
    "Mover": "Move",
    "Cruz con flechas": "Cross with arrows",
    "Selección alternativa": "Alternate select",
    "Flecha hacia arriba": "Up arrow",
    "Selección de vínculo": "Link select",
    "La manito de los enlaces": "The link hand",
    # Cerrar
    "¿Cerrar sin guardar?": "Close without saving?",
    "Tenés cambios que no aplicaste ni guardaste como preset. Si cerrás ahora, se pierden.":
        "You have changes you haven't applied or saved as a preset. If you close now, they'll be lost.",
    "Cerrar sin guardar": "Close without saving",
    "Guardar preset…": "Save preset…",
    "Cambios sin guardar": "Unsaved changes",
    "Tenés cambios sin guardar": "You have unsaved changes",
    "No salir": "Don't quit",
    "Seguir editando": "Keep editing",
    "¿Qué querés hacer antes de salir?": "What do you want to do before quitting?",
    "Salir sin guardar": "Quit without saving",
    "Se pierden los cambios que hiciste.": "The changes you made are lost.",
    "Guardar antes de salir": "Save before quitting",
    "Elegís un nombre y listo.": "Pick a name and you're done.",
    "Elegido": "Chosen",
    "Ponele un nombre": "Give it a name",
    "Así lo encontrás después en <b>Presets</b> y lo podés volver a usar con un clic.":
        "You'll find it later in <b>Presets</b> and can use it again with one click.",
    "Nombre": "Name",
    "Se guardan estos cursores:": "These cursors are saved:",
    "Guardar y salir": "Save and quit",
    "Reemplazar y salir": "Replace and quit",
    "La app se cierra después de guardar": "The app closes after saving",
    "Ya usaste el nombre «{name}». Si seguís, se reemplaza el guardado anterior.":
        "You already used the name “{name}”. If you continue, the previous save is replaced.",
    "Ponele un nombre para encontrarlo después en Presets.": "Give it a name so you can find it later in Presets.",
    "Así van a quedar ({size} px)": "This is how they'll look ({size} px)",
    "{role} (cursor del sistema)": "{role} (system cursor)",
    "Del sistema": "From the system",
    "Guardar y cerrar": "Save and close",
    "Reemplazar y cerrar": "Replace and close",
    "Nombre del preset": "Preset name",
    "CURSORES QUE SE GUARDAN": "CURSORS BEING SAVED",
    "Cambiados desde la última vez": "Changed since last time",
    "Ya existe un preset «{name}». Si seguís, se reemplaza por esta combinación.":
        "A preset called “{name}” already exists. If you continue, it's replaced with this combination.",
    "Cursores cambiados": "Changed cursors",
    "{n} de {total}": "{n} of {total}",
    "Sin nombre": "No name",
    "Preset": "Preset",
    "Si cerrás ahora, se pierde lo que no aplicaste ni guardaste como preset.":
        "If you close now, anything you haven't applied or saved as a preset is lost.",
    "{n} de {total} cursores": "{n} of {total} cursors",
    "Tema «{name}»": "Theme “{name}”",
    "Preset «{name}» con cambios": "Preset “{name}” with changes",
    # Tarjetas
    "Punto sugerido": "Suggested hotspot",
    "La app calculó el punto activo: revisalo con «Ajustar punto activo»":
        "The app calculated the hotspot: check it with “Adjust hotspot”",
    "Se quitó «{role}»": "Removed “{role}”",
    "Deshacer": "Undo",
    "Preset «{name}» con cambios sin guardar": "Preset “{name}” has unsaved changes",
    "Preset «{name}» cargado": "Preset “{name}” loaded",
    " · con cambios sin guardar": " · unsaved changes",
    "¿Reemplazar los cursores?": "Replace the cursors?",
    "Se van a reemplazar los {n} cursores asignados por los de la carpeta «{folder}».":
        "The {n} assigned cursors will be replaced with the ones in the folder “{folder}”.",
    "No se pudieron leer: {files}.": "Couldn't read: {files}.",
    "Ya existe un tema «{name}» que no fue creado con esta app.":
        "A theme called “{name}” already exists and wasn't created with this app.",
    "Solo se pueden borrar temas creados con esta app.": "Only themes created with this app can be deleted.",
    "Soltá para asignar": "Drop to assign",
    "● Probando en vivo": "● Live preview",
    "Clic para mover · Esc para terminar": "Click to move · Esc to finish",
    "Elegir archivo…": "Choose file…",
    "Cambiar…": "Change…",
    "Ajustar punto activo": "Adjust hotspot",
    "Sugerido": "Suggested",
    "Vuelve al punto activo original o sugerido": "Goes back to the original or suggested hotspot",
    "Listo": "Done",
    "x {x} · y {y}": "x {x} · y {y}",
    "{fmt} · {n} cuadros": "{fmt} · {n} frames",
    "Usa el del sistema": "Uses the system one",
    "Pasá el mouse para probarlo.\nHacé clic para mover el punto activo (la cruz roja).":
        "Hover to try it.\nClick to move the hotspot (the red cross).",
    "Elegir…": "Choose…",
    "Elegir": "Choose",
    "Restablecer punto activo": "Reset hotspot",
    "Quitar cursor": "Remove cursor",
    "Sin asignar": "Not assigned",
    " · animado": " · animated",
    " · punto sugerido": " · suggested hotspot",
    "No se pudo abrir «{name}»: {error}": "Couldn't open “{name}”: {error}",
    "Elegir cursor: {role}": "Choose cursor: {role}",
    "Cursores e imágenes (.ani, .cur, .ico, .png, .svg)": "Cursors and images (.ani, .cur, .ico, .png, .svg)",
    # Importar
    "Se asignaron {n} archivo(s). No supe dónde va: {files}. Arrastralos al cuadro que corresponde.":
        "{n} file(s) assigned. Couldn't tell where these go: {files}. Drag them onto the right card.",
    "Se asignaron {n} archivo(s)": "{n} file(s) assigned",
    "No se pudo leer la carpeta: {error}": "Couldn't read the folder: {error}",
    "En esa carpeta no hay archivos de cursor (.ani, .cur, .ico, .png, .svg).":
        "That folder has no cursor files (.ani, .cur, .ico, .png, .svg).",
    "Sin archivo (usarán los del sistema): {roles}.": "No file (they'll use the system ones): {roles}.",
    "Archivos sin ubicar: {files}. Podés arrastrarlos a un cuadro.":
        "Unplaced files: {files}. You can drag them onto a card.",
    "Algunos puntos activos (cruz roja) son sugeridos: revisalos.":
        "Some hotspots (red cross) are suggestions: check them.",
    "Se ordenaron {n} de {total} cursores.": "Sorted {n} of {total} cursors.",
    "Se ordenaron {n} de {total} cursores": "Sorted {n} of {total} cursors",
    "Elegí la carpeta del pack de cursores": "Choose the cursor pack folder",
    "Abrir": "Open",
    # Aplicar
    "Escribí un nombre para el tema antes de aplicarlo.": "Type a theme name before applying it.",
    "Ya hay un tema llamado «{name}» que no es de esta app. Elegí otro nombre.":
        "There's already a theme called “{name}” that wasn't made with this app. Choose another name.",
    "No elegiste la «Selección normal»": "You didn't choose “Normal select”",
    "Es el cursor que más se ve. ¿Aplicar igual? Se usará el del sistema para ese caso.":
        "It's the cursor you see the most. Apply anyway? The system one will be used for it.",
    "Aplicar igual": "Apply anyway",
    "No se pudo crear el tema: {error}": "Couldn't create the theme: {error}",
    "El tema se creó pero no se pudo activar: {error}. Elegilo en Configuración del sistema → Temas → Puntero del ratón.":
        "The theme was created but couldn't be activated: {error}. Pick it in System Settings → Themes → Mouse pointer.",
    "Cursor «{name}» aplicado": "Cursor “{name}” applied",
    # Presets
    "PRESETS GUARDADOS": "SAVED PRESETS",
    "Todavía no guardaste ningún preset": "You haven't saved any presets yet",
    "{count} de {total} · {size} px": "{count} of {total} · {size} px",
    "Guardar preset actual…": "Save current preset…",
    "Guarda los cuadros, el nombre y el tamaño": "Saves the cards, the name and the size",
    "Preset “{name}” cargado": "Preset “{name}” loaded",
    "Guardar preset": "Save preset",
    "Guardar": "Save",
    "Nombre del preset:": "Preset name:",
    "Se guarda una copia de los cursores, sus puntos activos, el nombre y el tamaño. No cambia el cursor que estás usando.":
        "A copy of the cursors, their hotspots, the name and the size is saved. Your current cursor doesn't change.",
    "Ya existe el preset «{name}»": "The preset “{name}” already exists",
    "¿Querés reemplazarlo por la combinación actual?": "Do you want to replace it with the current combination?",
    "Reemplazar": "Replace",
    "No se pudo guardar el preset: {error}": "Couldn't save the preset: {error}",
    "Preset “{name}” guardado": "Preset “{name}” saved",
    "No se pudo abrir el preset: {error}": "Couldn't open the preset: {error}",
    "Se abrió el preset, pero faltan archivos de: {roles}": "The preset opened, but files are missing for: {roles}",
    # Menú
    "Volver al cursor anterior": "Go back to previous cursor",
    "Restaura el que tenías antes de aplicar": "Restores the one you had before applying",
    "Borrar temas creados…": "Delete created themes…",
    "Elegí cuáles quitar del sistema": "Choose which ones to remove from the system",
    "Empezar desde cero": "Start from scratch",
    "Vacía los 15 cuadros, el nombre y el tamaño": "Clears the 15 cards, the name and the size",
    "Ajustes": "Settings",
    "Idioma de la app": "App language",
    "Acerca de Cursify": "About Cursify",
    "Versión {version}": "Version {version}",
    # Volver al anterior
    "¿Volver al cursor anterior?": "Go back to the previous cursor?",
    "Se va a activar «{name}» ({size} px), el cursor que tenías antes de aplicar uno con esta app.":
        "“{name}” ({size} px) will be activated, the cursor you had before applying one with this app.",
    "Volver": "Go back",
    "Volviste al cursor «{name}»": "Back to cursor “{name}”",
    "Todavía no aplicaste ningún cursor con esta app, así que no hay nada para restaurar.":
        "You haven't applied any cursor with this app yet, so there's nothing to restore.",
    # Borrar temas
    "Borrar temas creados": "Delete created themes",
    "Solo aparecen los temas creados con Cursify. Tus presets no se tocan.":
        "Only themes created with Cursify are listed. Your presets are not touched.",
    "Tema": "Theme",
    "Estado": "Status",
    "Cursores": "Cursors",
    "Creado": "Created",
    "En uso": "In use",
    "Borrar": "Delete",
    "Borrar el tema «{name}»": "Delete the theme “{name}”",
    "No hay temas creados con esta app.": "There are no themes created with this app.",
    "¿Borrar el tema «{name}»?": "Delete the theme “{name}”?",
    "Se borra la carpeta del tema. Tus presets no se tocan.":
        "The theme folder is deleted. Your presets are not touched.",
    "Es el cursor que estás usando ahora: antes de borrarlo se vuelve al cursor anterior.":
        "It's the cursor you're using now: before deleting it, the previous cursor is restored.",
    "No se pudo borrar: {error}": "Couldn't delete: {error}",
    "Tema «{name}» borrado": "Theme “{name}” deleted",
    # Empezar de cero
    "¿Empezar desde cero?": "Start from scratch?",
    "Se vacían los 15 cuadros, el nombre y el tamaño. Tus presets y los temas instalados no se tocan.":
        "The 15 cards, the name and the size are cleared. Your presets and installed themes are not touched.",
    "Empezar de cero": "Start over",
    "Listo, empezaste desde cero": "Done, you're starting from scratch",
    # Ajustes
    "Idioma": "Language",
    "Automático (idioma del sistema: {lang})": "Automatic (system language: {lang})",
    "Español": "Español",
    "English": "English",
    "español": "Spanish",
    "inglés": "English",
    "Idioma cambiado": "Language changed",
    # Acerca de
    "Convierte packs de cursores de Windows (.ani/.cur) en un tema para Linux Mint y lo aplica con un clic.":
        "Turns Windows cursor packs (.ani/.cur) into a Linux Mint theme and applies it in one click.",
}


def system_language():
    """'es' si el sistema está en español; si no, 'en'."""
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var, "")
        if value and value not in ("C", "POSIX"):
            return "es" if value.split(":")[0].lower().startswith("es") else "en"
    return "en"


def _load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def language_setting():
    """Lo que eligió el usuario: 'auto', 'es' o 'en'."""
    value = _load_settings().get("language", "auto")
    return value if value in CHOICES else "auto"


def set_language_setting(value):
    if value not in CHOICES:
        value = "auto"
    data = _load_settings()
    data["language"] = value
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    reload()


def _effective():
    setting = language_setting()
    return system_language() if setting == "auto" else setting


LANG = _effective()


def reload():
    global LANG
    LANG = _effective()
    return LANG


def T(text, **values):
    """Traduce ``text`` (escrito en español) al idioma activo y completa {marcadores}."""
    out = EN.get(text, text) if LANG == "en" else text
    return out.format(**values) if values else out
