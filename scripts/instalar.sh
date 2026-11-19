#!/usr/bin/env bash
# Instala Cursify para tu usuario (no necesita sudo).
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # raíz del proyecto
DEST="$HOME/.local/share/cursify"
BIN="$HOME/.local/bin/cursify"
DESKTOP="$HOME/.local/share/applications/cursify.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

if ! python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
    echo "Falta GTK para Python. Instalalo con:"
    echo "  sudo apt install python3-gi gir1.2-gtk-3.0"
    exit 1
fi

# Si estaba instalada con el nombre anterior (PunteroFácil), se quita esa versión.
# Tus presets, ajustes y temas creados se conservan.
rm -rf "$HOME/.local/share/punterofacil"
rm -f "$HOME/.local/bin/punterofacil" "$HOME/.local/share/applications/punterofacil.desktop" \
      "$HOME/.local/share/icons/hicolor/scalable/apps/punterofacil.svg"

rm -rf "$DEST"
mkdir -p "$DEST" "$(dirname "$BIN")" "$(dirname "$DESKTOP")"
cp -r "$SRC/cursify.py" "$SRC/interfaz" "$SRC/nucleo" "$SRC/formatos" "$SRC/recursos" "$DEST/"
find "$DEST" -name "__pycache__" -type d -prune -exec rm -rf {} +

# Ícono de la app (menú y panel).
mkdir -p "$ICON_DIR"
cp "$SRC/recursos/cursify.svg" "$ICON_DIR/cursify.svg"
gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true

cat > "$BIN" <<EOF
#!/bin/sh
exec python3 "$DEST/cursify.py" "\$@"
EOF
chmod +x "$BIN"

cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Cursify
GenericName=Cursores del mouse
Comment=Usá packs de cursores de Windows (.ani/.cur) en Linux Mint
Exec=$BIN %F
Icon=cursify
StartupWMClass=cursify
Terminal=false
Categories=X-AkiTools;
Keywords=cursor;mouse;ratón;puntero;ani;cur;punterofacil;
StartupNotify=true
EOF

update-desktop-database "$(dirname "$DESKTOP")" >/dev/null 2>&1 || true

# Sección «Aki Tools» en el menú (toda app con Categories=X-AkiTools; va ahí).
MENU_DIR="$HOME/.config/menus/applications-merged"
DIR_DIR="$HOME/.local/share/desktop-directories"
mkdir -p "$MENU_DIR" "$DIR_DIR"
if [ ! -f "$MENU_DIR/aki-tools.menu" ]; then
cat > "$MENU_DIR/aki-tools.menu" <<'MENU'
<!DOCTYPE Menu PUBLIC "-//freedesktop//DTD Menu 1.0//EN"
"http://www.freedesktop.org/standards/menu-spec/menu-1.0.dtd">
<!-- Sección «Aki Tools» del menú. Incluye toda app con Categories=X-AkiTools; -->
<Menu>
	<Name>Applications</Name>
	<Menu>
		<Name>Aki Tools</Name>
		<Directory>aki-tools.directory</Directory>
		<Include>
			<Category>X-AkiTools</Category>
		</Include>
	</Menu>
</Menu>
MENU
fi
if [ ! -f "$DIR_DIR/aki-tools.directory" ]; then
cat > "$DIR_DIR/aki-tools.directory" <<'DIR'
[Desktop Entry]
Version=1.0
Type=Directory
Name=Aki Tools
Comment=Herramientas hechas por Aki
Icon=applications-utilities
DIR
fi

# Apps Flatpak (Brave, Discord, VSCodium…): necesitan permiso de lectura para ver los
# temas de cursor de tu usuario. Es solo lectura y se puede quitar cuando quieras.
if command -v flatpak >/dev/null 2>&1; then
    answer="n"
    if [ -t 0 ]; then
        read -r -p "¿Permitir que las apps Flatpak usen tus temas de cursor? (solo lectura) [S/n] " answer || true
        answer="${answer:-s}"
    fi
    case "$answer" in
        [sSyY]*)
            flatpak override --user --filesystem=xdg-data/icons:ro --filesystem=~/.icons:ro \
                && echo "Listo: las apps Flatpak pueden leer tus temas de cursor." ;;
        *)
            echo "Flatpak: no se cambió nada. Para hacerlo después:"
            echo "  flatpak override --user --filesystem=xdg-data/icons:ro --filesystem=~/.icons:ro" ;;
    esac
fi

echo "Cursify quedó instalado."
echo "Abrilo desde el menú (Aki Tools → Cursify) o con el comando: cursify"
