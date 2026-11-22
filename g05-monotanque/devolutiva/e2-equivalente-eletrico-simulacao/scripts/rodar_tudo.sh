#!/bin/bash
# Roda todos os ensaios da devolutiva no VHIL (modelo base + variantes recompiladas de area e de tubo).
# Uso (Git Bash):  bash 3_scripts/rodar_tudo.sh      (feche o HIL SCADA antes)
set -e
BASE="$(cd "$(dirname "$0")/.." && pwd -W)"
PY="C:/Program Files/Typhoon HIL Control Center 2026.2/python3_portable/python.exe"
S="$BASE/3_scripts"; D="$BASE/4_dados/vhil"; V="$BASE/4_dados/variantes"
CPD="$BASE/2_entrega/simulacao/monotanque_equivalente_v2 Target files/monotanque_equivalente_v2.cpd"

# resposta em frequencia: 4,6 s de preparacao + transitorio e 3 periodos; ~60 amostras por periodo
bode=""
for w in 0.2 0.5 1 2 5 10 30 100 300 1000; do
  dur=$(python -c "import math;p=2*math.pi/($w*1.41421);print(round(4.6+3*p,2))")
  dec=$(python -c "import math;p=2*math.pi/($w*1.41421);print(max(1,min(50,int(p/(2e-5*60)))))")
  bode="$bode bode_w$w=4,$dur,w_rel:$w,dec:$dec"
done
"$PY" "$S/rodar_vhil_dev.py" "$CPD" "$D" \
  a=1,8 b=2,7 b2=3,3.5 c=4,17 \
  op020=1,6,degrau_pct:2,h_op_m:0.2 op035=1,7,degrau_pct:2,h_op_m:0.35 op050=1,8,degrau_pct:2,h_op_m:0.5 \
  op080=1,9,degrau_pct:2,h_op_m:0.8 op110=1,10,degrau_pct:2,h_op_m:1.1 \
  nl_p20=1,9,degrau_pct:20 nl_m20=1,9,degrau_pct:-20 nl_p50=1,10,degrau_pct:50 nl_m50=1,9,degrau_pct:-50 \
  li_p20=1,9,degrau_pct:20,modelo_orif:1 li_m20=1,9,degrau_pct:-20,modelo_orif:1 \
  li_p50=1,10,degrau_pct:50,modelo_orif:1 li_m50=1,9,degrau_pct:-50,modelo_orif:1 \
  k0050=1,18,degrau_pct:0,k_valvula:0.005 k0075=1,10,degrau_pct:0,k_valvula:0.0075 \
  k0150=1,7,degrau_pct:0,k_valvula:0.015 k0200=1,6,degrau_pct:0,k_valvula:0.02 \
  $bode

variante () {  # nome A l_tubo casos...
  nome=$1; A=$2; l=$3; shift 3
  mkdir -p "$V/$nome"
  "$PY" "$S/gerar_modelo_dev.py" "$V/$nome/modelo.tse" $A $l
  "$PY" "$S/rodar_vhil_dev.py" "$V/$nome/modelo Target files/modelo.cpd" "$D" "$@"
}
variante l0p1 0.5 0.1 l0p1_a=1,8 l0p1_b=2,7 l0p1_b2=3,3.5 l0p1_c=4,17
variante l10 0.5 10 l10_a=1,8 l10_dren=3,4
variante l100 0.5 100 l100_a=1,8 l100_dren=3,4
variante l1000 0.5 1000 l1000_a=1,10 l1000_dren=3,4
variante A025 0.25 1 A025_a=1,6
variante A1 1.0 1 A1_a=1,11
variante A2 2.0 1 A2_a=1,20
echo FIM
