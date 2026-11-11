# Reprodução no TyphoonSim - Fase 2, Entrega 02

## 1. Ambiente e arquivos

Execução confirmada no **TyphoonSim 2026.3 independente**, Windows, com a API
`typhoon-hil-api==1.32.1`. O aplicativo deve estar ativado. Use o SCADA
Standalone incluído no TyphoonSim; o Control Center não é necessário para
este procedimento offline.

| Arquivo | Uso |
|---|---|
| `modelo-offline.tse` | Circuito nativo r3a, disparo automático e Scope Captura. |
| `painel-offline.cus` | Presets, campos editáveis e acionamento do solver offline. |
| `iniciar_painel_offline.py` | Abre o painel no SCADA Standalone. |
| `executar_offline.py` | Executa e compara os nove casos pelo solver nativo. |
| `gerar_offline.py` / `gerar_painel_offline.py` | Recriam a variante e o painel offline. |
| `modelo.tse` / `painel.cus` / `executar_vhil.py` | Variante para HIL SCADA regular com Virtual HIL. |
| `inventario.json` | Blocos nativos e propriedades do modelo de 55 componentes; a variante offline substitui uma entrada por Step e adiciona Scope. |

## 2. Executar pelo SCADA Standalone

1. Da pasta `typhoonsim`, rodar `python iniciar_painel_offline.py`. Também
   é possível abrir **Standalone HIL SCADA** pelo menu Iniciar, abrir
   `painel-offline.cus` e acionar **Start simulation** na barra de ferramentas
   para ativar as macros do painel.
2. Conferir **Pasta dos scripts**. Deve apontar para a pasta `typhoonsim`
   desta entrega. Se a pasta foi movida e não for localizada automaticamente,
   informar o caminho e confirmar com Enter.
3. Selecionar um preset da tabela abaixo. Ele atualiza os sete campos.
   O gráfico continua exibindo a última captura até a execução terminar.
4. Para variação manual, confirmar cada valor com **Enter**. Ao alterar a
   vazão ou os coeficientes, clicar **Recalcular equilíbrio**. No caso r3b,
   manter Vref1=11,5 V e Vref2=6 V para reproduzir a condição fora do equilíbrio.
5. Clicar **Executar ensaio no TyphoonSim**. O painel prepara o modelo, reabre
   o `.tse` para inicializar o Scope e executa 20,25 s elétricos. Aguardar o
   status da captura antes de repetir o ensaio.
6. Conferir o gráfico, o erro máximo e o status de concordância. Os CSVs
   ficam em `../simulacao/dados/offline/`; resultados de presets oficiais
   ficam separados dos casos com parâmetros manuais, prefixados `manual-`.
7. Para demonstrar sensibilidade, executar r4-k2-2 e r4-q-0p5 e comparar
   com o nominal r3a. Os registros `scada-*.json` comprovam a execução pela
   interface nos três casos. A variação ocorre entre execuções offline.

## 3. Presets e resultados esperados

| Preset | Q_rel | G1_rel | G2_rel | D_deg (%) | D_pul (%) | Vref1 / Vref2 (V) |
|---|---:|---:|---:|---:|---:|---|
| r3a | 1 | 1 | 1 | 5 | 0 | 10 / 10 |
| r3b | 1 | 1 | 1 | 0 | 0 | 11,5 / 6 |
| r3c | 1 | 1 | 1 | 0 | 20 | 10 / 10 |
| r4-k2-1 | 1 | 1 | 1 | 5 | 0 | 10 / 10 |
| r4-k2-2 | 1 | 1 | 2 | 5 | 0 | 10 / 2,5 |
| r4-k2-3 | 1 | 1 | 3 | 5 | 0 | 10 / 1,111111 |
| r4-q-0p5 | 0,5 | 1 | 1 | 5 | 0 | 2,5 / 2,5 |
| r4-q-0p75 | 0,75 | 1 | 1 | 5 | 0 | 5,625 / 5,625 |
| r4-q-1 | 1 | 1 | 1 | 5 | 0 | 10 / 10 |

No r3a, V1 e V2 chegam a 11,025 V (1,1025 m). No r3b, o nível de saída
atinge aproximadamente 1,00469 m e retorna a 1 m. No r3c, o pulso de
20% dura 0,3 s elétricos (30 s originais); h2 atinge cerca de 1,04387 m.
Com k2×2, h1 final continua 1,1025 m e h2 final cai a 0,275625 m. Com
q0×0,5, **ambos** terminam em 0,275625 m. A diferença de h1 distingue os
efeitos dos dois parâmetros, embora o h2 final seja igual nesses dois casos.

## 4. Rodar pelo editor ou pela API

Para rodar diretamente o caso r3a, abrir `modelo-offline.tse` no TyphoonSim,
conferir **Stop time = 20,25 s**, executar e abrir o Scope **Captura**.
Exportar `Time`, `V1`, `V2` e `u_ensaio` em CSV.

Para automatizar em um Python separado, instalar `requirements.txt` e
apontar `TYPHOONPATH` para a instalação real:

```powershell
$env:TYPHOONPATH = 'C:\Program Files\TyphoonSim 2026.3'
python -m pip install -r requirements.txt
python executar_offline.py
# Apenas um caso:
python executar_offline.py --ensaio r3b
```

A automação foi testada com Python 3.10.11 e a API 1.32.1. O painel usa o
Python fornecido pelo aplicativo. Para recriar os arquivos, usar
`python gerar_offline.py --ensaio r3a` e `python gerar_painel_offline.py`.
A variante para VHIL é recriada por `gerar_modelo.py` e `gerar_painel.py`.

## 5. Configuração e conferência

- Offline: solver DAE/BDF, passo máximo 100 µs, inicial 1 µs, SP a 100 µs,
  tolerâncias absoluta 1e-9 e relativa 1e-7. Aquisição em **intervalo de
  0,001 s** no Scope; 20.251 amostras de 0 a 20,25 s.
- C1=C2=500 µF e Gnom=0,00316227766017 A/√V. A pré-carga é limitada a
  ±100 mA e liberada em 0,25 s. Faixa válida após inicialização: 1..12 V.
- Reconversão: dividir V1/V2 por 10 e multiplicar tempo por 100. O início
  do ensaio é a primeira amostra com u_ensaio>0,5, registrada em 0,251 s.
- Concordância: erro pontual de nível ≤2 mm e diferença relativa absoluta
  ≤1% por métrica não nula. Referência zero: tolerância absoluta de 1e-4 na
  unidade da métrica. Resultado observado: 9/9; pior caso 0,684309 mm e
  maior diferença de métrica 0,3333%.

Para comparar um CSV exportado manualmente, na pasta `simulacao`:

```powershell
python equivalente.py --typhoon dados/offline/r3a.csv --ensaio r3a --origem typhoonsim-offline
```

O arquivo deve ter tempo em segundos elétricos, V1/V2 em volts e u_ensaio.
`Time` e `Time (s)` são aceitos como nomes do tempo. Para outros nomes de
tensão/gatilho, usar `--v1`, `--v2` e `--gatilho`. O script `equivalente.py`
também oferece `--referencia` para gerar previsões em Python; esses arquivos
são separados dos dados reais.

## 6. Fluxo específico VHIL/HIL SCADA regular

O enunciado menciona execução em VHIL/SCADA. Os dados deste relatório são
do solver offline com controle via SCADA Standalone; **não houve execução
em VHIL**. Para reproduzir nesse modo, abrir `modelo.tse` no Control Center,
compilar para HIL404/configuração 1 (passo elétrico 1 µs, SP 100 µs), carregar
o `.cpd` em Virtual HIL e abrir `painel.cus` no HIL SCADA regular.

Armar Capture/Scope em 20 s, 1 kHz, V1/V2/u_ensaio, borda crescente em
0,5 e 0% de pré-trigger. Aguardar |Vj−Vrefj|<0,002 V, disparar e exportar.
`python executar_vhil.py` automatiza esse caminho quando houver `.cpd` e
Virtual HIL disponíveis. Os registros em `dados/vhil/` seriam separados.

Compilações, executáveis, `.cpd`, `.runx`, caches e backups não entram no
Git. Os `.tse`, `.cus`, scripts, CSVs e figuras pertencem à entrega.
