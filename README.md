# PES Java (reconstrução de base)

Este repositório foi reorganizado para voltar a um formato de desenvolvimento, partindo de artefatos compilados (`.class`) e recursos extraídos.

## O que foi feito

- `src/decompiled/`: saída de desassemblagem/decompilação via `javap -v -c -p` para as classes `a` a `h`.
- `src/main/resources/`: estrutura de recursos organizada por tipo (`lang`, `images`, `data`, `META-INF`).
- `src/main/resources/RESOURCE_INDEX.md`: índice dos arquivos binários **omitidos** em `src/main/resources` (com tamanho e SHA-256), apontando para os artefatos originais na raiz do repositório.

> Observação: neste ambiente não há decompilador Java de alto nível disponível (CFR/Procyon/JADX), então a reconstrução de código-fonte foi feita no nível de bytecode/disassembly para servir como base de engenharia reversa.

## Estrutura

```text
src/
  decompiled/
    a.javap.txt
    b.javap.txt
    c.javap.txt
    d.javap.txt
    e.javap.txt
    f.javap.txt
    g.javap.txt
    h.javap.txt
  main/
    resources/
      META-INF/
      RESOURCE_INDEX.md
      lang/
        .gitkeep
      images/
        .gitkeep
      data/
        s
        supplied by D@nilYcH.ini
```
