"""Lectura de cursores de Windows (.cur, .ico y .ani animados) en Python puro.

Cada cursor se convierte en una lista de ``Frame`` con píxeles RGBA (alfa no
premultiplicado), punto activo (hotspot) y duración en milisegundos.
"""

import struct

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class CursorError(Exception):
    """El archivo no es un cursor válido o usa un formato no soportado."""


class Frame:
    __slots__ = ("width", "height", "rgba", "xhot", "yhot", "delay")

    def __init__(self, width, height, rgba, xhot=0, yhot=0, delay=0):
        self.width = width
        self.height = height
        self.rgba = rgba
        self.xhot = xhot
        self.yhot = yhot
        self.delay = delay

    def copy(self, **changes):
        values = {name: getattr(self, name) for name in self.__slots__}
        values.update(changes)
        return Frame(**values)


# --------------------------------------------------------------------------
# Imágenes dentro de ICO/CUR (DIB o PNG)
# --------------------------------------------------------------------------

def _decode_dib(data, png_decoder):
    if data[:8] == PNG_MAGIC:
        if png_decoder is None:
            raise CursorError("el cursor contiene una imagen PNG y no hay decodificador")
        return png_decoder(bytes(data))

    if len(data) < 40:
        raise CursorError("imagen de cursor demasiado corta")
    header_size, width, height2, _planes, bpp, compression = struct.unpack_from("<IiiHHI", data, 0)
    colors_used = struct.unpack_from("<I", data, 32)[0]
    height = abs(height2) // 2
    if width <= 0 or height <= 0 or width > 1024 or height > 1024:
        raise CursorError("tamaño de imagen inválido")
    if bpp not in (1, 4, 8, 16, 24, 32):
        raise CursorError(f"profundidad de color no soportada ({bpp} bits)")

    offset = header_size
    palette = []
    if bpp <= 8:
        count = colors_used or (1 << bpp)
        for i in range(count):
            p = offset + 4 * i
            if p + 4 > len(data):
                break
            b, g, r = data[p], data[p + 1], data[p + 2]
            palette.append((r, g, b))
        offset += 4 * count
    elif compression == 3 and header_size == 40:
        offset += 12  # máscaras BI_BITFIELDS

    stride = ((width * bpp + 31) // 32) * 4
    xor = data[offset:offset + stride * height]
    if len(xor) < stride * height:
        raise CursorError("datos de imagen incompletos")
    offset += stride * height
    mask_stride = ((width + 31) // 32) * 4
    mask = data[offset:offset + mask_stride * height]
    has_mask = len(mask) >= mask_stride * height

    out = bytearray(width * height * 4)
    alpha_used = False
    black = (0, 0, 0)
    for y in range(height):
        src_row = height - 1 - y  # las imágenes DIB se guardan de abajo hacia arriba
        row = xor[src_row * stride:(src_row + 1) * stride]
        o = y * width * 4
        for x in range(width):
            if bpp == 32:
                b, g, r, a = row[4 * x], row[4 * x + 1], row[4 * x + 2], row[4 * x + 3]
                if a:
                    alpha_used = True
            else:
                a = 255
                if bpp == 24:
                    b, g, r = row[3 * x], row[3 * x + 1], row[3 * x + 2]
                elif bpp == 16:
                    v = row[2 * x] | (row[2 * x + 1] << 8)
                    r = ((v >> 10) & 31) * 255 // 31
                    g = ((v >> 5) & 31) * 255 // 31
                    b = (v & 31) * 255 // 31
                else:
                    if bpp == 8:
                        idx = row[x]
                    elif bpp == 4:
                        idx = (row[x >> 1] >> (4 if x % 2 == 0 else 0)) & 15
                    else:
                        idx = (row[x >> 3] >> (7 - (x & 7))) & 1
                    r, g, b = palette[idx] if idx < len(palette) else black
            out[o:o + 4] = bytes((r, g, b, a))
            o += 4

    # Sin canal alfa propio: la transparencia sale de la máscara AND.
    if bpp != 32 or not alpha_used:
        if has_mask:
            for y in range(height):
                src_row = height - 1 - y
                mrow = mask[src_row * mask_stride:(src_row + 1) * mask_stride]
                o = y * width * 4
                for x in range(width):
                    if (mrow[x >> 3] >> (7 - (x & 7))) & 1:
                        out[o + 4 * x + 3] = 0
                    else:
                        out[o + 4 * x + 3] = 255
        elif bpp == 32:
            for i in range(3, len(out), 4):
                out[i] = 255
    return width, height, bytes(out)


def parse_ico(data, png_decoder=None):
    """Devuelve el mejor ``Frame`` de un .ico o .cur (la imagen más grande)."""
    if len(data) < 6:
        raise CursorError("archivo vacío o dañado")
    reserved, kind, count = struct.unpack_from("<HHH", data, 0)
    if reserved != 0 or kind not in (1, 2) or count == 0:
        raise CursorError("no es un archivo .cur/.ico")

    best = None
    for i in range(count):
        p = 6 + 16 * i
        if p + 16 > len(data):
            break
        bw, bh, _cc, _res, f1, f2, size, offset = struct.unpack_from("<BBBBHHII", data, p)
        bw = bw or 256
        bh = bh or 256
        score = (bw * bh, f2 if kind == 1 else 0)
        if best is None or score > best[0]:
            best = (score, bw, bh, f1, f2, size, offset)
    if best is None:
        raise CursorError("el cursor no tiene imágenes")

    _score, bw, bh, f1, f2, size, offset = best
    width, height, rgba = _decode_dib(data[offset:offset + size], png_decoder)
    if kind == 2:
        # Hotspot guardado para el tamaño del directorio; se ajusta si difiere.
        xhot = f1 * width // bw if bw else f1
        yhot = f2 * height // bh if bh else f2
    else:
        xhot = yhot = 0
    xhot = min(max(xhot, 0), width - 1)
    yhot = min(max(yhot, 0), height - 1)
    return Frame(width, height, rgba, xhot, yhot, 0), kind == 2


def _iter_chunks(data, start, end):
    pos = start
    while pos + 8 <= end:
        cid = bytes(data[pos:pos + 4])
        size = struct.unpack_from("<I", data, pos + 4)[0]
        body_end = min(pos + 8 + size, end)
        yield cid, pos + 8, body_end
        pos += 8 + size + (size & 1)


def parse_ani(data, png_decoder=None):
    """Devuelve la lista de ``Frame`` (en orden de reproducción) de un .ani."""
    if data[:4] != b"RIFF" or data[8:12] != b"ACON":
        raise CursorError("no es un cursor animado .ani")
    riff_end = min(len(data), 8 + struct.unpack_from("<I", data, 4)[0])

    anih = None
    rates = None
    sequence = None
    icons = []

    def walk(start, end):
        nonlocal anih, rates, sequence
        for cid, b0, b1 in _iter_chunks(data, start, end):
            if cid == b"anih" and b1 - b0 >= 36:
                anih = struct.unpack_from("<9I", data, b0)
            elif cid == b"rate":
                n = (b1 - b0) // 4
                rates = list(struct.unpack_from(f"<{n}I", data, b0))
            elif cid == b"seq ":
                n = (b1 - b0) // 4
                sequence = list(struct.unpack_from(f"<{n}I", data, b0))
            elif cid == b"LIST" and b1 - b0 >= 4:
                if bytes(data[b0:b0 + 4]) == b"fram":
                    walk(b0 + 4, b1)
            elif cid == b"icon":
                icons.append(data[b0:b1])

    walk(12, riff_end)
    if not icons:
        raise CursorError("el .ani no tiene cuadros")

    raw_bitmaps = anih is not None and not (anih[8] & 1)
    frames = []
    first_hot = None
    for blob in icons:
        if raw_bitmaps:
            w, h, rgba = _decode_dib(blob, png_decoder)
            frame, is_cur = Frame(w, h, rgba), False
        else:
            frame, is_cur = parse_ico(blob, png_decoder)
        if is_cur and first_hot is None:
            first_hot = (frame, frame.xhot, frame.yhot)
        frames.append((frame, is_cur))

    # Cuadros sin hotspot propio heredan el del primer cursor.
    decoded = []
    for frame, is_cur in frames:
        if not is_cur and first_hot is not None:
            ref, hx, hy = first_hot
            frame.xhot = min(hx * frame.width // ref.width, frame.width - 1)
            frame.yhot = min(hy * frame.height // ref.height, frame.height - 1)
        decoded.append(frame)

    default_rate = (anih[7] if anih and anih[7] else 10)
    steps = (anih[2] if anih and anih[2] else 0) or (len(sequence) if sequence else len(decoded))
    result = []
    for s in range(steps):
        idx = sequence[s] if sequence and s < len(sequence) else s % len(decoded)
        if idx >= len(decoded):
            idx = s % len(decoded)
        jiffies = rates[s] if rates and s < len(rates) else default_rate
        delay = max(10, round(jiffies * 1000 / 60))
        result.append(decoded[idx].copy(delay=delay))
    if len(result) == 1:
        result[0].delay = 0
    return result


def load(path, png_decoder=None):
    """Carga un .cur/.ico/.ani y devuelve una lista de ``Frame``."""
    with open(path, "rb") as fh:
        data = fh.read()
    if data[:4] == b"RIFF":
        return parse_ani(data, png_decoder)
    frame, _ = parse_ico(data, png_decoder)
    return [frame]
