"""Referencia eletrica e comparacao de CSVs reais do Typhoon com a Entrega 01.

python equivalente.py --referencia
python equivalente.py --typhoon captura.csv --ensaio r3a --gatilho u_ensaio
Os dados previstos em Python nunca sao classificados como captura de VHIL.
"""
import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
FIG=HERE.parent/"relatorio/figuras"
DATA=HERE/"dados"
KV,KI,N=10.,1.,100.
TS=100e-6
CAP=.5*KI/(KV*N)
G0=.01*KI/math.sqrt(KV)
PRE=.25
TEND=20.


@dataclass(frozen=True)
class Caso:
    nome:str
    qrel:float=1.
    g1:float=1.
    g2:float=1.
    degrau:float=5.
    pulso:float=0.
    h10:float|None=None
    h20:float|None=None

    @property
    def h0(self):
        return (self.h10 if self.h10 is not None else (self.qrel/self.g1)**2,
                self.h20 if self.h20 is not None else (self.qrel/self.g2)**2)

    def entradas(self):
        h1,h2=self.h0
        return dict(precarga=1.,Vref1=KV*h1,Vref2=KV*h2,Q_rel=self.qrel,
                    D_deg=self.degrau,D_pul=self.pulso,G1_rel=self.g1,G2_rel=self.g2)

    def vazao(self,t):
        return .01*self.qrel*(1+self.degrau/100+self.pulso/100*(0<=t<30))


CASOS={c.nome:c for c in [Caso("r3a"),Caso("r3b",degrau=0,h10=1.15,h20=.6),
    Caso("r3c",degrau=0,pulso=20),Caso("r4-k2-1"),Caso("r4-k2-2",g2=2),
    Caso("r4-k2-3",g2=3),Caso("r4-q-0p5",qrel=.5),
    Caso("r4-q-0p75",qrel=.75),Caso("r4-q-1")]}


def original(caso,t):
    """EDOs e parametros da Entrega 01, em unidades hidraulicas."""
    def rhs(t,h):
        q1=.01*caso.g1*math.sqrt(max(h[0],0.))
        q2=.01*caso.g2*math.sqrt(max(h[1],0.))
        return [(caso.vazao(t)-q1)/.5,(q1-q2)/.5]
    sol=solve_ivp(rhs,(0,max(float(np.max(t)),.01)),caso.h0,
                  method="RK45",rtol=1e-9,atol=1e-11,max_step=.1,dense_output=True)
    if not sol.success: raise RuntimeError(sol.message)
    return sol.sol(t).T


def prever(caso):
    """Aproximacao ZOH com atraso de uma amostra na leitura das tensoes.

    O capacitor integra exatamente a corrente mantida em cada intervalo TS.
    Essa hipotese numerica nao substitui a verificacao do modelo compilado.
    """
    steps=round((PRE+TEND)/TS)
    stride=10
    rows=[]; v1=v2=old1=old2=0.
    ref1,ref2=np.array(caso.h0)*KV
    for j in range(steps+1):
        t=j*TS-PRE; pre=1. if t<-TS/2 else 0.; u=1-pre
        te=max(t,0.)
        i0=.01*caso.qrel*(1+u*(caso.degrau/100+caso.pulso/100*(te<.3)))
        i12=G0*caso.g1*math.sqrt(max(old1,0.))
        i2=G0*caso.g2*math.sqrt(max(old2,0.))
        ip1=pre*max(-.1,min(.1,2*(ref1-old1)))
        ip2=pre*max(-.1,min(.1,2*(ref2-old2)))
        if j%stride==0: rows.append((t,v1,v2,u))
        old1,old2=v1,v2
        v1+=(i0+ip1-i12)*TS/CAP
        v2+=(i12+ip2-i2)*TS/CAP
    return np.asarray(rows)


def escrever_csv(path,arr):
    path.parent.mkdir(parents=True,exist_ok=True)
    np.savetxt(path,arr,delimiter=",",header="tempo_eletrico_s,V1,V2,u_ensaio",
               comments="",fmt="%.12g")


def ler_csv(path,v1="V1",v2="V2",gatilho="u_ensaio"):
    text=Path(path).read_text(encoding="utf-8-sig")
    lines=[s for s in text.splitlines() if s.strip() and not s.lstrip().startswith("#")]
    delim=csv.Sniffer().sniff("\n".join(lines[:10]),delimiters=",;\t").delimiter
    rows=list(csv.reader(lines,delimiter=delim))
    def norm(s): return "".join(c.lower() for c in s if c.isalnum())
    header_index=None
    for i,row in enumerate(rows[:30]):
        keys=[norm(s) for s in row]
        if any(norm(v1)==k or norm("V("+v1+")")==k for k in keys):
            header_index=i; break
    if header_index is None: raise ValueError("Cabecalho com V1/V2 nao encontrado; use --v1 e --v2.")
    header=rows[header_index]; keys=[norm(s) for s in header]
    def index(wanted,aliases=()):
        options={norm(wanted),norm("V("+wanted+")"),*(norm(x) for x in aliases)}
        hits=[i for i,k in enumerate(keys) if k in options]
        if len(hits)!=1: raise ValueError(f"Coluna {wanted!r} ausente ou ambigua: {header}")
        return hits[0]
    ti=index("tempo_eletrico_s",("Time","Time (s)","tempo_s","t","t [s]"))
    a=index(v1); b=index(v2); g=index(gatilho)
    data=[]
    for row in rows[header_index+1:]:
        if len(row)!=len(header): continue
        try: data.append([float(row[k].replace(",",".")) for k in (ti,a,b,g)])
        except ValueError: continue
    arr=np.asarray(data)
    if arr.ndim!=2 or len(arr)<100: raise ValueError("CSV sem amostras suficientes.")
    if not np.isfinite(arr).all() or not (np.diff(arr[:,0])>0).all():
        raise ValueError("CSV contem valores invalidos ou tempo nao crescente.")
    return arr


def alinhar(arr):
    u=arr[:,3]; edges=np.flatnonzero((u[1:]>.5)&(u[:-1]<=.5))+1
    if len(edges)>1: raise ValueError("Ha mais de um disparo no CSV; recorte um unico ensaio.")
    if len(edges)==1: start=int(edges[0])
    elif u[0]>.5: start=0
    else: raise ValueError("A captura nao contem o disparo u_ensaio.")
    t=(arr[start:,0]-arr[start,0])*N
    h=arr[start:,1:3]/KV
    return t,h


def cruzamento(t,y,level,sign):
    idx=np.flatnonzero(sign*(y-level)>=0)
    if not len(idx): return None
    i=int(idx[0])
    if i==0: return float(t[0])
    return float(t[i-1]+(level-y[i-1])*(t[i]-t[i-1])/(y[i]-y[i-1]))


def metricas(caso,t,h):
    h1eq=(caso.qrel/caso.g1)**2; h2eq=(caso.qrel/caso.g2)**2
    out={"h2_final_m":float(np.mean(h[-max(2,len(h)//20):,1]))}
    if caso.degrau:
        yf=(caso.qrel*(1+caso.degrau/100)/caso.g2)**2
        dy=yf-h2eq; sg=1 if dy>0 else -1
        t10=cruzamento(t,h[:,1],h2eq+.1*dy,sg)
        t90=cruzamento(t,h[:,1],h2eq+.9*dy,sg)
        out["Kef_s_m2"]=(out["h2_final_m"]-h2eq)/(.01*caso.qrel*caso.degrau/100)
        out["t63_s"]=cruzamento(t,h[:,1],h2eq+.632*dy,sg)
        out["tr_s"]=None if t10 is None or t90 is None else t90-t10
        bad=np.flatnonzero(np.abs(h[:,1]-yf)>.02*abs(dy))
        if len(bad) and bad[-1]<len(t)-1:
            k=int(bad[-1]); e0=abs(h[k,1]-yf); e1=abs(h[k+1,1]-yf)
            out["ts_s"]=float(t[k]+(e0-.02*abs(dy))*(t[k+1]-t[k])/(e0-e1))
        else: out["ts_s"]=None
        out["sobressinal_pct"]=float(max(0.,np.max(sg*(h[:,1]-yf)))/abs(dy)*100)
    else:
        for j,name in [(0,"h1"),(1,"h2")]:
            k=int(np.argmax(h[:,j])); out[name+"_pico_m"]=float(h[k,j]); out[name+"_t_pico_s"]=float(t[k])
        if caso.nome=="r3b":
            mask=(t>=300)&(t<=800)&(np.abs(h[:,0]-h1eq)>1e-10)
            out["tau1_s"]=float(-1/np.polyfit(t[mask],np.log(abs(h[mask,0]-h1eq)),1)[0])
    return out


def comparar(caso,arr,origem,path_base=None):
    t,h=alinhar(arr)
    if t[-1]<1900: raise ValueError("Captura curta: use 20 s eletricos para atingir 2000 s reais.")
    ref=original(caso,t)
    measured=metricas(caso,t,h); expected=metricas(caso,t,ref)
    diff_mm=(h-ref)*1000
    rows=[]; ok=float(np.max(abs(diff_mm)))<=2.
    for name,value in measured.items():
        reference=expected[name]
        if value is None or reference is None:
            pct=None; passed=False
        elif abs(reference)<1e-9:
            pct=None; passed=abs(value-reference)<1e-4
        else:
            pct=100*(value-reference)/reference; passed=abs(pct)<=1.
        # Instante do maximo de h1 da condicao inicial e zero por definicao.
        rows.append(dict(grandeza=name,original=reference,equivalente=value,
                         diferenca_pct=pct,concorda=bool(passed)))
        ok=ok and passed
    record={"ensaio":caso.nome,"origem":origem,"entradas":caso.entradas(),
            "erro_maximo_mm":float(np.max(abs(diff_mm))),"concorda":bool(ok),"metricas":rows}
    FIG.mkdir(parents=True,exist_ok=True)
    prefix={"python-previsto":"previa","vhil":"vhil","typhoonsim-offline":"offline"}[origem]
    outstem=path_base or HERE/f"resultados-{prefix}-{caso.nome}"
    outstem.with_suffix(".json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
    fig,(ax,ae)=plt.subplots(2,1,figsize=(8,5.6),sharex=True,gridspec_kw={"height_ratios":[2,1]})
    for j,color in [(0,"C0"),(1,"C1")]:
        ax.plot(t,ref[:,j],color=color,lw=1.7,label=f"h{j+1} E01 (RK45)")
        ax.plot(t[::10],h[::10,j],"--",color=color,lw=1.1,label=f"h{j+1} equivalente")
        ae.plot(t,diff_mm[:,j],color=color,label=f"erro h{j+1}")
    label={"previa":"Previsao em Python","vhil":"Validacao VHIL","offline":"TyphoonSim offline"}[prefix]
    ax.set(ylabel="nivel [m]",title=label+f" - {caso.nome}")
    ax.legend(fontsize=9,ncol=2); ae.set(xlabel="tempo no dominio original [s]",ylabel="erro [mm]")
    ae.axhline(2,color="gray",ls=":"); ae.axhline(-2,color="gray",ls=":")
    ae.legend(fontsize=8,ncol=2)
    for a in (ax,ae): a.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(FIG/f"{prefix}-{caso.nome}.png",dpi=160); plt.close(fig)
    return record


def resumo(records,origem):
    lines=["# Resultados do equivalente eletrico", "",f"Origem dos dados: **{origem}**.",
           "\nEscalas: kv=10 V/m; ki=1 A/(m³/s); N=100; C1=C2=500 µF; G1=G2=0,00316227766017 A/√V.",
           "\nCriterios: erro pontual de nivel <=2 mm e diferenca <=1% nas metricas nao nulas. Para referencia zero, usa-se tolerancia absoluta de 1e-4 na unidade da metrica.",
           "\n| Ensaio | Erro maximo (mm) | Concorda |\n|---|---|---|"]
    for r in records: lines.append(f"| {r['ensaio']} | {r['erro_maximo_mm']:.6f} | {r['concorda']} |")
    for r in records:
        lines.extend([f"\n## {r['ensaio']}","\n| Grandeza | E01 | Equivalente | Diferenca (%) | Concorda |\n|---|---|---|---|---|"])
        for m in r["metricas"]:
            def fmt(v): return "n/a" if v is None else f"{v:.8g}"
            lines.append(f"| {m['grandeza']} | {fmt(m['original'])} | {fmt(m['equivalente'])} | {fmt(m['diferenca_pct'])} | {m['concorda']} |")
    suffix={"python-previsto":"previstos","vhil":"vhil","typhoonsim-offline":"offline"}[origem]
    (HERE/f"resultados-{suffix}.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--referencia",action="store_true")
    p.add_argument("--typhoon",type=Path)
    p.add_argument("--origem",choices=["vhil","typhoonsim-offline"],default="vhil")
    p.add_argument("--ensaio",choices=list(CASOS),default="r3a")
    p.add_argument("--gatilho",default="u_ensaio"); p.add_argument("--v1",default="V1"); p.add_argument("--v2",default="V2")
    args=p.parse_args()
    if args.typhoon:
        r=comparar(CASOS[args.ensaio],ler_csv(args.typhoon,args.v1,args.v2,args.gatilho),args.origem)
        resumo([r],args.origem); print(json.dumps(r,ensure_ascii=False,indent=2))
    else:
        records=[]
        for c in CASOS.values():
            arr=prever(c); escrever_csv(DATA/"previstos"/(c.nome+".csv"),arr)
            r=comparar(c,arr,"python-previsto"); records.append(r)
            print(c.nome,r["erro_maximo_mm"],r["concorda"],flush=True)
        resumo(records,"python-previsto")
