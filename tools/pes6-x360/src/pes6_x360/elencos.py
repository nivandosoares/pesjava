#!/usr/bin/env python3
"""Consulta jogadores, elencos e dorsais do PES 6 Xbox 360 em modo leitura."""
from pathlib import Path
import struct

from .inspecionar import Archive, parts, unwrap


def read_parts(archive, index):
    with archive.path.open("rb") as handle:
        data = unwrap(archive.read(handle, archive.entries[index]))
    return [data[row["offset"]:row["offset"] + row["bytes"]] for row in parts(data)]


def text(data):
    return data.split(b"\0", 1)[0].decode("utf-8", "replace")


def name_pairs(archive):
    content, = read_parts(archive, 6666)
    if len(content) != 94 * 130:
        raise ValueError("Tamanho inesperado na tabela de pares de nomes")
    pairs = {}
    for offset in range(0, len(content), 130):
        row = content[offset:offset + 130]
        index, = struct.unpack_from(">H", row)
        if index:
            pairs[index] = {
                "variante_a": text(row[2:48]),
                "variante_b": text(row[48:94]),
                "camisa_a": text(row[94:110]),
                "camisa_b": text(row[110:126]),
            }
    return pairs


def read_database(archive, index):
    records, lineups, shirts, extra = read_parts(archive, index)
    if len(records) % 152 or len(lineups) % 64 or len(shirts) * 2 != len(lineups):
        raise ValueError("Tamanhos de tabelas incompatíveis")
    paired = name_pairs(archive)
    players = []
    for offset in range(0, len(records), 152):
        row = records[offset:offset + 152]
        i = offset // 152
        player = {"indice": i, "nome": text(row[:46]), "camisa": text(row[46:62])}
        if i in paired:
            player["pares_de_nome"] = paired[i]
        players.append(player)
    teams = list(struct.iter_unpack(">32H", lineups))
    if any(index >= len(players) for lineup in teams for index in lineup):
        raise ValueError("Elenco aponta para jogador fora da base")
    return players, teams, shirts, len(extra)


def read_team_names(path):
    data = path.read_bytes()
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[:2] != b"MZ" or data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("Use a imagem PE extraída do XEX")
    start, count, base = 0xD55218, 214, 0x82000000

    def string(pointer):
        offset = pointer - base
        if not (0xAB000 <= offset < 0xAC759 or 0xA0B80 <= offset < 0xA1000):
            raise ValueError("A tabela de times depende da edição do PE")
        end = data.index(b"\0", offset, offset + 96)
        return text(data[offset:end])

    rows = []
    for i in range(count):
        offset = start + i * 24
        name, short, group, id_a, id_b = struct.unpack_from(">IIHHH", data, offset)
        rows.append({"nome": string(name), "sigla": string(short),
                     "campo_grupo": group, "campo_id_a": id_a, "campo_id_b": id_b,
                     "offset_pe": f"0x{offset:X}"})
    if rows[64]["nome"] != "Arsenal" or rows[143]["nome"] != "F.C. Barcelona":
        raise ValueError("A tabela PE não contém as referências esperadas")
    return rows
