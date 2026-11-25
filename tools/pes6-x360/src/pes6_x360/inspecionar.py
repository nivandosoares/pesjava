#!/usr/bin/env python3
"""Inspeciona os contêineres do PES 6 Xbox 360 em modo somente leitura."""
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
import struct
import zlib


@dataclass
class Entry:
    offset: int
    size: int
    name: str = ""


class Archive:
    def __init__(self, path):
        self.path = path
        self.size = path.stat().st_size
        with path.open("rb") as handle:
            magic, count = struct.unpack("<4sI", handle.read(8))
            if magic != b"AFS\0" or 16 + count * 8 > self.size:
                raise ValueError(f"Cabeçalho AFS inválido: {path}")
            self.entries = [Entry(*item) for item in
                            struct.iter_unpack("<II", handle.read(count * 8))]
            self.names_offset, self.names_size = struct.unpack("<II", handle.read(8))
            if self.names_size:
                if self.names_size != count * 48 or self.names_offset + self.names_size > self.size:
                    raise ValueError(f"Tabela de nomes AFS incompatível: {path}")
                handle.seek(self.names_offset)
                for item in self.entries:
                    item.name = handle.read(48)[:32].split(b"\0", 1)[0].decode("ascii", "replace")
        ranges = sorted((item.offset, item.offset + item.size) for item in self.entries if item.size)
        for i, (start, end) in enumerate(ranges):
            limit = self.names_offset if self.names_size else self.size
            if start < 16 + count * 8 or end > limit or (i and start < ranges[i - 1][1]):
                raise ValueError(f"Intervalo inválido na tabela AFS: {path}")

    def read(self, handle, entry, maximum=None):
        handle.seek(entry.offset)
        return handle.read(entry.size if maximum is None else min(entry.size, maximum))

    def inventory(self, deep=False):
        counts = Counter()
        inner = Counter()
        with self.path.open("rb") as handle:
            for entry in self.entries:
                kind = classify(self.read(handle, entry, 16))
                counts[kind] += 1
                if deep and (kind.startswith("WESYS") or kind == "zlib provável"):
                    data = unwrap(self.read(handle, entry))
                    inner["entradas_decodificadas"] += 1
                    inner["entradas_com_tabela_interna"] += bool(parts(data))
                    inner["entradas_com_cabecalho_dds"] += bool(next(dds_headers(data), None))
        report = {
            "arquivo": self.path.name, "bytes": self.size,
            "entradas": len(self.entries), "formatos": dict(counts),
            "nomes": bool(self.names_size),
            "offset_tabela_nomes": self.names_offset if self.names_size else None,
            "entradas_fora_do_alinhamento_0x800": sum(1 for row in self.entries
                                                       if row.size and row.offset % 2048),
        }
        if deep and inner:
            report["analise_interna"] = dict(inner)
        return report


def classify(data):
    if not data:
        return "vazia"
    if data[3:8] == b"WESYS" and len(data) >= 16:
        return {0:"WESYS sem compressão", 1:"WESYS zlib"}.get(data[2], "WESYS desconhecido")
    if data.startswith(b"\x80\0"):
        return "ADX provável"
    if data.startswith(b"AIXF"):
        return "AIX"
    if len(data) >= 2 and data[0] == 0x78 and int.from_bytes(data[:2], "big") % 31 == 0:
        return "zlib provável"
    if data[:4] in (b"KBDS", b"DNBW", b"FSGX"):
        return data[:4].decode("ascii")
    return "outro"


def decompress(data, expected=None):
    decoder = zlib.decompressobj()
    limit = 64 * 1024 * 1024
    decoded = decoder.decompress(data, limit + 1)
    if len(decoded) > limit or not decoder.eof:
        raise ValueError("Fluxo incompleto ou excede 64 MiB")
    if expected is not None and len(decoded) != expected:
        raise ValueError("Tamanho descomprimido difere do WESYS")
    return decoded


def unwrap(data):
    kind = classify(data)
    if kind == "WESYS zlib":
        length, expected = struct.unpack_from(">II", data, 8)
        if length > len(data) - 16:
            raise ValueError("Comprimento WESYS excede a entrada AFS")
        return decompress(data[16:16 + length], expected)
    if kind == "WESYS sem compressão":
        length = struct.unpack_from(">I", data, 8)[0]
        if length != len(data) - 16:
            raise ValueError("Comprimento WESYS sem compressão inesperado")
        return data[16:]
    if kind == "zlib provável":
        return decompress(data)
    return data


def parts(data):
    if len(data) < 8:
        return []
    count, table = struct.unpack_from(">II", data)
    end = table + 12 * count
    if table != 8 or not 0 < count <= 4096 or end > len(data):
        return []
    rows = list(struct.iter_unpack(">III", data[table:end]))
    if any(offset < end or offset + length > len(data) for offset,length,_ in rows):
        return []
    return [{"offset":offset,"bytes":length,"aux":f"{aux:08x}"} for offset,length,aux in rows]


def dds_headers(data):
    for hit in re.finditer(rb"DDS \x7c\x00\x00\x00", data):
        pos = hit.start()
        if pos + 128 > len(data) or struct.unpack_from("<I", data, pos + 76)[0] != 32:
            continue
        height, width = struct.unpack_from("<II", data, pos + 12)
        if 0 < width <= 8192 and 0 < height <= 8192:
            yield {"offset":pos,"largura":width,"altura":height,
                   "fourcc":data[pos+84:pos+88].decode("ascii","replace").strip("\x00")}


def describe(archive, index):
    if not 0 <= index < len(archive.entries):
        raise ValueError("Índice AFS fora do intervalo")
    entry = archive.entries[index]
    with archive.path.open("rb") as handle:
        data = archive.read(handle, entry)
    decoded = unwrap(data)
    return {
        "arquivo": archive.path.name, "indice": index, "nome": entry.name or None,
        "offset": entry.offset, "bytes_armazenados": entry.size, "formato": classify(data),
        "bytes_decodificados": len(decoded), "sha256_armazenado": sha256(data).hexdigest(),
        "partes": parts(decoded), "dds": list(dds_headers(decoded)),
    }, decoded


def compare(base, other):
    if len(base.entries) != len(other.entries):
        raise ValueError("Tabelas com comprimentos diferentes")
    with base.path.open("rb") as first, other.path.open("rb") as second:
        return [i for i, (a, b) in enumerate(zip(base.entries, other.entries))
                if a.size != b.size or base.read(first, a) != other.read(second, b)]
