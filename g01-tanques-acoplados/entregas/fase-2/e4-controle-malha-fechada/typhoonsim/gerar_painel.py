"""Gera o painel Standalone para trocar o perfil de medição entre rodadas."""
import ast
from dataclasses import asdict
from configuracao import CASOS,HERE,NOMINAL

RUN='''from pathlib import Path
from dataclasses import replace
import importlib.util
import sys
import tempfile

def w(nome):
    return panel.get_widget_by_fqn(nome)

pasta=Path(panel.get_property_value(w("Pasta"),"widget_value"))
try:
    local=Path(get_settings_dir_path())
    if (local/"rodar.py").is_file():
        pasta=local
except (NameError,TypeError):
    pass
if not (pasta/"rodar.py").is_file():
    raise RuntimeError("Preencha Pasta dos scripts com o diretório typhoonsim da E04 e confirme com Enter.")
sys.path.insert(0,str(pasta.resolve()))
from configuracao import CASOS
from rodar import executar
preset=panel.get_property_value(w("Caso"),"text")
base=CASOS[preset]
ajustes={k:float(panel.get_property_value(w(k),"widget_value"))
         for k in ("zero_mm","tau_s","ruido_mm")}
caso=replace(base,instrumento=replace(base.instrumento,**ajustes))
try:
    panel.set_property_value(w("Estado"),"text","Simulando "+preset+"...")
    diretorio=Path(tempfile.mkdtemp(prefix="g01-e4-scada-"))
    r=executar(preset,caso,destino=diretorio)
    spec=importlib.util.spec_from_file_location("graficos_e4",pasta.parent/"simulacao/graficos.py")
    graficos=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(graficos)
    png=diretorio/"ensaio.png"
    graficos.figura_ensaio(diretorio/(preset+".csv"),png,preset)
    panel.set_property_value(w("Grafico"),"image",str(png))
    ts=r["planta"]["acomodacao_s"]
    ts_texto="Não acomodou" if ts is None else f"{ts:.1f} s"
    texto=(f"Captura: {preset}\\nErro da leitura: {r['medida']['erro_mm']:+.2f} mm\\n"
           f"Erro da planta: {r['planta']['erro_mm']:+.2f} mm\\n"
           f"Acomodação da planta: {ts_texto}\\nEsforço: {r['esforco_ls']:.3f} L/s\\n"
           f"Dados: {diretorio}")
    panel.set_property_value(w("Estado"),"text",texto)
except Exception as exc:
    panel.set_property_value(w("Estado"),"text","Falha: "+str(exc))
    raise
'''


def gerar():
    from typhoon.api.scada import panel,const as c
    panel.create_new_panel()
    def widget(typ,n,x,y,w,h,**settings):
        item=panel.create_widget(typ,name=n,position=[x,y])
        if "label" in settings:
            settings={"use_label":True,**settings}
        for key,val in {"size":[w,h],**settings}.items():
            panel.set_property_value(item,key,val)
        return item

    widget(c.WT_TEXT_NOTE,"Titulo",20,10,1130,43,text="G01 | Controle de nível em malha fechada")
    widget(c.WT_TEXT_MACRO,"Pasta",20,61,700,45,label="Pasta dos scripts",
           input_width=480,value_type="string",widget_value="",on_use_code="pass")
    campos={"zero_mm":"Desvio de zero (mm)","tau_s":"Constante de tempo (s)",
            "ruido_mm":"Interferência de pico (mm)"}
    for j,(k,v) in enumerate(campos.items()):
        widget(c.WT_TEXT_MACRO,k,20+j*315,119,298,45,label=v,input_width=85,
               value_type="float",widget_value=getattr(NOMINAL,k),on_use_code="pass")
    presets=[*list(CASOS)[:9],"zero-mm-6","tau-s-60","ruido-mm-40",
             "d-zero-mm-6","d-tau-s-60","d-ruido-mm-40"]
    for i,preset in enumerate(presets):
        inst=asdict(CASOS[preset].instrumento)
        comandos=[f'panel.set_property_value(panel.get_widget_by_fqn("Caso"),"text",{preset!r})']
        comandos.extend(f'panel.set_property_value(panel.get_widget_by_fqn({k!r}),"widget_value",{inst[k]!r})'
                        for k in campos)
        comandos.append('panel.set_property_value(panel.get_widget_by_fqn("Estado"),"text","Preset selecionado. Clique Executar.")')
        codigo="\n".join(comandos)
        ast.parse(codigo)
        widget(c.WT_BUTTON_MACRO,f"Preset_{i}",20+i%4*280,177+i//4*38,266,33,
               label=preset,on_use_code=codigo)
    widget(c.WT_TEXT_NOTE,"Caso",20,346,225,40,text="subida-real")
    ast.parse(RUN)
    widget(c.WT_BUTTON_MACRO,"Executar",265,341,260,42,label="Executar no TyphoonSim",on_use_code=RUN)
    widget(c.WT_TEXT_NOTE,"Modo",555,347,580,45,
           text="Confirme valores com Enter. Ajustes valem na próxima rodada offline.")
    widget(c.WT_IMAGE,"Grafico",20,404,798,478,image_scaling="Keep aspect ratio")
    widget(c.WT_TEXT_NOTE,"Estado",850,404,280,285,
           text="Compare a leitura com o nível da planta. Presets calibrados aplicam a correção de dois pontos.")
    path=HERE/"painel.cus"
    panel.save_panel_as(str(path))
    panel.load_panel(str(path))
    assert panel.get_property_value(panel.get_widget_by_fqn("Caso"),"text")=="subida-real"
    return path


if __name__=="__main__":
    print(gerar(),flush=True)
