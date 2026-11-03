"""Resume execuções nativas reais e mede discrepâncias sem corrigir curvas."""
import csv,json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from modelo import *

def main():
 rows=[]
 for name,cfg in scenarios().items():
  meta=json.loads((ROOT/'resultados_typhoon'/(name+'.json')).read_text(encoding='utf-8'))
  rows.append(dict(caso=name,erro_max_K=meta['erro_max_vs_solucao_fechada_K'],erro_rel_elevacao_pct=100*meta['erro_max_vs_solucao_fechada_K']/(cfg['power']*sum(cfg['r'])),passo_s=meta['passo_nativo_s'],amostras=meta['amostras']))
 save_json(ROOT/'validacao_typhoon.json',rows)
 with (ROOT/'validacao_typhoon.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 fig,axes=plt.subplots(1,3,figsize=(12.5,3.7))
 for ax,trial in zip(axes,['degrau','livre','pulso']):
  name=trial+'_4r';cfg=scenarios()[name]
  d=np.genfromtxt(ROOT/'resultados_typhoon'/(name+'.csv'),delimiter=',',names=True)
  a=np.array([cfg['tc']+sum(exact(max(0.,float(t)),cfg)) for t in d['Time']])
  ax.plot(d['Time']*1000,d['T_j_K']-a,color='#163e69');ax.set_xlim(0,30)
  ax.set_title(trial);ax.set_xlabel('Tempo do ensaio (ms)');ax.set_ylabel('Typhoon − solução fechada (K)');ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(ROOT.parent/'Overleaf/figuras/validacao_typhoon.png',dpi=160);plt.close(fig)
 lines=['\\begin{center}\\begin{tabular}{lrr}\\toprule Ensaio nativo & Erro máximo [K] & Erro / elevação final [\\%]\\\\\\midrule']
 for row in rows[:6]:lines.append(row['caso'].replace('_','\\_')+' & '+f"{row['erro_max_K']:.6f}".replace('.',',')+' & '+f"{row['erro_rel_elevacao_pct']:.4f}".replace('.',',')+'\\\\')
 lines.append('\\bottomrule\\end{tabular}\\end{center}')
 (ROOT.parent/'Overleaf/tabela_typhoon.tex').write_text('\n'.join(lines),encoding='utf-8')
 print('Todos os 16 casos nativos presentes. Maior erro relativo:',max(r['erro_rel_elevacao_pct'] for r in rows))
if __name__=='__main__':main()
