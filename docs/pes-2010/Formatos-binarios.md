# Formatos binários verificados

O verificador (`verificar_recursos.py`, na área de trabalho local) lê o JAR diretamente, segue as referências e imprime as contagens. Use `python3 analise-midp/verificar_recursos.py pes_2010_800x480_162221.jar` a partir da pasta do JAR. Os offsets começam em zero e as palavras usam ordem big-endian.

| Entrada | Estrutura conferida |
|---|---|
| `m` | Primeiros 22 bytes com 11 referências relativas ao byte 1511. Cada grupo começa com uma contagem de um byte e contém offsets de dois bytes para `o`. As listas têm 326 entradas contando repetições, com 138 offsets de equipe distintos. |
| `o` | Cada equipe tem 16 referências de dois bytes para `p`, a partir do deslocamento 116 no registro. A partir de 149 são lidos dois nomes em UTF modificado. |
| `p` | Foram alcançados 1.995 registros distintos. Os três primeiros bytes contêm seis atributos de quatro bits. Seguem um byte de posição preferida e cor, um byte de posições possíveis e um nome com prefixo de tamanho. |
| `1` a `6`, `x`, `y` | Textos com comprimento em bytes de dois octetos e UTF modificado do Java. Cada idioma tem exatamente 449 textos e os arquivos de créditos e licenças têm 18 e 62, respectivamente. |
| `r` | Cabeçalho de dez grupos com quatro bytes cada. Cada grupo traz três componentes e a quantidade de variantes. As 24 variantes têm 32 bytes cada, com dez trios de coordenadas/tipo e um offset para `s`. O goleiro é posicionado à parte. |
| `s` | 19 tabelas distintas são alcançadas pelas variantes em `r`. Cada uma começa com a contagem de ligações. Cada byte seguinte conecta dois índices de jogadores, um em cada nibble. O motor deriva uma distância de referência para cada ligação. |
| `v` | O intervalo de 0 a 865 contém 14 matrizes, precedidas por uma contagem. Cada matriz começa com número de linhas e colunas de dois bytes, seguido pelos valores de 16 bits. Todas têm duas colunas. O intervalo de 866 a 1621 é carregado como dados de mergulho do goleiro. |

A estrutura de `r` e `s` explica como a formação continua reconhecível durante o jogo. Os dez pontos iniciais indicam posições de linha. As ligações fornecem distâncias de referência para o movimento relativo entre jogadores. Isso combina com o ajuste de escala e o espelhamento por equipe no código.

Referências: `catálogo` (`cGame.java:1886`), `formações` (`cGame.java:2516`), `ligações` (`cPlayer.java:6537`), `leitura dos roteiros` (`cPlayer.java:5273`). Ainda faltam a semântica de todos os campos do catálogo e dos roteiros e a decodificação completa dos atlas, sons e saves.
