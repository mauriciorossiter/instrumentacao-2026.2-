"""Prepara um ensaio no TyphoonSim independente; nao substitui VHIL/SCADA.

python gerar_offline.py --ensaio r3a
O arquivo gerado e modelo-offline.tse (variante com disparo automatico).
Abrir esse .tse no TyphoonSim, clicar Run e abrir o Scope Captura.
"""
import argparse
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'simulacao'))
from equivalente import CASOS


def gerar(nome,entradas=None,saida=None):
    from typhoon.api.schematic_editor import SchematicAPI
    m=SchematicAPI()
    if not m.load(str(HERE/'modelo.tse')): raise RuntimeError('Nao foi possivel abrir modelo.tse.')
    for key,value in (entradas or CASOS[nome].entradas()).items():
        if key!='precarga': m.set_property_value(m.prop(m.get_item(key),'def_value'),value)
    # No TyphoonSim SCADA Input conserva o valor padrao; usar degrau automatico.
    m.delete_item(m.get_item('precarga'))
    pre=m.create_component('core/Step',name='precarga',position=(7040,8600))
    for key,value in {'step_time':[.25],'initial_value':[1.],
                      'final_value':'0','execution_rate':.0001}.items():
        m.set_property_value(m.prop(pre,key),value)
    for name,term in [('u_ensaio_calc','in1'),('Tempo_ensaio','reset'),
                      ('Ativa_pre1','in1'),('Ativa_pre2','in1')]:
        m.create_connection(m.term(pre,'out'),m.term(m.get_item(name),term))
    scope=m.create_component('core/Scope',name='Captura',position=(9500,10000))
    m.set_property_value(m.prop(scope,'selected_signals'),['V1','V2','u_ensaio'])
    signals={s:{'viewports':[1 if s!='u_ensaio' else 2], 'type':'analog',
                'color':{str(1 if s!='u_ensaio' else 2):c},
                'display':{str(1 if s!='u_ensaio' else 2):'solid'}}
             for s,c in [('V1','#1573ad'),('V2','#e17819'),('u_ensaio','#404040')]}
    data={'signals':signals,'viewports':{str(i):{'log_scale_x':False,'log_scale_y':False,'y_axis_db':False} for i in range(1,5)},
          'plot_settings':{'layout':'Vertical','background_color':'white','legend_visible':True}}
    m.set_property_value(m.prop(scope,'signals_data'),json.dumps(data))
    m.set_model_property_value('simulation_time',20.25)
    m.set_model_property_value('data_sampling_rate',.001)
    m.set_model_property_value('max_sim_step',100e-6)
    output=Path(saida) if saida else HERE/'modelo-offline.tse'
    output.parent.mkdir(parents=True,exist_ok=True)
    if not m.save_as(str(output)): raise RuntimeError('O modelo offline nao foi salvo.')
    print(output,flush=True)
    return output


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--ensaio',choices=list(CASOS),default='r3a')
    gerar(ap.parse_args().ensaio)
