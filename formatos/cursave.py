"""Escritura de cursores de Windows (.cur y .ani) a partir de cuadros en memoria.

Se usa cuando hay que guardar un preset y el archivo original ya no existe:
los cursores se escriben desde lo que la app tiene cargado.
"""

import struct


def _cur_bytes(frame):
    w, h = frame.width, frame.height
    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    rows = []
    for y in range(h - 1, -1, -1):  # DIB: de abajo hacia arriba, en BGRA
        row = bytearray(frame.rgba[y * w * 4:(y + 1) * w * 4])
        row[0::4], row[2::4] = row[2::4], row[0::4]
        rows.append(bytes(row))
    mask = bytes(((w + 31) // 32) * 4 * h)  # máscara AND vacía: manda el canal alfa
    image = header + b"".join(rows) + mask
    directory = struct.pack("<HHH", 0, 2, 1)
    entry = struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, frame.xhot, frame.yhot, len(image), 22)
    return directory + entry + image


def _chunk(cid, body):
    pad = b"\0" if len(body) % 2 else b""
    return cid + struct.pack("<I", len(body)) + body + pad


def write_cur(path, frame):
    with open(path, "wb") as fh:
        fh.write(_cur_bytes(frame))


def write_ani(path, frames):
    count = len(frames)
    jiffies = [max(1, round(f.delay * 60 / 1000)) for f in frames]
    anih = struct.pack("<9I", 36, count, count, 0, 0, 0, 0, jiffies[0], 1)
    rate = struct.pack(f"<{count}I", *jiffies)
    icons = b"".join(_chunk(b"icon", _cur_bytes(f)) for f in frames)
    body = b"ACON" + _chunk(b"anih", anih) + _chunk(b"rate", rate) + _chunk(b"LIST", b"fram" + icons)
    with open(path, "wb") as fh:
        fh.write(b"RIFF" + struct.pack("<I", len(body)) + body)


def write(path_without_ext, frames):
    """Escribe .ani (si hay varios cuadros) o .cur. Devuelve la ruta final."""
    if len(frames) > 1:
        path = path_without_ext + ".ani"
        write_ani(path, frames)
    else:
        path = path_without_ext + ".cur"
        write_cur(path, frames[0])
    return path
