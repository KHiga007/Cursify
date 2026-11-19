#!/usr/bin/env bash
# Quita Cursify. Los temas de cursor que creaste quedan en ~/.local/share/icons.
set -euo pipefail

rm -rf "$HOME/.local/share/cursify"
rm -f "$HOME/.local/bin/cursify" "$HOME/.local/share/applications/cursify.desktop" \
      "$HOME/.local/share/icons/hicolor/scalable/apps/cursify.svg"
gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true

echo "Cursify se desinstaló."
echo "Los temas que creaste siguen en ~/.local/share/icons y se pueden elegir en"
echo "Configuración del sistema → Temas → Puntero del ratón."
echo "Tus presets y ajustes quedan en ~/.config/cursify (borrá esa carpeta si no los querés)."
echo "Si diste permiso a las apps Flatpak, se quita con:"
echo "  flatpak override --user --nofilesystem=xdg-data/icons --nofilesystem=~/.icons"
