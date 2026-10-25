"""Exportacoes e verificacoes do relatorio que complementam tanques.py.

Executar por `python tanques.py`. Os resultados sao calculados novamente;
nenhuma tabela numerica do PDF e usada como dado de entrada.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from scipy.integrate import solve_ivp
from tanques import (DATA, FIG, P, DSTEP, H_IC, TP, AMP, SOLVER, MAX_STEP,
                    RTOL, ATOL, algebra, f_nl, simulate, measure_step)


def diagrama():
    """Figura 1: balancos de massa, com a mesma vazao entre os tanques."""
    fig, ax = plt.subplots(figsize=(11, 3.6))
    ax.set(xlim=(0, 11.5), ylim=(0, 3.6)); ax.axis("off")
    for x, area, title in [(2.2, "A1", "Tanque 1"), (7.2, "A2", "Tanque 2")]:
        ax.add_patch(Rectangle((x, 1), 1.6, 1, fill=False, lw=1.7))
        ax.text(x+.8, 1.5, f"(1/{area}) ∫", ha="center", va="center", fontsize=15)
        ax.text(x+.8, .75, title, ha="center")
    for x in (1.5, 6.5):
        ax.add_patch(Circle((x, 1.5), .23, fill=False, lw=1.5))
        ax.text(x, 1.5, "Σ", ha="center", va="center", fontsize=16)
    def arrow(x1,y1,x2,y2):
        ax.annotate("", (x2,y2), (x1,y1), arrowprops=dict(arrowstyle="->",lw=1.5))
    arrow(.1,1.5,1.27,1.5); ax.text(.6,1.73,"qi",ha="center")
    arrow(1.73,1.5,2.2,1.5); arrow(3.8,1.5,4.6,1.5)
    ax.text(4.15,1.73,"h1",ha="center")
    ax.add_patch(Rectangle((4.6,1.0),1.2,1.0,fill=False,lw=1.7))
    ax.text(5.2,1.5,"k1√h1",ha="center",va="center",fontsize=14)
    arrow(5.8,1.5,6.27,1.5); ax.text(6.02,1.73,"q1",ha="center")
    ax.plot([6.05,6.05,1.5],[1.5,.3,.3],color="black",lw=1.3)
    arrow(1.5,.3,1.5,1.27)
    arrow(6.73,1.5,7.2,1.5); arrow(8.8,1.5,11.3,1.5)
    ax.text(10.7,1.73,"h2",ha="center")
    ax.plot([9.9,9.9],[1.5,2.8],color="black",lw=1.3)
    arrow(9.9,2.8,9.5,2.8)
    ax.add_patch(Rectangle((8.1,2.35),1.4,.9,fill=False,lw=1.7))
    ax.text(8.8,2.8,"k2√h2",ha="center",va="center",fontsize=14)
    ax.plot([8.1,6.5],[2.8,2.8],color="black",lw=1.3)
    arrow(6.5,2.8,6.5,1.73); ax.text(7.3,3.0,"q2",ha="center")
    ax.text(1.08,1.15,"+"); ax.text(1.65,1.05,"−")
    ax.text(6.08,1.15,"+"); ax.text(6.65,1.95,"−")
    arrow(1.5,2.8,1.5,1.73); ax.text(1.1,2.8,"qd (+)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig-01-diagrama-blocos.png"),dpi=180); plt.close(fig)


def exportar_dados(res, sb, sc, r):
    cases=[("degrau-01.csv",res[.01][0]),("degrau-05.csv",res[DSTEP][0]),
           ("condicao-inicial.csv",sb),("pulso.csv",sc)]
    for name,s in cases:
        arr=np.column_stack([s["t"],s["h1"],s["h2"],s["l1"],s["l2"]])
        np.savetxt(os.path.join(DATA,name),arr,delimiter=",",
                   header="tempo_s,h1_nl_m,h2_nl_m,h1_linear_m,h2_linear_m",comments="",fmt="%.12g")


def convergencia_rk4(p, r, lines):
    tf=300.; q=lambda t:p["q0"]*(1+DSTEP)
    y0=np.array([r["h1"],r["h2"]])
    ref=solve_ivp(f_nl,(0,tf),y0,args=(p,q),method="DOP853",rtol=1e-13,atol=1e-15,max_step=5.)
    if not ref.success: raise RuntimeError(ref.message)
    dts=np.array([10.,5.,2.5,1.25,.625]); errors=[]
    for dt in dts:
        y=y0.copy()
        for j in range(round(tf/dt)):
            t=j*dt
            k1=np.asarray(f_nl(t,y,p,q)); k2=np.asarray(f_nl(t+dt/2,y+dt*k1/2,p,q))
            k3=np.asarray(f_nl(t+dt/2,y+dt*k2/2,p,q)); k4=np.asarray(f_nl(t+dt,y+dt*k3,p,q))
            y+=dt*(k1+2*k2+2*k3+k4)/6
        errors.append(abs(y[1]-ref.y[1,-1]))
    errors=np.asarray(errors); order=np.polyfit(np.log(dts),np.log(errors),1)[0]
    assert 3.8<order<4.3, f"Ordem RK4 inesperada: {order}"
    fig,ax=plt.subplots(figsize=(6.2,3.6))
    ax.loglog(dts,errors,"o-",label=f"RK4: ordem medida {order:.2f}")
    ax.loglog(dts,errors[0]*(dts/dts[0])**4,"--",label="Referência: ordem 4")
    ax.set(xlabel="passo fixo Δt [s]",ylabel="erro absoluto em h2(300 s) [m]",title="Convergência do RK4")
    ax.grid(alpha=.3,which="both"); ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(FIG,"fig-05-convergencia-rk4.png"),dpi=170); plt.close(fig)
    lines.extend(["\n## Ordem de convergência do RK4\n","Referência DOP853, rtol=1e-13, atol=1e-15, passo máximo de 5 s; comparação em 300 s.",
                  "\n| Δt (s) | Erro em h2 (m) |\n|---|---|"])
    lines.extend(f"| {d:g} | {e:.6e} |" for d,e in zip(dts,errors))
    lines.append(f"\nOrdem medida: **{order:.4f}**.\n")


def amplitude(p, r, T, lines):
    deltas=np.array([-.30,-.20,-.10,-.05,.01,.05,.09]); gains=[]; times=[]
    fig,(ax,axr)=plt.subplots(1,2,figsize=(9,3.9))
    lines.extend(["\n## R5.4 — Amplitude do degrau\n","| Degrau (%) | Kef (s/m²) | Kef/Kdc | Exato 1+δ/2 | ts (s) | ts/ts,lin |\n|---|---|---|---|---|---|"])
    for delta in deltas:
        ss=simulate(p,lambda t,d=delta:p["q0"]*(1+d),[r["h1"],r["h2"]],T)
        hf=r["h2_nl"](delta); hs=ss["sol"](T)[1]
        keff=(hs-r["h2"])/(delta*p["q0"])
        _,_,ts=measure_step(ss["sol"],r["h2"],hf,T)
        gain=keff/r["K2"]; gains.append(gain); times.append(ts/r["ts"])
        assert abs(gain-(1+delta/2))<1e-5
        mask=ss["t"]<=1000
        ax.plot(ss["t"][mask],(ss["h2"][mask]-r["h2"])/(hf-r["h2"]),label=f"{100*delta:+g}%")
        lines.append(f"| {100*delta:+g} | {keff:.6f} | {gain:.6f} | {1+delta/2:.6f} | {ts:.3f} | {ts/r['ts']:.6f} |")
    ax.set(xlabel="tempo [s]",ylabel="resposta normalizada",title="Não linearidade do transitório"); ax.legend(ncol=2,fontsize=9)
    axr.plot(100*deltas,gains,"o",label="Kef/Kdc simulado")
    axr.plot(100*deltas,1+deltas/2,"-",label="Exato: 1 + δ/2")
    axr.plot(100*deltas,times,"s-",label="ts/ts,linear")
    axr.set(xlabel="degrau relativo δ [%]",ylabel="razão ao linearizado",title="Ganho e tempo de acomodação"); axr.legend(fontsize=9)
    for a in (ax,axr): a.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(os.path.join(FIG,"fig-07-amplitude-degrau.png"),dpi=170); plt.close(fig)


def balanco_massa(p,r,T,lines):
    lines.extend(["\n## Balanço integral de massa\n","Integração simultânea de h1, h2, volume de entrada e volume de saída.",
                  "\n| Ensaio | Resíduo máximo (m³) | Volume de entrada (m³) | Resíduo relativo |\n|---|---|---|---|"])
    cases=[("degrau",[r["h1"],r["h2"]],lambda t:p["q0"]*(1+DSTEP)),
           ("condição inicial",H_IC,lambda t:p["q0"]),
           ("pulso",[r["h1"],r["h2"]],lambda t:p["q0"]*(1+AMP) if t<TP else p["q0"])]
    for name,h0,q in cases:
        def rhs(t,y):
            dh=f_nl(t,y[:2],p,q)
            return [*dh,q(t),p["k2"]*np.sqrt(max(y[1],0))]
        sol=solve_ivp(rhs,(0,T),[*h0,0.,0.],rtol=RTOL,atol=ATOL,max_step=MAX_STEP)
        if not sol.success: raise RuntimeError(sol.message)
        residual=p["A1"]*(sol.y[0]-h0[0])+p["A2"]*(sol.y[1]-h0[1])-sol.y[2]+sol.y[3]
        error=np.max(np.abs(residual)); volume=sol.y[2,-1]
        assert error<1e-9, (name,error)
        lines.append(f"| {name} | {error:.6e} | {volume:.6f} | {error/volume:.6e} |")


def elasticidades(p,r,T,lines):
    keys=["A1","A2","k1","k2","q0"]; metrics=["h2","K2","t1","t2","t63","ts"]
    eps=1e-4; analytic={}; numerical={}
    for key in keys:
        rm=algebra({**p,key:p[key]*(1-eps)}); rp=algebra({**p,key:p[key]*(1+eps)})
        analytic[key]={m:(rp[m]-rm[m])/(2*eps*r[m]) for m in metrics}
        vals=[]
        for factor in (.9,1.,1.1):
            pp={**p,key:p[key]*factor}; rr=algebra(pp); duration=20*max(rr["t1"],rr["t2"])
            ss=simulate(pp,lambda t,qq=pp["q0"]:qq*1.01,[rr["h1"],rr["h2"]],duration)
            hf=rr["h2_nl"](.01); tc,_,ts=measure_step(ss["sol"],rr["h2"],hf,duration)
            vals.append({"K2":(ss["sol"](duration)[1]-rr["h2"])/(.01*pp["q0"]),"t63":tc,"ts":ts})
        numerical[key]={m:(vals[2][m]-vals[0][m])/(.2*vals[1][m]) for m in vals[1]}
    lines.extend(["\n## R5.5 — Elasticidades no ponto nominal\n",
                  "Diferença central: ±0,01% no linearizado; entre parênteses, ±10% no parâmetro e degrau de 1% no não linear. Esses testes locais podem extrapolar o domínio físico.",
                  "\n| Métrica | A1 | A2 | k1 | k2 | q0 |\n|---|---|---|---|---|---|"])
    for metric in metrics:
        cells=[]
        for key in keys:
            cell=f"{analytic[key][metric]:+.3f}"
            if metric in numerical[key]: cell+=f" ({numerical[key][metric]:+.3f})"
            cells.append(cell)
        lines.append(f"| {metric} | "+" | ".join(cells)+" |")


def hipoteses(p,r,T,ts_nominal,lines):
    lines.extend(["\n## Verificações das hipóteses H2-H5\n",
                  "H2/H3: estimativa ilustrativa com c entre 0,6 e 1,0, g=9,81 m/s² e viscosidade cinemática de 1e-6 m²/s. Esses valores não entram nas EDOs da planta."])
    areas=p["k1"]/(np.array([.6,1.])*np.sqrt(2*9.81))
    diam=np.sqrt(4*areas/np.pi)
    re=np.sqrt(2*9.81*np.array([p["hmin"],p["hmax"]])[:,None])*diam/1e-6
    lines.append(f"\nÁrea estimada do orifício: {min(areas):.6g} a {max(areas):.6g} m²; diâmetro: {min(diam):.5f} a {max(diam):.5f} m.")
    lines.append(f"Reynolds ilustrativo: {re.min():.1f} a {re.max():.1f}; máximo de (a/A1)² = {np.max((areas/p['A1'])**2):.6g}.")
    lines.extend(["\nH4: bomba de primeira ordem, partindo da vazão nominal, com degrau de +5%.",
                  "\n| tau da bomba (s) | ts de h2 (s) | Aumento sobre a bomba ideal (%) |\n|---|---|---|"])
    for tau in (1.,5.,10.):
        def rhs(t,y):
            dh=f_nl(t,y[:2],p,lambda _:y[2])
            return [*dh,(p["q0"]*(1+DSTEP)-y[2])/tau]
        sol=solve_ivp(rhs,(0,T),[r["h1"],r["h2"],p["q0"]],rtol=RTOL,atol=ATOL,max_step=MAX_STEP,dense_output=True)
        if not sol.success: raise RuntimeError(sol.message)
        _,_,ts=measure_step(sol.sol,r["h2"],r["h2_nl"](DSTEP),T)
        lines.append(f"| {tau:g} | {ts:.3f} | {100*(ts/ts_nominal-1):.4f} |")
    submerged=r["h2"]+(p["q0"]/p["k1"])**2
    lines.append(f"\nH5: com descarga afogada, o equilíbrio exigiria h1 = h2 + (qi/k1)² = {submerged:.2f} m, acima de hmax = {p['hmax']:.2f} m.")


def completar(p,r,res,sb,sc,T,lines):
    print("Exportando figuras e CSVs...",flush=True)
    diagrama(); exportar_dados(res,sb,sc,r)
    print("Verificando ordem RK4 e balanço de massa...",flush=True)
    convergencia_rk4(p,r,lines); balanco_massa(p,r,T,lines)
    print("R5.4: amplitude do degrau...",flush=True)
    amplitude(p,r,T,lines)
    print("R5.5: elasticidades...",flush=True)
    elasticidades(p,r,T,lines)
    hipoteses(p,r,T,res[DSTEP][4],lines)
    assert abs(res[DSTEP][1]-1.1025)<1e-10
    assert abs(res[DSTEP][2]-221.54)<.05
    assert abs(res[DSTEP][3]-350.30)<.05
    assert abs(res[DSTEP][4]-608.90)<.05
    print("Verificações numéricas aprovadas.",flush=True)
