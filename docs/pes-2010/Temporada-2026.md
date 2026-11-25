# Edição local da temporada 2026/27

A edição de 25 de novembro de 2026 atualiza 89 dos 104 clubes do catálogo, com 16 jogadores por clube. O pacote contém escudos para a seleção de equipe e o placar. As cores dos uniformes principal e alternativo foram ajustadas para 24 clubes nos moldes existentes. Cores, listras e detalhes são aproximações. Os escudos são redimensionados para os pequenos espaços disponíveis no Canvas. As bandeiras do estádio e as competições históricas usam os dados da edição original.

As 16 vagas preservam a estrutura tática do clube. A seleção prioriza posição e partidas registradas na fonte até a data da coleta. Atributos, aparência do jogador e numeração seguem os slots do motor Java. Alguns nomes são abreviados para caber na interface. As seleções nacionais e os clubes sem base confirmada de 2026 conservam seus registros originais.

## Jogar na área de trabalho do projeto

```bash
./midp-web/run.sh midp-web/season-2026/local/PES-2010-temporada-2026.jar 8774
```

Abra http://127.0.0.1:8774/ e selecione **Um jogador → Modo encontro** para escolher dois clubes. Os saves da edição usam um diretório separado. Os escudos atualizados são carregados pelo runtime próprio.

## Refazer o pacote na área de trabalho do projeto

```bash
python3 midp-web/season-2026/fetch.py /tmp/clubes-2026
python3 midp-web/season-2026/build.py pes_2010_800x480_162221.jar /tmp/clubes-2026 \
  midp-web/season-2026/local/PES-2010-temporada-2026.jar
```

O gerador usa Python com Pillow e grava ao lado do JAR um relatório JSON com a fonte de cada elenco e escudo, a seleção de jogadores e a indicação de paleta ajustada. O relatório reflete os dados disponíveis no momento da consulta. O gerador cria uma cópia, reempacota o catálogo e ajusta os dois comprimentos de leitura do recurso de jogadores. As coordenadas dos elementos gráficos e o código de jogo seguem a versão de entrada.

Fontes de referência para a temporada e os uniformes. [Elencos da Premier League](https://www.premierleague.com/en/news/4706139/see-all-the-202627-premier-league-squad-lists) · [Elenco do Arsenal na ESPN](https://www.espn.co.uk/football/team/squad/_/id/359/arsenal) · [Uniformes da Premier League](https://www.premierleague.com/en/news/4672981/premier-league-club-kits-for-202627-season) · [Uniforme do Barcelona](https://store.fcbarcelona.com/pages/fc-barcelona-home-kit-26-27) · [Loja da LALIGA](https://laligastore.com/en/collections/official-kits)

## Teste no runtime

Selecionei Arsenal e Liverpool, abri a tela de uniformes e dei a saída de bola. O placar usou os escudos novos e o nome de Gyökeres apareceu no campo.

Confira a [cobertura de clubes e fontes](Clubes-2026.md).
