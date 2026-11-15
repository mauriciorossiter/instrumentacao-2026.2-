"""Executa o solver offline e exporta os sinais e as métricas da E04."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import tempfile

import numpy as np
from configuracao import (CASOS, HERE, EVENTOS, ERRO_MM, TEMPO_S, SOBRESSINAL_PCT,
                          PICO_DIST_MM, RECUPERACAO_S, ESFORCO_LS, HMIN, HMAX)
from montar import CANAIS, montar


def medir(t,y,ref,ensaio):
    e=(y-ref)*1000
    permanente=t>=t[-1]-100
    ee=float(np.mean(e[permanente]))
    violacoes=np.flatnonzero(np.abs(e)>ERRO_MM+1e-3)
    if not len(violacoes):
        acomodacao=0.
    elif violacoes[-1]==len(t)-1:
        acomodacao=None
    else:
        acomodacao=round(float(t[violacoes[-1]+1]),3)
    pico=float(np.max(np.abs(e)))
    sentido=1 if EVENTOS[ensaio][0]>=1 else -1
    os=None if ensaio=="disturbio" else max(0.,float(np.max(sentido*e))/80*100)
    return {
        "erro_mm":ee,"erro_abs_max_fim_mm":float(np.max(np.abs(e[permanente]))),
        "acomodacao_s":acomodacao,"pico_mm":pico,"sobressinal_pct":os,
        "atende":{"erro":abs(ee)<=ERRO_MM+1e-3,
                  "acomodacao":acomodacao is not None and acomodacao<=(RECUPERACAO_S if ensaio=="disturbio" else TEMPO_S),
                  "pico":pico<=PICO_DIST_MM if ensaio=="disturbio" else os<=SOBRESSINAL_PCT}
    }


def analisar(nome,ensaio,perfil,instrumento,t,recorte):
    # A amostra em t=0 ainda pode preceder o disparo discreto da referência.
    ativo=recorte[:,-1]>.5
    t=t[ativo]
    ref,med,h2,h1,q,qin,_=recorte[ativo].T
    if not len(t) or not np.allclose(ref,EVENTOS[ensaio][0],atol=1e-6,rtol=0):
        raise RuntimeError("A referência registrada após o disparo está incorreta.")
    esforco=float(np.max(np.abs(q-10)))
    faixa=[float(min(h1.min(),h2.min())),float(max(h1.max(),h2.max()))]
    return {"preset":nome,"origem":"TyphoonSim 2026.3 offline","amostras":int(len(t)),
       "ensaio":ensaio,"perfil":perfil,"instrumento":instrumento,
       "medida":medir(t,med,ref,ensaio),"planta":medir(t,h2,ref,ensaio),
       "esforco_ls":esforco,"vazao_comando_ls":[float(q.min()),float(q.max())],
       "vazao_entrada_ls":[float(qin.min()),float(qin.max())],
       "faixa_planta_m":faixa,"atende_esforco":esforco<=ESFORCO_LS,
       "atende_faixa":faixa[0]>=HMIN and faixa[1]<=HMAX}

def executar(nome,cenario=None,destino=None,salvar=None,m=None):
    from typhoon.api.schematic_editor import SchematicAPI

    caso=cenario or CASOS[nome]
    destino=Path(destino or HERE.parent/"simulacao/dados").resolve()
    destino.mkdir(parents=True,exist_ok=True)
    m=m or SchematicAPI()
    with tempfile.TemporaryDirectory(prefix="g01-e4-") as tmp:
        modelo=montar(m,caso,Path(tmp)/"controle.tse")
        if salvar:
            shutil.copyfile(modelo,salvar)
        if not m.load(str(modelo)):
            raise RuntimeError("Modelo E04 não abriu para simular.")
        print("Simulando",nome,flush=True)
        m._start_offline_simulation()
        df=m._get_offline_simulation_results(scope_names=["Captura"])
        dados=df[["Time",*CANAIS]].to_numpy(dtype=float)
    if dados.shape[0]<25000 or dados[-1,0]<25.24 or not np.isfinite(dados).all():
        raise RuntimeError("Captura incompleta ou inválida.")
    t=np.round((dados[:,0]-.25)*100,8)
    inclui=t>=0
    recorte=dados[inclui]
    t=t[inclui]
    ref,med,h2,h1,q,qin,_=recorte[:,1:].T
    if abs(ref[-1]-EVENTOS[caso.ensaio][0])>1e-5 or abs(h2[0]-1)>1e-4:
        raise RuntimeError("A referência ou a pré-carga está incorreta.")
    if caso.perfil=="ideal" and np.max(np.abs(med-h2))>1e-5:
        raise RuntimeError("A leitura ideal deveria coincidir com h2.")
    r=analisar(nome,caso.ensaio,caso.perfil,asdict(caso.instrumento),t,recorte[:,1:])
    np.savetxt(destino/(nome+".csv"),np.column_stack((t,recorte[:,1:])),delimiter=",",
      fmt="%.9g", comments="",header="t_s,"+",".join(CANAIS))
    (destino/(nome+".json")).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(nome, {k:round(r[k]["erro_mm"],3) for k in ("medida","planta")},
          "ts planta",r["planta"]["acomodacao_s"],flush=True)
    return r


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ensaio",choices=CASOS,default="subida-real")
    p.add_argument("--grupo",choices=("principais","grade","grade-disturbio","todos"))
    p.add_argument("--saida",type=Path)
    p.add_argument("--salvar-modelo",type=Path)
    a=p.parse_args()
    from typhoon.api.schematic_editor import SchematicAPI
    m=SchematicAPI()
    principal=tuple(f"{k}-" for k in EVENTOS)
    grupos={
        "principais":[n for n in CASOS if n.startswith(principal)],
        "grade":[n for n in CASOS if not n.startswith((*principal,"d-"))],
        "grade-disturbio":[n for n in CASOS if n.startswith("d-")],
        "todos":list(CASOS)
    }
    nomes=grupos[a.grupo] if a.grupo else [a.ensaio]
    for nome in nomes:
        executar(nome,destino=a.saida,salvar=a.salvar_modelo if nome==a.ensaio else None,m=m)
