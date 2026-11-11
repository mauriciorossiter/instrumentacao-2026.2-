"""Executa o circuito nativo no TyphoonSim independente e confronta com a E01.

python executar_offline.py [--ensaio r3a]
Requer TyphoonSim 2026.3 ativado e a API oficial 1.32.1.
"""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import time
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'simulacao'))
from equivalente import CASOS,escrever_csv,comparar,resumo
from gerar_offline import gerar
from gerar_modelo import INPUTS


def executar(nomes,parametros=None,progresso=print):
    from typhoon.api.schematic_editor import SchematicAPI
    results=[]
    for nome in nomes:
        base=CASOS[nome]
        entradas=base.entradas()
        if parametros:entradas.update(parametros)
        if entradas['precarga']!=1.:entradas['precarga']=1.
        for k,v in entradas.items():
            _,lo,hi,_=INPUTS[k]
            if not np.isfinite(v) or not lo<=v<=hi:raise ValueError(f'{k}: usar um valor entre {lo:g} e {hi:g}.')
        caso=replace(base,qrel=float(entradas['Q_rel']),g1=float(entradas['G1_rel']),
                     g2=float(entradas['G2_rel']),degrau=float(entradas['D_deg']),pulso=float(entradas['D_pul']),
                     h10=float(entradas['Vref1'])/10,h20=float(entradas['Vref2'])/10)
        if not all(np.isclose(entradas[k],v) for k,v in base.entradas().items()):
            caso=replace(caso,nome='manual-'+nome)
        if not all(.1<=v<=1.2 for v in caso.h0):raise ValueError('Condicao inicial fora da faixa 0,1..1,2 m.')
        if caso.g1<=0 or caso.g2<=0 or caso.qrel<=0 or not np.isfinite(list(entradas.values())).all():
            raise ValueError('Vazao e coeficientes devem ser positivos e todos os valores devem ser finitos.')
        finais=[(caso.qrel*(1+caso.degrau/100)/g)**2 for g in (caso.g1,caso.g2)]
        if not all(.1<=v<=1.2 for v in finais):
            raise ValueError('Equilibrio final fora de 0,1..1,2 m: '+str([round(v,5) for v in finais])+'. Ajustar Q_rel, G1_rel, G2_rel ou D_deg.')
        source=HERE/'offline Target files'/f'{caso.nome}.tse'
        gerar(nome,entradas,source)
        m=SchematicAPI()
        # Reabrir inicializa a tabela interna do Scope; apenas setar a propriedade nao basta.
        if not m.load(str(source)):raise RuntimeError('Falha ao reabrir o modelo preparado.')
        start=time.monotonic()
        progresso('Executando '+caso.nome+' no TyphoonSim...',flush=True)
        m._start_offline_simulation()
        df=m._get_offline_simulation_results(scope_names=['Captura'])
        wanted=['Time','V1','V2','u_ensaio']
        if any(s not in df.columns for s in wanted):raise RuntimeError('Scope sem os tres canais esperados.')
        arr=df[wanted].to_numpy(dtype=float)
        if len(arr)<20000 or not np.isfinite(arr).all() or arr[-1,0]<20.24:
            raise RuntimeError('Captura incompleta ou invalida; nenhum resultado sera aprovado.')
        active=arr[:,3]>.5
        if np.any(arr[active,1:3]/10<.1) or np.any(arr[active,1:3]/10>1.2):
            raise ValueError('A trajetoria saiu da faixa fisica 0,1..1,2 m; revisar os parametros.')
        output=HERE.parent/'simulacao/dados/offline'/f'{caso.nome}.csv'
        escrever_csv(output,arr)
        r=comparar(caso,arr,'typhoonsim-offline')
        r['execucao']={'aplicativo':'TyphoonSim 2026.3','api':'typhoon-hil-api 1.32.1',
                       'modo':'offline','amostras':len(arr),'intervalo_aquisicao_s':float(np.median(np.diff(arr[:,0]))),
                       'duracao_eletrica_s':float(arr[-1,0]),'max_sim_step_s':.0001,
                       'sp_execution_rate_s':.0001,'segundos_processamento':round(time.monotonic()-start,3)}
        target=HERE.parent/'simulacao'/f'resultados-offline-{caso.nome}.json'
        target.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
        results.append(r)
        progresso(f"{caso.nome}: {len(arr)} amostras; erro_max_mm={r['erro_maximo_mm']:.6f}; concorda={r['concorda']}",flush=True)
    all_results=[]
    for nome in CASOS:
        f=HERE.parent/'simulacao'/f'resultados-offline-{nome}.json'
        if f.exists():all_results.append(json.loads(f.read_text(encoding='utf-8')))
    if all_results:resumo(all_results,'typhoonsim-offline')
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ensaio',choices=list(CASOS));args=p.parse_args()
    rows=executar([args.ensaio] if args.ensaio else list(CASOS))
    gerar('r3a')
    if not all(r['concorda'] for r in rows):raise SystemExit('Existe caso fora do criterio. Conferir resultados-offline.md.')
