<p align="center">
  <img src="recursos/cursify.svg" alt="Ícono de Cursify" width="112">
</p>

<h1 align="center">Cursify</h1>

<p align="center">
  Usá tus packs de cursores de Windows en Linux Mint, con un clic.
</p>

<p align="center">
  <img alt="Linux Mint" src="https://img.shields.io/badge/Linux%20Mint-Cinnamon-87CF3E?logo=linuxmint&logoColor=white">
  <img alt="Python 3" src="https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white">
  <img alt="GTK 3" src="https://img.shields.io/badge/GTK-3-4A86CF">
  <img alt="Licencia GPL-3.0" src="https://img.shields.io/badge/licencia-GPL--3.0-blue">
</p>

---

**Cursify** convierte un pack de cursores de Windows (`.ani`, `.cur`, `.ico`), o
imágenes sueltas (`.png`, `.svg`), en un tema de cursor de Linux y lo activa al
instante. Reconoce sola qué archivo va en cada situación, te deja retocar todo
antes de aplicarlo y guarda tus combinaciones como presets.

## Índice

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Cómo se usa](#cómo-se-usa)
- [Presets](#presets)
- [Apps Flatpak](#apps-flatpak)
- [Cómo funciona por dentro](#cómo-funciona-por-dentro)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Publicar una versión](#publicar-una-versión)
- [Desinstalar](#desinstalar)
- [Antes se llamaba PunteroFácil](#antes-se-llamaba-punterofácil)
- [Licencia](#licencia)

## Características

- **Formatos de Windows nativos**: lee cursores animados `.ani`, estáticos
  `.cur` e íconos `.ico`, además de `.png` y `.svg`.
- **Detección automática**: ubica cada archivo en una de las 15 situaciones del
  cursor, igual que en *Panel de control → Mouse → Punteros* de Windows.
- **Vista previa en vivo**: pasá el mouse por un cuadro y probás el cursor de
  verdad, animación incluida.
- **Punto activo editable**: con un clic elegís qué píxel "hace clic".
- **Arrastrar y soltar**: soltá una carpeta en la ventana para cargar el pack, o
  un archivo sobre un cuadro para cambiar solo ese.
- **Cuatro tamaños**: 24, 32, 48 y 64 px.
- **Presets**: guardás combinaciones completas y las volvés a aplicar cuando
  quieras, aunque hayas borrado el pack original.
- **Vuelta atrás**: un clic y volvés al cursor que tenías antes.
- **Español e inglés**: toma el idioma del sistema y se puede cambiar desde la app.
- **Sin sudo**: todo se instala y se guarda en tu usuario.

## Requisitos

- Linux Mint con Cinnamon. También aplica el cursor en GNOME y MATE si están.
- Python 3 con GTK 3 (PyGObject). Viene con Linux Mint. Si falta:

  ```bash
  sudo apt install python3-gi gir1.2-gtk-3.0
  ```

## Instalación

1. Descargá `cursify_X.Y.Z_all.deb` desde la página de
   [Releases](https://github.com/KHiga007/Cursify/releases/latest).
2. Abrilo con doble clic para instalarlo con el Instalador de paquetes, o desde
   la terminal:

   ```bash
   sudo apt install ./cursify_*_all.deb
   ```

3. Abrí **Cursify** desde el menú, en **Preferencias**.

Para desinstalarlo: `sudo apt remove cursify`.

También se abre desde la terminal:

```bash
cursify                       # abre la app
cursify ~/Descargas/MiPack    # abre la app con un pack ya cargado
```

## Cómo se usa

### 1. Cargar un pack

Tocá **Abrir carpeta de cursores…** o arrastrá la carpeta a la ventana. Cursify
ubica cada archivo usando, en este orden:

1. El `install.inf` del pack, si lo trae.
2. El nombre del archivo: reconoce nombres en inglés, en español y en otros
   idiomas (`aero_busy`, `texto`, `Link Select`, `手書き`…).
3. El número de orden de Windows (`01` = normal, `02` = ayuda, … `15` = vínculo).

### 2. Revisar las 15 situaciones

| | | |
|---|---|---|
| Selección normal | Selección de ayuda | Trabajando en segundo plano |
| Ocupado | Selección de precisión | Selección de texto |
| Escritura a mano | No disponible | Cambiar tamaño vertical |
| Cambiar tamaño horizontal | Cambiar tamaño en diagonal 1 | Cambiar tamaño en diagonal 2 |
| Mover | Selección alternativa | Selección de vínculo |

En cada cuadro podés:

- **Pasar el mouse** por la vista previa para probar el cursor.
- **Hacer clic** en la vista previa para mover el punto activo (la cruz roja).
  El botón **↻** lo devuelve al original.
- **Arrastrar un archivo** o usar **Elegir…** para cambiarlo.

Las situaciones que dejes vacías usan el cursor que tenías antes.

### 3. Aplicar

Elegí un nombre y un tamaño, y tocá **Aplicar cursor**. El cambio es inmediato.

En el menú **☰** podés volver al cursor anterior, borrar temas creados con la app
o empezar de cero.

## Presets

**Guardar preset** guarda la combinación actual (cursores, puntos activos y
tamaño) sin cambiar el cursor que estás usando. Desde **Presets ▾** podés abrir
uno para editarlo, aplicarlo directo o borrarlo.

Cada preset guarda una copia de sus archivos en `~/.config/cursify/presets`, así
sigue funcionando aunque borres el pack original.

## Apps Flatpak

Las apps Flatpak (Brave, Discord, VSCodium y otras) no ven los temas de cursor
de tu usuario si no tienen permiso. `scripts/instalar.sh` te ofrece dárselo, en
modo solo lectura. Para darlo o quitarlo a mano:

```bash
# Dar permiso (solo lectura)
flatpak override --user --filesystem=xdg-data/icons:ro --filesystem=~/.icons:ro

# Quitarlo
flatpak override --user --nofilesystem=xdg-data/icons --nofilesystem=~/.icons
```

## Cómo funciona por dentro

1. **Lectura**: `formatos/wincursor.py` decodifica los `.ani`, `.cur` e `.ico`
   (cuadros, tiempos de animación y punto activo).
2. **Asignación**: `nucleo/roles.py` asigna cada archivo a una situación y la
   traduce a todos los nombres de cursor que usan las apps de Linux (`left_ptr`,
   `pointer`, `text`, `wait`, `col-resize`…).
3. **Generación**: `nucleo/theme.py` escala cada cursor a 24, 32, 48 y 64 px y
   `formatos/xcursor.py` lo escribe en formato Xcursor. El tema se crea en
   `~/.local/share/icons/<nombre>`, con un enlace en `~/.icons`.
4. **Activación**: el tema y el tamaño se aplican en Cinnamon, y también en
   GNOME y MATE si están instalados.

Archivos que usa la app:

| Ruta | Contenido |
|---|---|
| `~/.local/share/icons/<nombre>` | Temas de cursor creados |
| `~/.config/cursify/presets/` | Presets guardados |
| `~/.config/cursify/state.json` | Cursor anterior (para volver atrás) |
| `~/.config/cursify/` | Ajustes, como el idioma |

## Estructura del proyecto

```
Cursify/
├── cursify.py          punto de entrada
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
│   ├── xcursor.py      escribe cursores en formato Xcursor
│   └── cursave.py      guarda cursores como .cur (para los presets)
├── recursos/
│   └── cursify.svg     ícono de la app
└── scripts/
    ├── instalar.sh     instala para tu usuario (desde el código)
    ├── desinstalar.sh
    └── crear-deb.sh    arma el instalador .deb para los releases
```

## Publicar una versión

1. Cambiá `__version__` en `nucleo/info.py`.
2. Hacé commit y subí una etiqueta con la misma versión:

   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

GitHub Actions arma el `.deb` con `scripts/crear-deb.sh` y publica el release.
Para armar el paquete en tu compu: `bash scripts/crear-deb.sh` (queda en `dist/`).

## Desinstalar

Si lo instalaste con el `.deb`:

```bash
sudo apt remove cursify
```

Si lo instalaste desde el código:

```bash
bash scripts/desinstalar.sh
```

Quita la app, el comando y la entrada del menú. Los temas que creaste siguen en
`~/.local/share/icons` y se pueden elegir en *Configuración del sistema → Temas →
Puntero del ratón*. Tus presets y ajustes quedan en `~/.config/cursify`: si no
los querés, borrá esa carpeta.

## Antes se llamaba PunteroFácil

La primera vez que abrís Cursify, copia tus presets y ajustes de
`~/.config/punterofacil` a `~/.config/cursify`. La carpeta vieja no se toca. Los
temas creados con PunteroFácil se siguen reconociendo como propios, y
`scripts/instalar.sh` quita la versión instalada con el nombre viejo.

## Licencia

Cursify se distribuye bajo la licencia [GNU GPL v3](LICENSE).
