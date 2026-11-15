"""Gráficos e resumo de capturas nativas; não simula a planta nem o instrumento."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT=Path(__file__).resolve().parent.parent
C=["#203b54","#007b8f","#bb5515"]
plt.rcParams.update({"font.size":11,"axes.titlesize":12,"axes.labelsize":10,
                     "font.family":"DejaVu Sans","figure.facecolor":"white"})


def csv(path):
    return np.loadtxt(path,skiprows=1,delimiter=',')


def figura_ensaio(captura,destino,caso):
    a=csv(captura)
    a=a[a[:,0]>=0]
    f,axs=plt.subplots(2,2,figsize=(10.2,5.1),sharex='col',layout='constrained',
                       gridspec_kw={"height_ratios":[3,1]})
    for j in range(2):
        t=a[:,0]; ref=a[:,j+1]; ideal=a[:,j+3]; real=a[:,j+5]
        ax=axs[0,j]
        ax.plot(t,ref,color=C[0],lw=2.7,label="Planta")
        ax.plot(t,ideal,color=C[1],lw=1.4,dashes=(2,2),label="Medição ideal")
        ax.plot(t,real,color=C[2],lw=1.55,label="Medição real simulada")
        ax.set_title(f"Tanque {j+1}")
        axs[1,j].plot(t,(real-ref)*1000,color=C[2],lw=1)
        axs[1,j].axhline(0,color=C[0],lw=.7,alpha=.55)
        axs[1,j].set_xlabel("Tempo físico (s)")
        ax.set_xlim(0,{"degrau":650,"inicial":550,"pulso":300}[caso])
    axs[0,0].set_ylabel("Nível (m)")
    axs[1,0].set_ylabel("Real − ideal (mm)")
    axs[0,0].legend(fontsize=8,loc='best')
    for ax in axs.flat: ax.grid(alpha=.22)
    f.savefig(destino,dpi=172)
    plt.close(f)


def cadeia(destino):
    fig,ax=plt.subplots(figsize=(12.0,3.8))
    ax.set(xlim=(0,12),ylim=(0,4)); ax.axis('off')
    def box(x,y,w,h,t,label,col):
        ax.add_patch(Rectangle((x,y),w,h,facecolor="#f7fbfc",edgecolor=col,lw=1.6))
        ax.text(x+w/2,y+h*.66,t,ha='center',va='center',fontsize=11,weight='bold',color=col)
        ax.text(x+w/2,y+h*.29,label,ha='center',va='center',fontsize=9.2,color=C[0])
    def arr(x,y,u,v):
        ax.add_patch(FancyArrowPatch((x,y),(u,v),arrowstyle='-|>',mutation_scale=13,
                                    lw=1.5,color=C[0],shrinkA=0,shrinkB=0))
    box(.10,1.08,1.55,.99,"Planta E02","h = V/10",C[0])
    box(2.08,2.61,2.05,.92,"Caminho ideal","ganho 1, sem atraso",C[1])
    ax.plot([1.65,1.87,1.87],[1.58,1.58,3.07],color=C[0],lw=1.5)
    arr(1.87,3.07,2.08,3.07); arr(4.13,3.07,5.00,3.07)
    ax.text(5.1,3.07,"Nível ideal (m)",va="center",color=C[1],fontsize=12,weight='bold')
    items=[(2.08,1.60,"Tomada","p = ρ g h",C[1]),(4.10,1.98,"HSC 160MG","5 V · 0,5 a 4,5 V",C[2]),
           (6.51,1.59,"Filtro RC","f₍c₎ = 0,2 Hz",C[2]),(8.54,1.29,"ADC","12 bits",C[2]),
           (10.25,1.61,"Conversão","nível real (m)",C[1])]
    arr(1.87,1.58,2.08,1.58)
    for i,(x,w,t,l,c) in enumerate(items):
        box(x,1.08,w,.99,t,l,c)
        if i+1<len(items): arr(x+w,1.58,items[i+1][0],1.58)
    ax.text(5.09,.54,"Atraso na tomada, ganho, zero e curvatura",ha="center",fontsize=9.5,color=C[2])
    ax.text(8.19,.19,"Interferência antes do filtro · correção de zero após o ADC",
            ha="center",fontsize=9.5,color=C[0])
    fig.subplots_adjust(left=.01,right=.99,top=.99,bottom=.02)
    fig.savefig(destino,dpi=180)
    plt.close(fig)


def resumo(capturas,figs):
    figs.mkdir(parents=True,exist_ok=True)
    for caso in ("degrau","inicial","pulso"):
        figura_ensaio(capturas/(caso+".csv"),figs/(caso+".png"),caso)
    cadeia(figs/"cadeia.png")
    f,axes=plt.subplots(1,3,figsize=(12.4,3.55),layout="constrained")
    ref=csv(capturas/"so-filtro.csv")
    for ax,nomes,rotulos,titulo in zip(axes,
      (["zero-6mm","zero-20mm","zero-60mm"],["tau-0p2s","tau-10s","tau-60s"],["ruido-2mm","ruido-10mm","ruido-40mm"]),
      (["6 mm","20 mm","60 mm"],["0,2 s","10 s","60 s"],["±2 mm","±10 mm","±40 mm"]),
      ("Deslocamento de zero","Dinâmica da tomada","Interferência após o RC")):
        for nome,label,col in zip(nomes,rotulos,C):
            a=csv(capturas/(nome+".csv")); t=a[:,0]
            baseref=ref[:,6] if nome.startswith("ruido") else a[:,4]
            ax.plot(t,(a[:,6]-baseref)*1000,label=label,color=col)
        ax.set(title=titulo,xlabel="Tempo físico (s)",
               xlim=(690,697) if titulo.startswith("Interferência") else (0,600))
        ax.grid(alpha=.24); ax.legend(fontsize=8)
    axes[0].set_ylabel("Diferença em h₂ (mm)")
    f.savefig(figs/"exacerbacao.png",dpi=180);plt.close(f)
    ripple={}
    for val in (2,10,40):
        a=csv(capturas/f"ruido-{val}mm.csv")
        mask=a[:,0]>1800
        tt=a[mask,0]
        y=(a[mask,6]-ref[mask,6])*1000
        coeff=np.linalg.lstsq(np.c_[np.ones(len(tt)),np.sin(2*np.pi*.8*tt),
                                    np.cos(2*np.pi*.8*tt)],y,rcond=None)[0]
        ripple[str(val)]={"amplitude_prevista_mm":val/np.sqrt(17),
                          "amplitude_observada_mm":float(np.hypot(coeff[1],coeff[2]))}
    (ROOT/"simulacao/atenuacao.json").write_text(json.dumps(ripple,indent=2)+"\n",encoding="utf-8")
    return ripple


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--capturas",type=Path,default=ROOT/"simulacao/dados")
    a=p.parse_args()
    print(resumo(a.capturas,ROOT/"relatorio/figuras"))
