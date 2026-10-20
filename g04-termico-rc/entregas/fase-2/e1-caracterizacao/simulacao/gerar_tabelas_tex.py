import csv,json
from modelo import *

out=ROOT.parent/'Overleaf'
summary=json.loads((ROOT/'resultados_rk4/resumo.json').read_text(encoding='utf-8'))
nom=summary['casos']['degrau_4r']
rows=[]
for key,label,unit in [('gain_K_W','Ganho DC no fim','K/W'),('T_equilibrio_K','Equilíbrio no fim','K'),('t10_s','Tempo 10\\%','ms'),('t90_s','Tempo 90\\%','ms'),('subida_10_90_s','Subida 10--90\\%','ms'),('acomodacao_2pct_s','Acomodação 2\\%','ms')]:
    scale=1000 if unit=='ms' else 1
    rows.append(f"{label} [{unit}] & {nom['algebra'][key]*scale:.8f} & {nom['medido'][key]*scale:.8f} & {nom['diferenca_pct'][key]:.6g}\\\\")
poles=json.loads((ROOT/'polos_medidos.json').read_text(encoding='utf-8'))
for p in poles:rows.append(f"Polo {p['ramo']} [s$^{{-1}}$] & {p['algebrico_s_1']:.8f} & {p['medido_s_1']:.8f} & {p['diferenca_pct']:.3g}\\\\")
table='\\begin{center}\\small\\begin{tabular}{lrrr}\\toprule Grandeza & Álgebra & RK4 medido & Diferença [\\%]\\\\\\midrule\n'+'\n'.join(rows)+'\n\\bottomrule\\end{tabular}\\end{center}'
(out/'tabelas_validacao.tex').write_text(table,encoding='utf-8')
rows=[]
for r in json.loads((ROOT/'sensibilidade_resumo.json').read_text(encoding='utf-8')):
    rows.append(f"{r['parametro']} & {r['fator']:g} & {r['ganho_K_W']:.6f} & {r['T_final_RK4_K']:.6f} & {r['t_2pct_RK4_s']*1000:.6f} & {r['polo_alterado_s_1']:.6f}\\\\")
table='\\begin{center}\\small\\begin{tabular}{lrrrrr}\\toprule Parâm. & Fator & $K_0$ [K/W] & $T_j(t_f)$ [K] & $t_{2\\%}$ [ms] & Polo alterado [s$^{-1}$]\\\\\\midrule\n'+'\n'.join(rows)+'\n\\bottomrule\\end{tabular}\\end{center}'
(out/'tabela_sensibilidade.tex').write_text(table,encoding='utf-8')
