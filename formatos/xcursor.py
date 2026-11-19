"""Escritura de archivos Xcursor (el formato de cursores de Linux)."""

import struct

IMAGE_TYPE = 0xFFFD0002
MAGIC = b"Xcur"


def rgba_to_argb(rgba):
    """RGBA no premultiplicado -> ARGB premultiplicado (little-endian: B G R A)."""
    out = bytearray(len(rgba))
    for i in range(0, len(rgba), 4):
        r, g, b, a = rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]
        if a == 255:
            out[i:i + 4] = bytes((b, g, r, 255))
        elif a:
            out[i] = (b * a + 127) // 255
            out[i + 1] = (g * a + 127) // 255
            out[i + 2] = (r * a + 127) // 255
            out[i + 3] = a
        # a == 0 -> queda en cero
    return bytes(out)


def write(path, images):
    """Escribe un Xcursor.

    ``images``: lista de tuplas (tamaño_nominal, ancho, alto, xhot, yhot,
    retardo_ms, rgba). Los cuadros de una animación van en orden.
    """
    images = sorted(images, key=lambda im: im[0])  # orden estable por tamaño
    count = len(images)
    position = 16 + 12 * count
    toc = []
    chunks = []
    for nominal, width, height, xhot, yhot, delay, rgba in images:
        xhot = min(max(int(xhot), 0), width - 1)
        yhot = min(max(int(yhot), 0), height - 1)
        chunk = struct.pack("<9I", 36, IMAGE_TYPE, nominal, 1, width, height,
                            xhot, yhot, int(delay)) + rgba_to_argb(rgba)
        toc.append(struct.pack("<3I", IMAGE_TYPE, nominal, position))
        chunks.append(chunk)
        position += len(chunk)
    with open(path, "wb") as fh:
        fh.write(struct.pack("<4sIII", MAGIC, 16, 0x10000, count))
        fh.writelines(toc)
        fh.writelines(chunks)


def read_image(path, size=32):
    """Lee el primer cuadro del tamaño más cercano a ``size``. Devuelve (ancho, alto, rgba)."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] != MAGIC:
        raise ValueError("no es un Xcursor")
    _magic, header, _version, ntoc = struct.unpack_from("<4sIII", data, 0)
    best = None
    for i in range(ntoc):
        kind, subtype, position = struct.unpack_from("<3I", data, header + 12 * i)
        if kind == IMAGE_TYPE and (best is None or abs(subtype - size) < abs(best[0] - size)):
            best = (subtype, position)
    if best is None:
        return None
    _h, _t, _s, _v, width, height, _xh, _yh, _d = struct.unpack_from("<9I", data, best[1])
    pixels = data[best[1] + 36:best[1] + 36 + width * height * 4]
    out = bytearray(len(pixels))
    for i in range(0, len(pixels), 4):
        b, g, r, a = pixels[i], pixels[i + 1], pixels[i + 2], pixels[i + 3]
        if a:  # deshace el premultiplicado
            out[i:i + 4] = bytes((min(255, r * 255 // a), min(255, g * 255 // a),
                                  min(255, b * 255 // a), a))
    return width, height, bytes(out)
