"""Gera figuras do relatório e os intervalos de primeira falha observada."""
import argparse
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/"typhoonsim"))
from configuracao import CASOS,GRADE,nome_grade,margem_fase

FIG=ROOT/"relatorio/figuras"
PLANTA="#14374f"
MED="#b35118"
REF="#586775"
REAL="#b35118"
CAL="#087986"
IDE="#405976"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
    "axes.spines.top":False,"axes.spines.right":False,"axes.titleweight":"bold"})


def csv(file):
    return np.loadtxt(file,delimiter=",",skiprows=1)


def figura_ensaio(file, dest, nome):
    a=csv(file)
    t, ref, med, h2, h1, q, ent, _=a.T
    f,ax=plt.subplots(2,1,figsize=(8.8,5.35),sharex=True,layout="constrained",
                      gridspec_kw={"height_ratios":[3,1]})
    ax[0].plot(t,ref,"--",color=REF,lw=1.15,label="Referência")
    ax[0].plot(t,h2,color=PLANTA,lw=2,label="Nível da planta")
    ax[0].plot(t,med,color=MED,lw=1.5,alpha=.9,label="Leitura realimentada")
    ax[0].fill_between(t,ref-.004,ref+.004,color="#cddbe4",alpha=.3,label="Faixa de ±4 mm")
    ax[1].plot(t,q,color=CAL,lw=1.5,label="Bomba")
    if np.max(np.abs(ent-q))>.01:
        ax[1].plot(t,ent,"--",color=MED,lw=1.2,label="Entrada com distúrbio")
    ax[0].set(ylabel="Nível de T2 (m)",title=nome)
    ax[1].set(ylabel="Vazão (L/s)",xlabel="Tempo físico após evento (s)",xlim=(0,1350))
    for k in ax:
        k.grid(alpha=.23)
        k.legend(loc="best",fontsize=8)
    f.savefig(dest,dpi=170)
    plt.close(f)


def casos_principais(capturas):
    ensaios={"subida":"Subida para 1,08 m","disturbio":"Entrada extra de 0,50 L/s",
             "descida":"Descida para 0,92 m"}
    for n,titulo in ensaios.items():
        fig,ax=plt.subplots(2,3,figsize=(12.5,5.3),sharex=True,sharey="row",
                            layout="constrained",gridspec_kw={"height_ratios":[3,1.2]})
        for col,(perfil,label) in enumerate(zip(("ideal","real","calibrado"),
                                                ("Ideal","Real nominal","Real calibrado"))):
            t,ref,med,h2,h1,q,ent,_=csv(capturas/f"{n}-{perfil}.csv").T
            ax[0,col].fill_between(t,ref-.004,ref+.004,color="#d8e6ed",alpha=.55)
            ax[0,col].plot(t,ref,"--",color=REF,lw=1,label="Referência")
            ax[0,col].plot(t,h2,color=PLANTA,lw=2.3,label="Planta")
            ax[0,col].plot(t,med,color=MED,lw=1.45,linestyle=":",label="Leitura")
            ax[1,col].plot(t,q,color=CAL,lw=1.4,label="Bomba")
            if n=="disturbio":
                ax[1,col].plot(t,ent,"--",color=MED,lw=1.1,label="Entrada")
            ax[0,col].set_title(label)
            ax[1,col].set(xlabel="Tempo físico (s)",xlim=(0,1300))
            for a in ax[:,col]:
                a.grid(alpha=.2)
        ax[0,0].set_ylabel("Nível de T2 (m)")
        ax[1,0].set_ylabel("Vazão (L/s)")
        ax[0,0].legend(loc="best",fontsize=8)
        ax[1,0].legend(loc="best",fontsize=8)
        fig.suptitle(titulo,fontsize=14,fontweight="bold")
        fig.savefig(FIG/f"{n}.png",dpi=175);plt.close(fig)


def circuito():
    fig,ax=plt.subplots(figsize=(12,3.35))
    ax.set(xlim=(0,12),ylim=(0,4))
    ax.axis("off")
    def box(x,y,w,title,subtitle,col):
        ax.add_patch(Rectangle((x,y),w,.90,lw=1.6,ec=col,fc="#f6fafb"))
        ax.text(x+w/2,y+.60,title,ha="center",color=col,weight="bold",fontsize=11)
        ax.text(x+w/2,y+.23,subtitle,ha="center",color=PLANTA,fontsize=9)
    def arrow(a,b,c,d,color=PLANTA):
        ax.add_patch(FancyArrowPatch((a,b),(c,d),lw=1.55,mutation_scale=12,
                    arrowstyle="-|>",color=color,shrinkA=0,shrinkB=0))
    box(.35,2.50,1.6,"Referência","r em metros",PLANTA)
    box(2.30,2.50,1.7,"Erro","e = r − medição",PLANTA)
    box(4.37,2.50,1.59,"Controlador","PI",CAL)
    box(6.42,2.50,1.77,"Bomba","Limite 7–13 L/s",CAL)
    box(8.64,2.50,2.40,"Planta E02","Tanques 1 e 2",PLANTA)
    for x,x1 in ((1.95,2.3),(4,4.37),(5.96,6.42),(8.19,8.64)):
        arrow(x,2.95,x1,2.95)
    box(5.10,.60,3.02,"Instrumentação E03","Ideal, real ou calibrada",MED)
    ax.plot([9.84,9.84,8.83],[2.50,1.05,1.05],color=PLANTA,lw=1.55)
    arrow(8.83,1.05,8.12,1.05)
    ax.plot([5.10,3.15],[1.05,1.05],color=MED,lw=1.55)
    arrow(3.15,1.05,3.15,2.50,MED)
    ax.text(10,1.88,"Nível da planta h₂",ha="left",fontsize=9,color=PLANTA)
    ax.text(4,.79,"Leitura realimentada",ha="center",fontsize=9,color=MED)
    ax.text(8.41,3.65,"Distúrbio de vazão",ha="center",fontsize=9,color=PLANTA)
    arrow(8.41,3.52,8.41,3.03)
    fig.subplots_adjust(left=.01,right=.99,top=.99,bottom=.02)
    fig.savefig(FIG/"realimentacao.png",dpi=180);plt.close(fig)


def sinal_correto(met,canal,crit):
    if crit=="esforco": return met["atende_esforco"]
    if crit=="faixa": return met["atende_faixa"]
    return met[canal]["atende"][crit]


def mapa(dados,ensaio="subida"):
    f, axs=plt.subplots(4,3,figsize=(11.6,8.2),sharex="col",layout="constrained")
    resumo={}
    for j,(campo,vals) in enumerate(GRADE.items()):
        rr=[dados[nome_grade(campo,v,ensaio)] for v in vals]
        resumo[campo]={}
        for can in ("planta","medida"):
            resumo[campo][can]={}
            for c in ("erro","acomodacao","pico","esforco","faixa"):
                i=next((i for i,z in enumerate(rr) if not sinal_correto(z,can,c)),None)
                resumo[campo][can][c]=None if i is None else {
                    "primeira_falha":vals[i],"anterior":None if not i else vals[i-1]}
        for i,(k,lim,ylabel) in enumerate((("erro_mm",4,"|Erro final| (mm)"),
                      ("acomodacao_s",1000 if ensaio=="disturbio" else 900,"Retorno à faixa (s)"),
                      (("pico_mm",60,"Pico absoluto (mm)") if ensaio=="disturbio" else ("sobressinal_pct",10,"Sobressinal (%)")),
                      ("esforco_ls",1.5,"Esforço (L/s)"))):
            a=axs[i,j]
            a.axhline(lim,color="#8b3335",ls="--",lw=1)
            for can,col,marker,ls in [("planta",PLANTA,"o","-"),("medida",MED,"x",":")]:
                if i==3 and can=="medida":
                    continue
                yy=[x[k] if i==3 else x[can][k] for x in rr]
                y=[2550 if v is None else abs(v) for v in yy]
                a.plot(vals,y,ls,color=col,marker=marker,ms=4,label=can.capitalize())
                for xx,zz,orig in zip(vals,y,yy):
                    if orig is None: a.plot(xx,zz,"^",ms=7,mfc="white",mec=col)
            a.grid(alpha=.21)
            if j==0: a.set_ylabel(ylabel)
            if i==0:
                a.set_title({"zero_mm":"Erro de zero (mm)","tau_s":"Tomada lenta (s)",
                             "ruido_mm":"Interferência de pico (mm)"}[campo])
            if i==3: a.set_xlabel("Intensidade")
    axs[0,0].legend(fontsize=8)
    f.savefig(FIG/f"mapa-{ensaio}.png",dpi=177);plt.close(f)
    return resumo


def compactar(dados):
    f,ax=plt.subplots(1,3,figsize=(12,3.45),layout="constrained")
    for a,(campo,vs) in zip(ax,GRADE.items()):
        rr=[dados[nome_grade(campo,v)] for v in vs]
        if campo=="zero_mm":
            a.plot(vs,[abs(x["planta"]["erro_mm"]) for x in rr],"o-",color=PLANTA)
            a.axhline(4,color="#962e38",ls="--")
            a.set(xlabel="Erro de zero (mm)",ylabel="|Erro da planta| (mm)",title="Patamar físico fora da referência")
        elif campo=="tau_s":
            a.plot(vs,[x["planta"]["sobressinal_pct"] for x in rr],"o-",color=PLANTA)
            a.axhline(10,color="#962e38",ls="--")
            a.set(xlabel="Constante de tempo (s)",ylabel="Sobressinal de T2 (%)",title="Tomada lenta reduz amortecimento")
        else:
            for can,col in (("planta",PLANTA),("medida",MED)):
                a.plot(vs,[x[can]["erro_abs_max_fim_mm"] for x in rr],"o-",color=col,label=can.capitalize())
            a.axhline(4,color="#962e38",ls="--")
            a.set(xlabel="Interferência aplicada (mm)",ylabel="Pico de erro no regime (mm)",title="Leitura oscila mais que a planta")
            a.legend(fontsize=8)
        a.grid(alpha=.2)
    f.savefig(FIG/"mapa-sintese.png",dpi=180);plt.close(f)


def calibrar_fig(capturas):
    f,ax=plt.subplots(figsize=(9.8,4.1),layout="constrained")
    for perfil,color in (("ideal",IDE),("real",REAL),("calibrado",CAL)):
        a=csv(capturas/f"subida-{perfil}.csv")
        ax.plot(a[:,0],(a[:,3]-a[:,1])*1000,color=color,lw=1.75,label=perfil.capitalize())
    ax.axhspan(-4,4,color="#d7e7ee",alpha=.65,label="Faixa de ±4 mm")
    ax.axhline(0,color="#6c7d89",ls="--",lw=1)
    ax.set(xlim=(0,1150),ylim=(-31,9),xlabel="Tempo físico (s)",
           ylabel="Nível da planta − referência (mm)")
    ax.grid(alpha=.24);ax.legend(loc="lower right",fontsize=9)
    f.savefig(FIG/"calibracao.png",dpi=180);plt.close(f)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--capturas",type=Path,required=True)
    a=p.parse_args()
    dados={n:json.loads((a.capturas/(n+".json")).read_text(encoding="utf-8")) for n in CASOS}
    casos_principais(a.capturas)
    circuito()
    compactar(dados)
    calibrar_fig(a.capturas)
    o={"limiares_na_grade":{e:mapa(dados,e) for e in ("subida","disturbio")},"margens":[
        {"tau_s":t,"cruzamento_rad_s":margem_fase(t)[0],"fase_graus":margem_fase(t)[1]}
             for t in (0,*GRADE["tau_s"])]}
    (ROOT/"simulacao/mapa.json").write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
