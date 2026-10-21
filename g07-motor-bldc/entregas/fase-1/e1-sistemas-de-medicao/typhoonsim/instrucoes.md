# Instruções — simulações do G07 (Fase 1, Entrega 01)

Termistor NTC + blindagem no motor BLDC MOONS' R42BLD30L3.

Em ambos os modelos há duas linhas iguais:

- `G07_V_ref`: linha **sem** blindagem
- `G07_V_out`: linha **com** blindagem

A comparação entre as duas mede a atenuação da blindagem.

---

## Como rodar (vale para os dois)

1. Abra o `.tse` no TyphoonSim.
2. Se precisar mudar algum parâmetro, edite no **Model Initialization**.
3. Compile. O console mostra os valores esperados da rodada; se essas linhas não aparecerem, algo está errado.
4. Simule.
5. Dê duplo clique em `Scope1` para ver os gráficos.

---

## Teste 1 — `modelo.tse`

Circuito isolado, sem motor. O ruído é uma senoide de 18 V e a simulação dura 10 ms.

**Rodadas:** mude só estas três variáveis no Model Initialization.

| Rodada | `T_teste` | `f_ruido` | `cobertura` | A esperado |
|---|---|---|---|---|
| 1 | 0 | 10e3 | 0.95 | 26,0 dB |
| 2 | 0 | 20e3 | 0.95 | 26,0 dB |
| 3 | 0 | 40e3 | 0.95 | 26,0 dB |
| 4 (controle) | 0 | 10e3 | 0 | 0,0 dB |
| 5 | 65 | 10e3 | 0.95 | 26,0 dB |
| 6 | 130 | 10e3 | 0.95 | 26,0 dB |

**Como medir:** pule o primeiro ciclo e leia máximo e mínimo com o cursor.

- Amplitude: `|V| = (Vmax − Vmin) / 2`
- DC: `(Vmax + Vmin) / 2`
- Atenuação: `A = 20·log10(|V_ref| / |V_out|)`

**Aprovado se:**

- A ficar entre 25 e 27 dB nas rodadas com cobertura 0.95;
- A ficar ≈ 0 dB no controle (rodada 4);
- o DC de `V_out` for igual ao v_T calculado: 0,104 V a 0 °C, 1,04 V a 65 °C e 2,07 V a 130 °C.

---

## Teste 2 — `modelo1.tse`

Motor R42BLD30L3 em malha fechada, com PWM de 10 kHz. A temperatura varre 0 → 130 → 0 °C em 1 s. Não é preciso mudar nada: basta compilar e simular.

**O que deve aparecer no Scope:**

| Sinal | Esperado |
|---|---|
| `n` | sobe a ≈ 4000 rpm em ~20 ms e fica lá |
| `G07_T_motor` | triângulo 0 → 130 → 0 °C |
| `G07_V_ref` | picos de ≈ ±33 a 35 V nas bordas do PWM |
| `G07_V_out` | sobreposto a `G07_vT_ideal` (0,104 → 2,068 V) |

A simulação leva alguns minutos, e o gráfico pode parecer parado por um tempo. Isso é normal.

---

## Não mexa nestes pontos

- **Atraso de 1 ms na função C `G07_NTC_divisor`:** a fonte do sensor começa em 0 V e só assume v_T depois de 1 ms. Se a fonte for diferente de zero em t = 0, **o motor não parte** no TyphoonSim.
- **Parâmetros do motor, controle e lógica Hall:** são os do R42BLD30L3, já validados.
- **Aviso do `Carrier` no console** ("Number of signal samples might be insufficient"): é do modelo original e pode ser ignorado.
