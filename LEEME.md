# Cursify

Convierte packs de cursores de Windows (`.ani`, `.cur`, `.ico`) —o imágenes
`.png`/`.svg`— en un tema de cursor para Linux Mint y lo activa con un clic.

## Instalar

```bash
cd Cursify
bash scripts/instalar.sh
```

Después aparece en el menú como **Cursify**. También se abre con
`cursify` (o `cursify /ruta/a/la/carpeta` para cargar un pack directo).

Para probarla sin instalar: `python3 cursify.py`.

## Estructura

```
Cursify/
├── cursify.py          punto de entrada (abre la app)
├── interfaz/
│   └── app.py          ventana e interfaz GTK
├── nucleo/
│   ├── theme.py        arma el tema de cursor y lo aplica
│   ├── roles.py        las 15 situaciones y cómo reconocer cada archivo
│   ├── presets.py      guardar, abrir y borrar presets
│   ├── i18n.py         textos e idiomas
│   └── info.py         nombre, versión y migración desde PunteroFácil
├── formatos/
│   ├── wincursor.py    lee .ani, .cur e .ico de Windows
│   ├── xcursor.py      escribe cursores en formato Xcursor (Linux)
│   └── cursave.py      guarda cursores como .cur (para los presets)
├── recursos/
│   └── cursify.svg     ícono de la app
└── scripts/
    ├── instalar.sh
    └── desinstalar.sh
```

## Uso

1. **Abrir carpeta de cursores…** (o arrastrar la carpeta a la ventana).
   La app ubica cada archivo en su situación usando, en este orden:
   el `install.inf` del pack, el nombre del archivo (`aero_busy`, `texto`,
   `Link Select`, `手書き`…) y el número de orden de Windows (`01` = normal,
   `02` = ayuda, … `15` = vínculo).
2. Revisar los 15 cuadros:
   - Pasá el mouse por la vista previa para **probar** el cursor de verdad.
   - Hacé **clic** en la vista previa para mover el **punto activo** (la cruz
     roja: el píxel que "hace clic"). El botón ↻ vuelve al original.
   - Arrastrá un archivo a un cuadro, o usá **Elegir…**, para cambiarlo.
3. Elegir nombre y tamaño y tocar **Aplicar cursor**.

## Presets

**Guardar preset** guarda la combinación actual (cursores, puntos activos y
tamaño) sin tocar el cursor que estás usando. En **Presets ▾** podés abrir uno
para editarlo, aplicarlo directo o borrarlo. Se guardan con una copia de los
archivos en `~/.config/cursify/presets`, así siguen andando aunque borres
el pack original.

En el menú ☰: volver al cursor que tenías antes, borrar temas creados con la
app o empezar de cero (vacía también el nombre).

## Qué hace por dentro

- Crea el tema en `~/.local/share/icons/<nombre>` (con un enlace en `~/.icons`),
  en tamaños 24, 32, 48 y 64 px, con todos los nombres de cursor que usan las
  apps de Linux.
- Las situaciones que dejes vacías usan el cursor que tenías antes.
- Lo activa en Cinnamon (y en GNOME/MATE si están).

## Apps Flatpak

Brave, Discord, VSCodium y otras apps Flatpak necesitan permiso de lectura para ver
los temas de cursor de tu usuario. `scripts/instalar.sh` lo pregunta (solo lectura). Para
darlo o quitarlo a mano:

```bash
flatpak override --user --filesystem=xdg-data/icons:ro --filesystem=~/.icons:ro
flatpak override --user --nofilesystem=xdg-data/icons --nofilesystem=~/.icons
```

## Desinstalar

```bash
bash scripts/desinstalar.sh
```

## Antes se llamaba PunteroFácil

La primera vez que abrís Cursify, copia tus presets y ajustes de
`~/.config/punterofacil` a `~/.config/cursify` (la carpeta vieja no se toca).
Los temas creados con PunteroFácil se siguen reconociendo como propios.
`scripts/instalar.sh` quita la versión instalada con el nombre viejo.
