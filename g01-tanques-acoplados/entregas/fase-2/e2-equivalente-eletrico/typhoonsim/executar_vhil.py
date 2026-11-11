"""Executa os 9 ensaios reais pela API HIL; nao aceita uma compilacao sem .cpd.

Requer Typhoon HIL Control Center com Virtual HIL disponivel.
python executar_vhil.py [--ensaio r3a] [--nao-compilar]
"""
import argparse
import json
from pathlib import Path
import sys
import time
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'simulacao'))
from equivalente import CASOS, escrever_csv, comparar, resumo


def exigir(ok,mensagem):
    if ok is False: raise RuntimeError(mensagem)


def executar(nomes,compilar=True):
    from typhoon.api.schematic_editor import SchematicAPI
    from typhoon.api import hil
    m=SchematicAPI()
    exigir(m.load(str(HERE/'modelo.tse')),'Falha ao abrir modelo.tse')
    if compilar: exigir(m.compile(),'Compilacao recusada. Conferir console e licenca.')
    cpd=Path(m.get_compiled_model_file(str(HERE/'modelo.tse')))
    if not cpd.exists():
        raise RuntimeError('O .cpd nao foi gerado. Abrir o modelo no Typhoon HIL Control Center, '
                           'compilar para HIL404 e selecionar Virtual HIL. '
                           'TyphoonSim independente nao oferece este fluxo de HIL SCADA.')
    exigir(hil.load_model(str(cpd),vhil_device=True),'Virtual HIL nao carregou o modelo.')
    records=[]
    try:
        for nome in nomes:
            caso=CASOS[nome]
            hil.stop_simulation()
            for key,value in caso.entradas().items():
                exigir(hil.set_scada_input_value(key,value),'Falha na entrada '+key)
            exigir(hil.start_simulation(),'Falha ao iniciar Virtual HIL.')
            # Aguardar o estado fisico; VHIL pode executar mais devagar que tempo real.
            deadline=time.monotonic()+180
            targets=np.array(caso.h0)*10
            while True:
                valores=np.array(hil.read_analog_signals(['V1','V2']),dtype=float)
                if np.max(np.abs(valores-targets))<.002: break
                if time.monotonic()>deadline: raise TimeoutError('Pre-carga nao convergiu: '+nome)
                time.sleep(.05)
            dt=float(hil.get_sim_step())
            decimation=round(.001/dt)
            if not np.isclose(decimation*dt,.001): raise ValueError('Passo nao divide 1 ms.')
            buffer=[]
            exigir(hil.start_capture([decimation,3,20000,False],
                ['Analog','u_ensaio',.5,'Rising edge',0.,True],
                ['V1','V2','u_ensaio'],dataBuffer=buffer,timeout=300),
                'Nao foi possivel armar a captura.')
            exigir(hil.set_scada_input_value('precarga',0.),'Falha ao disparar ensaio.')
            deadline=time.monotonic()+320
            while hil.capture_in_progress():
                if time.monotonic()>deadline: raise TimeoutError('Captura excedeu prazo: '+nome)
                time.sleep(.1)
            if not buffer: raise RuntimeError('Captura sem dados: '+nome)
            signals,y,t=buffer[0]
            arr=np.column_stack([t,*[y[signals.index(s)] for s in ['V1','V2','u_ensaio']]])
            output=HERE.parent/'simulacao/dados/vhil'/f'{nome}.csv'
            escrever_csv(output,arr)
            record=comparar(caso,arr,'vhil'); records.append(record)
            resumo(records,'vhil')
            print(nome,'erro_mm=',record['erro_maximo_mm'],'concorda=',record['concorda'],flush=True)
        manifest={'origem':'vhil','versao':hil.get_sw_version(),'ensaios':[r['ensaio'] for r in records]}
        (HERE.parent/'simulacao/dados/vhil/execucao.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    finally: hil.stop_simulation()
    if not all(r['concorda'] for r in records): raise RuntimeError('Existe ensaio fora do criterio; conferir resultados-vhil.md.')


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--ensaio',choices=list(CASOS)); ap.add_argument('--nao-compilar',action='store_true')
    args=ap.parse_args(); executar([args.ensaio] if args.ensaio else list(CASOS),not args.nao_compilar)
