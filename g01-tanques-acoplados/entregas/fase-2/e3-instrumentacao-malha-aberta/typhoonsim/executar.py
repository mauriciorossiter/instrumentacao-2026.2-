"""Executa o modelo nativo, guarda sinais e calcula métricas. CLI e SCADA usam a mesma rotina."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import tempfile
import time

import numpy as np
from gerar_modelo import CANAIS, HERE, gerar
from parametros import CASOS, N, NOMINAL
from metricas import comparar


def executar(preset, inst=None, saida=None, exportar_modelo=None, m=None):
    from typhoon.api.schematic_editor import SchematicAPI

    caso, padrao=CASOS[preset]
    inst = inst or padrao
    destino=Path(saida or HERE.parent/"simulacao/dados").resolve()
    destino.mkdir(parents=True,exist_ok=True)
    m = m or SchematicAPI()
    inicio=time.monotonic()
    with tempfile.TemporaryDirectory(prefix="g01-e3-") as pasta:
        simulacao=gerar(m,caso,inst,Path(pasta)/"medicao.tse")
        if exportar_modelo:
            from shutil import copyfile
            copyfile(simulacao,exportar_modelo)
        if not m.load(str(simulacao)):
            raise RuntimeError("Falha ao abrir o modelo instrumentado.")
        print("Simulando",preset,flush=True)
        m._start_offline_simulation()
        df=m._get_offline_simulation_results(scope_names=["Captura"])
        dados=df[["Time",*CANAIS]].to_numpy(dtype=float)
    if len(dados)<20000 or dados[-1,0]<20.24 or not np.isfinite(dados).all():
        raise RuntimeError("Captura incompleta ou inválida.")
    disparo=np.flatnonzero(dados[:,3]>.5)
    if not disparo.size:
        raise RuntimeError("Disparo não encontrado.")
    t=np.round((dados[:,0]-.25)*N, 8)
    # Retém os últimos 5 s físicos de pré-carga para estimar o nível anterior.
    incluir=(t>=-5-1e-9)
    # Para equilíbrio no degrau e pulso, usamos as amostras anteriores a t=0.
    # Para o ensaio de condição inicial, a referência temporal é o início do teste.
    incluir=(t>=-1e-9) if caso=="inicial" else incluir
    t=t[incluir]
    dados=dados[incluir]
    ref=dados[:,8:10]
    ideal=dados[:,4:6]
    real=dados[:,6:8]
    erro_no=1000*float(np.max(np.abs(ref-dados[:,1:3]/10)))
    if erro_no>0.2: raise RuntimeError(f"Referência amostrada diverge do nó: {erro_no} mm")
    if np.max(np.abs(real-ref))>0.2: raise RuntimeError("Cadeia fora do intervalo previsto; verificar Scope e ganhos.")
    metricas=comparar(t,ref,ideal,real,caso)
    saida_csv=destino/(preset+".csv")
    arr=np.column_stack((t,ref,ideal,real))
    np.savetxt(saida_csv,arr,delimiter=",",fmt="%.9g",comments="",
               header="t_s,h1_planta_m,h2_planta_m,h1_ideal_m,h2_ideal_m,h1_real_m,h2_real_m")
    result={"preset":preset,"ensaio":caso,"origem":"typhoonsim-offline",
            "versao":"2026.3","parametros":asdict(inst),"amostras":int(len(t)),
            "passo_captura_s":round(float(np.median(np.diff(t))),9),
            "tempo_execucao_s":round(time.monotonic()-inicio,2),
            "diferenca_max_amostragem_no_mm":erro_no,"metricas":metricas}
    (destino/(preset+".json")).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(preset,{k:round(v["erro_max_mm"],3) for k,v in metricas.items()},flush=True)
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ensaio",choices=CASOS,default="degrau")
    p.add_argument("--todos",action="store_true")
    p.add_argument("--saida",type=Path)
    p.add_argument("--salvar-modelo",type=Path)
    a=p.parse_args()
    from typhoon.api.schematic_editor import SchematicAPI
    m=SchematicAPI()
    for nome in CASOS if a.todos else [a.ensaio]:
        executar(nome,saida=a.saida,exportar_modelo=a.salvar_modelo if nome=="degrau" else None,m=m)
