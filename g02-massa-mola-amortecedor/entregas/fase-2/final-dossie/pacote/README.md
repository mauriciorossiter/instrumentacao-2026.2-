# Pacote de repetibilidade — Entrega Final, G02 (massa-mola-amortecedor)

ECOM060 Instrumentação Eletrônica · UFAL · 2026.2 · Prof. Maurício Beltrão Rossiter
Pedro Henrique Vieira Giló · Thiago Fellype Marques Laurentino · Caio Oliveira França dos Anjos

## Objetivo

Permitir que uma pessoa de fora repita, só com esta pasta, os itens 4 (malha aberta), 6 (controle com instrumento
real) e 7 (ponto de ruptura) do dossiê, além dos demais. A pergunta é: **um PID que funciona com medição ideal
continua funcionando com a medição do sensor piezo + lock-in?** Não continua: o atraso do filtro do lock-in faz a
malha oscilar, e o desvio de sensibilidade desloca o regime. O item 8 mostra como corrigir.

## Versões

| Ferramenta | Versão |
|---|---|
| TyphoonSim / Typhoon HIL Control Center | 2026.2 (dispositivo VHIL+) |
| Python | 3.12 (numpy, scipy, matplotlib) |
| gcc (opcional, só para `testar_cfun.py`) | qualquer C99 |

## Arquivos

```
pacote/
  README.md                 este arquivo
  e1/                       Entrega 01: caracterizacao.py, estilo.py, instrucoes.md
  e2/                       Entrega 02: modelo.tse, painel.cus, instrucoes.md (equivalente elétrico)
  e3/                       Entrega 03: modelo.tse, painel.cus, instrucoes.md (malha aberta por padrão)
  e4/                       Entrega 04 e Final: modelo.tse, painel.cus, instrucoes.md (sistema completo)
  codigo/                   gemeo.py, analise_final.py, gerar_typhoon.py, validar_tse.py, testar_cfun.py, README.md
  dados/                    um CSV por figura do dossiê + previsoes-item7.json + resultados-final.json
```

## Roteiro

**No TyphoonSim (demonstração)**

1. Abrir `e4/modelo.tse` no TyphoonSim 2026.2 e conferir *Model Settings*: VHIL+, passo máximo 1e-4 s.
2. *Compile* → *Load to VHIL*; abrir `e4/painel.cus` no HIL SCADA; *Start simulation*.
3. **Item 5:** botão **1) Instrumento IDEAL**. O degrau de 10 cm acomoda em ≈ 0,45 s, com sobressinal de 2,4 %.
4. **Item 6:** botão **2) Instrumento REAL**. `x_real` oscila (sobressinal de ≈ 285 %), enquanto `y_med` parece
   "quase certo".
5. **Item 4:** Malha = aberta; Seletor = real; Amplitude = 10; todas as características em "desligado" (chopagem
   ligada); **DISPARAR**. Ligar uma característica por vez e disparar de novo (valores esperados na Tabela 3 do
   dossiê).
6. **Item 7:** Malha = fechada; Seletor = real; características desligadas. Anotar a previsão
   (`dados/previsoes-item7.json`) e digitar `fc_Hz` = 5; 6,5; 7; 10; 15; 17, disparando em cada um. Em seguida
   `fc_Hz` = 10, sensibilidade ligada, `S_real_mVN` = 39,2; 40; 40,8; 41,2.
7. **Item 8:** botões **3)** (só calibração: instável) e **4)** (calibração + correção: atende). Robustez: no
   cenário 4, `fc_Hz` = 0,9 → oscila; `fc_corr_Hz` = 0,85 → volta a atender.

**No gêmeo numérico (todas as figuras e CSV)**

8. `cd codigo && python analise_final.py ../figuras ../dados`: gera `previsoes-item7.json` **antes** das
   varreduras e depois as figuras 03 a 08 e os CSV (≈ 80 s).
9. `python caracterizacao.py ../figuras ../dados` (Entrega 01) e `python analise_e2_e3.py ...` (Entregas 02 e 03).
10. Opcional: `python testar_cfun.py ../e4/modelo.tse tmp` compila o C dos blocos e compara com o gêmeo.
11. Opcional: `python gerar_typhoon.py final ../e4` regenera `modelo.tse` e `painel.cus` a partir do código.

## Rastreabilidade

| Figura / tabela do dossiê | Arquivo no pacote | Ensaio | Passo |
|---|---|---|---|
| Fig. 1 (sistema e equivalente) | diagrama; modelo em `e2/modelo.tse` | — | 1 |
| Fig. 2 (Figura 1 preenchida) | diagrama; blocos em `e4/modelo.tse` | — | 1 |
| Tab. 1 (adaptação do sensor) | `e4/modelo.tse`, `codigo/README.md` | — | 1 |
| Fig. 3 (características) | `dados/fig-03-caracteristicas.csv` | malha aberta, 10 N | 8 |
| Fig. 4 e Tab. 3 (malha aberta) | `dados/fig-04-malha-aberta-isoladas.csv` | (a) degrau, malha aberta | 5, 8 |
| Fig. 5 (controle ideal) | `dados/fig-05-controle-ideal.csv` | (a) degrau 10 cm, seletor ideal | 3, 8 |
| Fig. 6, Tab. 4 (controle real) | `dados/fig-06-controle-real.csv`, `dados/resultados-final.json` | (a), seletor real | 4, 8 |
| Fig. 7, Tab. 5 (ruptura) | `dados/fig-07-ponto-de-ruptura*.csv`, `dados/fig-07-previsao-linear.csv`, `dados/previsoes-item7.json` | (a), varreduras de fc e S | 6, 8 |
| Fig. 8, Tab. 6 (compensação) | `dados/fig-08-compensacao.csv`, `dados/fig-08-compensacao-robustez.csv` | (a), cenários 2 a 4 | 7, 8 |
| Item 8, ruído residual | `dados/resultados-final.json` (`ruido_residual`) | malha aberta, 10 N | 8 |

## Resultado esperado (resumo)

| | ideal | real | real + calibração + correção |
|---|---|---|---|
| erro de regime | 0,0 % | +30 % (oscilando) | −0,2 % |
| acomodação 2 % | 0,45 s | não acomoda | 0,51 s |
| sobressinal | 2,4 % | 285 % | 5,6 % |
| esforço de pico | 20 N | 31 N | 22 N |
