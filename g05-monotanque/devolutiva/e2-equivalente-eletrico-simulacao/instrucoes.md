# Devolutiva da Entrega 02: equivalente elétrico v2 do Monotanque (G05)

## Ferramenta

- **Typhoon HIL Control Center 2026.2**: Schematic Editor + HIL SCADA, em **VHIL** (HIL virtual, sem hardware).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `monotanque_equivalente_v2.tse` | circuito: 1 capacitor (tanque), 1 indutor (inércia da água no tubo), 1 resistor (escoamento), fonte da parte não linear, bomba e consumo; só biblioteca `core`, sem C function |
| `painel_monotanque_v2.cus` | painel HIL SCADA: ensaio, ponto de operação, modo do orifício, válvula, leituras e gráficos |

## Parâmetros

| Grandeza | Tanque | Escala | Circuito |
|---|---|---|---|
| nível h0 | 0,50 m | k_v = 10 V/m | V0 = 5 V |
| vazão qi0 | 7,071 L/s | k_i = 1000 A/(m³/s) (1 A = 1 L/s) | I0 = 7,071 A |
| tempo | τ = 70,7 s | k_t = 100 | τ_c = 0,707 s |
| área A | 0,5 m² | C = A·k_i/(k_v·k_t) | C = 0,5 F |
| tubo de saída (l = 1 m) | I_h = l/(g·a) = 27,1 s²/m² | L = k_v·I_h/(k_i·k_t) | L = 2,71 mH |
| orifício k | 0,01 m^2,5/s | R = 2√V0/K_e | R = 1,414 Ω + e(i) |

Área e comprimento do tubo são parâmetros de construção: ficam em **Model → Model Initialization** (`A` e `l_tubo`);
mudar e recompilar. Os demais (ensaio, nível de operação, válvula k, modo do orifício, consumo) mudam ao vivo no SCADA.

## Como rodar

1. Schematic Editor → Ctrl+O → `monotanque_equivalente_v2.tse`.
2. Seta de *Compile and (re)load model in HIL SCADA* → **Compile and (re)load model in SCADA VHIL MODE**.
3. No HIL SCADA, abrir `painel_monotanque_v2.cus`, conferir **VIRTUAL HIL MODE** e **ACTIVE**, clicar em **Lock** e **Start**.
4. A cada disparo a bomba leva o nível ao valor inicial em 1 s de gráfico (100 s de tanque); então o ensaio começa.

| Ajuste no painel | Esperado |
|---|---|
| (a) Degrau na bomba → DISPARAR | h: 0,500 → 0,720 m |
| Resistência de saída = Linearizado, ensaio (a) | h: 0,500 → 0,700 m (só o resistor) |
| (b) Volta a h_op, bomba ligada | h: 1,0 → 0,500 m |
| (b) Drenagem livre | tanque vazio em ≈ 100 s |
| (c) Senoide na bomba | ±0,071 m em torno de 0,50 m, atraso ≈ 45° |
| (c) com frequência 100 | nível quase parado; vazão de saída já atenuada pela inércia |
| Degrau 0 e k = 0.005 | h → 2,0 m (passa de 1,2 m) |

## Gerar as figuras do relatório

| Script (`scripts/`) | Função |
|---|---|
| `gerar_modelo_dev.py` | recria o `.tse` pela API (argumentos opcionais: área e comprimento do tubo) |
| `gerar_painel_dev.py` | recria o `.cus` pela API |
| `rodar_vhil_dev.py` | executa ensaios no VHIL e grava h, qi, qo e e em `.npz` |
| `rodar_tudo.sh` | roda todos os ensaios do relatório, inclusive as variantes de área e de tubo |
| `analisar_dev.py` | resolve os modelos de referência (E01 e v2), gera as figuras 1 a 8 e `resultados_dev.json` |

Captura: Python do Typhoon (`C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe`), com o
HIL SCADA fechado. Análise: Python 3.12 com NumPy, SciPy, Matplotlib e schemdraw.
