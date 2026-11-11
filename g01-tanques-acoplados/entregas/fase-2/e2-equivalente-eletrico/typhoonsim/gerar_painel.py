"""Gera o painel .cus com a API oficial do HIL SCADA (nao Standalone)."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'simulacao'))
from equivalente import CASOS


def gerar():
    from typhoon.api.scada import panel
    from typhoon.api.scada import const as c
    panel.create_new_panel()

    def widget(typ,name,x,y,w,h,**props):
        item=panel.create_widget(typ,name=name,position=[x,y])
        for key,value in {'size':[w,h],**props}.items():
            panel.set_property_value(item,key,value)
        return item

    widget(c.WT_TEXT_NOTE,'Titulo',25,15,1000,45,
           text='G01 | Fase 2 - Entrega 02 | Equivalente eletrico dos tanques')
    widget(c.WT_TEXT_NOTE,'Escalas',25,65,1000,50,
           text='10 V = 1 m; 10 mA = 10 L/s; 1 s eletrico = 100 s reais. Usar HIL SCADA + Virtual HIL.')
    defaults=CASOS['r3a'].entradas()
    for j,(name,value) in enumerate(defaults.items()):
        x=25+(j%4)*250; y=130+(j//4)*90
        widget(c.WT_TEXT_MACRO,name,x,y,220,60,label=name,
               widget_value=value,value_type='float',
               on_use_code=f'hil.set_scada_input_value({name!r}, value=float(inputValue))')
    for j,name in enumerate(['h1_m','h2_m']):
        widget(c.WT_DIGITAL,'Leitura_'+name,1060,130+j*90,220,70,
               label=name,signals=name,data_type='Analog signal',unit='m',decimals=5)

    for j,(name,caso) in enumerate(CASOS.items()):
        commands=['hil.set_scada_input_value("precarga", value=1.0)']
        for key,value in caso.entradas().items():
            if key!='precarga': commands.append(f'hil.set_scada_input_value({key!r}, value={value!r})')
            commands.append(f'panel.set_property_value(panel.get_widget_by_fqn({key!r}), "widget_value", {value!r})')
        widget(c.WT_BUTTON_MACRO,'Preset_'+name,25+(j%5)*250,320+(j//5)*65,220,45,
               label=name,on_use_code='\n'.join(commands))
    widget(c.WT_BUTTON_MACRO,'Precarregar',25,465,260,50,label='1. Pre-carga',
           on_use_code='hil.set_scada_input_value("precarga", value=1.0)\npanel.set_property_value(panel.get_widget_by_fqn("precarga"), "widget_value", 1.0)')
    widget(c.WT_BUTTON_MACRO,'Disparar',310,465,260,50,label='2. Iniciar ensaio',
           on_use_code='hil.set_scada_input_value("precarga", value=0.0)\npanel.set_property_value(panel.get_widget_by_fqn("precarga"), "widget_value", 0.0)')
    widget(c.WT_TEXT_NOTE,'Roteiro',600,455,700,75,
           text='Selecionar preset; aguardar V1/V2 (>=0,25 s simulados); armar captura; iniciar ensaio.\nExportar CSV com V1, V2 e u_ensaio. Conferir instrucoes.md.')
    widget(c.WT_CAPTURE_SCOPE,'Captura',25,560,1240,560,
           capture_signals=[{'Name':s,'Type':'Analog','Viewports':[1 if s!='u_ensaio' else 2]}
                            for s in ['V1','V2','u_ensaio']],
           capture_trigger=['Analog','u_ensaio','Rising edge',0.0,False,0.5],
           time_interval=20.,sample_rate=1000,capture_legend=True)
    path=Path(__file__).with_name('painel.cus')
    result=panel.save_panel_as(str(path))
    if result is False or not path.exists(): raise RuntimeError('Painel nao foi salvo.')
    print(path,flush=True)
    return path


if __name__=='__main__': gerar()
