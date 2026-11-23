# Roteiro do vídeo — Fase 1, Entrega 03 (5 a 8 min)

Gravação contínua de tela com narração (OBS ou similar), em 1080p. Na tela: TyphoonSim/HIL SCADA com
`typhoonsim/painel.cus` e, quando indicado, os slides de `apresentacao/apresentacao.pdf`. **Todos os integrantes
falam.** Pelo menos um controle do SCADA é operado ao vivo (vários, na verdade).

Antes de gravar: compilar e carregar `typhoonsim/modelo.tse` no VHIL, abrir o painel, iniciar a simulação e deixar
a janela do gráfico em 6 s.

| Tempo | Quem | Tela | Fala / ação |
|---|---|---|---|
| 0:00–1:00 | Pedro | slides 1–2, depois o esquemático | Apresentar a cadeia: força em N rms modulada a 100 Hz, piezo 7BB-20-6 (S nominal de 40 mV/N, Ct–Rin), pré-amp ×25, lock-in com Butterworth de 1 Hz. As três camadas da E02: estática, dinâmica e espectral. Mostrar no esquemático onde está cada uma. |
| 1:00–2:00 | Thiago | painel | **Ensaio (a):** combo = (a), Amplitude = 0,6, DISPARAR. Descrever: o medido segue o ideal com ≈ 0,3 s de atraso e fica em 0,37 N (−38 %, sensibilidade real). Ligar a **calibração** e disparar de novo: vai a 0,60 N. |
| 2:00–3:00 | Thiago | painel | **Ensaio (b):** a cadeia carregada com 0,6 N e a força retirada em t = 1 s. Resposta livre: decai suavemente a zero em ≈ 1 s, sem oscilar (Butterworth com ζ = 0,707). |
| 3:00–4:00 | Caio | painel | **Ensaio (c):** pulso de 0,9 N por 0,5 s. O pulso chega atenuado e atrasado, e o patamar volta ao original. O lock-in alisa transitórios rápidos. |
| 4:00–5:00 | Caio | painel | **Previsão e teste:** "Vou mudar a amplitude para 1,0 N. Sem calibração, prevejo 1,0 × 0,615 = 0,615 N". Digitar 1,0 e disparar → ≈ 0,62 N. Confirmado. |
| 5:00–6:00 | Pedro | painel + slide 5 | **Síntese R13:** desligar todas as camadas e ligar uma por vez. A estática é a que mais afasta (−38 %). A dinâmica seria a pior (sem chopagem a leitura some: mostrar com a chopagem desligada), mas a chopagem a anula. A espectral deixa só ≈ 7 mN rms. Coerente com o piezo: tolerância grande, não mede força estática, e a detecção síncrona rejeita offset e 60 Hz. |
| 6:00–6:20 | Todos | slide 6 | Fechamento: arquivos e roteiro no GitHub, mini relatório com o índice de tempos. |

Depois de gravar: subir o vídeo (YouTube não listado ou Drive com permissão para o professor), colar o link em
`relatorio/mini-relatorio-video.pdf` (item 2; o PDF tem o campo reservado) e em `video/link.md`, e conferir o índice
de tempos com o vídeo final.
