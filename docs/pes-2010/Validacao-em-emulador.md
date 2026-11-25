# Validação do jogo em emulador

Executei o JAR original no frontend Libretro do FreeJ2ME-Plus, sem janela, em 480×800. A sequência navegou por Português, Um toque, som desligado, jogo instantâneo, carregamento e entrada das equipes. O botão **Saltar** levou à tela **Pontapé de saída**, com jogadores, minimapa, placar e controles desenhados. Uma execução exibiu cores alteradas; a repetição documentada abaixo produziu uma imagem legível com cores diferentes da primeira. Também registrou ausência de `/disclaimer` e falta de suporte a AMR-NB durante a abertura. Esses avisos permitiram continuar até o campo. [FreeJ2ME-Plus](https://github.com/TASEmulators/freej2me-plus)

Uma coleta durante a apresentação das equipes registrou 66 imagens diferentes em 5,01 segundos, cerca de **13,2 imagens por segundo**. A coleta compara imagens consecutivas e não conta chamadas internas do motor. Ela confirma a ordem de grandeza da taxa observada nessa cena, sem estabelecer a cadência em um aparelho original.

Em outra execução, no modo Um toque, o toque em **(240, 620)** colocou a bola em jogo. A primeira captura após o toque mostrou o relógio em 00:05, e a captura posterior já mostrou 01:03, com mudança de posição da bola, jogadores e câmera. Nessa sequência houve **67 imagens diferentes em 5,01 s** de partida ativa. O toque seguinte em (400, 290) fez parte da sequência, mas o efeito específico dele não foi isolado do movimento que já estava acontecendo.

## Coordenadas de toque lidas no código

O toque chega em pixels físicos. A função divide os dois eixos por dois antes de testar as regiões abaixo. As desigualdades são estritas. Os códigos são entradas internas cuja interpretação depende da fase da partida. A tabela descreve o código, incluindo regiões ainda sem teste individual no emulador.

| Y lógico | X entre 0 e 80 | X entre 80 e 160 | X entre 160 e 240 |
|---|---:|---:|---:|
| 10 a 101 | 660 | 661 | 662 |
| 101 a 192 | 663 | 664 no modo padrão | 665 |
| 192 a 283 | 666 | 667 | 668 |
| 283 a 332 | 669 | 659 no padrão, 664 em Um toque | — |

Abaixo de Y 332, X menor que 61 simula a tecla de função esquerda e X maior que 179 simula a direita. O toque físico em (38, 680) acionou a tecla esquerda nos menus e pulou a entrada das equipes. Há um tratamento próprio para arrastar no replay. `Entrada por toque` (`cGame.java:773`)

## Reprodução

O script de captura (`capturar_midp.py`, na área de trabalho local) usa Python com Pillow, Java e o arquivo `freej2me_plus-lr.jar` distribuído no ZIP do frontend. Use uma pasta de saída vazia para repetir a configuração inicial. Os tempos podem variar de acordo com a máquina. Os pares são coordenadas físicas e os números isolados são esperas em segundos.

```bash
python3 analise-midp/capturar_midp.py --amostrar 5 \
  /caminho/freej2me_plus-lr.jar pes_2010_800x480_162221.jar /tmp/pes-midp-teste \
  4.5 70,422 38,680 38,680 38,680 240,570 38,680 11 38,680 4 240,620 2 400,290 1
```

Foi usado o build com SHA-256 `8f4366717c77ac941999452316193b7160748aff485e3746d1e0bf43635e4fb9`. [Downloads do FreeJ2ME-Plus](https://github.com/TASEmulators/freej2me-plus/releases/tag/nightlies)
