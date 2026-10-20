"""Pós-processamento dos CSVs, sem alterar dados brutos."""
import csv
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from modelo import *

PACKAGE=ROOT.parent
FIG=PACKAGE/'Overleaf/figuras'
FIG.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})

def load(name):
    return np.genfromtxt(ROOT/'resultados_rk4'/(name+'.csv'),delimiter=',',names=True)

def save(fig,name):
    fig.tight_layout();fig.savefig(FIG/(name+'.png'),dpi=160);plt.close(fig)

def main():
    cfgs=scenarios();summary=json.loads((ROOT/'resultados_rk4/resumo.json').read_text(encoding='utf-8'))
    for trial in ['degrau','livre','pulso']:
        name=trial+'_4r';d=load(name);cfg=cfgs[name];alg=algebra(cfg)
        t=d['tempo_s'];analytic=np.array([cfg['tc']+sum(exact(float(a),cfg)) for a in t])
        fig,ax=plt.subplots(2,1,figsize=(10.5,6.1),sharex=True,gridspec_kw={'height_ratios':[1,3]})
        ax[0].plot(t*1000,d['potencia_W'],color='#163e69');ax[0].set_ylabel('Potência (W)')
        ax[1].plot(t*1000,d['T_j_K'],label='RK4, h = 2 µs',color='#163e69',lw=2)
        ax[1].plot(t[::20]*1000,analytic[::20],label='Solução fechada',color='#c84c35',ls='--')
        ax[1].set_ylabel('Temperatura da junção (K)');ax[1].set_xlabel('Tempo (ms)')
        if trial=='degrau':
            for frac,label in [(.1,'10%'),(.9,'90%'),(.98,'98%')]:
                tx=cfg['step']+root_time(frac,cfg);yy=cfg['tc']+frac*cfg['power']*sum(cfg['r'])
                ax[1].plot(tx*1000,yy,'o',ms=5,color='#237647')
                ax[1].annotate(f'{label}: {(tx-cfg["step"])*1000:.3f} ms',xy=(tx*1000,yy),xytext=(18+frac*25,yy-3+frac*4),fontsize=9,arrowprops={'arrowstyle':'-'})
            ax[1].axhline(alg['T_equilibrio_K'],color='#666',ls=':',label='Equilíbrio calculado')
        if trial=='livre':
            ax[1].plot(0,d['T_j_K'][0],'o',color='#237647');ax[1].annotate(f'IC: {d["T_j_K"][0]:.3f} K',(0,d['T_j_K'][0]),xytext=(15,d['T_j_K'][0]-2),fontsize=9)
        if trial=='pulso':
            ix=int(np.argmax(d['T_j_K']));ax[1].plot(t[ix]*1000,d['T_j_K'][ix],'o',color='#237647')
            ax[1].annotate(f'Pico: {d["T_j_K"][ix]:.3f} K\nem {t[ix]*1000:.2f} ms',(t[ix]*1000,d['T_j_K'][ix]),xytext=(25,d['T_j_K'][ix]-3),fontsize=9)
            ax[0].axvline(OFF*1000,color='#666',ls=':')
        for a in ax:a.grid(alpha=.2);a.set_xlim(0,80 if trial!='degrau' else 45)
        ax[1].legend(fontsize=9);fig.suptitle('Quatro ramos Foster: '+trial+' (domínio térmico)')
        save(fig,trial)
    fig,axes=plt.subplots(1,3,figsize=(13,4.4))
    for ax,param in zip(axes,['R1','C1','R4']):
        for factor,color in zip([.2,1.,5.],['#237647','#163e69','#c84c35']):
            d=load(f'{param}_x{factor:g}');ax.plot(d['tempo_s']*1000,d['T_j_K'],label=f'{factor:g} × nominal',color=color)
        ax.set_xlim(0,50 if param!='R4' else 500);ax.set_title(param+' (outros fixos)');ax.set_xlabel('Tempo (ms)');ax.grid(alpha=.2);ax.legend(fontsize=9)
    axes[0].set_ylabel('Temperatura da junção (K)');save(fig,'sensibilidade')
    t=np.geomspace(1e-5,.25,500)
    z4=np.array([sum(r*(-math.expm1(-v/ti)) for r,ti in zip(R4,TAU4)) for v in t])
    z2=np.array([sum(r*(-math.expm1(-v/ti)) for r,ti in zip(R2,TAU2)) for v in t])
    error=100*(z2-z4)/z4
    save_json(ROOT/'comparacao_reducao.json',dict(max_erro_rel_pct=float(max(abs(error))),rms_rel_pct=float(np.sqrt(np.mean(error**2))),max_erro_abs_K_W=float(max(abs(z2-z4))),faixa_s=[1e-5,.25]))
    fig,ax=plt.subplots(2,1,figsize=(10,5.2),sharex=True)
    ax[0].semilogx(t*1000,z4,label='Fabricante: 4 ramos',color='#163e69');ax[0].semilogx(t*1000,z2,'--',label='Aproximação anterior: 2 ramos',color='#c84c35')
    ax[0].set_ylabel('Zth (K/W)');ax[0].legend();ax[1].semilogx(t*1000,error,color='#c84c35');ax[1].set_ylabel('Erro relativo (%)');ax[1].set_xlabel('Tempo (ms)')
    for a in ax:a.grid(alpha=.2)
    save(fig,'reducao')
    # Polos medidos dos estados da resposta livre, não copiados da tabela algébrica.
    free=load('livre_4r');pole_rows=[]
    for i,ti in enumerate(TAU4):
        ia=np.argmin(abs(free['tempo_s']-.5*ti));ib=np.argmin(abs(free['tempo_s']-1.5*ti))
        measured=math.log(float(free[f'theta{i+1}_K'][ib]/free[f'theta{i+1}_K'][ia]))/(free['tempo_s'][ib]-free['tempo_s'][ia])
        expected=-1/ti
        pole_rows.append(dict(ramo=i+1,algebrico_s_1=expected,medido_s_1=measured,diferenca_pct=100*abs((measured-expected)/expected)))
    save_json(ROOT/'polos_medidos.json',pole_rows)
    comparison=[];nom=summary['casos']['degrau_4r']
    for key,label,unit in [('gain_K_W','Ganho estático estimado no fim','K/W'),('T_equilibrio_K','Temperatura de equilíbrio estimada no fim','K'),('subida_10_90_s','Subida 10–90%','s'),('acomodacao_2pct_s','Acomodação 2%','s')]:
        comparison.append(dict(grandeza=label,unidade=unit,algebrico=nom['algebra'][key],simulado=nom['medido'][key],diferenca_pct=nom['diferenca_pct'][key]))
    with (ROOT/'validacao_cruzada.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(comparison[0]));w.writeheader();w.writerows(comparison)
    sensitivity=[]
    for name,cfg in cfgs.items():
        if cfg['group']!='sensibilidade':continue
        row=summary['casos'][name]
        sensitivity.append(dict(parametro=cfg['parameter'],fator=cfg['scale'],valor=(cfg['r'] if cfg['parameter'].startswith('R') else cfg['c'])[int(cfg['parameter'][1:])-1],ganho_K_W=row['algebra']['gain_K_W'],T_final_RK4_K=row['medido']['T_equilibrio_K'],t_2pct_RK4_s=row['medido']['acomodacao_2pct_s'],polo_alterado_s_1=row['algebra']['poles_s_1'][int(cfg['parameter'][1:])-1]))
    save_json(ROOT/'sensibilidade_resumo.json',sensitivity)
    with (ROOT/'sensibilidade.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(sensitivity[0]));w.writeheader();w.writerows(sensitivity)
    # Dados dos slides: os gráficos no PPTX permanecem editáveis.
    slides={}
    for name in ['degrau_4r','livre_4r','pulso_4r','R1_x0.2','R1_x1','R1_x5','C1_x0.2','C1_x1','C1_x5','R4_x0.2','R4_x1','R4_x5']:
        d=load(name);limit=.5 if name.startswith('R4') else .05;idx=np.where(d['tempo_s']<=limit)[0][::max(1,int(limit/RECORD/250))]
        slides[name]=dict(t_ms=(1000*d['tempo_s'][idx]).tolist(),T_K=d['T_j_K'][idx].tolist())
    save_json(ROOT/'dados_slides.json',slides)
    print('Figuras, tabelas, polos e dados editáveis preparados.')

if __name__=='__main__':main()
