# Como funciona o PES 2010 para Java MIDP

O motor simula um jogo de futebol em coordenadas inteiras e desenha o resultado com sprites 2D em perspectiva. Há três níveis de decisão. O aplicativo escolhe qual tela está ativa, o árbitro determina em que fase a partida está, e cada jogador escolhe ou executa uma ação dentro daquela fase.

A análise usa o arquivo `pes_2010_800x480_162221.jar`. O manifesto identifica PES 2010, versão 1.0.0, build 2066, fornecedor Connect2Media, MIDP 2.0 e CLDC 1.0. SHA-256 do JAR: `02f977697922f7a5dccd05aa9181067f0b943c227cb0e2c82eb4fe4bee0da1aa`.

## Como navegar pela análise

- [Índice das oito classes e de suas rotinas](Indice-do-codigo.md)
- [Tabela dos estados da interface de 0 a 85](Estados-da-interface.md)
- [Inventário de todas as entradas do JAR](Inventario-do-JAR.md)
- [Formatos binários conferidos diretamente no pacote](Formatos-binarios.md)
- [Execução e testes de toque em emulador](Validacao-em-emulador.md)

O Java gerado localmente na pasta `referencia` foi recuperado com Vineflower 1.10.1. Usei também CFR 0.152 para comparar rotinas centrais. Os nomes das classes e boa parte dos campos e métodos vieram do binário. Nomes locais como `var17` foram produzidos pelo descompilador. Em geral, `s` indica membro estático, `m` indica membro da instância e `a2` sugere matriz. A análise do código é complementada por testes com o JAR original no emulador e pela leitura direta de parte dos recursos. Ainda faltam validar todos os gestos por contexto e decodificar os demais campos binários. A compilabilidade da saída Java também não foi verificada.

## Reprodução da leitura

Com uma cópia local do JAR e o Vineflower 1.10.1, execute:

```bash
java -jar vineflower-1.10.1.jar --folder pes_2010_800x480_162221.jar referencia
```

As referências a nomes e linhas nesta documentação usam essa saída. O manifesto do PES 2008 que já existe neste repositório identifica outra edição.

## As oito classes

| Classe | Responsabilidade |
|---|---|
| `a` | MIDlet. Cria a tela, responde ao ciclo de vida e opera o áudio MIDP. |
| `cGame` | Tela, entrada, menus, fluxo de carregamento, competições, desafios, edição, recursos e saves. |
| `cPitch` | Partida. Controla relógio, árbitro, organização coletiva, câmera, HUD e replay. |
| `cPlayer` | Jogador. Converte intenções humanas ou da CPU em movimento, animações e ações com a bola. |
| `cBall` | Bola única. Guarda posição, velocidade, efeito, previsão, colisões e desenho. |
| `cGraphicEngine` | Desenha gramado, camadas do estádio e componentes do cenário. |
| `cSprite` | Guarda quadros de animação, módulos de imagem e posição na animação. |
| `cMath` | Trigonometria por tabela, distâncias, interseções, raízes e números aleatórios. |

## Da abertura até o primeiro toque

1. O MIDP instancia `a` pelo manifesto. A classe cria `cGame` e inicializa o áudio em uma thread própria. Em `startApp`, torna o Canvas a tela atual e inicia a primeira solicitação de pintura.
2. O Canvas começa no estado 66, a tela de aviso. A interface avança por telas de abertura e configuração. A máquina de estados roda a saída da tela antiga, a entrada da nova e a ação do quadro. Um `long` guarda o histórico em blocos de 7 bits para a operação de voltar.
3. A escolha de modo determina quais telas de seleção e quais recursos serão usados. O estado 7 carrega a partida por etapas. A escalação pode trabalhar com até 16 jogadores no menu por equipe. Em campo, o código cria 22 instâncias e liga os titulares aos respectivos elencos.
4. O estado 63 configura a partida ativa. Cada quadro atualiza a simulação em `cPitch.sUpdate` e desenha em `cPitch.sDisplay`. O estado 62 trata a pausa e o 64 trata o replay. O menu de formação durante a partida tem estado próprio, 47.
5. `paint` dirige o trabalho e agenda a próxima passagem via `Display.callSerially`. Há metas de 11 quadros por segundo na inicialização e 13 ao entrar em partida ou replay. As chamadas de espera e o custo da pintura afetam a cadência real.

Evidência: `entrada` (`a.java:28`), `carregamento` (`cGame.java:5615`), `partida` (`cGame.java:10153`), `máquina de telas` (`cGame.java:10307`), `pintura` (`cGame.java:11940`).

## O que acontece num quadro de partida

Em termos humanos, o jogo primeiro examina o que a bola fez, depois organiza as equipes ao redor dessa situação, aplica as decisões do árbitro e avança os jogadores. A ordem importa porque jogadores e bola compartilham o último toque, o último chute, o jogador controlado e a fase do árbitro.

1. Se estiver em pausa ou replay, a atualização normal retorna. Quando o relógio está autorizado a correr, soma um quadro ao tempo e credita posse ao time do último jogador a tocar na bola.
2. `cBall.sBallUpdate` avança a bola e testa contatos. O técnico ajusta as linhas táticas em função da bola e do lado em vantagem. A grade de ocupação e as notas de posição são atualizadas a cada quatro quadros.
3. Em quadros alternados, o jogo procura jogadores aptos a chegar a posições futuras da bola. Ele testa distância e altura, com regras distintas para goleiro e jogador de linha. Essa previsão alimenta a escolha de quem disputa a jogada.
4. O árbitro muda a fase do jogo conforme o evento. A atualização individual de cada jogador aplica as decisões de controle, da IA ou de uma sequência roteirizada. A apresentação vem depois.

### Entrada, jogador e IA

O Canvas recebe teclado e toque e traduz os eventos para máscaras. No início do quadro ele deriva sinais adicionais a partir da duração e da liberação do toque. `cPlayer` interpreta esses sinais conforme a ação disponível. Portanto, coordenadas de toque e códigos MIDP pertencem à entrada, enquanto as decisões de correr, passar, chutar, desarmar e trocar de jogador pertencem à partida. A configuração de controle de um toque muda o tratamento dessas intenções.

A CPU tem decisões coletivas e individuais. O técnico escolhe candidatos, dá referências de formação e atribui responsabilidades de cobertura. O jogador executa estados como drible, recepção, apoio, defesa, espera, reposição e defesa do goleiro. A camada de movimento orienta o corpo, busca alvos, evita jogadores e respeita restrições de formação ou de bola parada. Passe em profundidade, tabela, chute e desarme têm rotinas próprias. Ações podem depender de alcance, ângulo, posse, atributos e fase da animação. `mStateScriptExecute` interpreta passos usados em sequências específicas, por isso um estado de animação pode ter efeito na simulação.

Evidência: `toque` (`cGame.java:773`), `teclado` (`cGame.java:1373`), `atualização individual` (`cPlayer.java:183`), `roteiros` (`cPlayer.java:5299`).

### Bola e árbitro

A bola mantém `x` e `y` no gramado e `z` para a altura. O eixo longitudinal do campo é `x`, na direção dos gols. A cada passo o código calcula a próxima posição e trata chão, estruturas do gol, elementos laterais e jogadores. Na fase aérea, um ramo reduz a velocidade vertical em 15 unidades por passo, aplica perda de velocidade e altera a direção conforme o efeito. Há caminhos distintos para bola presa a um jogador, domínio e toque. Boa parte das escalas usa inteiros com fatores de 256, com escalas diferentes na projeção.

Há funções separadas para prever posição e prever gol. O árbitro usa os contatos, as linhas e o estado da bola para tratar saída, reposição, gol, falta e pênalti. No impedimento, calcula linhas, registra candidatos no passe e verifica o envolvimento do recebedor no contato. Um gol segue para a contabilização do placar e de autoria antes dos fluxos de celebração e reposição. Os métodos do árbitro também preparam a posição de jogadores para bolas paradas. A regra é parte da máquina de estados, então a geometria isolada de uma colisão não basta para reproduzir o jogo.

Evidência: `estado da bola` (`cBall.java:235`), `registro de gol` (`cPitch.java:4499`), `árbitro` (`cPitch.java:4578`).

## Imagem, câmera, replay e áudio

O construtor usa 480×800 e cria um buffer de 240×400. A última etapa da pintura lê os pixels e duplica cada um em um bloco 2×2. A faixa 240×348 aparece como região usada pela partida. O método de mudança de tamanho detecta a orientação horizontal e aciona a lógica de aviso. Isso explica por que o nome do arquivo tem dimensões em outra ordem.

Na projeção, a profundidade no plano altera a escala, e a altura da bola desloca sua posição desenhada. A câmera acrescenta o deslocamento na tela. A apresentação compõe gramado, estádio, jogadores, sombras, bola e HUD usando imagens e recortes. A ordem de composição é importante para saber o que aparece atrás de cada elemento. Há conversão separada para minimapa. O replay registra instantâneos em um buffer com 130 posições e lê câmera, bola e desenhos dos jogadores para reproduzir os quadros. O caminho de visualização preserva o estado que estava ativo antes do desenho do instantâneo.

O áudio usa a API de mídia MIDP. Os trechos vêm de um pacote e o primeiro byte do trecho escolhe MIDI ou AMR. A rotina de áudio lê pedidos para tocar ou interromper música e efeitos e verifica o status do player MIDP.

Evidência: `pintura` (`cGame.java:11940`), `leitura de replay` (`cPitch.java:1954`), `gravação de replay` (`cPitch.java:2557`), `render do estádio` (`cGraphicEngine.java`), `áudio` (`a.java`).

## Modos, dados e saves

A interface tem caminhos para partida rápida, seleção de equipes e uniformes, formação e substituições, competições, treinamento, desafios de falta e gol mais rápido, missões, edição de equipe e galeria. `sCompetition*` concentra tabela, chaveamento, próximos jogos, classificação e artilharia. Há simulação de partidas que a pessoa não controla. Menus, tela de formação e partida têm estruturas relacionadas, mas nem todos os atributos são mantidos no mesmo objeto durante todo o fluxo.

| Recurso | Uso identificado |
|---|---|
| `0` | Pacote misto com itens de interface, fontes/imagens e áudio. |
| `1`–`6` | Tabelas de 449 textos por idioma, lidas com `DataInputStream.readUTF`. |
| `j`–`l` | Gráficos de interface e telas de formação. `k` também serve às rotinas de competição. |
| `m`, `n` | Catálogo de grupos e offsets de competições, logotipo de grupo e imagens de bandeiras. |
| `o`, `p`, `q` | Registros de equipe, registros de jogadores e gráficos de bandeiras/uniformes. |
| `r`, `s` | Formações do menu e posições usadas no campo, respectivamente. |
| `t`, `u` | Recursos do campo e da interface da partida, além de bola e imagens usadas nas fases do árbitro. |
| `v`, `w` | Recursos de jogadores e animações, além de cenário e ícones de partida. |
| `x`, `y`, `z` | Créditos, licenças e ícone do MIDlet. |

Os loaders trabalham com offsets e comprimentos fixos. Uma entrada com assinatura PNG no início pode conter muitas imagens e outros dados em sequência. Para certas imagens indexadas, o código altera a paleta e recalcula o CRC antes de criar a imagem MIDP. Cada registro de equipe em `o` oferece, a partir do byte 116, 16 referências de dois bytes em big-endian para registros de jogador em `p`. No byte 149 começam dois nomes em UTF modificado. O registro de jogador começa com três bytes que empacotam seis atributos de quatro bits. Depois vêm posição preferida e cor no mesmo byte, máscara de posições e nome em UTF modificado.

Configurações e progresso usam RMS `RecordStore`, registro 1 por chave. `cnf` tem 21 bytes de configuração. `fgc` e `fkc` têm 25 bytes de recordes. `fkcp` tem 9 bytes de progresso do desafio de falta. `cup`, `lg`, `sc` e `uefa` são saves de competição. Há também serialização para equipe editada. O código contém ramos para propriedades de demonstração e divulgação do MIDlet. O manifesto fornecido não declara essas propriedades.

Evidência: `RMS` (`cGame.java:1807`), `equipe` (`cGame.java:1863`), `textos` (`cGame.java:2806`), `estádio` (`cGraphicEngine.java:49`).

## Como aproveitar isso num projeto próprio para PC ou Web

A primeira entrega de engenharia pode ser uma partida de teste com equipes e arte próprias, campo simples e a câmera desligável. O mesmo núcleo pode rodar sem janela para testar a sequência de entradas. Na Web, Canvas 2D serve para a primeira apresentação e IndexedDB para progresso estruturado. No PC, um frontend desktop pode consumir as mesmas ações e instantâneos.

1. Modele o relógio de simulação e as ações de controle. Defina quando o botão foi apertado, mantido e solto. Registre entradas com o número do passo.
2. Para estudar a sensação do original, compare primeiro aritmética e ordem de atualização. Se usar JavaScript, inclua casos para multiplicação com overflow de 32 bits, divisão inteira, promoção para `long` e deslocamentos com sinal. Faça a simulação avançar independentemente dos quadros de desenho.
3. Implemente movimento, contato com a bola e os eventos de partida. Os primeiros cenários comparáveis são bola parada, passe rasteiro, chute aéreo, defesa, gol e saída pela lateral. Registre posição, velocidade, fase do árbitro e último toque após cada passo.
4. Introduza comportamento tático em camadas. Comece com busca de jogador elegível e ocupação defensiva. Depois acrescente apoio, cobertura, movimentação sem bola, goleiro e decisões de passe ou chute.
5. Use instantâneos para câmera, desenho e replay. Acrescente menus, competições e armazenamento depois que a partida de teste for reproduzível.

Para uma validação futura em emulador, vale observar primeiro o tempo real entre quadros, a correspondência dos toques por contexto, os caminhos de reposição e a duração das animações. A comparação quadro a quadro permitiria confirmar as interpretações de sinais e constantes que hoje se apoiam na leitura estática.
