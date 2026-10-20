"""Integra as EDOs térmicas por RK4 fixo, independentemente da solução fechada.

Somente biblioteca padrão. Não apresenta resultados Python como TyphoonSim.
"""
import csv
import math
import platform
import sys
import time
from modelo import *

def simulate(cfg,dt=DT):
    x=initial(cfg);ts=tau(cfg);rows=[]
    n=math.ceil(cfg['duration']/dt);stride=round(RECORD/dt)
    # Todas as bordas coincidem com a malha. Input é amostrado à esquerda.
    for k in range(n+1):
        t=k*dt
        if k%stride==0 or k==n:rows.append([t,power(t,cfg),cfg['tc']+sum(x),*x])
        if k==n:break
        p=power((k+.25)*dt,cfg)
        for i in range(len(x)):
            target=cfg['r'][i]*p;ti=ts[i];v=x[i]
            k1=(target-v)/ti
            k2=(target-v+.5*dt*(-k1))/ti
            k3=(target-v+.5*dt*(-k2))/ti
            k4=(target-v-dt*k3)/ti
            x[i]+=dt*(k1+2*k2+2*k3+k4)/6
    return rows

def crossing(rows,target,rising=True,after=STEP):
    for a,b in zip(rows,rows[1:]):
        if a[0]<after:continue
        if (a[2]<=target<=b[2]) if rising else (a[2]>=target>=b[2]):
            return a[0]+(target-a[2])*(b[0]-a[0])/(b[2]-a[2])
    return None

def measure(rows,cfg):
    alg=algebra(cfg)
    error=max(abs(row[2]-cfg['tc']-sum(exact(row[0],cfg))) for row in rows)
    if cfg['trial']!='degrau':return dict(erro_max_K=error,T_final_K=rows[-1][2])
    delta=cfg['power']*sum(cfg['r']);edge=cfg['step']
    t10=crossing(rows,cfg['tc']+.1*delta,after=edge)-edge
    t90=crossing(rows,cfg['tc']+.9*delta,after=edge)-edge
    settle=crossing(rows,cfg['tc']+.98*delta,after=edge)-edge
    return dict(erro_max_K=error,gain_K_W=(rows[-1][2]-cfg['tc'])/cfg['power'],
                T_equilibrio_K=rows[-1][2],t10_s=t10,t90_s=t90,
                subida_10_90_s=t90-t10,acomodacao_2pct_s=settle,
                sobressinal_pct=max(0.,(max(r[2] for r in rows)-alg['T_equilibrio_K'])/delta*100))

def main():
    cfgs=scenarios();out=ROOT/'resultados_rk4';out.mkdir(exist_ok=True)
    # Previsões são registradas antes de qualquer integração desta execução.
    save_json(ROOT/'previsoes_ANTES_da_simulacao.json',predictions())
    save_json(ROOT/'parametros.json',cfgs)
    summary={'solver':'RK4 explícito fixo nas EDOs, Python '+platform.python_version(),
             'passo_s':DT,'periodo_registro_s':RECORD,'casos':{}}
    for name,cfg in cfgs.items():
        start=time.monotonic();rows=simulate(cfg)
        with (out/(name+'.csv')).open('w',newline='',encoding='utf-8') as f:
            w=csv.writer(f);w.writerow(['tempo_s','potencia_W','T_j_K']+[f'theta{i+1}_K' for i in range(len(cfg['r']))]);w.writerows(rows)
        measured=measure(rows,cfg);alg=algebra(cfg)
        assert all(math.isfinite(v) for row in rows for v in row)
        assert measured['erro_max_K']<1e-4,(name,measured)
        differences={k:100*abs(measured[k]-alg[k])/abs(alg[k]) if alg[k] else None
                     for k in measured if k in alg and isinstance(alg[k],(float,int))}
        summary['casos'][name]=dict(algebra=alg,medido=measured,diferenca_pct=differences,
             amostras=len(rows),tempo_real_s=time.monotonic()-start)
        print(name,'erro max K:',measured['erro_max_K'],flush=True)
    # Convergência independente com passos h, h/2 e h/4, mesmos tempos de registro.
    convergence=[]
    for h in [DT,DT/2,DT/4]:
        rows=simulate(cfgs['degrau_4r'],h)
        convergence.append(dict(h_s=h,**measure(rows,cfgs['degrau_4r'])))
    summary['convergencia']=convergence
    save_json(out/'resumo.json',summary)

if __name__=='__main__':main()
