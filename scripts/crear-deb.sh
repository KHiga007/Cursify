#!/usr/bin/env bash
# Arma el instalador .deb de Cursify para publicar en un release.
# Uso: bash scripts/crear-deb.sh        → deja el paquete en dist/
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # raíz del proyecto
VERSION="$(python3 -c "import sys; sys.path.insert(0, '$SRC'); from nucleo.info import __version__; print(__version__)")"
PKG="cursify_${VERSION}_all"
OUT="$SRC/dist"
BUILD="$(mktemp -d)"
ROOT="$BUILD/$PKG"
trap 'rm -rf "$BUILD"' EXIT

# Archivos de la app → /usr/share/cursify
mkdir -p "$ROOT/usr/share/cursify"
cp -r "$SRC/cursify.py" "$SRC/interfaz" "$SRC/nucleo" "$SRC/formatos" "$SRC/recursos" \
      "$ROOT/usr/share/cursify/"
find "$ROOT" -name "__pycache__" -type d -prune -exec rm -rf {} +

# Comando «cursify»
mkdir -p "$ROOT/usr/bin"
cat > "$ROOT/usr/bin/cursify" <<'EOF'
#!/bin/sh
exec python3 /usr/share/cursify/cursify.py "$@"
EOF

# Ícono
mkdir -p "$ROOT/usr/share/icons/hicolor/scalable/apps"
cp "$SRC/recursos/cursify.svg" "$ROOT/usr/share/icons/hicolor/scalable/apps/cursify.svg"

# Entrada del menú: sección «Preferencias» (Settings;DesktopSettings).
mkdir -p "$ROOT/usr/share/applications"
cat > "$ROOT/usr/share/applications/cursify.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Cursify
GenericName=Cursores del mouse
GenericName[en]=Mouse cursors
Comment=Usá packs de cursores de Windows (.ani/.cur) en Linux Mint
Comment[en]=Use Windows cursor packs (.ani/.cur) on Linux Mint
Exec=cursify %F
Icon=cursify
StartupWMClass=cursify
Terminal=false
Categories=GTK;Settings;DesktopSettings;
Keywords=cursor;mouse;ratón;puntero;ani;cur;tema;theme;
StartupNotify=true
EOF

# Documentación y licencia
mkdir -p "$ROOT/usr/share/doc/cursify"
cp "$SRC/README.md" "$ROOT/usr/share/doc/cursify/"
cp "$SRC/LICENSE" "$ROOT/usr/share/doc/cursify/copyright"

# Permisos estándar
find "$ROOT/usr" -type d -exec chmod 755 {} +
find "$ROOT/usr" -type f -exec chmod 644 {} +
chmod 755 "$ROOT/usr/bin/cursify" "$ROOT/usr/share/cursify/cursify.py"

# Metadatos del paquete
SIZE="$(du -sk "$ROOT/usr" | cut -f1)"
mkdir -p "$ROOT/DEBIAN"
cat > "$ROOT/DEBIAN/control" <<EOF
Package: cursify
Version: $VERSION
Section: x11
Priority: optional
Architecture: all
Depends: python3, python3-gi, gir1.2-gtk-3.0
Installed-Size: $SIZE
Maintainer: KHiga007 <KHiga007@users.noreply.github.com>
Homepage: https://github.com/KHiga007/Cursify
Description: Usá packs de cursores de Windows en Linux Mint
 Cursify convierte packs de cursores de Windows (.ani, .cur, .ico) o
 imágenes (.png, .svg) en un tema de cursor de Linux y lo activa con un
 clic. Reconoce qué archivo va en cada situación, permite ajustar el punto
 activo y guarda combinaciones como presets.
EOF

# Al instalar se compila el código de Python (así la app arranca más rápido)
# y al quitar el paquete se borra esa caché.
cat > "$ROOT/DEBIAN/postinst" <<'EOF'
#!/bin/sh
set -e
python3 -m compileall -q /usr/share/cursify >/dev/null 2>&1 || true
EOF
cat > "$ROOT/DEBIAN/prerm" <<'EOF'
#!/bin/sh
set -e
find /usr/share/cursify -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
EOF
chmod 755 "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/prerm"

mkdir -p "$OUT"
dpkg-deb --root-owner-group --build "$ROOT" "$OUT/$PKG.deb" >/dev/null
echo "Listo: dist/$PKG.deb"
