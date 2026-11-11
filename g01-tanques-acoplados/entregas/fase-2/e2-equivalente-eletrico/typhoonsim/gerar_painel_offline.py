"""Painel SCADA Standalone que prepara e executa o circuito no TyphoonSim.

O painel inicia execucoes offline completas; nao modifica uma simulacao HIL.
"""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'simulacao'))
from equivalente import CASOS

BOOT='''from pathlib import Path
import sys
try:
    _pasta=Path(get_settings_dir_path())
except (NameError,TypeError):
    _pasta=Path()
if not (_pasta/"executar_offline.py").exists():
    _pasta=Path(panel.get_property_value(panel.get_widget_by_fqn("Pasta"),"widget_value"))
if not (_pasta/"executar_offline.py").exists():
    raise RuntimeError("Ajustar Pasta para a pasta typhoonsim desta entrega.")
panel.set_property_value(panel.get_widget_by_fqn("Pasta"),"widget_value",str(_pasta.resolve()))
_pasta=_pasta.resolve()
if str(_pasta) not in sys.path: sys.path.insert(0,str(_pasta))
'''

RUN=BOOT+'''import json
from datetime import datetime, timezone
import importlib
import executar_offline as _exec_mod
importlib.reload(_exec_mod)
executar=_exec_mod.executar
_status=panel.get_widget_by_fqn("Estado")
_nome=panel.get_property_value(panel.get_widget_by_fqn("Caso"),"text")
_param={k:float(panel.get_property_value(panel.get_widget_by_fqn(k),"widget_value"))
        for k in ["Q_rel","G1_rel","G2_rel","D_deg","D_pul","Vref1","Vref2"]}
panel.set_property_value(_status,"text","Executando "+_nome+" no solver nativo do TyphoonSim...")
try:
    _r=executar([_nome],parametros=_param)[0]
    _grafico=_pasta.parent/"relatorio"/"figuras"/("offline-"+_r["ensaio"]+".png")
    panel.set_property_value(panel.get_widget_by_fqn("Grafico"),"image",str(_grafico))
    panel.set_property_value(_status,"text",("Ultima captura: "+_r["ensaio"]+"\\n"
        +str(_r["execucao"]["amostras"])+" amostras reais\\nErro maximo: "+format(_r["erro_maximo_mm"],".6f")
        +" mm\\nConcorda: "+str(_r["concorda"])+"\\nModo: TyphoonSim offline\\nSCADA Standalone"))
    _evidencia={"interface":"SCADA Standalone","solver":"TyphoonSim offline","ensaio":_r["ensaio"],
                "parametros":_param,"concorda":_r["concorda"],"instante_utc":datetime.now(timezone.utc).isoformat()}
    _destino=_pasta.parent/"simulacao"/"dados"/"offline"/("scada-"+_r["ensaio"]+".json")
    _destino.write_text(json.dumps(_evidencia,indent=2,ensure_ascii=False),encoding="utf-8")
except Exception as _erro:
    panel.set_property_value(_status,"text","Falha: "+str(_erro))
    raise
'''


def gerar():
    from typhoon.api.scada import panel,const as c
    panel.create_new_panel()
    def widget(typ,name,x,y,w,h,**props):
        z=panel.create_widget(typ,name=name,position=[x,y])
        if 'label' in props:props={'use_label':True,**props}
        for k,v in {'size':[w,h],**props}.items():panel.set_property_value(z,k,v)
        return z
    widget(c.WT_TEXT_NOTE,'Titulo',20,10,1140,40,text='G01 - Equivalente eletrico | SCADA Standalone + TyphoonSim offline')
    widget(c.WT_TEXT_MACRO,'Pasta',20,60,700,45,label='Pasta dos scripts',input_width=480,value_type='string',widget_value=str(HERE),on_use_code='pass')
    values=CASOS['r3a'].entradas()
    keys=['Q_rel','G1_rel','G2_rel','D_deg','D_pul','Vref1','Vref2']
    for j,k in enumerate(keys):
        widget(c.WT_TEXT_MACRO,k,20+(j%4)*285,125+(j//4)*62,260,48,label=k,value_type='float',widget_value=values[k],on_use_code='pass')
    equilibrium='''_q=float(panel.get_property_value(panel.get_widget_by_fqn("Q_rel"),"widget_value"))
for _j in (1,2):
    _g=float(panel.get_property_value(panel.get_widget_by_fqn("G"+str(_j)+"_rel"),"widget_value"))
    panel.set_property_value(panel.get_widget_by_fqn("Vref"+str(_j)),"widget_value",10*(_q/_g)**2)
'''
    widget(c.WT_BUTTON_MACRO,'Equilibrio',875,187,260,48,label='Recalcular equilibrio',on_use_code=equilibrium)
    for j,(nome,caso) in enumerate(CASOS.items()):
        lines=[f'panel.set_property_value(panel.get_widget_by_fqn("Caso"),"text",{nome!r})']
        for k,v in caso.entradas().items():
            if k!='precarga':lines.append(f'panel.set_property_value(panel.get_widget_by_fqn({k!r}),"widget_value",{v!r})')
        lines.append(f'panel.set_property_value(panel.get_widget_by_fqn("Estado"),"text","Selecionado: {nome}. Clicar Executar ensaio. O grafico mostra a ultima captura.")')
        widget(c.WT_BUTTON_MACRO,'Preset_'+nome,20+(j%5)*230,260+(j//5)*52,210,40,label=nome,on_use_code='\n'.join(lines))
    widget(c.WT_TEXT_NOTE,'CasoLabel',20,372,130,32,text='Caso selecionado:')
    widget(c.WT_TEXT_NOTE,'Caso',160,372,230,32,text='r3a')
    widget(c.WT_BUTTON_MACRO,'Executar',420,367,290,48,label='Executar ensaio no TyphoonSim',on_use_code=RUN)
    widget(c.WT_TEXT_NOTE,'Modo',760,365,380,60,text='Ajustes entre execucoes offline.\nSem dispositivo HIL ou Control Center.')
    widget(c.WT_IMAGE,'Grafico',20,435,800,560,image=str(HERE.parent/'relatorio/figuras/offline-r3a.png'),image_scaling='Keep aspect ratio')
    widget(c.WT_TEXT_NOTE,'Estado',850,435,310,250,text='Pronto. Selecionar caso, ajustar valores e executar.\nO grafico inicial e a captura real r3a ja arquivada.')
    widget(c.WT_TEXT_NOTE,'Escalas',850,710,310,200,text='v=10h; i=q; t_original=100t_eletrico\n20,25 s eletricos por execucao\nAquisicao: intervalo 1 ms\nCriterios: <=2 mm e <=1% nas metricas\nCSVs em simulacao/dados/offline')
    out=HERE/'painel-offline.cus';panel.save_panel_as(str(out));print(out,flush=True);return out


if __name__=='__main__':gerar()
