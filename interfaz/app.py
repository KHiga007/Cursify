"""Interfaz gráfica de Cursify (GTK 3)."""

import os
import re
import sys
import time
import threading
import urllib.parse

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, Pango  # noqa: E402

from formatos import wincursor  # noqa: E402
from nucleo import i18n, presets, roles, theme  # noqa: E402
from nucleo.i18n import T  # noqa: E402
from nucleo.info import APP_NAME, __version__  # noqa: E402

PREVIEW_H = 140        # alto de la vista previa
CANVAS_W = 176         # ancho del lienzo de la vista previa (tarjeta mínima menos el relleno)
CARD_MIN_WIDTH = 196   # ancho mínimo de una tarjeta
CARD_MAX_WIDTH = 260   # ancho al que se apunta como máximo
CARD_SPACING = 12      # separación entre tarjetas
MAX_COLUMNS = 6
TOAST_MS = 2600
TOAST_ACTION_MS = 6000   # con botón «Deshacer» el aviso dura más
DRIVE_SUFFIX = re.compile(r"-\d{8}T\d{6}Z(?:-\d+)*$")  # sufijo que agrega Google Drive al bajar
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # raíz del proyecto
ICON_FILE = os.path.join(ROOT_DIR, "recursos", "cursify.svg")
SIZE_CHOICES = [(24, "Pequeño (24 px)"), (32, "Normal (32 px)"),
                (48, "Grande (48 px)"), (64, "Muy grande (64 px)")]
DEFAULT_SIZE = 32

# Cómo se agrupan las tarjetas en pantalla. El orden interno de roles.ROLES
# (y por lo tanto el de los presets y del tema) no cambia.
SECTIONS = [
    ("Esenciales", "Los que más vas a ver",
     ["normal", "help", "working", "busy", "text", "link"]),
    ("Precisión y edición", "Apuntar, dibujar y bloquear",
     ["precision", "handwriting", "unavailable", "alternate"]),
    ("Mover y redimensionar", "Bordes y esquinas de ventanas",
     ["vertical", "horizontal", "diagonal1", "diagonal2", "move"]),
]

LOGO_SVG = (b'<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24">'
            b'<path d="M5 2.5V20l4.6-4.4 3.1 6.6 3-1.4-3-6.4H19z" fill="#ffffff"/></svg>')

CSS = b"""
@define-color pf_bg #141417;
@define-color pf_topbar #18181c;
@define-color pf_line #26262c;
@define-color pf_card #1c1c21;
@define-color pf_card_border #2a2a31;
@define-color pf_popover #202026;
@define-color pf_popover_border #36363f;
@define-color pf_text #ececf0;
@define-color pf_muted #a1a1ab;
@define-color pf_accent #c92f68;
@define-color pf_accent_hover #b02658;
@define-color pf_pink #ff7aa8;
@define-color pf_ok #5fd38d;
@define-color pf_danger #ff9b93;

window.pf-window, window.pf-window .pf-root {
    background-color: @pf_bg;
    color: @pf_text;
}
.pf-window label { text-shadow: none; }
.pf-muted { color: @pf_muted; font-size: 12px; }
.pf-bold { font-weight: bold; }

/* ---------- Barra superior ---------- */
.pf-topbar {
    background-color: @pf_topbar;
    border-bottom: 1px solid @pf_line;
    padding: 12px 20px;
}
.pf-logo {
    background-color: @pf_accent;
    border-radius: 10px;
    min-width: 36px;
    min-height: 36px;
}
.pf-app-title { font-weight: bold; font-size: 17px; color: @pf_text; }
.pf-app-subtitle { font-size: 12px; }
levelbar.pf-progress trough {
    min-height: 6px;
    min-width: 180px;
    border-radius: 3px;
    background-color: @pf_line;
    border: none;
    padding: 0;
    box-shadow: none;
}
levelbar.pf-progress block {
    min-height: 6px;
    border-radius: 3px;
    border: none;
    box-shadow: none;
}
levelbar.pf-progress block.filled { background-color: @pf_accent; }
levelbar.pf-progress block.empty { background-color: transparent; }

/* ---------- Botones ---------- */
.pf-window button, .pf-popover button, .pf-dialog button {
    min-height: 40px;
    border-radius: 10px;
    background-image: none;
    background-color: #222228;
    border: 1px solid #33333b;
    color: @pf_text;
    text-shadow: none;
    box-shadow: none;
    -gtk-icon-shadow: none;
    padding: 0 14px;
}
.pf-window button:hover, .pf-popover button:hover, .pf-dialog button:hover {
    background-color: #2b2b33;
}
.pf-window button:disabled, .pf-popover button:disabled {
    background-color: #1d1d22;
    color: #8a8a94;
}
.pf-window button:disabled label, .pf-popover button:disabled label { color: #8a8a94; }
.pf-window button.pf-primary {
    background-color: @pf_accent;
    border-color: @pf_accent;
    color: #ffffff;
    font-weight: bold;
}
.pf-window button.pf-primary:hover { background-color: @pf_accent_hover; }
.pf-window button.pf-primary:disabled {
    background-color: #1d1d22;
    border-color: #33333b;
    color: #8a8a94;
}
.pf-window button.pf-icon-button {
    min-width: 36px;
    min-height: 36px;
    padding: 0;
}

/* ---------- Campos ---------- */
.pf-window entry, .pf-window combobox button, .pf-dialog entry {
    background-image: none;
    background-color: #1b1b20;
    border: 1px solid #33333b;
    border-radius: 10px;
    color: @pf_text;
    min-height: 40px;
    box-shadow: none;
}
.pf-window entry { padding: 0 12px; }
.pf-window entry:focus, .pf-dialog entry:focus,
.pf-window combobox button:focus, .pf-window combobox button:checked {
    border-color: @pf_pink;
    box-shadow: inset 0 0 0 1px @pf_pink;
}
.pf-field-label { color: @pf_muted; font-size: 12px; font-weight: bold; }

/* ---------- Popovers ---------- */
popover.pf-popover {
    background-color: @pf_popover;
    border: 1px solid @pf_popover_border;
    border-radius: 12px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
    color: @pf_text;
    padding: 8px;
}
.pf-popover list, .pf-popover row { background-color: transparent; }
.pf-popover row { border-radius: 10px; padding: 8px 10px; }
.pf-popover row:hover { background-color: #2b2b33; }
.pf-popover row:selected { background-color: #2b2b33; color: @pf_text; }
.pf-popover-title { color: @pf_muted; font-size: 11px; font-weight: bold; letter-spacing: 1px; }
.pf-popover button.pf-menuitem {
    background-color: transparent;
    border-color: transparent;
    padding: 6px 10px;
}
.pf-popover button.pf-menuitem:hover { background-color: #2b2b33; }
.pf-popover button.pf-menuitem:disabled { background-color: transparent; }
.pf-popover .pf-danger, .pf-popover .pf-danger label { color: @pf_danger; }
.pf-popover separator { background-color: @pf_popover_border; min-height: 1px; margin: 6px 0; }
.pf-save-icon {
    background-color: @pf_accent;
    border-radius: 8px;
    min-width: 28px;
    min-height: 28px;
    color: #ffffff;
}

/* ---------- Panel del tema ---------- */
.pf-panel {
    background-color: @pf_card;
    border: 1px solid @pf_card_border;
    border-radius: 14px;
    padding: 14px 16px;
}

/* ---------- Zona para soltar ---------- */
.pf-dropzone {
    border: 2px dashed #3a3a44;
    border-radius: 14px;
    padding: 22px;
    color: @pf_muted;
}
.pf-dropzone.pf-hover, .pf-dropzone.pf-drop {
    border-color: @pf_pink;
    color: @pf_text;
    background-color: #1d171b;
}
.pf-dropzone.pf-hover image, .pf-dropzone.pf-drop image { color: @pf_pink; }

/* ---------- Secciones y tarjetas ---------- */
.pf-section-title { font-weight: bold; font-size: 16px; color: @pf_text; }
.pf-window flowbox { background-color: transparent; }
.pf-window flowboxchild { padding: 0; background-color: transparent; }
.pf-card {
    background-color: #1c1c21;
    border: 1px solid #2a2a31;
    border-radius: 14px;
    padding: 10px;
}
.pf-card.pf-card-hover { background-color: #202026; border-color: #4a4a55; }
.pf-card.pf-card-editing { border-color: @pf_accent; }
.pf-card.pf-card-dragover { background-color: #22161c; border: 2px dashed @pf_pink; padding: 9px; }
.pf-card-title { font-weight: bold; font-size: 14px; color: @pf_text; }
.pf-preview {
    border-radius: 10px;
    background-color: #26262c;
    background-image: linear-gradient(45deg, #2f2f36 25%, transparent 25%, transparent 75%, #2f2f36 75%),
                      linear-gradient(45deg, #2f2f36 25%, transparent 25%, transparent 75%, #2f2f36 75%);
    background-size: 16px 16px, 16px 16px;
    background-position: 0 0, 8px 8px;
}
.pf-preview.pf-preview-empty {
    background-color: #18181c;
    background-image: none;
    border: 2px dashed #3a3a44;
}
.pf-preview.pf-preview-editing { box-shadow: inset 0 0 0 2px @pf_accent; }
.pf-preview-drop {
    background-color: #3a1d2a;
    border-radius: 10px;
    color: @pf_pink;
}
.pf-preview-drop image { color: @pf_pink; }
.pf-chip {
    background-color: #141417;
    color: #d6d6dc;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 999px;
}
.pf-chip.pf-chip-num { color: @pf_pink; font-size: 12px; font-weight: 700; }
.pf-chip.pf-chip-accent { background-color: @pf_accent; color: #ffffff; }
.pf-dot { min-width: 7px; min-height: 7px; border-radius: 4px; }
.pf-dot-ok { background-color: @pf_ok; }
.pf-window .pf-card button { min-height: 34px; border-radius: 9px; padding: 0 10px; }
.pf-window .pf-card button.pf-icon-button { min-width: 34px; min-height: 34px; padding: 0; }
.pf-window .pf-card button.pf-btn-soft {
    background-color: #2a1a22;
    border-color: #5a2a40;
    color: #ffb3cd;
}
.pf-window .pf-card button.pf-btn-soft label, .pf-window .pf-card button.pf-btn-soft image { color: #ffb3cd; }
.pf-window .pf-card button.pf-btn-soft:hover { background-color: #34202a; }

.pf-chip.pf-chip-warn { background-color: #3a2e1a; color: #ffd48a; }
.pf-window button.pf-toast-action {
    min-height: 30px;
    background-color: @pf_accent;
    border-color: @pf_accent;
    color: #ffffff;
    font-weight: bold;
}
.pf-window button.pf-toast-action:hover { background-color: @pf_accent_hover; }

/* ---------- Tabla de temas ---------- */
.pf-dialog list.pf-table { background-color: transparent; }
.pf-dialog list.pf-table row {
    border-bottom: 1px solid #2a2a31;
    padding: 6px 4px;
    background-color: transparent;
}
.pf-dialog list.pf-table row:hover { background-color: #222228; }
.pf-table-header { padding: 0 4px 4px 4px; border-bottom: 1px solid #33333b; }
.pf-dialog .pf-status-active { color: @pf_ok; font-weight: bold; }
.pf-dialog { background-color: @pf_bg; color: @pf_text; }
/* ---------- Ventana "Cerrar sin guardar" (A3: contorno rojo y verde claro) ---------- */
window.pf-close-dialog { background-color: transparent; }
.pf-close-card {
    background-color: #1c1c21;
    border: 1px solid #36363f;
    border-radius: 16px;
}
.pf-close-card.pf-joined { border-radius: 16px 0 0 16px; border-right-width: 0; }
.pf-close-dialog button.pf-stay {
    min-height: 34px;
    padding: 0 10px;
    border-radius: 10px;
    background-color: transparent;
    border: 1px solid rgba(43, 29, 0, 0.35);
}
.pf-close-dialog button.pf-stay label, .pf-close-dialog button.pf-stay image { color: #2b1d00; font-weight: bold; }
.pf-close-dialog button.pf-stay:hover { background-color: rgba(43, 29, 0, 0.12); }
.pf-close-dialog button.pf-choice { min-height: 64px; padding: 12px 16px; border-radius: 12px; }
.pf-dialog .pf-choice-title { font-size: 15px; font-weight: bold; }
.pf-dialog .pf-choice-sub { font-size: 13px; }
.pf-close-dialog button.pf-choice-discard { background-color: transparent; border: 1px solid #c93a3f; }
.pf-close-dialog button.pf-choice-discard image, .pf-close-dialog button.pf-choice-discard .pf-choice-title { color: #ff8a85; }
.pf-close-dialog button.pf-choice-discard .pf-choice-sub { color: #d9a6a1; }
.pf-close-dialog button.pf-choice-discard:hover { background-color: rgba(201, 58, 63, 0.14); }
.pf-close-dialog button.pf-choice-discard:disabled { opacity: 0.4; background-color: transparent; }
.pf-close-dialog button.pf-choice-save { background-color: #5fd38d; border: 1px solid #5fd38d; }
.pf-close-dialog button.pf-choice-save image, .pf-close-dialog button.pf-choice-save .pf-choice-title,
.pf-close-dialog button.pf-choice-save .pf-choice-tick { color: #0f2a1a; }
.pf-close-dialog button.pf-choice-save .pf-choice-sub { color: #1f4a30; }
.pf-close-dialog button.pf-choice-save:hover { background-color: #74dd9c; }
.pf-close-dialog button.pf-choice-save.pf-chosen { box-shadow: 0 0 0 3px rgba(95, 211, 141, 0.30); }
.pf-dialog .pf-choice-tick { font-size: 12px; font-weight: bold; }
.pf-save-panel-top { padding: 14px 16px 6px 16px; }
.pf-close-dialog button.pf-back-link {
    min-height: 32px;
    padding: 0 10px 0 6px;
    border-radius: 8px;
    background-color: transparent;
    border-color: transparent;
}
.pf-close-dialog button.pf-back-link label, .pf-close-dialog button.pf-back-link image { color: @pf_muted; font-weight: bold; }
.pf-close-dialog button.pf-back-link:hover { background-color: #2b2b33; }
.pf-save-note image { color: @pf_muted; }
.pf-close-card.pf-joined .pf-close-header { border-radius: 15px 0 0 0; }
.pf-save-panel {
    background-color: #1c1c21;
    border: 1px solid #36363f;
    border-left: 1px solid #2f6b47;
    border-radius: 0 16px 16px 0;
}
.pf-save-panel.pf-separate { border: 1px solid #2f6b47; border-radius: 16px; }
.pf-save-panel-head { padding: 12px 10px 12px 20px; border-bottom: 1px solid #2a2a31; }
.pf-save-badge {
    background-color: #1d3326;
    border: 1px solid #2f6b47;
    border-radius: 10px;
    min-width: 34px;
    min-height: 34px;
}
.pf-save-badge image { color: #7ee2a8; }
.pf-dialog .pf-save-panel-title { font-weight: bold; font-size: 17px; color: @pf_text; }
.pf-dialog button.pf-close-x.pf-panel-x image { color: @pf_muted; }
.pf-dialog button.pf-close-x.pf-panel-x:hover { background-color: #2b2b33; }
.pf-save-panel-body { padding: 20px; }
.pf-dialog entry.pf-save-entry {
    min-height: 44px;
    padding: 0 14px;
    border-radius: 10px;
    background-image: none;
    background-color: #141417;
    color: @pf_text;
    font-size: 15px;
}
.pf-dialog entry.pf-entry-ok, .pf-dialog entry.pf-entry-ok:focus {
    border: 1px solid #5fd38d;
    box-shadow: 0 0 0 3px rgba(95, 211, 141, 0.18);
}
.pf-dialog entry.pf-entry-warn, .pf-dialog entry.pf-entry-warn:focus {
    border: 1px solid #f5b742;
    box-shadow: 0 0 0 3px rgba(245, 183, 66, 0.18);
}
.pf-dialog .pf-save-warn, .pf-dialog image.pf-save-warn { color: #ffd48a; font-size: 13px; }
.pf-thumb {
    border-radius: 7px;
    background-color: #26262c;
    background-image: linear-gradient(45deg, #2f2f36 25%, transparent 25%, transparent 75%, #2f2f36 75%),
                      linear-gradient(45deg, #2f2f36 25%, transparent 25%, transparent 75%, #2f2f36 75%);
    background-size: 12px 12px, 12px 12px;
    background-position: 0 0, 6px 6px;
    border: 2px solid transparent;
}
.pf-thumb.pf-thumb-changed { border-color: #5fd38d; }
.pf-thumb.pf-thumb-empty { background-image: none; background-color: #18181c; border: 2px dashed #3a3a44; }
.pf-thumb-legend { min-width: 10px; min-height: 10px; border-radius: 3px; border: 2px solid #5fd38d; }
.pf-thumb.pf-thumb-system { border: 2px dashed #44444d; }
.pf-thumb-legend-system { min-width: 10px; min-height: 10px; border-radius: 3px; border: 2px dashed #6a6a75; }
.pf-thumb-box { padding: 12px; }
.pf-close-header.pf-close-header-save { background-color: #5fd38d; border-bottom: 1px solid #3fb571; }
.pf-close-header-save image.pf-warn-icon, .pf-dialog .pf-close-header-save .pf-close-title,
.pf-dialog .pf-close-header-save button.pf-close-x image { color: #0f2a1a; }
.pf-dialog .pf-close-header-save button.pf-close-x:hover,
.pf-close-dialog .pf-close-header-save button.pf-close-x:focus { background-color: rgba(15, 42, 26, 0.14); }
.pf-save-panel-foot { padding: 16px 20px 20px 20px; border-top: 1px solid #2a2a31; }
.pf-save-panel-foot button { min-height: 44px; border-radius: 10px; padding: 0 14px; font-weight: bold; }
.pf-close-dialog button.pf-btn-back { background-color: transparent; border: 1px solid #44444d; }
.pf-close-dialog button.pf-btn-back label { color: @pf_text; }
.pf-close-dialog button.pf-btn-back:hover { background-color: #2b2b33; }
.pf-close-dialog button.pf-btn-replace { background-color: #f5b742; border: 1px solid #f5b742; }
.pf-close-dialog button.pf-btn-replace label, .pf-close-dialog button.pf-btn-replace image { color: #2b1d00; }
.pf-close-dialog button.pf-btn-save.pf-active { box-shadow: 0 0 0 3px rgba(95, 211, 141, 0.28); }
.pf-close-header {
    background-color: #f5b742;
    border-bottom: 1px solid #d99a22;
    border-radius: 15px 15px 0 0;
    padding: 10px 10px 10px 22px;
}
.pf-close-header image.pf-warn-icon { color: #2b1d00; }
.pf-dialog .pf-close-title { font-weight: bold; font-size: 17px; color: #2b1d00; }
.pf-dialog button.pf-close-x {
    min-width: 36px;
    min-height: 36px;
    padding: 0;
    background-color: transparent;
    border-color: transparent;
}
.pf-dialog button.pf-close-x image { color: #2b1d00; }
.pf-dialog button.pf-close-x:hover { background-color: rgba(43, 29, 0, 0.14); }
.pf-close-list {
    background-color: #18181c;
    border: 1px solid #2a2a31;
    border-radius: 12px;
}
.pf-close-row { padding: 9px 12px; }
.pf-close-sep { min-height: 1px; background-color: #2a2a31; margin: 0 12px; }
.pf-close-icon {
    background-color: #26262c;
    border-radius: 8px;
    min-width: 30px;
    min-height: 30px;
}
.pf-close-icon image { color: @pf_pink; }
.pf-dialog .pf-close-key { color: @pf_muted; font-size: 14px; }
.pf-dialog .pf-close-value { color: @pf_text; font-size: 14px; font-weight: bold; }
.pf-close-body { padding: 20px 24px 4px 24px; }
.pf-dialog .pf-close-text { font-size: 15px; color: @pf_text; }
.pf-close-actions { padding: 18px 24px 22px 24px; }
.pf-close-actions button { min-height: 44px; border-radius: 10px; padding: 0 16px; font-weight: bold; }
.pf-dialog button.pf-btn-discard {
    background-color: transparent;
    border: 1px solid #c93a3f;
}
.pf-dialog button.pf-btn-discard label, .pf-dialog button.pf-btn-discard image { color: #ff8a85; }
.pf-dialog button.pf-btn-discard:hover { background-color: rgba(201, 58, 63, 0.14); }
.pf-dialog button.pf-btn-save {
    background-color: #5fd38d;
    border: 1px solid #5fd38d;
}
.pf-dialog button.pf-btn-save label, .pf-dialog button.pf-btn-save image { color: #0f2a1a; }
.pf-dialog button.pf-btn-save:hover { background-color: #74dd9c; }
.pf-dialog button.pf-btn-save:disabled {
    background-color: #2a2a31;
    background-image: none;
    border: 1px solid #36363f;
    box-shadow: none;
}
.pf-dialog button.pf-btn-save:disabled label { color: #6f6f7a; }
/* The Mint theme draws a light focus outline and its own gradients on buttons:
   reset them so the buttons match the design. */
.pf-close-dialog button {
    background-image: none;
    text-shadow: none;
    -gtk-icon-shadow: none;
    box-shadow: none;
    outline-style: none;
    outline-width: 0;
}
.pf-close-dialog button:focus { outline-style: none; outline-width: 0; box-shadow: none; }
.pf-close-dialog button.pf-btn-discard:focus { border-color: #ff8a85; }
.pf-close-dialog button.pf-close-x:focus { background-color: rgba(43, 29, 0, 0.14); }
.pf-dialog label { color: @pf_text; }
.pf-dialog button.pf-icon-button { min-width: 36px; min-height: 36px; padding: 0; }
.pf-dialog .pf-field-label { color: @pf_muted; font-size: 12px; font-weight: bold; }
.pf-dialog .pf-muted { color: @pf_muted; font-size: 12px; }
.pf-dialog .pf-bold { font-weight: bold; }

/* ---------- Avisos ---------- */
.pf-toast {
    background-color: @pf_popover;
    border: 1px solid @pf_popover_border;
    border-radius: 12px;
    padding: 12px 18px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
    color: @pf_text;
}
.pf-toast image { color: @pf_pink; }

scrolledwindow.pf-scroller, scrolledwindow.pf-scroller viewport { background-color: @pf_bg; }

/* ---------- Mensajes que no se cierran solos ---------- */
.pf-window infobar, .pf-window infobar revealer > box {
    background-image: none;
    background-color: #24242a;
    color: @pf_text;
    border: none;
    border-bottom: 1px solid @pf_line;
    text-shadow: none;
}
.pf-window infobar.warning revealer > box { background-color: #3a2e1a; }
.pf-window infobar.error revealer > box { background-color: #4a1f26; }
.pf-window infobar label { color: @pf_text; }
"""


# --------------------------------------------------------------------------
# Utilidades de dibujo
# --------------------------------------------------------------------------

def _paths_from_selection(data):
    paths = []
    for uri in data.get_uris() or []:
        if uri.startswith("file://"):
            paths.append(urllib.parse.unquote(uri[7:]))
    if not paths:
        text = data.get_text() or ""
        paths = [p.strip() for p in text.splitlines() if p.strip()]
    return paths


def _mark(pb, x, y):
    """Dibuja una cruz roja (punto activo) sobre ``pb``."""
    w, h = pb.get_width(), pb.get_height()
    for d in range(-5, 6):
        if abs(d) > 1:
            if 0 <= x + d < w and 0 <= y < h:
                pb.new_subpixbuf(x + d, y, 1, 1).fill(0xE01B24FF)
            if 0 <= y + d < h and 0 <= x < w:
                pb.new_subpixbuf(x, y + d, 1, 1).fill(0xE01B24FF)
    if 0 <= x < w and 0 <= y < h:
        pb.new_subpixbuf(x, y, 1, 1).fill(0xE01B24FF)


def _guides(pb, x, y):
    """Guías finas (1 px, rosa al 60 %) que cruzan el punto activo, mezcladas con composite."""
    w, h = pb.get_width(), pb.get_height()
    line = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, max(w, h), max(w, h))
    line.fill(0xFF7AA899)
    if 0 <= y < h:
        line.composite(pb, 0, y, w, 1, 0, y, 1, 1, GdkPixbuf.InterpType.NEAREST, 255)
    if 0 <= x < w:
        line.composite(pb, x, 0, 1, h, x, 0, 1, 1, GdkPixbuf.InterpType.NEAREST, 255)


def _ring(pb, x, y, radius):
    """Círculo rojo de 1 px alrededor del punto activo."""
    import math
    w, h = pb.get_width(), pb.get_height()
    done = set()
    steps = max(24, int(2 * math.pi * radius * 2))
    for i in range(steps):
        a = 2 * math.pi * i / steps
        px, py = int(round(x + radius * math.cos(a))), int(round(y + radius * math.sin(a)))
        if (px, py) not in done and 0 <= px < w and 0 <= py < h:
            done.add((px, py))
            pb.new_subpixbuf(px, py, 1, 1).fill(0xE01B24FF)


FLOPPY_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="{px}" height="{px}" viewBox="0 0 24 24">
<path d="M5 3h11.2L21 7.8V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z" fill="none" stroke="{color}"
 stroke-width="2" stroke-linejoin="round"/>
<path d="M7 3.5v4.5a1 1 0 0 0 1 1h7a1 1 0 0 0 1-1V3.5" fill="none" stroke="{color}" stroke-width="2"
 stroke-linejoin="round"/>
<rect x="6.5" y="13" width="11" height="7" rx="1" fill="none" stroke="{color}" stroke-width="2"/>
<rect x="12.5" y="4.5" width="2" height="3" fill="{color}"/>
</svg>"""


def _floppy(px, color="#0f2a1a"):
    """Ícono de disquete (guardar), dibujado acá para que se vea igual con cualquier tema."""
    try:
        loader = GdkPixbuf.PixbufLoader.new_with_type("svg")
        loader.write(FLOPPY_SVG.format(px=px, color=color).encode())
        loader.close()
        return Gtk.Image.new_from_pixbuf(loader.get_pixbuf())
    except Exception:  # noqa: BLE001  (sin soporte SVG: ícono del tema)
        return Gtk.Image.new_from_icon_name(_first_icon(("media-floppy-symbolic", "document-save-symbolic")),
                                            Gtk.IconSize.BUTTON)


def _first_icon(names):
    """Primer ícono de la lista que exista en el tema actual."""
    icons = Gtk.IconTheme.get_default()
    for name in names:
        if icons is not None and icons.has_icon(name):
            return name
    return names[-1]


def _logo_image():
    try:
        loader = GdkPixbuf.PixbufLoader()
        loader.write(LOGO_SVG)
        loader.close()
        return Gtk.Image.new_from_pixbuf(loader.get_pixbuf())
    except GLib.Error:
        return Gtk.Image.new_from_icon_name("input-mouse-symbolic", Gtk.IconSize.LARGE_TOOLBAR)


def _label(text, *classes, xalign=0.0, markup=False, wrap=False):
    lbl = Gtk.Label(xalign=xalign)
    if markup:
        lbl.set_markup(text)
    else:
        lbl.set_text(text)
    if wrap:
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    for cls in classes:
        lbl.get_style_context().add_class(cls)
    return lbl


def _icon_button(icon, tooltip):
    button = Gtk.Button.new_from_icon_name(icon, Gtk.IconSize.BUTTON)
    button.set_tooltip_text(tooltip)
    button.get_accessible().set_name(tooltip)
    button.get_style_context().add_class("pf-icon-button")
    return button


# --------------------------------------------------------------------------
# Tarjeta de cada situación
# --------------------------------------------------------------------------

class RoleCard(Gtk.FlowBoxChild):
    """Tarjeta de una situación: vista previa arriba, texto y acciones abajo.

    Estados: vacía, asignada, mouse encima, ajustando el punto activo y
    arrastrando un archivo encima. ``_refresh()`` decide qué se ve.
    """

    def __init__(self, window, role, number):
        super().__init__()
        self.window = window
        self.role = role
        self.source = None
        self.auto_hotspot = False   # el punto activo actual es el sugerido
        self.suggested = None       # punto sugerido (o None = el del archivo)
        self.editing = False
        self.dragover = False
        self.hovering = False
        self._frames = []
        self._index = 0
        self._timer = 0
        self._layout = None  # (escala, desplazamiento_x, desplazamiento_y) dentro del lienzo
        self._live_cursors = None   # cursores de prueba (uno por cuadro) para la prueba animada
        self._live_index = 0
        self._live_timer = 0
        self.set_can_focus(False)
        self.set_size_request(CARD_MIN_WIDTH, -1)

        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.card.get_style_context().add_class("pf-card")
        self.add(self.card)

        self.card.pack_start(self._build_preview(number), False, False, 0)

        # Texto: nombre + (archivo asignado o descripción).
        self.title = _label(T(role.label), "pf-card-title", wrap=True)
        self.title.set_max_width_chars(1)
        self.title.set_lines(2)
        self.title.set_ellipsize(Pango.EllipsizeMode.END)
        self.title.set_tooltip_text(T(role.label))
        self.card.pack_start(self.title, False, False, 0)
        self.info_stack = Gtk.Stack()
        self.info_stack.set_homogeneous(False)
        file_row = Gtk.Box(spacing=7)
        dot = Gtk.Box()
        dot.set_valign(Gtk.Align.CENTER)
        dot.get_style_context().add_class("pf-dot")
        dot.get_style_context().add_class("pf-dot-ok")
        self.file_label = _label("", "pf-muted")
        self.file_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.file_label.set_max_width_chars(1)
        file_row.pack_start(dot, False, False, 0)
        file_row.pack_start(self.file_label, True, True, 0)
        hint = _label(T(role.hint), "pf-muted")
        hint.set_ellipsize(Pango.EllipsizeMode.END)
        hint.set_max_width_chars(1)
        self.info_stack.add_named(file_row, "file")
        self.info_stack.add_named(hint, "hint")
        self.card.pack_start(self.info_stack, False, False, 0)

        self.card.pack_end(self._build_actions(), False, False, 0)

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.drag_dest_add_text_targets()
        self.connect("drag-data-received", self._on_drop)
        self.connect("drag-motion", self._on_drag_motion)
        self.connect("drag-leave", lambda *_: self._set_dragover(False))
        self.connect("drag-drop", lambda *_: self._set_dragover(False) or False)
        self.connect("destroy", lambda *_: self._stop())
        # Los Gtk.Stack solo cambian a hijos visibles: se muestran antes del primer _refresh().
        self.show_all()
        self._refresh()

    # ------------------------------------------------------------ armado
    def _chip(self, text, *classes, halign=Gtk.Align.START, valign=Gtk.Align.START):
        chip = _label(text, "pf-chip", *classes, xalign=0.5)
        chip.set_halign(halign)
        chip.set_valign(valign)
        chip.set_margin_start(8)
        chip.set_margin_end(8)
        chip.set_margin_top(8)
        chip.set_margin_bottom(8)
        return chip

    def _build_preview(self, number):
        # Gtk.Overlay no dibuja fondo ni borde en GTK 3: la clase pf-preview va en una
        # caja que lo envuelve (damero, radio, borde punteado y contorno de edición).
        self.preview = Gtk.Box()
        self.preview.set_size_request(-1, PREVIEW_H)
        self.preview.get_style_context().add_class("pf-preview")
        self.overlay = Gtk.Overlay()
        self.preview.pack_start(self.overlay, True, True, 0)

        # Página "normal": imagen animada o estado vacío. Página "drop": soltá para asignar.
        self.preview_stack = Gtk.Stack()
        self.preview_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.events = Gtk.EventBox()
        self.events.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK
                               | Gdk.EventMask.BUTTON_PRESS_MASK)
        self.events.connect("button-press-event", self._on_click)
        self.events.connect("enter-notify-event", self._on_enter)
        self.events.connect("leave-notify-event", self._on_leave)
        self.events.connect("realize", lambda *_: self._update_test_cursor())

        self.content_stack = Gtk.Stack()
        self.image = Gtk.Image()
        self.image.set_halign(Gtk.Align.CENTER)
        self.image.set_valign(Gtk.Align.CENTER)
        self.content_stack.add_named(self.image, "image")
        empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        empty.set_halign(Gtk.Align.CENTER)
        empty.set_valign(Gtk.Align.CENTER)
        self.system_image = Gtk.Image()
        self.system_image.set_opacity(0.35)
        empty.pack_start(self.system_image, False, False, 0)
        empty.pack_start(_label(T("Usa el del sistema"), "pf-muted", xalign=0.5), False, False, 0)
        self.content_stack.add_named(empty, "empty")
        self.events.add(self.content_stack)
        self.preview_stack.add_named(self.events, "normal")

        drop = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        drop.get_style_context().add_class("pf-preview-drop")
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6,
                        halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER, vexpand=True)
        icon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.DND)
        inner.pack_start(icon, False, False, 0)
        inner.pack_start(_label(T("Soltá para asignar"), "pf-bold", xalign=0.5), False, False, 0)
        drop.pack_start(inner, True, True, 0)
        self.preview_stack.add_named(drop, "drop")
        self.overlay.add(self.preview_stack)

        # Chips encima de la vista previa (no reciben clics).
        self.chip_num = self._chip(f"{number:02d}", "pf-chip-num")
        self.chip_format = self._chip("", halign=Gtk.Align.END)
        self.chip_size = self._chip("", halign=Gtk.Align.END, valign=Gtk.Align.END)
        self.live_revealer = Gtk.Revealer()
        self.live_revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self.live_revealer.set_halign(Gtk.Align.START)
        self.live_revealer.set_valign(Gtk.Align.END)
        self.live_revealer.add(self._chip(T("● Probando en vivo"), "pf-chip-accent"))
        self.chip_suggested = self._chip(T("Punto sugerido"), "pf-chip-warn", valign=Gtk.Align.END)
        self.chip_suggested.set_tooltip_text(T("La app calculó el punto activo: revisalo con «Ajustar punto activo»"))
        self.chip_suggested.set_no_show_all(True)
        self.chip_edit = self._chip(T("Clic para mover · Esc para terminar"), "pf-chip-wide",
                                    halign=Gtk.Align.CENTER, valign=Gtk.Align.END)
        self.chip_edit.set_no_show_all(True)
        for chip in (self.chip_num, self.chip_format, self.chip_size, self.chip_suggested,
                     self.live_revealer, self.chip_edit):
            self.overlay.add_overlay(chip)
            self.overlay.set_overlay_pass_through(chip, True)
        self.chip_format.set_no_show_all(True)
        self.chip_size.set_no_show_all(True)
        return self.preview

    def _build_actions(self):
        self.actions = Gtk.Stack()
        self.actions.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        choose = Gtk.Button()
        box = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        box.pack_start(Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON),
                       False, False, 0)
        box.pack_start(Gtk.Label(label=T("Elegir archivo…")), False, False, 0)
        choose.add(box)
        choose.get_style_context().add_class("pf-btn-soft")
        choose.connect("clicked", self._on_choose)
        self.actions.add_named(choose, "empty")

        assigned = Gtk.Box(spacing=6)
        change = Gtk.Button(label=T("Cambiar…"))
        change.connect("clicked", self._on_choose)
        adjust = _icon_button(_first_icon(("find-location-symbolic", "crosshairs-symbolic",
                                           "zoom-fit-best-symbolic")), T("Ajustar punto activo"))
        adjust.connect("clicked", lambda *_: self.start_editing())
        remove = _icon_button("user-trash-symbolic", T("Quitar cursor"))
        remove.connect("clicked", lambda *_: self.window.remove_with_undo(self))
        assigned.pack_start(change, True, True, 0)
        assigned.pack_start(adjust, False, False, 0)
        assigned.pack_start(remove, False, False, 0)
        self.actions.add_named(assigned, "assigned")

        editing = Gtk.Box(spacing=6)
        suggested = Gtk.Button()
        sbox = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER)
        sbox.pack_start(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON),
                        False, False, 0)
        sbox.pack_start(Gtk.Label(label=T("Sugerido")), False, False, 0)
        suggested.add(sbox)
        suggested.set_tooltip_text(T("Vuelve al punto activo original o sugerido"))
        suggested.connect("clicked", self._on_suggested)
        done = Gtk.Button(label=T("Listo"))
        done.get_style_context().add_class("pf-primary")
        done.connect("clicked", lambda *_: self.stop_editing())
        editing.pack_start(suggested, True, True, 0)
        editing.pack_start(done, True, True, 0)
        self.actions.add_named(editing, "editing")
        return self.actions

    # ----------------------------------------------------------------- datos
    def set_source(self, source, suggest=True):
        if self.editing:
            self.stop_editing()
        self.source = source
        self.suggested = None
        self.auto_hotspot = False
        if source is not None:
            # El sugerido se calcula aparte, así «Sugerido» puede volver a él.
            probe = theme.Source(source.path, source.frames)
            if theme.suggest_hotspot(probe, self.role.key):
                self.suggested = probe.hotspot
            if suggest and source.hotspot is None and self.suggested is not None:
                source.hotspot = self.suggested
                self.auto_hotspot = True
        self._refresh()
        self.window.on_assignments_changed()

    def load_path(self, path):
        try:
            source = theme.load_source(path)
        except (OSError, wincursor.CursorError, Exception) as exc:  # noqa: BLE001
            self.window.show_error(T("No se pudo abrir «{name}»: {error}",
                                     name=os.path.basename(path), error=exc))
            return False
        self.set_source(source)
        return True

    # ---------------------------------------------------------------- estado
    def _toggle(self, widget, cls, on):
        ctx = widget.get_style_context()
        (ctx.add_class if on else ctx.remove_class)(cls)

    def _refresh(self):
        """Decide qué se ve según source / editing / dragover / hovering."""
        self._stop()
        assigned = self.source is not None
        if not assigned:
            self.editing = False
        self._toggle(self.preview, "pf-preview-empty", not assigned)
        self._toggle(self.preview, "pf-preview-editing", self.editing)
        self._toggle(self.card, "pf-card-editing", self.editing)
        self._toggle(self.card, "pf-card-hover", self.hovering and assigned and not self.dragover)
        self._toggle(self.card, "pf-card-dragover", self.dragover)
        self.preview_stack.set_visible_child_name("drop" if self.dragover else "normal")
        self.live_revealer.set_reveal_child(self.hovering and assigned and not self.editing)
        self._update_suggested_chip()
        self.chip_edit.set_visible(self.editing)

        if not assigned:
            self._frames = []
            self._layout = None
            self._load_system_image()
            self.content_stack.set_visible_child_name("empty")
            self.chip_format.hide()
            self.chip_size.hide()
            self.info_stack.set_visible_child_name("hint")
            self.actions.set_visible_child_name("empty")
            self._update_test_cursor()
            return

        self.content_stack.set_visible_child_name("image")
        self.info_stack.set_visible_child_name("file")
        self.file_label.set_text(self.source.name)
        self.file_label.set_tooltip_text(self.source.path)
        self.actions.set_visible_child_name("editing" if self.editing else "assigned")
        self._update_chips()
        self._build_previews()
        self._index = 0
        self._show_frame()
        self._update_test_cursor()

    def _update_chips(self):
        if self.source is None:
            return
        ctx = self.chip_format.get_style_context()
        if self.editing:
            hx, hy = self.source.current_hotspot()
            self.chip_format.set_text(T("x {x} · y {y}", x=hx, y=hy))
            ctx.add_class("pf-chip-accent")
        else:
            fmt = os.path.splitext(self.source.path)[1].lstrip(".").upper() or "?"
            if self.source.animated:
                fmt = T("{fmt} · {n} cuadros", fmt=fmt, n=len(self.source.frames))
            self.chip_format.set_text(fmt)
            ctx.remove_class("pf-chip-accent")
        self.chip_format.show()
        self.chip_size.set_text(f"{self.window.selected_size()} px")
        self.chip_size.set_visible(not self.editing)

    def _update_suggested_chip(self):
        self.chip_suggested.set_visible(self.source is not None and self.auto_hotspot
                                        and not self.editing and not self.hovering)

    def _load_system_image(self):
        # M7: el cursor del tema que se usa de verdad para las situaciones vacías (el
        # cursor anterior), no el tema creado con la app que pueda estar activo.
        pixbuf = None
        found = theme.system_cursor_image(self.role.xnames[0], 32)
        if found is not None:
            w, h, rgba = found
            pixbuf = theme.rgba_to_pixbuf(w, h, rgba)
        display = Gdk.Display.get_default()
        if pixbuf is None and display is not None:
            try:
                cursor = Gdk.Cursor.new_from_name(display, self.role.xnames[0])
                pixbuf = cursor.get_image() if cursor is not None else None
            except Exception:  # noqa: BLE001
                pixbuf = None
        if pixbuf is not None:
            w, h = pixbuf.get_width(), pixbuf.get_height()
            f = 40 / max(w, h)
            pixbuf = pixbuf.scale_simple(max(1, round(w * f)), max(1, round(h * f)),
                                         GdkPixbuf.InterpType.BILINEAR)
            self.system_image.set_from_pixbuf(pixbuf)
        else:
            self.system_image.set_from_icon_name("input-mouse-symbolic", Gtk.IconSize.DIALOG)

    # -------------------------------------------------------------- dibujo
    def _build_previews(self):
        """Cuadros de la animación sobre un lienzo transparente, con la cruz del punto activo
        (y en modo ajuste, guías y círculo). Sin pycairo: se compone sobre el pixbuf."""
        frames = self.source.effective_frames()
        first = frames[0]
        cw, ch = CANVAS_W, PREVIEW_H
        scale = min((cw - 16) / first.width, (ch - 16) / first.height)
        if scale >= 1:
            scale = float(int(scale))  # aumento entero: se ve nítido
        sw, sh = max(1, int(first.width * scale)), max(1, int(first.height * scale))
        ox, oy = (cw - sw) // 2, (ch - sh) // 2
        self._layout = (scale, ox, oy)
        interp = GdkPixbuf.InterpType.NEAREST if scale >= 1 else GdkPixbuf.InterpType.HYPER
        self._frames = []
        for f in frames:
            pb = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, cw, ch)
            pb.fill(0x00000000)
            src = theme.rgba_to_pixbuf(f.width, f.height, f.rgba)
            fw, fh = max(1, int(f.width * scale)), max(1, int(f.height * scale))
            src.composite(pb, ox, oy, min(fw, cw - ox), min(fh, ch - oy),
                          ox, oy, scale, scale, interp, 255)
            hx = ox + int((f.xhot + 0.5) * scale)
            hy = oy + int((f.yhot + 0.5) * scale)
            if self.editing:
                _guides(pb, hx, hy)
                _ring(pb, hx, hy, 7)
            _mark(pb, hx, hy)
            self._frames.append((pb, f.delay))

    def _show_frame(self):
        if not self._frames:
            return False
        pb, delay = self._frames[self._index]
        self.image.set_from_pixbuf(pb)
        if len(self._frames) > 1:
            self._timer = GLib.timeout_add(max(delay, 20), self._next_frame)
        return False

    def _next_frame(self):
        self._timer = 0
        if not self._frames:
            return False
        self._index = (self._index + 1) % len(self._frames)
        self._show_frame()
        return False

    def _stop(self):
        if self._timer:
            GLib.source_remove(self._timer)
            self._timer = 0
        self._stop_live()
        self._live_cursors = None

    def _stop_live(self):
        if self._live_timer:
            GLib.source_remove(self._live_timer)
            self._live_timer = 0

    def _start_live(self):
        """Mientras el mouse está encima, el cursor de prueba se anima como en el tema."""
        gdk_window = self.events.get_window()
        if gdk_window is None or self.source is None or not self.source.animated:
            return
        if self._live_cursors is None:
            size = self.window.selected_size()
            display = gdk_window.get_display()
            frames = self.source.effective_frames()
            base = max(frames[0].width, frames[0].height)
            self._live_cursors = []
            for f in frames:
                sf = theme.frame_for_size(f, base, size)
                pb = theme.rgba_to_pixbuf(sf.width, sf.height, sf.rgba)
                try:
                    cursor = Gdk.Cursor.new_from_pixbuf(display, pb, sf.xhot, sf.yhot)
                except Exception:  # noqa: BLE001
                    self._live_cursors = []
                    return
                self._live_cursors.append((cursor, f.delay))
        self._live_index = 0
        self._stop_live()
        self._live_step()

    def _live_step(self):
        self._live_timer = 0
        gdk_window = self.events.get_window()
        if not self._live_cursors or gdk_window is None or not self.hovering:
            return False
        cursor, delay = self._live_cursors[self._live_index]
        gdk_window.set_cursor(cursor)
        self._live_index = (self._live_index + 1) % len(self._live_cursors)
        self._live_timer = GLib.timeout_add(max(delay, 20), self._live_step)
        return False

    def _update_test_cursor(self):
        gdk_window = self.events.get_window()
        if gdk_window is None:
            return
        if self.source is None:
            gdk_window.set_cursor(Gdk.Cursor.new_from_name(gdk_window.get_display(), "pointer"))
            return
        f = self.source.effective_frames()[0]
        sf = theme.frame_for_size(f, max(f.width, f.height), self.window.selected_size())
        pb = theme.rgba_to_pixbuf(sf.width, sf.height, sf.rgba)
        try:
            gdk_window.set_cursor(Gdk.Cursor.new_from_pixbuf(gdk_window.get_display(), pb,
                                                             sf.xhot, sf.yhot))
        except Exception:  # noqa: BLE001
            pass

    def refresh_test_cursor(self):
        """Se llama al cambiar el tamaño elegido."""
        self._live_cursors = None
        self._update_test_cursor()
        if self.source is not None:
            self._update_chips()

    # ------------------------------------------------- modo «ajustar punto»
    def start_editing(self):
        if self.source is None or self.editing:
            return
        other = self.window.editing_card
        if other is not None and other is not self:
            other.stop_editing()
        self.window.editing_card = self
        self.editing = True
        self._refresh()

    def stop_editing(self):
        if self.window.editing_card is self:
            self.window.editing_card = None
        if not self.editing:
            return
        self.editing = False
        self.auto_hotspot = False  # al terminar de ajustar, el punto queda confirmado
        self._refresh()

    def nudge(self, dx, dy):
        """Mueve el punto activo con el teclado (en el modo de ajuste)."""
        if self.source is None or not self.editing:
            return
        first = self.source.frames[0]
        hx, hy = self.source.current_hotspot()
        self.source.hotspot = (min(max(hx + dx, 0), first.width - 1),
                               min(max(hy + dy, 0), first.height - 1))
        self.auto_hotspot = False
        self._refresh()
        self.window.on_assignments_changed()

    def _on_suggested(self, *_):
        if self.source is None:
            return
        self.source.hotspot = self.suggested
        self.auto_hotspot = self.suggested is not None
        self._refresh()
        self.window.on_assignments_changed()

    # ------------------------------------------------------------- eventos
    def _on_enter(self, *_):
        self.hovering = True
        if self.source is not None:
            self._toggle(self.card, "pf-card-hover", not self.dragover)
            self.live_revealer.set_reveal_child(not self.editing)
            self._update_suggested_chip()
            self._start_live()
        return False

    def _on_leave(self, _widget, event):
        if event.detail == Gdk.NotifyType.INFERIOR:
            return False
        self.hovering = False
        self._toggle(self.card, "pf-card-hover", False)
        self.live_revealer.set_reveal_child(False)
        self._update_suggested_chip()
        self._stop_live()
        self._update_test_cursor()
        return False

    def _on_click(self, _widget, event):
        if event.button != 1:
            return False
        if self.source is None:
            self._on_choose()
            return True
        if not self.editing or self._layout is None:
            return False  # el punto activo solo se mueve en el modo «Ajustar punto activo»
        alloc = self.events.get_allocation()
        scale, ox, oy = self._layout
        px = event.x - (alloc.width - CANVAS_W) / 2 - ox
        py = event.y - (alloc.height - PREVIEW_H) / 2 - oy
        first = self.source.frames[0]
        self.source.hotspot = (int(min(max(px / scale, 0), first.width - 1)),
                               int(min(max(py / scale, 0), first.height - 1)))
        self.auto_hotspot = False
        self._refresh()
        self.window.on_assignments_changed()
        return True

    def _on_choose(self, *_):
        dialog = Gtk.FileChooserNative.new(T("Elegir cursor: {role}", role=T(self.role.label)),
                                           self.window, Gtk.FileChooserAction.OPEN,
                                           T("Elegir"), T("Cancelar"))
        filt = Gtk.FileFilter()
        filt.set_name(T("Cursores e imágenes (.ani, .cur, .ico, .png, .svg)"))
        for ext in roles.SUPPORTED_EXT:
            filt.add_pattern("*" + ext)
            filt.add_pattern("*" + ext.upper())
        dialog.add_filter(filt)
        if self.window.last_folder:
            dialog.set_current_folder(self.window.last_folder)
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            path = dialog.get_filename()
            self.window.last_folder = os.path.dirname(path)
            self.load_path(path)
        dialog.destroy()

    def _set_dragover(self, on):
        if self.dragover == on:
            return
        self.dragover = on
        self._toggle(self.card, "pf-card-dragover", on)
        self._toggle(self.card, "pf-card-hover", False)
        self.preview_stack.set_visible_child_name("drop" if on else "normal")

    def _on_drag_motion(self, *_):
        self._set_dragover(True)
        return False

    def _on_drop(self, _widget, _ctx, _x, _y, data, _info, _time):
        self._set_dragover(False)
        paths = _paths_from_selection(data)
        if not paths:
            return
        if os.path.isdir(paths[0]) or len(paths) > 1:
            GLib.idle_add(self.window.import_paths, paths, True)
        else:
            self.load_path(paths[0])


class PresetRow(Gtk.ListBoxRow):
    def __init__(self, info, loaded, dirty=False):
        super().__init__()
        self.preset_name = info["name"]
        box = Gtk.Box(spacing=10)
        icon = Gtk.Image.new_from_icon_name("input-mouse-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name = _label(info["name"], "pf-bold")
        name.set_ellipsize(Pango.EllipsizeMode.END)
        texts.pack_start(name, False, False, 0)
        detail = T("{count} de {total} · {size} px", count=info["count"],
                   total=len(roles.ROLES), size=info["size"])
        if dirty:
            detail += T(" · con cambios sin guardar")
        texts.pack_start(_label(detail, "pf-muted"), False, False, 0)
        box.pack_start(icon, False, False, 0)
        box.pack_start(texts, True, True, 0)
        if loaded:
            box.pack_end(Gtk.Image.new_from_icon_name("object-select-symbolic", Gtk.IconSize.BUTTON),
                         False, False, 0)
        self.add(box)


# --------------------------------------------------------------------------
# Ventana principal
# --------------------------------------------------------------------------

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title=APP_NAME)
        self.set_default_size(1280, 880)
        if os.path.isfile(ICON_FILE):
            self.set_icon_from_file(ICON_FILE)
        else:
            self.set_icon_name("input-mouse")
        self.get_style_context().add_class("pf-window")
        self.last_folder = (GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
                            or os.path.expanduser("~"))
        if not os.path.isdir(self.last_folder):
            self.last_folder = os.path.expanduser("~")
        self._busy = False
        self._toast_timer = 0
        self.loaded_preset = None
        self._preset_dirty = False
        self._loading_preset = False
        self._auto_name = ""     # último nombre puesto automáticamente desde una carpeta
        self._importing = False
        self._unsaved = False    # hay cambios que no se aplicaron ni se guardaron en un preset
        self._baseline = {}      # cómo estaba cada cursor la última vez que se aplicó/guardó
        self.cards = {}

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.get_style_context().add_class("pf-root")
        self.add(root)
        root.pack_start(self._build_topbar(), False, False, 0)

        self.infobar = Gtk.InfoBar(show_close_button=True)
        self.info_label = Gtk.Label(xalign=0)
        self.info_label.set_line_wrap(True)
        self.infobar.get_content_area().add(self.info_label)
        self.infobar.connect("response", lambda bar, _r: bar.set_revealed(False))
        self.infobar.set_revealed(False)
        root.pack_start(self.infobar, False, False, 0)

        # Contenido desplazable dentro de un overlay (para el aviso flotante).
        overlay = Gtk.Overlay()
        root.pack_start(overlay, True, True, 0)
        scroller = Gtk.ScrolledWindow()
        scroller.get_style_context().add_class("pf-scroller")
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        overlay.add(scroller)
        overlay.add_overlay(self._build_toast())
        overlay.set_overlay_pass_through(self.toast_revealer, True)  # no tapa clics
        self.main_overlay = overlay

        self.editing_card = None  # tarjeta en modo «Ajustar punto activo» (como mucho una)
        self.connect("key-press-event", self._on_key_press)
        self.connect("delete-event", self._on_delete_event)
        self.flows = []
        self._columns = 0
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        content.connect("size-allocate", self._on_content_allocate)
        content.set_margin_start(20)
        content.set_margin_end(20)
        content.set_margin_top(20)
        content.set_margin_bottom(28)
        scroller.add(content)

        content.pack_start(self._build_panel(), False, False, 0)
        content.pack_start(self._build_dropzone(), False, False, 0)

        role_numbers = {r.key: i for i, r in enumerate(roles.ROLES, start=1)}
        for title, subtitle, keys in SECTIONS:
            section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            head = Gtk.Box(spacing=10)
            head.pack_start(_label(T(title), "pf-section-title"), False, False, 0)
            sub = _label(T(subtitle), "pf-muted")
            sub.set_valign(Gtk.Align.BASELINE)
            head.pack_start(sub, False, False, 0)
            section.pack_start(head, False, False, 0)
            flow = Gtk.FlowBox()
            flow.set_selection_mode(Gtk.SelectionMode.NONE)
            flow.set_homogeneous(True)
            flow.set_min_children_per_line(1)
            flow.set_max_children_per_line(6)
            flow.set_row_spacing(CARD_SPACING)
            flow.set_column_spacing(CARD_SPACING)
            flow.set_valign(Gtk.Align.START)
            self.flows.append(flow)
            flow.set_activate_on_single_click(False)
            for key in keys:
                card = RoleCard(self, roles.ROLE_BY_KEY[key], role_numbers[key])
                self.cards[key] = card
                flow.add(card)
            section.pack_start(flow, False, False, 0)
            content.pack_start(section, False, False, 0)

        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.COPY)
        self.drag_dest_add_uri_targets()
        self.connect("drag-data-received", self._on_window_drop)
        # Mientras se arrastra algo sobre la ventana, la zona para soltar se resalta.
        self.connect("drag-motion", lambda *_: self._dropzone_state("pf-drop", True))
        self.connect("drag-leave", lambda *_: self._dropzone_state("pf-drop", False))

        self._update_progress()

    # ------------------------------------------------------ reacomodo
    def _on_content_allocate(self, _widget, allocation):
        """Misma cantidad de columnas en las 3 secciones, según el ancho disponible."""
        width = allocation.width + CARD_SPACING
        fit = width // (CARD_MIN_WIDTH + CARD_SPACING)                 # cuántas entran sin bajar de 196 px
        wanted = -(-width // (CARD_MAX_WIDTH + CARD_SPACING))          # cuántas hacen falta para no pasar de 260 px
        # Hasta 6 columnas (el grupo de 6 llena la fila); solo en pantallas muy anchas se
        # agregan más para que las tarjetas no pasen de ~260 px.
        columns = max(1, min(fit, max(MAX_COLUMNS, wanted)))
        if columns != self._columns:
            self._columns = columns
            GLib.idle_add(self._apply_columns, columns)

    def _on_delete_event(self, *_):
        """Al cerrar con cambios sin aplicar ni guardar, pregunta qué hacer."""
        if not self._unsaved or self.assigned_count() == 0:
            return False  # se cierra normalmente
        answer = self._ask_close()
        if answer in ("discard", "saved"):
            return False                       # cerrar (sin guardar, o ya guardado en el panel)
        return True                            # cancelar: la ventana queda abierta

    def _ask_close(self):
        """Salida con cambios en dos modales, de a uno: el aviso y, si se elige «Guardar preset»,
        el modal para guardarlo (el aviso se oculta). «Volver» regresa al aviso."""
        while True:
            answer = self._close_warning_dialog()
            if answer != "save":
                return answer
            result = self._close_save_dialog()
            if result in ("saved", "cancel"):
                return result
            # "back": se vuelve a mostrar el aviso

    def _new_close_dialog(self):
        dialog = Gtk.Dialog(transient_for=self, modal=True)
        dialog.set_decorated(False)
        dialog.set_resizable(False)
        dialog.get_style_context().add_class("pf-dialog")
        dialog.get_style_context().add_class("pf-close-dialog")
        screen = dialog.get_screen()
        visual = screen.get_rgba_visual() if screen is not None else None
        if visual is not None and screen.is_composited():
            dialog.set_visual(visual)          # esquinas redondeadas de verdad
        area = dialog.get_content_area()
        area.set_border_width(0)
        area.set_spacing(0)
        return dialog, area

    def _close_warning_dialog(self):
        """Modal 1 (A3 · contorno rojo y verde claro). Devuelve "discard", "save" o "cancel"."""
        dialog, area = self._new_close_dialog()
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.get_style_context().add_class("pf-close-card")
        card.set_size_request(480, -1)
        area.pack_start(card, True, True, 0)

        # Franja de advertencia: ícono, título y X (= Cancelar).
        header = Gtk.Box(spacing=12)
        header.get_style_context().add_class("pf-close-header")
        warn = Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        warn.get_style_context().add_class("pf-warn-icon")
        header.pack_start(warn, False, False, 0)
        header.pack_start(_label(T("Cambios sin guardar"), "pf-close-title"), True, True, 0)
        close = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        close.get_style_context().add_class("pf-close-x")
        close.set_tooltip_text(T("Cancelar"))
        close.get_accessible().set_name(T("Cancelar"))
        close.connect("clicked", lambda *_: dialog.response(Gtk.ResponseType.CANCEL))
        header.pack_end(close, False, False, 0)
        card.pack_start(header, False, False, 0)

        # Mensaje y resumen de lo que se perdería.
        body_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body_box.get_style_context().add_class("pf-close-body")
        body = _label(T("Si cerrás ahora, se pierde lo que no aplicaste ni guardaste como preset."),
                      "pf-close-text", wrap=True)
        body.set_max_width_chars(46)
        body_box.pack_start(body, False, False, 0)
        # Detalle: lista con íconos (cursores cambiados, tamaño, nombre).
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        details.get_style_context().add_class("pf-close-list")
        name = self.name_entry.get_text().strip()
        rows = [("input-mouse-symbolic", T("Cursores cambiados"),
                 T("{n} de {total}", n=self.changed_count(), total=len(roles.ROLES))),
                (_first_icon(("measure-symbolic", "zoom-fit-best-symbolic", "view-fullscreen-symbolic")),
                 T("Tamaño"), f"{self.selected_size()} px"),
                (_first_icon(("tag-symbolic", "bookmark-new-symbolic", "document-edit-symbolic")),
                 T("Nombre del tema"), name or T("Sin nombre"))]
        if self.loaded_preset:
            rows.append(("document-save-symbolic", T("Preset"), self.loaded_preset))
        for i, (icon, key, value) in enumerate(rows):
            if i:
                sep = Gtk.Box()
                sep.get_style_context().add_class("pf-close-sep")
                details.pack_start(sep, False, False, 0)
            row = Gtk.Box(spacing=12)
            row.get_style_context().add_class("pf-close-row")
            badge = Gtk.Box()
            badge.get_style_context().add_class("pf-close-icon")
            badge.set_center_widget(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON))
            row.pack_start(badge, False, False, 0)
            row.pack_start(_label(key, "pf-close-key"), True, True, 0)
            val = _label(value, "pf-close-value", xalign=1.0)
            val.set_ellipsize(Pango.EllipsizeMode.END)
            val.set_max_width_chars(22)
            row.pack_end(val, False, False, 0)
            details.pack_start(row, False, False, 0)
        body_box.pack_start(details, False, False, 0)
        card.pack_start(body_box, False, False, 0)

        # Dos botones del mismo ancho: rojo (borra) y verde (guarda).
        buttons = Gtk.Box(spacing=10, homogeneous=True)
        buttons.get_style_context().add_class("pf-close-actions")

        def action_button(icon, text, css):
            button = Gtk.Button()
            inner = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
            image = icon if isinstance(icon, Gtk.Widget) else Gtk.Image.new_from_icon_name(
                icon, Gtk.IconSize.BUTTON)
            inner.pack_start(image, False, False, 0)
            inner.pack_start(Gtk.Label(label=text), False, False, 0)
            button.add(inner)
            button.get_style_context().add_class(css)
            return button

        discard = action_button("user-trash-symbolic", T("Cerrar sin guardar"), "pf-btn-discard")
        save = action_button(_floppy(16), T("Guardar preset"), "pf-btn-save")
        save_arrow = Gtk.Image.new_from_icon_name("go-next-symbolic", Gtk.IconSize.BUTTON)
        save.get_child().pack_start(save_arrow, False, False, 0)   # → abre el otro modal
        discard.connect("clicked", lambda *_: dialog.response(Gtk.ResponseType.REJECT))
        save.connect("clicked", lambda *_: dialog.response(Gtk.ResponseType.ACCEPT))
        buttons.pack_start(discard, True, True, 0)
        buttons.pack_start(save, True, True, 0)
        card.pack_start(buttons, False, False, 0)

        save.set_can_default(True)
        dialog.set_default(save)               # Enter = ir a guardar
        dialog.show_all()
        save.grab_focus()
        self._close_width = dialog.get_preferred_width()[1]   # el segundo modal usa el mismo ancho
        answer = dialog.run()
        dialog.destroy()
        return {Gtk.ResponseType.ACCEPT: "save", Gtk.ResponseType.REJECT: "discard"}.get(answer, "cancel")

    def _close_save_dialog(self):
        """Modal 2 «Guardar preset». Devuelve "saved", "back" (Volver / X / Esc) o "cancel"."""
        dialog, area = self._new_close_dialog()
        BACK = 1
        size = self.selected_size()
        # Misma estructura que el aviso: tarjeta de 480, franja de color, cuerpo y dos botones.
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.get_style_context().add_class("pf-close-card")
        card.set_size_request(max(480, getattr(self, "_close_width", 480)), -1)
        area.pack_start(card, True, True, 0)

        header = Gtk.Box(spacing=12)
        header.get_style_context().add_class("pf-close-header")
        header.get_style_context().add_class("pf-close-header-save")
        icon = _floppy(24)
        header.pack_start(icon, False, False, 0)
        header.pack_start(_label(T("Guardar preset"), "pf-close-title"), True, True, 0)
        back_x = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.BUTTON)
        back_x.get_style_context().add_class("pf-close-x")
        back_x.set_tooltip_text(T("Volver"))
        back_x.get_accessible().set_name(T("Volver"))
        header.pack_end(back_x, False, False, 0)
        card.pack_start(header, False, False, 0)

        body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        body.get_style_context().add_class("pf-close-body")

        field = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        field_label = _label(T("Nombre del preset"), "pf-field-label")
        entry = Gtk.Entry()
        entry.get_style_context().add_class("pf-save-entry")
        entry.get_style_context().add_class("pf-entry-ok")
        entry.set_text(self.loaded_preset or self.name_entry.get_text().strip())
        entry.set_placeholder_text(T("Ej.: Botan"))
        field_label.set_mnemonic_widget(entry)
        field.pack_start(field_label, False, False, 0)
        field.pack_start(entry, False, False, 0)
        warn_row = Gtk.Box(spacing=8)
        warn_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic", Gtk.IconSize.MENU)
        warn_icon.get_style_context().add_class("pf-save-warn")
        warn_icon.set_valign(Gtk.Align.START)
        warn_text = _label("", "pf-save-warn", wrap=True)
        warn_text.set_max_width_chars(44)  # que el aviso no ensanche el modal
        warn_row.pack_start(warn_icon, False, False, 0)
        warn_row.pack_start(warn_text, True, True, 0)
        warn_row.set_no_show_all(True)
        field.pack_start(warn_row, False, False, 0)
        body.pack_start(field, False, False, 0)

        # Grilla: cada cursor como va a quedar, al tamaño elegido. Las situaciones sin cursor
        # muestran el del sistema (es el que se usa en ese caso).
        body.pack_start(_label(T("Así van a quedar ({size} px)", size=size), "pf-field-label"),
                        False, False, 0)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class("pf-close-list")
        box.get_style_context().add_class("pf-thumb-box")
        grid = Gtk.Grid(column_spacing=8, row_spacing=8, column_homogeneous=True)
        CELL, INNER = 72, 60
        for i, role in enumerate(roles.ROLES):
            card_ = self.cards[role.key]
            cell = Gtk.Box()
            cell.set_size_request(CELL, CELL)
            ctx = cell.get_style_context()
            ctx.add_class("pf-thumb")
            pb = None
            if card_.source is None:
                ctx.add_class("pf-thumb-system")
                cell.set_tooltip_text(T("{role} (cursor del sistema)", role=T(role.label)))
                found = theme.system_cursor_image(role.xnames[0], size)
                if found is not None:
                    w, h, rgba = found
                    pb = theme.rgba_to_pixbuf(w, h, rgba)
            else:
                cell.set_tooltip_text(T(role.label))
                if self._signature(card_) != self._baseline.get(role.key):
                    ctx.add_class("pf-thumb-changed")
                f = card_.source.effective_frames()[0]
                sf = theme.frame_for_size(f, max(f.width, f.height), size)
                pb = theme.rgba_to_pixbuf(sf.width, sf.height, sf.rgba)
            if pb is not None:
                w, h = pb.get_width(), pb.get_height()
                if max(w, h) > INNER:              # sólo se achica si no entra en el recuadro
                    k = INNER / max(w, h)
                    pb = pb.scale_simple(max(1, round(w * k)), max(1, round(h * k)),
                                         GdkPixbuf.InterpType.HYPER)
                cell.set_center_widget(Gtk.Image.new_from_pixbuf(pb))
            grid.attach(cell, i % 5, i // 5, 1, 1)
        box.pack_start(grid, False, False, 0)
        body.pack_start(box, False, False, 0)
        card.pack_start(body, False, False, 0)

        foot = Gtk.Box(spacing=10, homogeneous=True)
        foot.get_style_context().add_class("pf-close-actions")
        back = Gtk.Button()
        back_box = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        back_box.pack_start(Gtk.Image.new_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON),
                            False, False, 0)
        back_box.pack_start(Gtk.Label(label=T("Volver")), False, False, 0)
        back.add(back_box)
        back.get_style_context().add_class("pf-btn-back")
        confirm = Gtk.Button()
        confirm_box = Gtk.Box(spacing=8, halign=Gtk.Align.CENTER)
        confirm_icon = _floppy(16)
        confirm_box.pack_start(confirm_icon, False, False, 0)
        confirm_label = Gtk.Label(label=T("Guardar y cerrar"))
        confirm_box.pack_start(confirm_label, False, False, 0)
        confirm.add(confirm_box)
        confirm.get_style_context().add_class("pf-btn-save")
        foot.pack_start(back, True, True, 0)
        foot.pack_start(confirm, True, True, 0)
        card.pack_start(foot, False, False, 0)

        def check_name(*_):
            name = entry.get_text().strip()
            exists = bool(name) and presets.exists(name)
            warn_row.set_visible(exists)
            warn_icon.show()
            warn_text.show()
            if exists:
                warn_text.set_text(T("Ya existe un preset «{name}». Si seguís, se reemplaza por esta "
                                     "combinación.", name=theme.safe_name(name)))
            # «Reemplazar» corto: así el panel no se ensancha cuando aparece el aviso.
            confirm_label.set_text(T("Reemplazar") if exists else T("Guardar y cerrar"))
            confirm.get_style_context().remove_class("pf-btn-replace" if not exists else "pf-btn-save")
            confirm.get_style_context().add_class("pf-btn-replace" if exists else "pf-btn-save")
            ectx = entry.get_style_context()   # color del borde: verde o ámbar
            ectx.remove_class("pf-entry-ok" if exists else "pf-entry-warn")
            ectx.add_class("pf-entry-warn" if exists else "pf-entry-ok")
            confirm.set_sensitive(bool(name))   # sólo se puede guardar con un nombre escrito
            pixbuf = _floppy(16, "#0f2a1a" if name else "#6f6f7a").get_pixbuf()
            if pixbuf is not None:
                confirm_icon.set_from_pixbuf(pixbuf)

        def do_save(*_):
            name = entry.get_text().strip()
            sources = {k: c.source for k, c in self.cards.items() if c.source}
            if not name or not sources:
                return
            try:
                saved = presets.save_preset(name, self.selected_size(), sources)
            except Exception as exc:  # noqa: BLE001
                warn_row.show()
                warn_text.set_text(T("No se pudo guardar el preset: {error}", error=exc))
                return
            if not self.name_entry.get_text().strip():
                self.name_entry.set_text(saved)
            self._set_loaded_preset(saved)
            self._unsaved = False
            self._reset_baseline()
            dialog.response(Gtk.ResponseType.ACCEPT)

        entry.connect("changed", check_name)
        entry.connect("activate", do_save)     # Enter en el nombre = guardar y cerrar
        confirm.connect("clicked", do_save)
        back.connect("clicked", lambda *_: dialog.response(BACK))
        back_x.connect("clicked", lambda *_: dialog.response(BACK))

        def on_key(_w, event):
            if event.keyval == Gdk.KEY_Escape:   # Esc = Volver al aviso
                dialog.response(BACK)
                return True
            return False

        dialog.connect("key-press-event", on_key)
        dialog.show_all()
        check_name()
        entry.grab_focus()
        entry.select_region(0, -1)
        answer = dialog.run()
        dialog.destroy()
        if answer == Gtk.ResponseType.ACCEPT:
            return "saved"
        if answer == BACK:
            return "back"
        return "cancel"

    def _on_key_press(self, _widget, event):
        card = self.editing_card
        if card is None:
            return False
        if event.keyval == Gdk.KEY_Escape:
            card.stop_editing()
            return True
        moves = {Gdk.KEY_Left: (-1, 0), Gdk.KEY_Right: (1, 0), Gdk.KEY_Up: (0, -1), Gdk.KEY_Down: (0, 1)}
        if event.keyval in moves and not isinstance(self.get_focus(), Gtk.Entry):
            step = 5 if event.state & Gdk.ModifierType.SHIFT_MASK else 1
            dx, dy = moves[event.keyval]
            card.nudge(dx * step, dy * step)
            return True
        return False

    def _apply_columns(self, columns):
        # Solo el máximo: el mínimo queda en 1 para que la ventana se pueda achicar.
        for flow in self.flows:
            flow.set_max_children_per_line(columns)
        return False

    # -------------------------------------------------------------- armado
    def _build_topbar(self):
        bar = Gtk.Box(spacing=14)
        bar.get_style_context().add_class("pf-topbar")

        logo = Gtk.Box()
        logo.get_style_context().add_class("pf-logo")
        logo.set_valign(Gtk.Align.CENTER)
        logo.set_size_request(36, 36)
        img = _logo_image()
        img.set_halign(Gtk.Align.CENTER)
        img.set_valign(Gtk.Align.CENTER)
        logo.set_center_widget(img)
        bar.pack_start(logo, False, False, 0)

        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        titles.set_valign(Gtk.Align.CENTER)
        titles.pack_start(_label(APP_NAME, "pf-app-title"), False, False, 0)
        titles.pack_start(_label(T("Armá y aplicá tu tema de cursores"), "pf-muted",
                                 "pf-app-subtitle"), False, False, 0)
        bar.pack_start(titles, False, False, 0)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        bar.pack_start(spacer, True, True, 0)

        progress = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        progress.set_valign(Gtk.Align.CENTER)
        self.count_label = _label("", "pf-muted", xalign=1.0)
        self.level = Gtk.LevelBar()
        self.level.set_mode(Gtk.LevelBarMode.CONTINUOUS)
        self.level.set_min_value(0)
        self.level.set_max_value(len(roles.ROLES))
        for offset in ("low", "high", "full"):
            self.level.remove_offset_value(offset)
        self.level.set_size_request(180, 6)
        self.level.get_style_context().add_class("pf-progress")
        progress.pack_start(self.count_label, False, False, 0)
        progress.pack_start(self.level, False, False, 0)
        bar.pack_start(progress, False, False, 6)

        self.presets_button = Gtk.MenuButton()
        presets_box = Gtk.Box(spacing=6)
        self.presets_label = Gtk.Label(label=T("Presets"))
        self.presets_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.presets_label.set_max_width_chars(18)
        self.presets_label.set_width_chars(7)  # que «Presets» no quede en «…» en ventanas angostas
        presets_box.pack_start(self.presets_label, False, False, 0)
        presets_box.pack_start(Gtk.Image.new_from_icon_name("pan-down-symbolic", Gtk.IconSize.BUTTON),
                               False, False, 0)
        self.presets_button.add(presets_box)
        self.presets_button.set_tooltip_text(T("Tus combinaciones de cursores guardadas"))
        self.presets_popover = self._new_popover(self.presets_button)
        self.presets_button.set_popover(self.presets_popover)
        self.presets_button.connect("toggled", self._on_presets_toggled)
        self.presets_button.set_valign(Gtk.Align.CENTER)
        bar.pack_start(self.presets_button, False, False, 0)

        apply_box = Gtk.Box(spacing=8)
        self.spinner = Gtk.Spinner()
        self.spinner.set_no_show_all(True)
        apply_box.pack_start(self.spinner, False, False, 0)
        apply_box.pack_start(Gtk.Label(label=T("Aplicar cursor")), False, False, 0)
        self.apply_button = Gtk.Button()
        self.apply_button.add(apply_box)
        self.apply_button.get_style_context().add_class("pf-primary")
        self.apply_button.connect("clicked", self._on_apply)
        self.apply_button.set_valign(Gtk.Align.CENTER)
        bar.pack_start(self.apply_button, False, False, 0)

        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic",
                                                                Gtk.IconSize.BUTTON))
        self.menu_button.set_tooltip_text(T("Más opciones"))
        self.menu_button.get_accessible().set_name(T("Más opciones"))
        self.menu_button.get_style_context().add_class("pf-icon-button")
        self.menu_popover = self._new_popover(self.menu_button)
        self.menu_button.set_popover(self.menu_popover)
        self.menu_button.connect("toggled", self._on_menu_toggled)
        self.menu_button.set_valign(Gtk.Align.CENTER)
        bar.pack_start(self.menu_button, False, False, 0)
        return bar

    def _new_popover(self, relative):
        popover = Gtk.Popover.new(relative)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.get_style_context().add_class("pf-popover")
        return popover

    def _build_panel(self):
        """Panel del tema en una fila compacta: cada título con su control al lado."""
        panel = Gtk.Box(spacing=24)
        panel.get_style_context().add_class("pf-panel")

        def field(title, widget):
            row = Gtk.Box(spacing=10)
            row.set_valign(Gtk.Align.CENTER)
            if title:
                lbl = _label(title, "pf-field-label")
                lbl.set_valign(Gtk.Align.CENTER)
                lbl.set_mnemonic_widget(widget)
                row.pack_start(lbl, False, False, 0)
            widget.set_valign(Gtk.Align.CENTER)
            row.pack_start(widget, False, False, 0)
            panel.pack_start(row, False, False, 0)
            return row



        self.name_entry = Gtk.Entry()
        self.name_entry.set_placeholder_text(T("Ej.: Botan"))
        self.name_entry.get_accessible().set_name(T("Nombre del tema"))
        self.name_entry.set_width_chars(28)
        self.name_entry.connect("changed", self._mark_preset_dirty)
        field(T("Nombre del tema"), self.name_entry)

        self.size_combo = Gtk.ComboBoxText()
        for size, label in SIZE_CHOICES:
            self.size_combo.append(str(size), T(label))
        _current_theme, current_size = theme.current_cursor()
        best = min(SIZE_CHOICES, key=lambda c: abs(c[0] - (current_size or 24)))[0]
        self.size_combo.set_active_id(str(max(best, DEFAULT_SIZE)))
        self.size_combo.connect("changed", lambda *_: (self._refresh_test_cursors(),
                                                       self._mark_preset_dirty()))
        self.size_combo.get_accessible().set_name(T("Tamaño"))
        field(T("Tamaño"), self.size_combo)
        return panel

    def _build_dropzone(self):
        """Recuadro para abrir o soltar la carpeta. Se oculta cuando ya hay cursores."""
        self.drop_revealer = Gtk.Revealer()
        self.drop_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        zone = Gtk.Box(spacing=12)
        zone.get_style_context().add_class("pf-dropzone")
        inner = Gtk.Box(spacing=12, halign=Gtk.Align.CENTER, hexpand=True)
        inner.pack_start(Gtk.Image.new_from_icon_name("folder-open-symbolic", Gtk.IconSize.DND),
                         False, False, 0)
        inner.pack_start(_label(T("Abrir carpeta o arrastrala acá"), "pf-bold"), False, False, 0)
        zone.pack_start(inner, True, True, 0)
        self.dropzone = zone

        events = Gtk.EventBox()
        events.add(zone)
        events.set_tooltip_text(T("Hacé clic para elegir la carpeta del pack, o arrastrala "
                                  "y soltala sobre la ventana: los cursores se asignan solos"))
        events.add_events(Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)
        events.connect("enter-notify-event", lambda *_: self._dropzone_state("pf-hover", True))
        events.connect("leave-notify-event", self._on_dropzone_leave)
        events.connect("button-release-event", self._on_dropzone_click)
        events.connect("realize", self._on_dropzone_realize)
        self.drop_revealer.add(events)
        return self.drop_revealer

    def _dropzone_state(self, cls, on):
        ctx = self.dropzone.get_style_context()
        (ctx.add_class if on else ctx.remove_class)(cls)
        return False

    def _on_dropzone_leave(self, _widget, event):
        if event.detail != Gdk.NotifyType.INFERIOR:
            self._dropzone_state("pf-hover", False)
        return False

    def _on_dropzone_click(self, _widget, event):
        if event.button == 1:
            self._on_open_folder()
        return True

    def _on_dropzone_realize(self, widget):
        window = widget.get_window()
        if window is not None:
            window.set_cursor(Gdk.Cursor.new_from_name(widget.get_display(), "pointer"))

    def _build_toast(self):
        self.toast_revealer = Gtk.Revealer()
        self.toast_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.toast_revealer.set_halign(Gtk.Align.CENTER)
        self.toast_revealer.set_valign(Gtk.Align.END)
        self.toast_revealer.set_margin_bottom(24)
        box = Gtk.Box(spacing=10)
        box.get_style_context().add_class("pf-toast")
        box.pack_start(Gtk.Image.new_from_icon_name("object-select-symbolic", Gtk.IconSize.BUTTON),
                       False, False, 0)
        self.toast_label = _label("")
        box.pack_start(self.toast_label, False, False, 0)
        self.toast_action = Gtk.Button()
        self.toast_action.get_style_context().add_class("pf-toast-action")
        self.toast_action.set_no_show_all(True)
        self.toast_action.connect("clicked", self._on_toast_action)
        self._toast_callback = None
        box.pack_start(self.toast_action, False, False, 0)
        self.toast_revealer.add(box)
        return self.toast_revealer

    # --------------------------------------------------------------- estado
    def selected_size(self):
        return int(self.size_combo.get_active_id() or DEFAULT_SIZE)

    def assigned_count(self):
        return sum(1 for c in self.cards.values() if c.source)

    def _refresh_test_cursors(self):
        for card in self.cards.values():
            card.refresh_test_cursor()

    def on_assignments_changed(self):
        self._update_progress()
        self._mark_preset_dirty()

    @staticmethod
    def _signature(card):
        """Lo que identifica el cursor de una tarjeta: archivo y punto activo."""
        if card.source is None:
            return None
        hotspot = card.source.hotspot
        return (card.source.path, tuple(hotspot) if hotspot is not None else None)

    def _reset_baseline(self):
        self._baseline = {k: self._signature(c) for k, c in self.cards.items()}

    def changed_count(self):
        """Cursores distintos de la última vez que se aplicó, guardó o cargó."""
        return sum(1 for k, c in self.cards.items() if self._signature(c) != self._baseline.get(k))

    def _mark_preset_dirty(self, *_):
        if not self._loading_preset:
            self._unsaved = True
        if self.loaded_preset and not self._loading_preset and not self._preset_dirty:
            self._preset_dirty = True
            self._update_presets_label()

    def _update_presets_label(self):
        if not hasattr(self, "presets_label"):
            return
        if self.loaded_preset:
            text = self.loaded_preset + (" •" if self._preset_dirty else "")
            tip = T("Preset «{name}» con cambios sin guardar", name=self.loaded_preset) \
                if self._preset_dirty else T("Preset «{name}» cargado", name=self.loaded_preset)
        else:
            text, tip = T("Presets"), T("Tus combinaciones de cursores guardadas")
        self.presets_label.set_text(text)
        self.presets_button.set_tooltip_text(tip)

    def _update_progress(self):
        if not hasattr(self, "drop_revealer"):
            return
        n = self.assigned_count()
        total = len(roles.ROLES)
        self.count_label.set_markup(T("<b>{n}</b> de {total} asignados", n=n, total=total))
        self.level.set_value(n)
        can_apply = n > 0 and not self._busy
        self.apply_button.set_sensitive(can_apply)
        self.apply_button.set_tooltip_text(None if n else T("Asigná al menos un cursor para aplicar"))
        self.drop_revealer.set_reveal_child(n == 0)

    def _set_loaded_preset(self, name):
        self.loaded_preset = name
        self._preset_dirty = False
        self._update_presets_label()

    def show_toast(self, text, action=None):
        """Aviso flotante. ``action`` = (texto del botón, función), p. ej. «Deshacer»."""
        self.toast_label.set_text(text)
        self._toast_callback = action[1] if action else None
        if action:
            self.toast_action.set_label(action[0])
            self.toast_action.show()
        else:
            self.toast_action.hide()
        # Sin botón deja pasar los clics; con botón tiene que poder recibirlos.
        self.main_overlay.set_overlay_pass_through(self.toast_revealer, action is None)
        self.toast_revealer.set_reveal_child(True)
        if self._toast_timer:
            GLib.source_remove(self._toast_timer)
        self._toast_timer = GLib.timeout_add(TOAST_ACTION_MS if action else TOAST_MS, self._hide_toast)

    def _on_toast_action(self, *_):
        callback, self._toast_callback = self._toast_callback, None
        self._hide_toast()
        if callback:
            callback()

    def _hide_toast(self):
        if self._toast_timer:
            GLib.source_remove(self._toast_timer)
        self._toast_timer = 0
        self._toast_callback = None
        self.toast_revealer.set_reveal_child(False)
        self.main_overlay.set_overlay_pass_through(self.toast_revealer, True)
        return False

    def remove_with_undo(self, card):
        """Quita el cursor de una tarjeta y ofrece «Deshacer» unos segundos."""
        previous = card.source
        if previous is None:
            return
        auto = card.auto_hotspot
        card.set_source(None)

        def undo():
            card.set_source(previous, suggest=False)
            card.auto_hotspot = auto
            card._update_suggested_chip()

        self.show_toast(T("Se quitó «{role}»", role=T(card.role.label)), (T("Deshacer"), undo))

    def show_error(self, text):
        self.show_message(text, Gtk.MessageType.ERROR)

    def show_message(self, text, kind=Gtk.MessageType.INFO):
        """Mensajes que conviene leer con calma (errores y detalles de la importación)."""
        self.info_label.set_text(text)
        self.infobar.set_message_type(kind)
        self.infobar.set_revealed(True)

    def _confirm(self, title, detail, ok_label, destructive=False, parent=None):
        dialog = Gtk.MessageDialog(transient_for=parent or self, modal=True,
                                   message_type=Gtk.MessageType.QUESTION,
                                   buttons=Gtk.ButtonsType.NONE, text=title)
        dialog.get_style_context().add_class("pf-dialog")
        dialog.format_secondary_text(detail)
        dialog.add_buttons(T("Cancelar"), Gtk.ResponseType.CANCEL, ok_label, Gtk.ResponseType.OK)
        if destructive:
            dialog.get_widget_for_response(Gtk.ResponseType.OK).get_style_context().add_class(
                "destructive-action")
        answer = dialog.run()
        dialog.destroy()
        return answer == Gtk.ResponseType.OK

    # ------------------------------------------------------------ importar
    def import_paths(self, paths, from_drop=False):
        folders = [p for p in paths if os.path.isdir(p)]
        if folders:
            n = self.assigned_count()
            if from_drop and n and not self._confirm(
                    T("¿Reemplazar los cursores?"),
                    T("Se van a reemplazar los {n} cursores asignados por los de la carpeta «{folder}».",
                      n=n, folder=os.path.basename(os.path.normpath(folders[0]))),
                    T("Reemplazar")):
                return False
            self.import_folder(folders[0])
            return False
        assigned = 0
        unknown = []
        for path in paths:
            key = roles.guess_role_by_name(os.path.basename(path))
            if key and self.cards[key].load_path(path):
                assigned += 1
            else:
                unknown.append(os.path.basename(path))
        if unknown:
            self.show_message(T("Se asignaron {n} archivo(s). No supe dónde va: {files}. "
                                "Arrastralos al cuadro que corresponde.",
                                n=assigned, files=", ".join(unknown)),
                              Gtk.MessageType.WARNING)
        else:
            self.show_toast(T("Se asignaron {n} archivo(s)", n=assigned))
        return False

    def import_folder(self, folder):
        """Ubica los archivos y los lee en segundo plano (packs pesados no traban la ventana)."""
        if self._importing:
            return
        try:
            assignment, leftovers, where = roles.auto_assign(folder)
        except OSError as exc:
            self.show_error(T("No se pudo leer la carpeta: {error}", error=exc))
            return
        if not assignment and not leftovers:
            self.show_message(T("En esa carpeta no hay archivos de cursor "
                                "(.ani, .cur, .ico, .png, .svg)."), Gtk.MessageType.WARNING)
            return
        self.last_folder = where
        self._importing = True
        self._busy = True
        self._update_progress()
        self.spinner.show()
        self.spinner.start()

        def work():
            loaded, failed = {}, []
            for key, path in assignment.items():
                try:
                    loaded[key] = theme.load_source(path)
                except Exception:  # noqa: BLE001
                    failed.append(os.path.basename(path))
            GLib.idle_add(self._finish_import, folder, assignment, leftovers, loaded, failed)

        threading.Thread(target=work, daemon=True).start()

    def _finish_import(self, folder, assignment, leftovers, loaded, failed):
        self._importing = False
        self._busy = False
        self.spinner.stop()
        self.spinner.hide()
        for role in roles.ROLES:
            self.cards[role.key].set_source(loaded.get(role.key))

        # Nombre sugerido: el de la carpeta sin el sufijo de Google Drive. No pisa un
        # nombre que hayas escrito a mano.
        name = DRIVE_SUFFIX.sub("", os.path.basename(os.path.normpath(folder))) or "MiCursor"
        current = self.name_entry.get_text().strip()
        if not current or current == self._auto_name:
            self._auto_name = theme.safe_name(name)
            self.name_entry.set_text(self._auto_name)
        self._set_loaded_preset(None)

        n = len(loaded)
        details = []
        missing = [T(r.label) for r in roles.ROLES if r.key not in loaded]
        if failed:
            details.append(T("No se pudieron leer: {files}.", files=", ".join(failed)))
        if missing:
            details.append(T("Sin archivo (usarán los del sistema): {roles}.", roles=", ".join(missing)))
        if leftovers:
            details.append(T("Archivos sin ubicar: {files}. Podés arrastrarlos a un cuadro.",
                             files=", ".join(os.path.basename(p) for p in leftovers)))
        if any(c.auto_hotspot for c in self.cards.values()):
            details.append(T("Algunos puntos activos (cruz roja) son sugeridos: revisalos."))
        if details:
            self.show_message(T("Se ordenaron {n} de {total} cursores.", n=n, total=len(roles.ROLES))
                              + " " + " ".join(details),
                              Gtk.MessageType.WARNING if (failed or leftovers or missing)
                              else Gtk.MessageType.INFO)
        else:
            self.infobar.set_revealed(False)
        self._update_progress()
        self.show_toast(T("Se ordenaron {n} de {total} cursores", n=n, total=len(roles.ROLES)))
        return False

    def _on_open_folder(self, *_):
        dialog = Gtk.FileChooserNative.new(T("Elegí la carpeta del pack de cursores"), self,
                                           Gtk.FileChooserAction.SELECT_FOLDER,
                                           T("Abrir"), T("Cancelar"))
        if self.last_folder:
            dialog.set_current_folder(self.last_folder)
        if dialog.run() == Gtk.ResponseType.ACCEPT:
            self.import_folder(dialog.get_filename())
        dialog.destroy()

    def _on_window_drop(self, _w, _ctx, _x, _y, data, _info, _time):
        self._dropzone_state("pf-drop", False)
        paths = _paths_from_selection(data)
        if paths:
            GLib.idle_add(self.import_paths, paths, True)

    # -------------------------------------------------------------- aplicar
    def _on_apply(self, *_):
        if self._busy:
            return  # todavía se está leyendo una carpeta o armando otro tema
        if not self.name_entry.get_text().strip():
            self.show_message(T("Escribí un nombre para el tema antes de aplicarlo."),
                              Gtk.MessageType.WARNING)
            self.name_entry.grab_focus()
            return
        name = theme.safe_name(self.name_entry.get_text())
        self.name_entry.set_text(name)
        if theme.theme_exists_foreign(name):
            self.show_error(T("Ya hay un tema llamado «{name}» que no es de esta app. "
                              "Elegí otro nombre.", name=name))
            return
        # Copias: si mientras se arma el tema movés un punto activo, no se mezcla.
        assignments = {k: c.source.snapshot() for k, c in self.cards.items() if c.source}
        if not assignments:
            return
        if "normal" not in assignments and not self._confirm(
                T("No elegiste la «Selección normal»"),
                T("Es el cursor que más se ve. ¿Aplicar igual? Se usará el del sistema para ese caso."),
                T("Aplicar igual")):
            return
        size = self.selected_size()
        inherits, _ = theme.previous_cursor()
        if theme.safe_name(inherits) == name:
            inherits = "Adwaita"

        self._busy = True
        self._update_progress()
        self.spinner.show()
        self.spinner.start()

        def work():
            try:
                theme.build_theme(name, assignments, inherits=inherits)
                error = None
            except Exception as exc:  # noqa: BLE001
                error = exc
            GLib.idle_add(self._apply_done, name, size, error)

        threading.Thread(target=work, daemon=True).start()

    def _apply_done(self, name, size, error):
        self._busy = False
        self.spinner.stop()
        self.spinner.hide()
        self._update_progress()
        if error is not None:
            self.show_error(T("No se pudo crear el tema: {error}", error=error))
            return False
        try:
            theme.apply_theme(name, size)
        except Exception as exc:  # noqa: BLE001
            self.show_message(T("El tema se creó pero no se pudo activar: {error}. Elegilo en "
                                "Configuración del sistema → Temas → Puntero del ratón.", error=exc),
                              Gtk.MessageType.WARNING)
            return False
        self._unsaved = False
        self._reset_baseline()
        self.show_toast(T("Cursor «{name}» aplicado", name=name))
        return False

    # -------------------------------------------------------------- presets
    def _clear_popover(self, popover):
        child = popover.get_child()
        if child is not None:
            popover.remove(child)
            child.destroy()

    def _on_presets_toggled(self, button):
        if not button.get_active():
            return
        popover = self.presets_popover
        self._clear_popover(popover)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_size_request(320, -1)
        title = _label(T("PRESETS GUARDADOS"), "pf-popover-title")
        title.set_margin_start(10)
        title.set_margin_top(4)
        box.pack_start(title, False, False, 0)

        saved = presets.list_presets_info()
        if saved:
            listbox = Gtk.ListBox()
            listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            listbox.set_activate_on_single_click(True)
            for info in saved:
                loaded = (self.loaded_preset is not None
                          and theme.safe_name(info["name"]) == theme.safe_name(self.loaded_preset))
                listbox.add(PresetRow(info, loaded, loaded and self._preset_dirty))
            listbox.connect("row-activated", self._on_preset_row)
            scroller = Gtk.ScrolledWindow()
            scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scroller.set_propagate_natural_height(True)
            scroller.set_max_content_height(360)
            scroller.add(listbox)
            box.pack_start(scroller, False, False, 0)
        else:
            empty = _label(T("Todavía no guardaste ningún preset"), "pf-muted")
            empty.set_margin_start(10)
            empty.set_margin_top(6)
            empty.set_margin_bottom(6)
            box.pack_start(empty, False, False, 0)

        box.pack_start(Gtk.Separator(), False, False, 0)

        save_icon = Gtk.Image.new_from_icon_name("document-save-symbolic", Gtk.IconSize.BUTTON)
        save_icon.get_style_context().add_class("pf-save-icon")
        save = self._menu_button_item(save_icon, T("Guardar preset actual…"),
                                      T("Guarda los cuadros, el nombre y el tamaño"),
                                      self._on_save_preset)
        save.set_sensitive(self.assigned_count() > 0)
        box.pack_start(save, False, False, 0)

        box.show_all()
        popover.add(box)

    def _on_preset_row(self, _listbox, row):
        self.presets_popover.popdown()
        if self._load_preset(row.preset_name):
            self.show_toast(T("Preset “{name}” cargado", name=row.preset_name))

    def _ask_preset_name(self, default):
        dialog = Gtk.Dialog(title=T("Guardar preset"), transient_for=self, modal=True)
        dialog.get_style_context().add_class("pf-dialog")
        dialog.add_buttons(T("Cancelar"), Gtk.ResponseType.CANCEL, T("Guardar"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_spacing(8)
        area.set_border_width(14)
        area.add(_label(T("Nombre del preset:")))
        entry = Gtk.Entry(text=default, activates_default=True)
        entry.set_placeholder_text(T("Ej.: Botan"))
        area.add(entry)
        note = _label(T("Se guarda una copia de los cursores, sus puntos activos, el nombre y el "
                        "tamaño. No cambia el cursor que estás usando."), "pf-muted", wrap=True)
        note.set_max_width_chars(42)
        area.add(note)
        dialog.show_all()
        answer = dialog.run()
        name = entry.get_text().strip()
        dialog.destroy()
        return name if answer == Gtk.ResponseType.OK and name else None

    def _on_save_preset(self, *_):
        self.presets_popover.popdown()
        sources = {k: c.source for k, c in self.cards.items() if c.source}
        if not sources:
            return
        name = self._ask_preset_name(self.loaded_preset or self.name_entry.get_text().strip())
        if not name:
            return
        if presets.exists(name) and not self._confirm(
                T("Ya existe el preset «{name}»", name=theme.safe_name(name)),
                T("¿Querés reemplazarlo por la combinación actual?"), T("Reemplazar")):
            return
        try:
            saved = presets.save_preset(name, self.selected_size(), sources)
        except Exception as exc:  # noqa: BLE001
            self.show_error(T("No se pudo guardar el preset: {error}", error=exc))
            return
        if not self.name_entry.get_text().strip():
            self.name_entry.set_text(saved)
        self._set_loaded_preset(saved)
        self._unsaved = False
        self._reset_baseline()
        self.show_toast(T("Preset “{name}” guardado", name=saved))
        return True

    def _load_preset(self, name):
        try:
            title, size, entries = presets.load_preset(name)
        except Exception as exc:  # noqa: BLE001
            self.show_error(T("No se pudo abrir el preset: {error}", error=exc))
            return False
        self._loading_preset = True
        failed = []
        for role in roles.ROLES:
            card = self.cards[role.key]
            entry = entries.get(role.key)
            if entry is None:
                card.set_source(None)
                continue
            path, hotspot = entry
            try:
                source = theme.load_source(path)
            except Exception:  # noqa: BLE001
                failed.append(T(role.label))
                card.set_source(None)
                continue
            source.hotspot = hotspot
            card.set_source(source, suggest=False)
        self.name_entry.set_text(title)
        if str(size) in [str(s) for s, _ in SIZE_CHOICES]:
            self.size_combo.set_active_id(str(size))
        self._loading_preset = False
        self._unsaved = False
        self._reset_baseline()
        self._set_loaded_preset(title)
        self.infobar.set_revealed(False)
        if failed:
            self.show_message(T("Se abrió el preset, pero faltan archivos de: {roles}",
                                roles=", ".join(failed)),
                              Gtk.MessageType.WARNING)
        return True

    # ----------------------------------------------------------------- menú
    def _menu_button_item(self, icon_widget, title, subtitle, callback, danger=False):
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.get_style_context().add_class("pf-menuitem")
        box = Gtk.Box(spacing=12)
        icon_widget.set_valign(Gtk.Align.CENTER)
        box.pack_start(icon_widget, False, False, 0)
        texts = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title_label = _label(title, "pf-bold")
        if danger:
            title_label.get_style_context().add_class("pf-danger")
            button.get_style_context().add_class("pf-danger")
        texts.pack_start(title_label, False, False, 0)
        texts.pack_start(_label(subtitle, "pf-muted"), False, False, 0)
        box.pack_start(texts, True, True, 0)
        button.add(box)
        button.get_accessible().set_name(title)
        button.connect("clicked", callback)
        return button

    def _on_menu_toggled(self, button):
        if not button.get_active():
            return
        popover = self.menu_popover
        self._clear_popover(popover)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_size_request(320, -1)

        def icon(name):
            return Gtk.Image.new_from_icon_name(name, Gtk.IconSize.LARGE_TOOLBAR)

        box.pack_start(self._menu_button_item(icon("folder-open-symbolic"), T("Abrir otra carpeta…"),
                                              T("También podés arrastrarla a la ventana"),
                                              self._on_menu_open_folder), False, False, 0)
        box.pack_start(Gtk.Separator(), False, False, 0)
        restore = self._menu_button_item(icon("edit-undo-symbolic"), T("Volver al cursor anterior"),
                                         T("Restaura el que tenías antes de aplicar"),
                                         self._on_restore)
        restore.set_sensitive(theme.has_previous())
        box.pack_start(restore, False, False, 0)
        delete = self._menu_button_item(icon("user-trash-symbolic"), T("Borrar temas creados…"),
                                        T("Elegí cuáles quitar del sistema"), self._on_delete_theme)
        delete.set_sensitive(bool(theme.list_own_themes()))
        box.pack_start(delete, False, False, 0)
        box.pack_start(Gtk.Separator(), False, False, 0)
        box.pack_start(self._menu_button_item(icon("edit-clear-all-symbolic"), T("Empezar desde cero"),
                                              T("Vacía los 15 cuadros, el nombre y el tamaño"),
                                              self._on_clear_all, danger=True), False, False, 0)
        box.pack_start(Gtk.Separator(), False, False, 0)
        box.pack_start(self._menu_button_item(icon("preferences-system-symbolic"), T("Ajustes"),
                                              T("Idioma de la app"), self._on_settings),
                       False, False, 0)
        box.pack_start(self._menu_button_item(icon("help-about-symbolic"), T("Acerca de Cursify"),
                                              T("Versión {version}", version=__version__),
                                              self._on_about),
                       False, False, 0)
        box.show_all()
        popover.add(box)

    def _on_menu_open_folder(self, *_):
        self.menu_popover.popdown()
        self._on_open_folder()

    def _on_restore(self, *_):
        self.menu_popover.popdown()
        if not theme.has_previous():
            self.show_message(T("Todavía no aplicaste ningún cursor con esta app, "
                                "así que no hay nada para restaurar."))
            return
        previous, size = theme.previous_cursor()
        if not self._confirm(T("¿Volver al cursor anterior?"),
                             T("Se va a activar «{name}» ({size} px), el cursor que tenías antes "
                               "de aplicar uno con esta app.", name=previous, size=size),
                             T("Volver")):
            return
        restored = theme.restore_previous()
        if restored:
            self.show_toast(T("Volviste al cursor «{name}»", name=restored))

    def _on_delete_theme(self, *_):
        """Lista tipo tabla de los temas creados, con un botón de borrar por fila."""
        self.menu_popover.popdown()
        dialog = Gtk.Dialog(title=T("Borrar temas creados"), transient_for=self, modal=True)
        dialog.get_style_context().add_class("pf-dialog")
        dialog.set_default_size(620, 420)
        dialog.add_button(T("Cerrar"), Gtk.ResponseType.CLOSE)
        area = dialog.get_content_area()
        area.set_spacing(10)
        area.set_border_width(16)
        note = _label(T("Solo aparecen los temas creados con Cursify. Tus presets no se tocan."),
                      "pf-muted", wrap=True)
        area.pack_start(note, False, False, 0)

        groups = [Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL) for _ in range(4)]

        def row_box(cells, header=False):
            box = Gtk.Box(spacing=12)
            for i, widget in enumerate(cells):
                if i < 4:
                    groups[i].add_widget(widget)
                box.pack_start(widget, i == 0, True, 0)
            if header:
                box.get_style_context().add_class("pf-table-header")
            return box

        header = row_box([_label(T("Tema"), "pf-field-label"), _label(T("Estado"), "pf-field-label"),
                          _label(T("Cursores"), "pf-field-label"), _label(T("Creado"), "pf-field-label"),
                          Gtk.Box()], header=True)
        header.get_children()[-1].set_size_request(40, -1)
        area.pack_start(header, False, False, 0)

        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        listbox.get_style_context().add_class("pf-table")
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(listbox)
        area.pack_start(scroller, True, True, 0)
        empty = _label(T("No hay temas creados con esta app."), "pf-muted", xalign=0.5)
        empty.set_no_show_all(True)
        area.pack_start(empty, False, False, 8)

        def fill():
            for child in listbox.get_children():
                listbox.remove(child)
            current, _size = theme.current_cursor()
            items = theme.list_own_themes_info()
            for info in items:
                name = info["name"]
                active = theme.safe_name(current) == name
                status = _label(T("En uso") if active else "—",
                                "pf-status-active" if active else "pf-muted")
                when = time.strftime("%d/%m/%Y", time.localtime(info["mtime"])) if info["mtime"] else "—"
                delete = _icon_button("user-trash-symbolic", T("Borrar el tema «{name}»", name=name))
                delete.connect("clicked", lambda _b, n=name, a=active: on_delete(n, a))
                title = _label(name, "pf-bold")
                title.set_ellipsize(Pango.EllipsizeMode.END)
                row = Gtk.ListBoxRow()
                row.set_activatable(False)
                row.add(row_box([title, status, _label(str(info["count"]), xalign=0),
                                 _label(when, "pf-muted"), delete]))
                listbox.add(row)
            listbox.show_all()
            empty.set_visible(not items)
            scroller.set_visible(bool(items))
            header.set_visible(bool(items))

        def on_delete(name, active):
            detail = T("Se borra la carpeta del tema. Tus presets no se tocan.")
            if active:
                detail = T("Es el cursor que estás usando ahora: antes de borrarlo se vuelve al "
                           "cursor anterior.") + " " + detail
            if not self._confirm(T("¿Borrar el tema «{name}»?", name=name), detail, T("Borrar"),
                                 destructive=True, parent=dialog):
                return
            try:
                if active:
                    _current, current_size = theme.current_cursor()
                    if not theme.restore_previous():
                        theme.set_cursor(theme.theme_inherits(name) or "Adwaita", current_size)
                theme.delete_theme(name)
            except Exception as exc:  # noqa: BLE001
                self.show_error(T("No se pudo borrar: {error}", error=exc))
                return
            fill()
            self.show_toast(T("Tema «{name}» borrado", name=name))

        fill()
        dialog.show_all()
        fill()  # vuelve a aplicar la visibilidad después de show_all
        dialog.run()
        dialog.destroy()

    def _on_clear_all(self, *_):
        self.menu_popover.popdown()
        if not self._confirm(T("¿Empezar desde cero?"),
                             T("Se vacían los 15 cuadros, el nombre y el tamaño. "
                               "Tus presets y los temas instalados no se tocan."),
                             T("Empezar de cero"), destructive=True):
            return
        for card in self.cards.values():
            card.set_source(None)
        self.name_entry.set_text("")
        self.size_combo.set_active_id(str(DEFAULT_SIZE))
        self._set_loaded_preset(None)
        self.infobar.set_revealed(False)
        self._unsaved = False
        self._reset_baseline()
        self.show_toast(T("Listo, empezaste desde cero"))

    def _on_settings(self, *_):
        self.menu_popover.popdown()
        dialog = Gtk.Dialog(title=T("Ajustes"), transient_for=self, modal=True)
        dialog.get_style_context().add_class("pf-dialog")
        dialog.add_buttons(T("Cancelar"), Gtk.ResponseType.CANCEL, T("Guardar"), Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)
        area = dialog.get_content_area()
        area.set_spacing(8)
        area.set_border_width(16)
        row = Gtk.Box(spacing=12)
        row.pack_start(_label(T("Idioma"), "pf-field-label"), False, False, 0)
        combo = Gtk.ComboBoxText()
        system = T("español") if i18n.system_language() == "es" else T("inglés")
        combo.append("auto", T("Automático (idioma del sistema: {lang})", lang=system))
        combo.append("es", "Español")
        combo.append("en", "English")
        combo.set_active_id(i18n.language_setting())
        row.pack_start(combo, True, True, 0)
        area.add(row)
        dialog.show_all()
        answer = dialog.run()
        choice = combo.get_active_id()
        dialog.destroy()
        if answer != Gtk.ResponseType.OK or not choice:
            return
        before = i18n.LANG
        i18n.set_language_setting(choice)
        if i18n.LANG != before:
            GLib.idle_add(self.get_application().rebuild_window)

    def export_state(self):
        return {"sources": {k: (c.source, c.auto_hotspot) for k, c in self.cards.items()},
                "name": self.name_entry.get_text(),
                "size": self.size_combo.get_active_id(),
                "preset": self.loaded_preset,
                "dirty": self._preset_dirty,
                "unsaved": self._unsaved,
                "baseline": dict(self._baseline),
                "folder": self.last_folder}

    def import_state(self, state):
        for key, (source, auto) in state["sources"].items():
            card = self.cards[key]
            card.set_source(source, suggest=False)
            card.auto_hotspot = auto
        self.name_entry.set_text(state["name"])
        if state["size"]:
            self.size_combo.set_active_id(state["size"])
        self._set_loaded_preset(state["preset"])
        if state.get("dirty"):
            self._preset_dirty = True
            self._update_presets_label()
        self._unsaved = state.get("unsaved", False)
        self._baseline = state.get("baseline", {})
        self.last_folder = state["folder"]
        self._update_progress()

    def _on_about(self, *_):
        self.menu_popover.popdown()
        about = Gtk.AboutDialog(transient_for=self, modal=True)
        about.set_program_name(APP_NAME)
        about.set_version(__version__)
        about.set_logo_icon_name("input-mouse")
        about.set_comments(T("Convierte packs de cursores de Windows (.ani/.cur) en un tema "
                             "para Linux Mint y lo aplica con un clic."))
        about.run()
        about.destroy()

# Dónde queda la app instalada: con scripts/instalar.sh (usuario) o con el paquete .deb.
INSTALL_DIRS = (os.path.expanduser("~/.local/share/cursify"), "/usr/share/cursify")


def is_installed():
    """True si se ejecuta una copia instalada (y no la carpeta del proyecto)."""
    here = os.path.realpath(ROOT_DIR)
    return any(here == os.path.realpath(d) for d in INSTALL_DIRS)


class CursifyApp(Gtk.Application):
    def __init__(self):
        # La copia del proyecto usa otro identificador: así no choca con la instalada.
        app_id = "ar.akimori.Cursify" if is_installed() else "ar.akimori.Cursify.Dev"
        super().__init__(application_id=app_id)
        self.window = None
        self._pending = []

    def do_startup(self):
        Gtk.Application.do_startup(self)
        settings = Gtk.Settings.get_default()
        if settings is not None:
            settings.set_property("gtk-application-prefer-dark-theme", True)
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider,
                                                 Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def rebuild_window(self):
        """Vuelve a crear la ventana (al cambiar el idioma) conservando lo cargado."""
        old = self.window
        state = old.export_state() if old else None
        geometry = old.get_size() if old else None
        self.window = MainWindow(self)
        if geometry:
            self.window.resize(*geometry)
        self.window.show_all()
        if state:
            self.window.import_state(state)
        self.window.present()
        if old:
            old.destroy()
        self.window.show_toast(T("Idioma cambiado"))
        return False

    def do_activate(self):
        if self.window is None:
            self.window = MainWindow(self)
            self.window.show_all()
        self.window.present()
        if self._pending:
            paths, self._pending = self._pending, []
            GLib.idle_add(self.window.import_paths, paths)


def main(argv=None):
    argv = sys.argv if argv is None else argv
    GLib.set_prgname("cursify")          # nombre de la ventana (StartupWMClass del .desktop)
    GLib.set_application_name(APP_NAME)
    app = CursifyApp()
    app._pending = [os.path.abspath(p) for p in argv[1:] if os.path.exists(p)]
    return app.run(argv[:1])
