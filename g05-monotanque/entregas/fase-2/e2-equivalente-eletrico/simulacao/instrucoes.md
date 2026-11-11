# Fase 2, Entrega 02: equivalente elétrico do Monotanque (G05)

## Ferramenta

- **Typhoon HIL Control Center 2026.2**: Schematic Editor + HIL SCADA, executando em **VHIL** (HIL virtual, sem hardware).

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `monotanque_equivalente_eletrico.tse` | circuito equivalente (só elementos nativos da biblioteca `core`, sem C function) |
| `painel_monotanque_e2.cus` | painel HIL SCADA: seleção de ensaio, parâmetros, leituras e gráficos |

## Parâmetros

| Grandeza | Tanque (E01) | Escala | Circuito |
|---|---|---|---|
| nível h | 0,50 m | k_v = 10 V/m | V0 = 5 V |
| vazão qi0 | 7,071 L/s | k_i = 1000 A/(m³/s) (1 A = 1 L/s) | I0 = 7,071 A |
| tempo | τ = 70,71 s | k_t = 100 | τ_c = 0,7071 s |
| área A | 0,5 m² | C = A·k_i/(k_v·k_t) | 0,5 F (banco 0,125 a 2 F) |
| orifício k | 0,01 m^2,5/s | K_e = k·k_i/√k_v | 3,162 A/√V |

Passo do VHIL: 20 µs; passo dos blocos de sinal: 100 µs. Evento dos ensaios em t = 0,5 s do circuito (50 s no tanque); até lá o nível fica preso na condição inicial (pré-carga com R = 1 mΩ).

## Como rodar

1. Abrir o Typhoon HIL Control Center 2026.2 → **Schematic Editor** → Ctrl+O → `monotanque_equivalente_eletrico.tse`.
2. Na seta ao lado de *Compile and (re)load model in HIL SCADA*, escolher **Compile and (re)load model in SCADA VHIL MODE**.
3. No HIL SCADA, abrir `painel_monotanque_e2.cus`, conferir **VIRTUAL HIL MODE** e **ACTIVE**, clicar em **Lock**.
4. **Start**. O painel volta aos valores padrão (degrau 20 %, h(0) = 1,0 m, amplitude 10 %, A = 0,5 m², k = 0,01, qd = 0).
5. Ensaios e valores esperados:

| Ajuste | Esperado |
|---|---|
| (a) Degrau na bomba → DISPARAR | h: 0,500 → 0,720 m; 63 % em 80,5 s |
| (b) Condição inicial, bomba ligada | h: 1,0 → 0,500 m |
| (b) Drenagem livre | tanque vazio em ≈ 100 s |
| (c) Senoide na bomba | amplitude 0,0707 m, atraso 45° |
| (a) com Área = 2 m² | 0,72 m, t63 ≈ 322 s |
| Degrau 0 e k = 0.005 | h → 2,0 m (passa de 1,2 m em ≈ 148 s) |

Para repetir um ensaio ou mudar parâmetros: **Stop** → ajustar no painel → **Start**.

## Gerar as figuras do relatório

Esta parte só é necessária para refazer as figuras; para rodar os ensaios basta a seção anterior.

| Script (`scripts/`) | Função |
|---|---|
| `rodar_vhil_e2.py` | executa os ensaios no VHIL e grava h, qi e qo de cada ensaio em `.npz` |
| `analisar_e2.py` | sobrepõe VHIL e Entrega 01, calcula a tabela de grandezas e gera as figuras 01, 02 e 05 a 09 |
| `gerar_modelo_e2.py` | recria o `.tse` pela API do Schematic Editor (opcional) |
| `gerar_painel_e2.py` | recria o `.cus` pela API do HIL SCADA (opcional) |

As figuras 03 e 04 são prints do Schematic Editor e do HIL SCADA.

Requisitos: Python do próprio Typhoon (`C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe`) para a captura; Python 3.12 com NumPy, SciPy e Matplotlib para a análise. Compile o `.tse` uma vez (passo 2 acima) e feche o HIL SCADA antes de usar a API.

```
set TPY="C:\Program Files\Typhoon HIL Control Center 2026.2\python3_portable\python.exe"
set CPD="monotanque_equivalente_eletrico Target files\monotanque_equivalente_eletrico.cpd"
set DEC=20
%TPY% scripts\rodar_vhil_e2.py %CPD% dados a=1,7.2 a1pct=1,7.6,degrau_pct:1 b=2,5.2 b2=3,1.8
set DEC=100
%TPY% scripts\rodar_vhil_e2.py %CPD% dados c=4,36.3 A0125=1,15.7,A_m2:0.125 A025=1,15.7,A_m2:0.25 A05=1,15.7 A1=1,15.7,A_m2:1 A2=1,15.7,A_m2:2 k0005=1,30.7,degrau_pct:0,k_valvula:0.005 k00075=1,30.7,degrau_pct:0,k_valvula:0.0075 k001=1,30.7,degrau_pct:0 k0015=1,30.7,degrau_pct:0,k_valvula:0.015 k002=1,30.7,degrau_pct:0,k_valvula:0.02
python scripts\analisar_e2.py dados ..\relatorio\figuras resultados_e2.json
```

Cada caso é `nome=ensaio,duração_no_circuito[,entrada:valor...]` (ensaio 1 = degrau, 2 = condição inicial, 3 = drenagem, 4 = senoide). O modelo hidráulico da Entrega 01 é recalculado em `analisar_e2.py` com o mesmo solver RK45.
