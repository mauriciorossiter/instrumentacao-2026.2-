"""Gera uma rede Foster térmica nativa, em K e W, sem C functions.
Resposta livre: pré-aquecimento numérico por 20 tau_max antes de remover P.
"""
import argparse
import hashlib
import json
import math
from modelo import *
NATIVE_DT=DT/4  # 0,5 us: menor erro de atualização da rede térmica nativa

def generate(name):
    from typhoon.api.schematic_editor import SchematicAPI
    cfg=scenarios()[name];m=SchematicAPI();print('Gerando',name,flush=True)
    m.create_new_model(name='G04_Fase2_'+name.replace('.','p'))
    try:
        def new(kind,name,x,y,props=None):
            h=m.create_component('core/'+kind,name=name,position=(x,y))
            for key,value in (props or {}).items():
                if key in ('execution_rate','exec_rate'):value=NATIVE_DT
                m.set_property_value(m.prop(h,key),value)
            return h
        def wire(a,ta,b,tb):m.create_connection(m.term(a,ta),m.term(b,tb))
        warmup=math.ceil(20*max(tau(cfg))/RECORD)*RECORD if cfg['trial']=='livre' else 0.
        p=new('Step','Potencia_W',600,450,dict(step_time=warmup or cfg['step'],initial_value=cfg['power'] if warmup else 0.,final_value=0. if warmup else cfg['power'],execution_rate=DT))
        off=new('Step','Retorno_W',600,600,dict(step_time=cfg['off'],initial_value=0.,final_value=cfg['power'] if cfg['trial']=='pulso' else 0.,execution_rate=DT))
        u=new('Sum','Entrada_P_W',850,450,dict(signs='+-',execution_rate=DT))
        wire(p,'out',u,'in');wire(off,'out',u,'in1')
        plant=new('Thermal network','Planta_Termica_SI',1150,450,dict(N='1',network_type='Foster',Rth=cfg['r'],Tth=tau(cfg),T_ambient_flag=False,init_temps=0.,execution_rate=DT,exec_rate=DT))
        wire(u,'out',plant,'Pin')
        tc=new('Constant','Capsula_K',1150,650,dict(value=cfg['tc'],execution_rate=DT))
        wire(tc,'out',plant,'Tref')
        for source,terminal,title,x,ypos in [(u,'out','P_W',850,300),(plant,'Tout','Tj_termico_K',1150,300)]:
            probe=new('Probe',title,x,ypos,dict(execution_rate=DT));wire(source,terminal,probe,'in')
        # Adaptador isolado de OBSERVAÇÃO exigido pelo backend/Scope 2026.3.
        # 1 V no adaptador representa numericamente 1 K. Não é planta elétrica,
        # não tem carga nem altera a equação térmica ou os estados.
        adapter=new('Signal Controlled Voltage Source','Adaptador_observacao_1V_por_K',1700,450,dict(execution_rate=DT))
        meas=new('Voltage Measurement','T_j_K',1950,450)
        ground=new('Ground','GND_observacao',1700,650)
        wire(plant,'Tout',adapter,'in');wire(adapter,'p_node',meas,'p_node')
        wire(adapter,'n_node',meas,'n_node');wire(adapter,'n_node',ground,'node')
        view={'signals':{'T_j_K':{'viewports':[1],'type':'analog','color':{'1':'#163e69'},'display':{'1':'solid'}}},'viewports':{str(i):{'log_scale_x':False,'log_scale_y':False,'y_axis_db':False} for i in range(1,5)},'plot_settings':{'legend_visible':True,'background_color':'white','layout':'Vertical'}}
        new('Scope','Resultados',1450,700,dict(selected_signals=json.dumps(['T_j_K']),signals_data=json.dumps(view)))
        m.set_model_property_value('hil_device','HIL404')
        m.set_model_property_value('hil_configuration_id',6)
        m.set_model_property_value('sys_sp_rate_1',NATIVE_DT)
        m.set_model_property_value('simulation_time',cfg['duration']+warmup)
        m.set_model_property_value('data_sampling_rate',RECORD)
        m.set_model_property_value('max_sim_step',NATIVE_DT)
        m.create_comment('G04 / Fase2 Entrega01. Dominio TERMICO: P em W; theta e T em K.\n'
                         f'Planta Foster em bloco termico nativo, zero C functions; Ts={NATIVE_DT:g} s.\n'
                         'Parametros e condicoes iniciais: arquivo JSON homonimo ao modelo.',position=(600,150))
        dest=ROOT/'modelos'/('G04_'+name+'.tse');dest.parent.mkdir(exist_ok=True)
        assert m.save_as(str(dest));m.close_model();assert m.load(str(dest))
        save_json(dest.with_suffix('.json'),dict(caso=name,parametros=cfg,passo_nativo_s=NATIVE_DT,pre_aquecimento_s=warmup,sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),componentes=11,c_functions=0,reabertura_nativa=True,observacao='adaptador isolado 1 V/K, sem efeito na planta'))
        return dest
    finally:m.close_model()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--caso',default='degrau_4r',choices=list(scenarios())+['todos']);a=p.parse_args()
    for name in scenarios() if a.caso=='todos' else [a.caso]:print(generate(name),flush=True)
