#!/usr/bin/env python3
"""Monta cópias locais do XEX e de cv.img com os clubes identificados."""
from pathlib import Path
import struct
import zlib

from PIL import Image

HERE = Path(__file__).resolve().parent
from .elencos import read_team_names
from .inspecionar import Archive, parts, unwrap


def clubs():
    for line in (HERE / "clubes.tsv").read_text().splitlines():
        if line and not line.startswith("#"):
            row, badge, old, new, short, source = line.split("\t")
            yield int(row), int(badge), old, new, short, source


def align(n, unit):
    return (n + unit - 1) // unit * unit


def rewrite_xex(source, pe_path, destination, mapping):
    labels = read_team_names(pe_path)
    pe = bytearray(pe_path.read_bytes())
    headers = source.read_bytes()
    if headers[:4] != b"XEX2":
        raise ValueError("XEX2 esperado")
    header_length, = struct.unpack_from(">I", headers, 8)
    count, = struct.unpack_from(">I", headers, 20)
    lookup = dict(struct.iter_unpack(">II", headers[24:24+count*8]))
    execution = struct.unpack_from(">4I", headers, lookup[0x40006])
    if execution[0] != 0x617138EB or execution[3] != 0x4B4E07DA:
        raise ValueError("Este mapa exige Media ID 617138EB e Title ID 4B4E07DA")
    free, end = 0xA0B80, 0xA1000
    if any(pe[free:end]):
        raise ValueError("A área de preenchimento esperada está ocupada")
    for row, badge, old, new, short, _ in mapping:
        item = labels[row]
        if item["nome"] != old or item["campo_id_b"] != badge:
            raise ValueError(f"Registro de time divergente: {row} ({old})")
        pointers = []
        for value in (new, short):
            encoded = value.encode("utf-8") + b"\0"
            if free + len(encoded) > end:
                raise ValueError("Área de nomes insuficiente")
            pe[free:free+len(encoded)] = encoded
            pointers.append(0x82000000 + free)
            free = align(free + len(encoded), 4)
        struct.pack_into(">II", pe, int(item["offset_pe"],16), *pointers)

    header = bytearray(headers[:header_length])
    format_offset = lookup[0x3FF]
    old_length, = struct.unpack_from(">I", header, format_offset)
    header[format_offset:format_offset+old_length] = bytes(old_length)
    struct.pack_into(">IHH", header, format_offset, 8, 0, 0)
    with destination.open("xb") as handle:
        handle.write(header)
        handle.write(pe)


def wrap(original, decoded):
    if original[3:8] != b"WESYS" or original[2] not in (0, 1):
        raise ValueError("Entrada WESYS esperada")
    if original[2] == 0:
        return original[:8] + struct.pack(">II", len(decoded), 0) + decoded
    payload = zlib.compress(decoded, 9)
    data = original[:8] + struct.pack(">II", len(payload), len(decoded)) + payload
    return data.ljust(align(len(data), 4), b"\0")


def we_image(data):
    if data[:4] != b"WE00":
        raise ValueError("Escudo WE00 esperado")
    w, h = struct.unpack_from(">HH", data, 8)
    if w != h or w not in (64, 128):
        raise ValueError("Dimensões inesperadas no escudo")
    if data[6:8] == b"\x03\x20" and len(data) == 16 + w*h*4:
        return Image.frombytes("RGBA",(w,h),data[16:])
    if data[6:8] != b"\x03\x08" or len(data) != 1040 + w*h:
        raise ValueError("Formato de pixels desconhecido")
    im = Image.frombytes("P", (w,h), data[1040:])
    im.putpalette(data[16:1040], rawmode="RGBA")
    return im.convert("RGBA")


def replace_crest(template, path):
    width, height = we_image(template).size
    with Image.open(path) as source:
        badge = source.convert("RGBA")
    badge = badge.crop(badge.getbbox())
    badge.thumbnail((width-4,height-4), Image.Resampling.LANCZOS)
    art = Image.new("RGBA", (width,height))
    art.alpha_composite(badge, ((width-badge.width)//2,(height-badge.height)//2))
    if template[7] == 32:
        return template[:16] + art.tobytes()
    palette_image = art.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
    colors = bytes(palette_image.getpalette("RGBA")).ljust(1024,b"\0")
    return template[:16] + colors + palette_image.tobytes()


def patch_badges(parent, mapping, logos):
    raw = unwrap(parent)
    records = parts(raw)
    if len(records) != 207:
        raise ValueError("Esperados 207 escudos por banco")
    by_badge = {item[1]:item[-1] for item in mapping}
    result = bytearray(raw[:records[0]["offset"]])
    names_start = align(max(row["offset"] + row["bytes"] for row in records), 4)
    name_offsets = [int(row["aux"], 16) for row in records]
    if any(not names_start <= offset < len(raw) or raw.find(b"\0", offset) < 0
           for offset in name_offsets):
        raise ValueError("Tabela de nomes dos escudos inválida")
    for index, record in enumerate(records):
        start, length = record["offset"], record["bytes"]
        stored = raw[start:start+length]
        if index in by_badge:
            art = replace_crest(unwrap(stored), logos / (by_badge[index] + ".png"))
            stored = wrap(stored,art)
            # O comprimento no TOC exclui o padding depois do fluxo comprimido.
            stored = stored[:16+struct.unpack_from(">I",stored,8)[0]]
        struct.pack_into(">II",result,8+index*12,len(result),len(stored))
        result.extend(stored)
        result.extend(bytes(align(len(result),4)-len(result)))
    name_delta = len(result) - names_start
    for index, offset in enumerate(name_offsets):
        struct.pack_into(">I", result, 8 + index * 12 + 8, offset + name_delta)
    result.extend(raw[names_start:])
    return wrap(parent,result)


def patch_cv(source, destination, mapping, logos):
    archive = Archive(source)
    if archive.names_size:
        raise ValueError("Este reempacotador espera cv.img sem tabela de nomes")
    with source.open("rb") as handle, destination.open("xb") as out:
        replacements = {i:patch_badges(archive.read(handle,archive.entries[i]),mapping,logos)
                        for i in (2710,2711)}
        first = next(item.offset for item in archive.entries if item.size)
        handle.seek(0)
        out.write(handle.read(first))
        index = []
        for i,item in enumerate(archive.entries):
            start = out.tell()
            size = len(replacements[i]) if i in replacements else item.size
            index.append((start,size))
            if i in replacements:
                out.write(replacements[i])
            elif size:
                out.write(archive.read(handle,item))
            if size:
                out.write(bytes(align(out.tell(),2048)-out.tell()))
        out.seek(8)
        for pair in index:
            out.write(struct.pack("<II",*pair))
        original_footer_index = next(i for i,item in enumerate(archive.entries)
                                     if item.offset == archive.names_offset and item.size)
        out.write(struct.pack("<II",index[original_footer_index][0],0))
