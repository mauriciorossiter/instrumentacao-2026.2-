# Simulação — G07, Fase 2, Entrega 02: equivalente elétrico (TyphoonSim e VHIL/SCADA)

Motor BLDC MOONS' R42BLD30L3. O bloco `Brushless DC Machine` da Entrega 01 foi substituído por um circuito equivalente com elementos nativos. A parte mecânica usa a analogia força–tensão: 1 A em `G07_i_omega` = 1000 rpm e 1 V em `G07_v_Te` = 10 mN·m.

## Arquivos

Modelo: `modelo_equivalente.tse` (Typhoon HIL Control Center **2026.3**). Painel do HIL SCADA: `painel_equivalente.cus` (entradas `G07_k_fator` e `G07_dR`, mostrador de `n` e Capture/Scope). O ensaio é escolhido em *Model > Model settings > Model initialization* (`g07_modo` e demais variáveis; manter `g07_Td = 0.02`). Dados: `dados-vhil-e2/` (R3 no Virtual HIL, Capture do SCADA) e `dados-typhoon-e2/` (mesmos ensaios no TyphoonSim).

## Componentes novos no `.tse`

| Nome | Tipo (`core/…`) | Valor |
|---|---|---|
| `G07_ia`, `G07_ib`, `G07_ic` | Current Measurement (saída de sinal, 50 µs) | — |
| `G07_Rs_a/b/c` | Resistor | `Rs` = 1,60 Ω |
| `G07_Ls_a/b/c` | Inductor | `Ls` = 1,90 mH |
| `G07_dR_a/b/c` | Signal Controlled Voltage Source (50 µs) | `G07_dR`·i_x |
| `G07_e_a/b/c` | Signal Controlled Voltage Source (50 µs) | FCEM (k/2)·ω·f(θe) |
| `G07_V_Te` + `G07_KV_Te` | Signal Controlled Voltage Source + Gain | K_V·T_e, K_V = 100 V/(N·m) |
| `G07_i_omega` | Current Measurement | i_m = K_I·ω |
| `G07_L_J` | Inductor | `L_J` = J·K_V/K_I = 34,558 mH |
| `G07_R_B` | Resistor | `R_B` = B·K_V/K_I = 10,472 mΩ |
| `G07_V_carga` + `G07_KV_carga` | Signal Controlled Voltage Source + Gain | K_V·(b2·n² + T_d + partida) |
| `G07_v_Te`, `G07_v_carga` | Voltage Measurement | — |
| `G07_k_fator`, `G07_dR` | SCADA Input | 1 e 0 (R4) |
| `G07_Acoplamento` | C function (10·Ts = 50 µs) | trapézio f(θe), ω·f, Σ f·i, θ_m |
| `G07_E2_ref` | conexão | referencia a malha mecânica ao neutro N (necessária no tempo real) |

## Ensaios (Model initialization)

Em *Model > Model settings > Model initialization*, substituir o trecho de `g07_modo` até `g07_t_p2` pelo bloco do ensaio. Bloco **original** (ensaio (a); voltar a ele no fim):

```
g07_modo = 1
g07_d_ini = 0.0
g07_d_deg = 0.7074
g07_t_deg = 0.0
g07_t_ci = 0.15
g07_d_ci = 0.0
g07_Td = 0.02
g07_t_p1 = 0.10
g07_t_p2 = 0.20
```

Nos outros ensaios, mudar só o que a tabela indica (o restante fica como no bloco original).

| Ensaio | CSV | Mudar no bloco | Esperado no VHIL | Esperado no TyphoonSim |
|---|---|---|---|---|
| (a) degrau do repouso | `vhil_a.csv` | — (bloco original) | ≈ 3658 rpm, t_s ≈ 13 ms, pico ≈ 6,4 A | ≈ 3623 rpm, t_s ≈ 14 ms |
| (a') degrau pequeno | `vhil_a2.csv` | `g07_d_ini = 0.867`, `g07_d_deg = 0.95`, `g07_t_deg = 0.15` | 3919 → 4270 rpm, t63 ≈ 4 ms | 3944 → 4244 rpm |
| (b) CI, d = 0 | `vhil_b.csv` | `g07_modo = 2` | 2535 / 1849 / 1018 rpm em 0,16 / 0,17 / 0,20 s | igual |
| (b') CI, d = 0,55 | `vhil_b2.csv` | `g07_modo = 2`, `g07_d_ci = 0.55` | ≈ 2941 rpm | ≈ 2900 rpm |
| (c) pulso de carga, MA | `vhil_c.csv` | `g07_modo = 3` | 3661 → 3431 rpm (Δn ≈ −230) | 3623 → 3390 rpm |
| (c') pulso de carga, MF | `vhil_c2.csv` | `g07_modo = 4` | ≈ 4000 rpm, mínimo ≈ 3922 rpm | igual |
| malha fechada | — | `g07_modo = 0` | ≈ 3998 rpm | ≈ 3998 rpm |

Não use `g07_d_ci = 0.5` nem o degrau 0,867 → 0,887: o PWM do modelo tem resolução de 0,1 em d (o degrau não aparece ou o resultado depende do arredondamento). A linha `g07_Td = 0.02` é obrigatória (sem ela a compilação falha em `G07_Partida_numerica`).

R4 (SCADA, bloco original, modelo rodando há alguns segundos): nominal ≈ 3458 rpm; `G07_k_fator` = 0,896 → ≈ 3570 e 1,3375 → ≈ 3068 rpm; `G07_dR` = −1,1 → ≈ 3700 e 0,63 → ≈ 3319 rpm. Voltar a `G07_k_fator` = 1 e `G07_dR` = 0 no fim.

## Como executar no VHIL/SCADA

1. Abrir `modelo_equivalente.tse` no Schematic Editor, perspectiva **tempo real** (*View > Change perspective*).
2. Ajustar as variáveis do ensaio, compilar e conferir no console `modo de ensaio = …` e `L_J=0.034558 H R_B=0.010472 ohm`.
3. Abrir o HIL SCADA, carregar `modelo_equivalente Target files/modelo_equivalente.cpd` escolhendo **Virtual HIL** na janela de conexão, e abrir o painel `painel_equivalente.cus`. Após cada nova compilação: *Model > Reload Model*.
4. Capture/Scope (já no painel) em modo *Capture*: *Time interval* 0,30 s, *Sample rate* 50 KSPS; em *Signals*, os sinais `n`, `torque`, `Ia`, `Ib`, `Ic`, `G07_motor_duty`, `G07_v_carga`; nas configurações de gatilho (ícone à direita do **S**): Analog, `n`, Rising edge, threshold 20, offset 5 %, **Use first trigger** marcado.
5. Com a simulação parada, clicar no botão de captura com gatilho (**T↑**; a barra mostra *Waiting for trigger*) e depois em *Start simulation* (▶ na barra do SCADA). A curva aparece em poucos segundos; parar a simulação. Exportar: primeiro ícone vermelho da barra inferior do Capture > formato CSV > *Save data*, com o nome da tabela, em `dados-vhil-e2/`.
6. R4: com o bloco original compilado, iniciar a simulação, esperar alguns segundos, digitar os valores de `G07_k_fator` e `G07_dR` nas caixas do painel e ler `n` no mostrador.
7. Ao terminar, voltar ao bloco original e fechar o Schematic Editor **sem salvar** se não quiser gravar o último ensaio no `.tse`.

## TyphoonSim

Perspectiva TyphoonSim (DAE/BDF, passo máximo 2 µs, 0,3 s já gravados no modelo): ajustar o bloco do ensaio, compilar, simular e exportar o `Scope_motor` em CSV para `dados-typhoon-e2/` (`a_degrau_repouso`, `a_degrau_equilibrio`, `b_ci_d0`, `b_ci_d055`, `c_pulso_MA`, `c_pulso_MF`, `mf_original`).

## Verificação

Em regime, `G07_v_Te`/(100·|i_fase|) ≈ 0,047–0,048 N·m/A, e `G07_i_omega`·1000 = `n` [rpm].
