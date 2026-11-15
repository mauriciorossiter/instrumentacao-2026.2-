"""Gera o painel SCADA Standalone para ajustes entre execuções offline."""
import ast
from dataclasses import asdict
from pathlib import Path

from parametros import CASOS, NOMINAL
HERE=Path(__file__).resolve().parent
RUN='''from pathlib import Path
import sys, tempfile
from dataclasses import replace
_pasta=Path(panel.get_property_value(panel.get_widget_by_fqn("Pasta"),"widget_value"))
try:
    _origem=Path(get_settings_dir_path())
    if (_origem/"executar.py").is_file():
        _pasta=_origem
except (NameError, TypeError):
    pass
if not (_pasta/"executar.py").is_file():
    raise RuntimeError("Preencha Pasta dos scripts com o diretório typhoonsim da E03 e confirme com Enter.")
sys.path.insert(0,str(_pasta.resolve()))
from parametros import CASOS
from executar import executar
_st=panel.get_widget_by_fqn("Estado")
_preset=panel.get_property_value(panel.get_widget_by_fqn("Caso"),"text")
_caso,_base=CASOS[_preset]
_ajustes={k: float(panel.get_property_value(panel.get_widget_by_fqn(k),"widget_value"))
          for k in vars(_base)}
try:
    panel.set_property_value(_st,"text","Executando "+_preset+" no TyphoonSim...")
    _dir=Path(tempfile.mkdtemp(prefix="g01-e3-scada-"))
    _r=executar(_preset,inst=replace(_base,**_ajustes),saida=_dir)
    sys.path.insert(0,str(_pasta.parent/"simulacao"))
    from graficos import figura_ensaio
    _png=_dir/"captura.png"
    figura_ensaio(_dir/(_preset+".csv"),_png,_caso)
    panel.set_property_value(panel.get_widget_by_fqn("Grafico"),"image",str(_png))
    _m=_r["metricas"]
    panel.set_property_value(_st,"text",f"Captura: {_preset} | {_r['amostras']} pontos\\nErro máx. T1: {_m['h1']['erro_max_mm']:.2f} mm\\nErro máx. T2: {_m['h2']['erro_max_mm']:.2f} mm\\nArquivos temporários: {_dir}")
except Exception as _erro:
    panel.set_property_value(_st,"text","Falha: "+str(_erro))
    raise
'''


def gerar():
    from typhoon.api.scada import panel,const as c
    panel.create_new_panel()
    def widget(typ,name,x,y,w,h,**props):
        z=panel.create_widget(typ,name=name,position=[x,y])
        if "label" in props:
            props={"use_label":True,**props}
        for k,v in {"size":[w,h],**props}.items():
            panel.set_property_value(z,k,v)
        return z
    widget(c.WT_TEXT_NOTE,"Titulo",20,10,1110,43,
           text="G01 | Instrumentação em malha aberta – TyphoonSim offline")
    widget(c.WT_TEXT_MACRO,"Pasta",20,62,700,45,label="Pasta dos scripts",
           input_width=480,value_type="string",widget_value="",on_use_code="pass")
    nomes={"zero_mm":"Erro de zero (mm)","ganho_pct":"Erro de ganho (%)",
           "tau_s":"Constante da tomada (s)","ruido_mm":"Interferência de pico (mm)",
           "fc_hz":"Corte RC (Hz; 0 desliga)","adc_bits":"ADC (bits; 0 desliga)",
           "correcao_mm":"Correção de zero (mm)","curvatura_mm":"Curvatura (mm)"}
    for j,(k,v) in enumerate(asdict(NOMINAL).items()):
        widget(c.WT_TEXT_MACRO,k,20+(j%4)*286,119+(j//4)*54,266,47,label=nomes[k],
               input_width=85,value_type="float",widget_value=v,on_use_code="pass")
    for j,(nome,(_,inst)) in enumerate(CASOS.items()):
        linhas=[f'panel.set_property_value(panel.get_widget_by_fqn("Caso"),"text",{nome!r})']
        linhas.extend(f'panel.set_property_value(panel.get_widget_by_fqn({k!r}),"widget_value",{v!r})'
                      for k,v in asdict(inst).items())
        linhas.append('panel.set_property_value(panel.get_widget_by_fqn("Estado"),"text","Preset carregado. Clique Executar.")')
        code="\n".join(linhas);ast.parse(code)
        widget(c.WT_BUTTON_MACRO,f"Preset_{j}",20+(j%6)*190,235+(j//6)*40,174,32,
               label=nome,on_use_code=code)
    widget(c.WT_TEXT_NOTE,"Caso",23,370,225,45,text="degrau")
    ast.parse(RUN)
    widget(c.WT_BUTTON_MACRO,"Executar",260,364,250,44,label="Executar no TyphoonSim",on_use_code=RUN)
    widget(c.WT_TEXT_NOTE,"Modo",565,366,555,45,
           text="Ajustes entre rodadas do solver. Zero em τ, fc e bits ativa bypass.")
    widget(c.WT_IMAGE,"Grafico",20,432,815,440,image_scaling="Keep aspect ratio")
    widget(c.WT_TEXT_NOTE,"Estado",865,432,295,255,
           text="Escolha um preset, confirme ajustes com Enter e clique Executar.")
    alvo=HERE/"painel.cus"
    panel.save_panel_as(str(alvo))
    print(alvo,flush=True)
    panel.load_panel(str(alvo))
    assert panel.get_property_value(panel.get_widget_by_fqn("Caso"),"text")=="degrau"
    return alvo


if __name__=="__main__":
    gerar()
