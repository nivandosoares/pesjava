# PES Java - estrutura pré-build reconstruída

Projeto de pesquisa com código Java preservado e notas de compilação.

## PES 2010

[Artigo ilustrado — Do Java de bolso ao navegador](docs/pes-2010/Artigo.md) · [Documentação técnica](docs/pes-2010/README.md)

## PES 6 para Xbox 360

[CLI de nomes e escudos](tools/pes6-x360/README.md) · [How to update your PES 6 Option File on Xbox 360](docs/pes-6-xbox-360/option-file.md)

## PES 2008

**Arquivos principais**

- [prebuild/](<prebuild/>)

Reconstrução em formato de projeto para continuidade de desenvolvimento reverso.

## Entregas

- `prebuild/src/main/java/*.java`: arquivos `.java` por classe (`a`..`h`) em formato stub para base de reimplementação.
- `prebuild/src/main/resources/assets/lang/*.txt` e `assets/data/*.{txt,ini}`: recursos textuais extraídos.
- `prebuild/src/main/resources/META-INF/MANIFEST.MF`: manifesto preservado.
- `scripts/generate_prebuild_assets.py`: script para gerar localmente os assets binários e arquivos derivados.

## Binários não compatíveis (geração local)

Para evitar versionamento de binários não compatíveis no layout pré-build, os arquivos abaixo são gerados localmente:

- `prebuild/src/main/resources/assets/images/*.png`
- `prebuild/src/main/resources/assets/data/*.dat`

Execute:

```bash
python scripts/generate_prebuild_assets.py
```

## Observações

- Os `.java` foram reconstruídos a partir de `javap` (não são decompilação de alto nível completa).
- Tipos de arquivo foram inferidos por assinatura de bytes (ex.: PNG) e conteúdo.
