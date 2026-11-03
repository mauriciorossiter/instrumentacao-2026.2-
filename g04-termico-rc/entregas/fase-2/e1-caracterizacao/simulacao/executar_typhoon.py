"""Executa TyphoonSim offline e exporta os dados nativos. Nunca faz polling VHIL."""
import argparse
import hashlib
import json
import pickle
import time
from modelo import *

def run(name):
    import numpy as np
    import pandas as pd
    from typhoon.api.schematic_editor import SchematicAPI
    from typhoon_modelo import generate
    path=generate(name);m=SchematicAPI();start=time.monotonic()
    try:
        assert m.load(str(path));print('Solver TyphoonSim:',name,flush=True)
        try:m._start_offline_simulation()
        except Exception:
            print('Mensagens de compilacao:',m.last_compilation_messages(),flush=True)
            raise
        result=m._get_offline_simulation_results(scope_names=['Resultados'])
        out=ROOT/'resultados_typhoon';out.mkdir(exist_ok=True)
        (out/(name+'_nativo.pkl')).write_bytes(pickle.dumps(result))
        if isinstance(result,dict):result=result['Resultados']
        if not isinstance(result,pd.DataFrame):raise TypeError(type(result))
        print('Colunas:',list(result.columns),'linhas:',len(result),flush=True)
        assert len(result)>100
        assert 'Time' in result
        assert np.isfinite(result.to_numpy()).all()
        result.to_csv(out/(name+'_bruto.csv'),index=False)
        modelmeta=json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
        warmup=modelmeta['pre_aquecimento_s']
        if warmup:
            result=result.loc[result['Time']>=warmup-1e-10].copy()
            result['Time']=result['Time']-warmup
        result.to_csv(out/(name+'.csv'),index=False)
        cfg=scenarios()[name]
        analytical=np.array([cfg['tc']+sum(exact(max(0.,float(t)),cfg)) for t in result['Time']])
        error=float(np.max(np.abs(result['T_j_K']-analytical)))
        assert error<.01*cfg['power']*sum(cfg['r']),('Divergencia nativa acima de 1% da elevacao de equilibrio',name,error)
        save_json(out/(name+'.json'),dict(caso=name,backend='TyphoonSim offline nativo',versao='THCC 2026.3',
            parametros=cfg,passo_nativo_s=modelmeta['passo_nativo_s'],pre_aquecimento_s=warmup,erro_max_vs_solucao_fechada_K=error,colunas=list(result.columns),amostras=len(result),
            sha256_tse=hashlib.sha256(path.read_bytes()).hexdigest(),tempo_real_s=time.monotonic()-start))
    finally:m.close_model()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--caso',default='degrau_4r',choices=list(scenarios())+['todos']);a=p.parse_args()
    for name in scenarios() if a.caso=='todos' else [a.caso]:run(name)
