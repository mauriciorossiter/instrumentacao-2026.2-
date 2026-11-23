# Código externo e scripts — G02 (massa-mola-amortecedor)

ECOM060 Instrumentação Eletrônica · UFAL · 2026.2

## Blocos C function dentro do `modelo.tse`

Não há DLL nem arquivo-fonte externo: todo o código está nos blocos C function do próprio `.tse`.
Usamos C function só onde a biblioteca nativa não resolve.

| Bloco | O que faz | Por que não é nativo |
|---|---|---|
| `gerador_ensaios` | ensaios (a) degrau, (b) condição inicial, (c) pulso, (d) perturbação; o relógio reinicia na borda de subida de `disparo` | reiniciar o ensaio pelo SCADA sem recompilar |
| `portadora_chopper` | portadora √2·sin(2π·100·t), ou 1 sem chopagem | liga/desliga da chopagem pelo SCADA |
| `sensor_piezo` | camada estática: sensibilidade real, limiar (0,02 N), resolução (0,01 N) | quantização e zona morta com chaves |
| `ruido_branco` | ruído gaussiano, xorshift32 + Box-Muller, semente fixa | a biblioteca não tem ruído gaussiano que compile para o HIL |
| `interferencia` | offset 3 mV + deriva 5 mV a 0,05 Hz + 60 Hz de 20 mV | chaves e amplitudes editáveis |
| `condicionamento_lockin` | pré-amp G, demodulação síncrona, Butterworth de 2ª ordem com **fc ajustável pelo SCADA** (Tustin a 10 kHz) | a função de transferência nativa não muda fc em execução |
| `processamento_compensacao` | escala K = 1/(S_nom·G), calibração de 1 ponto, correção calculada da dinâmica do filtro | idem |
| `controlador_PID` | PID com derivada na medição, filtro Tf = 10 ms, saturação de ±60 N, anti-windup | malha aberta/fechada e ganhos pelo SCADA |
| `seletor_ideal_real` | escolhe a leitura que vai ao controlador | — |

Planta (`L_massa`, `R_amortecedor`, `C_mola`), piezo (`Vs_piezo`, `Ct_piezo`, `Rin_preamp`), medidores e
entradas SCADA são componentes nativos.

## Scripts Python (Python 3.12, numpy, scipy, matplotlib)

| Script | Uso | Saída |
|---|---|---|
| `gemeo.py` | gêmeo numérico: a mesma cadeia do `.tse`, passo a passo a 10 kHz | módulo |
| `analise_final.py` | `python analise_final.py <figuras> <dados>` | figuras 03 a 08 do dossiê, CSV, `previsoes-item7.json` |
| `caracterizacao.py` | `python caracterizacao.py <figuras> <dados>` | figuras e CSV da Entrega 01 |
| `analise_e2_e3.py` | `python analise_e2_e3.py <fig_e2> <dados_e2> <fig_e3> <dados_e3>` | figuras das Entregas 02 e 03 |
| `analise_f1e3.py` | `python analise_f1e3.py <figuras> <dados>` | figuras da Fase 1, Entrega 03 |
| `gerar_typhoon.py` | `python gerar_typhoon.py <f1e3\|e2\|e3\|final> <pasta>` | `modelo.tse` e `painel.cus` |
| `validar_tse.py` | `python validar_tse.py <modelo.tse>` | confere terminais e ligações |
| `testar_cfun.py` | `python testar_cfun.py <modelo.tse> <pasta>` (precisa de gcc) | compila o C dos blocos e compara com o gêmeo |
| `estilo.py` | cores e estilo das figuras | módulo |

`pip install numpy scipy matplotlib` basta. As previsões do item 7 são gravadas em JSON, com data, **antes**
das varreduras simuladas (`analise_final.py`, bloco "previsoes").

## Conferência do código C

`testar_cfun.py` extrai o código C de cada bloco do `modelo.tse`, compila com `gcc -std=c99 -Wall` (sem avisos)
e roda a malha completa em C. A diferença máxima no deslocamento contra `gemeo.py` foi de 0,02 cm nos cenários
ideal, real e real compensado.
