# MIDP Web

Este projeto executa um JAR MIDP local na JVM do computador com uma camada de compatibilidade escrita neste repositório. O navegador recebe quadros PNG e envia eventos de toque e teclado pelo servidor local. O código do jogo e os recursos são carregados diretamente do JAR.

## Rodar

É necessário Java 21 ou posterior com o módulo `jdk.compiler` e suporte a Java 2D. No checkout local em que o runtime foi implementado, execute a partir da pasta que contém `midp-web`:

```bash
./midp-web/run.sh
```

O endereço padrão é http://127.0.0.1:8771/. Para escolher o JAR e a porta:

```bash
./midp-web/run.sh /caminho/do/jogo.jar 8772
```

Use clique ou toque diretamente sobre a tela do jogo. As setas e Enter correspondem ao direcional e à tecla de confirmação. Q e E correspondem às teclas de função esquerda e direita. Tela cheia amplia a área da tela. Suavizar ativa interpolação do navegador; desligado, preserva as bordas dos pixels.

O processo local precisa permanecer aberto enquanto houver uma sessão. O servidor só escuta em loopback e foi projetado para um único jogador por processo. Use apenas JARs de confiança, pois eles executam no processo Java local.

## Camadas

- `src/javax/microedition` implementa o subconjunto das APIs que o JAR usa. A tela mantém uma fila de eventos com toque, teclas, pintura e chamadas em série. Imagens e recortes passam por Java 2D.
- `src/Launcher.java` lê o manifesto, carrega o MIDlet, publica o último quadro e encaminha eventos. As gravações RMS ficam na pasta local `saves/`.
- `web/` trata a exibição e converte coordenadas CSS para o espaço físico de 480×800. Tela cheia e suavização operam na apresentação.

A implementação de mídia é silenciosa. A JVM local e o subset de MIDP ainda têm de ser avaliados com outros JARs. A opção de suavização interpola o quadro existente. Imagens realmente HD exigem arte em maior resolução e um compositor que conheça os recortes dos atlas sem alterar as coordenadas de jogo. A interface Web tem resolução independente e já pode receber acabamento visual próprio inspirado em celulares da época.

## Validação com PES 2010

Em um perfil RMS novo, o JAR apresentou os menus de idioma, controle e som. A sequência de toques abriu o jogo instantâneo e pulou a entrada das equipes. Depois de aparecer o controle de pontapé de saída, um toque na posição física (240, 620) colocou a bola em jogo. A captura mostrou o relógio em 00:23 com jogadores em movimento.

## Fluxo de execução

1. A JVM abre o JAR, lê `MIDlet-1` no manifesto e instancia a classe indicada.
2. O MIDlet chama a API de compatibilidade `Display` e entrega a tela a um `Canvas`.
3. Java 2D desenha os quadros. O servidor local envia o último quadro em PNG e recebe eventos de entrada da mesma origem.
4. O navegador mostra cada quadro e converte o ponto tocado no elemento para pixels do Canvas de 480×800. Tela cheia e interpolação afetam a apresentação.
5. A implementação RMS serializa registros no computador por nome de JAR. A edição de 2026/27 tem seu próprio diretório de saves.

O primeiro protótipo Web ajudou a testar controles e um passo de simulação de 13 Hz. O runtime próprio executa diretamente a classe original dentro da JVM. Os testes do FreeJ2ME-Plus em [Validação em emulador](Validacao-em-emulador.md) serviram para comparar o fluxo e identificar as coordenadas de toque.
