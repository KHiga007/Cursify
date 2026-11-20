<p align="center">
  <img src="recursos/cursify.svg" alt="Ícono de Cursify" width="112">
</p>

<h1 align="center">Cursify</h1>

<p align="center">
  Usá tus packs de cursores de Windows en Linux Mint, con un clic.
</p>

<p align="center">
  <img alt="Linux Mint" src="https://img.shields.io/badge/Linux%20Mint-Cinnamon%20%7C%20MATE%20%7C%20Xfce-87CF3E?logo=linuxmint&logoColor=white">
  <img alt="Python 3" src="https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white">
  <img alt="GTK 3" src="https://img.shields.io/badge/GTK-3-4A86CF">
  <img alt="Licencia GPL-3.0" src="https://img.shields.io/badge/licencia-GPL--3.0-blue">
</p>

<!-- Captura de la app: agregar recursos/captura.png y mostrarla acá -->

## Inicio rápido

1. Descargá el instalador `.deb` desde [Releases](https://github.com/KHiga007/Cursify/releases/latest).
2. Abrilo con doble clic para instalarlo.
3. Abrí **Cursify** desde el menú, en **Preferencias**, y soltá la carpeta de tu pack en la ventana.

## Características

- **Formatos de Windows**: cursores animados `.ani`, estáticos `.cur` e íconos `.ico`, además de `.png` y `.svg`.
- **Detección automática**: ubica cada archivo en una de las 15 situaciones del cursor, como en Windows.
- **Vista previa en vivo**: pasás el mouse por un cuadro y probás el cursor de verdad, animación incluida.
- **Presets**: guardás tus combinaciones y las volvés a aplicar aunque borres el pack original.
- **Vuelta atrás**: un clic y volvés al cursor que tenías antes.
- **Español e inglés**: toma el idioma del sistema y se puede cambiar desde la app.

## Instalación

Funciona en todas las ediciones de Linux Mint (Cinnamon, MATE y Xfce), también en LMDE, y en GNOME.

1. Descargá `cursify_X.Y.Z_all.deb` desde [Releases](https://github.com/KHiga007/Cursify/releases/latest).
2. Abrilo con doble clic, o instalalo desde la terminal:

   ```bash
   sudo apt install ./cursify_*_all.deb
   ```

3. Abrí **Cursify** desde el menú, en **Preferencias**, o con el comando `cursify`.

Para abrir la app con un pack ya cargado: `cursify ~/Descargas/MiPack`.

## Cómo se usa

### 1. Cargar un pack

Tocá **Abrir carpeta de cursores…** o arrastrá la carpeta a la ventana. Cursify ubica cada archivo usando, en este orden:

1. El `install.inf` del pack, si lo trae.
2. El nombre del archivo, en inglés, español y otros idiomas (`aero_busy`, `texto`, `Link Select`, `手書き`…).
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
- **Hacer clic** en la vista previa para mover el punto activo (la cruz roja). El botón **↻** lo devuelve al original.
- **Arrastrar un archivo** o usar **Elegir…** para cambiarlo.

Las situaciones que dejes vacías usan el cursor que tenías antes.

### 3. Aplicar

Elegí un nombre y un tamaño (24, 32, 48 o 64 px) y tocá **Aplicar cursor**. El cambio es inmediato.

### 4. Guardar un preset

**Guardar preset** guarda la combinación actual (cursores, puntos activos y tamaño) sin cambiar el cursor que estás usando. Desde **Presets ▾** podés abrir uno para editarlo, aplicarlo directo o borrarlo.

## Problemas frecuentes

<details>
<summary><b>Brave, Discord o VSCodium siguen con el cursor viejo</b></summary>

Son apps Flatpak y necesitan permiso para leer tus temas de cursor. Dáselo en modo solo lectura:

```bash
flatpak override --user --filesystem=xdg-data/icons:ro --filesystem=~/.icons:ro
```

Para quitarlo:

```bash
flatpak override --user --nofilesystem=xdg-data/icons --nofilesystem=~/.icons
```
</details>

<details>
<summary><b>¿Cómo vuelvo al cursor que tenía antes?</b></summary>

Abrí el menú **☰** y elegí volver al cursor anterior. Desde ahí también podés borrar temas creados con la app o empezar de cero.
</details>

<details>
<summary><b>¿Cómo desinstalo Cursify?</b></summary>

```bash
sudo apt remove cursify
```

Los temas que creaste siguen en `~/.local/share/icons` y se pueden elegir en *Configuración del sistema → Temas → Puntero del ratón*. Tus presets y ajustes quedan en `~/.config/cursify`: si no los querés, borrá esa carpeta.
</details>

## Detalles técnicos

<details>
<summary><b>Cómo funciona por dentro</b></summary>

1. **Lectura**: `formatos/wincursor.py` decodifica los `.ani`, `.cur` e `.ico` (cuadros, tiempos de animación y punto activo).
2. **Asignación**: `nucleo/roles.py` asigna cada archivo a una situación y la traduce a los nombres de cursor que usan las apps de Linux (`left_ptr`, `pointer`, `text`, `wait`…).
3. **Generación**: `nucleo/theme.py` escala cada cursor a 24, 32, 48 y 64 px, y `formatos/xcursor.py` lo escribe en formato Xcursor.
4. **Activación**: el tema se aplica en el escritorio que uses: Cinnamon, MATE, Xfce o GNOME.
</details>

<details>
<summary><b>Archivos que crea en tu usuario</b></summary>

| Ruta | Contenido |
|---|---|
| `~/.local/share/icons/<nombre>` | Temas de cursor creados (con un enlace en `~/.icons`) |
| `~/.config/cursify/presets/` | Presets guardados |
| `~/.config/cursify/state.json` | Cursor anterior, para volver atrás |
| `~/.config/cursify/settings.json` | Ajustes, como el idioma |
</details>

<details>
<summary><b>Estructura del proyecto</b></summary>

```
Cursify/
├── cursify.py          punto de entrada
├── interfaz/           ventana e interfaz GTK
├── nucleo/             temas, situaciones, presets, idiomas
├── formatos/           lectura y escritura de .ani, .cur, .ico y Xcursor
├── recursos/           ícono
└── scripts/            instalación y armado del .deb
```
</details>

## Licencia

Cursify se distribuye bajo la licencia [GNU GPL v3](LICENSE).
