# Previsões definidas antes dos ensaios da cadeia

A planta permanece em malha aberta. Nenhuma saída do instrumento retorna à bomba nem aos orifícios. Em todos os ensaios a referência é o nível dos nós da mesma execução (h = V/10); a referência ideal deve coincidir.

## R1: números de projeto

- A faixa de projeto da E01 é 0,10 a 1,20 m, equivalente a 0,981–11,772 kPa manométricos em água com ρ = 1000 kg/m³, g = 9,81 m/s².
- No ponto nominal, τ₁ = τ₂ = 100 s, polo de 0,00159 Hz, e a cascata de h₂ tem corte a 0,00102 Hz. Na faixa, τᵢ = 100√hᵢ s, com τ mínimo de 31,6 s (0,00503 Hz). O pulso de 30 s motiva observar até cerca de 1/30 = 0,033 Hz; não se trata de um limite espectral rígido para o degrau.
- Um degrau de vazão de 1% leva o equilíbrio de 1,0000 para 1,0201 m. Para distinguir a menor excursão definida na E01, propomos resolução ≤2 mm (~10 incrementos na excursão) e incerteza expandida alvo U(k=2) ≤4 mm (~20% da excursão). São critérios de projeto; verificar U exige calibração e orçamento experimentais.
- O HSC manométrico de 160 mbar alcança 1,631 m de coluna de água. A banda de erro total de ±1% da escala já representa ±16,31 mm, portanto a ficha não garante a meta de 4 mm. A precisão BFSL de ±0,25% vale em condições de referência e não equivale à banda de erro total.

## R5: previsões quantitativas isoladas

Usaremos o ensaio E02 r3a (degrau de +5%), mantendo o resto da planta e a cadeia idealizados. A excitação e as escalas nominais permanecem iguais.

| Efeito isolado | Níveis | Previsão |
|---|---|---|
| Deslocamento de zero equivalente | +6 / +20 / +60 mm | Erro de patamar igual ao deslocamento. Cruzamentos em percentuais da excursão, medidos entre o próprio inicial e final, preservam o tempo de subida. |
| Constante de tempo da tomada/sensor | 0,2 / 10 / 60 s físicos | Patamar preservado. A curva sobe mais tarde: para τ muito menor que a escala da planta, atraso de cruzamento ≈ τ; quando τ se aproxima de 100 s, o alargamento da resposta fica visível. O erro transitório é aproximadamente −τ dh/dt para τ pequeno. |
| Interferência periódica pós-sensor | ±2 / ±10 / ±40 mm a 0,8 Hz físicos | Com passa-baixas de 0,2 Hz, amplitude residual ≈ 0,243 vezes a entrada: 0,485 / 2,425 / 9,701 mm, contra a mesma referência filtrada sem interferência. O valor médio sofre pouca alteração. |

A interferência senoidal representa captação periódica repetível na interface, não é uma especificação de ruído do HSC. Os casos de 60 mm, 60 s e 40 mm são hipóteses didáticas de falha/exacerbação.
