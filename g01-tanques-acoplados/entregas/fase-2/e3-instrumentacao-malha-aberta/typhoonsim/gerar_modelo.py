"""Estende o equivalente da E02 com dois canais nativos de medição."""
import json, math
from pathlib import Path
from parametros import N, PLANTA, P_FS, RHO_G, SLOPE, VS

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "e2-equivalente-eletrico/typhoonsim/modelo-offline.tse"
CANAIS = ["V1", "V2", "u_ensaio", "ideal_h1", "ideal_h2", "real_h1", "real_h2", "h1_m", "h2_m"]
DT = .0001


def gerar(m, ensaio, inst, output):
    inst.validar()
    if not m.load(str(BASE)):
        raise RuntimeError(f"Falha ao abrir a planta da E02: {BASE}")
    d, p, v1, v2 = PLANTA[ensaio]
    for nome, val in dict(D_deg=d, D_pul=p, Vref1=v1, Vref2=v2).items():
        m.set_property_value(m.prop(m.get_item(nome), "def_value"), val)

    def bloco(nome, tipo, x, y, **props):
        b = m.create_component("core/" + tipo, name=nome, position=(x,y))
        for chave, val in props.items():
            m.set_property_value(m.prop(b,chave), val)
        return b

    def liga(a,b,entrada="in",saida="out"):
        m.create_connection(m.term(a,saida),m.term(b,entrada))

    ciclo = bloco("Fase_interferente","Gain",10400,8600,
                  gain=2*math.pi*.8*N,execution_rate=DT)
    liga(m.get_item("Tempo_ensaio"),ciclo)
    seno = bloco("Interferente_0p8Hz","Trigonometric function",10600,8600,
                 trigonometric_fn="sin",execution_rate=DT)
    liga(ciclo,seno)

    for j, v0 in enumerate((v1,v2),1):
        y = 9000+(j-1)*650
        x = 10400
        def node(nome, tipo, dy=0, **kw):
            nonlocal x
            x += 180
            return bloco(f"{nome}_T{j}",tipo,x,y+dy,execution_rate=DT,**kw)
        def ganho(prev,nome,k,dy=0):
            b = node(nome,"Gain",dy,gain=k)
            liga(prev,b)
            return b
        def soma(prev,nome,segundo,sinais="++"):
            b=node(nome,"Sum",signs=sinais)
            liga(prev,b,"in")
            liga(segundo,b,"in1")
            return b
        def cte(nome,v,dy=155):
            return node(nome,"Constant",dy,value=v)
        def passa(prev,nome,f_hz,init):
            b=node(nome,"Low-Pass Filter",frequency=f_hz*N,init_out=init)
            liga(prev,b)
            return b

        def probe(prev,nome,dy):
            nonlocal x
            x += 180
            b=bloco(f"{nome}{j}","Probe",x,y+dy,execution_rate=DT,override_signal_name=True,signal_name=f"{nome}{j}")
            liga(prev,b)

        h = m.get_item(f"Escala_h{j}")
        if h is None:
            # Mede a tensão do mesmo nó, sem alterar sua carga.
            h=node("Nivel_da_planta","Gain",gain=.1)
            liga(m.get_item(f"V{j}"),h)
        probe(ganho(h,"Ideal_unitario",1,-170),"ideal_h",-170)
        pressao=ganho(h,"Pressao_Pa",RHO_G)
        h0=v0/10
        if inst.tau_s:
            # A tomada começa estabilizada; a pré-carga artificial não é um ensaio hidráulico.
            base_pressao = ganho(m.get_item("precarga"),"Pressao_na_precarga",h0*RHO_G,195)
            ativa=node("Pressao_durante_ensaio","Product",signs="**")
            liga(pressao,ativa)
            liga(m.get_item("u_ensaio_calc"),ativa,"in1")
            pressao=soma(ativa,"Pressao_com_inicio_estavel",base_pressao)
            pressao=passa(pressao,"Dinamica_tomada",1/(2*math.pi*inst.tau_s),h0*RHO_G)
        # Função de transferência ratiométrica em volts da saída condicionada.
        k_gain=1+inst.ganho_pct/100
        variavel=ganho(pressao,"Sensibilidade_HSC",.8*VS/P_FS)
        dist=ganho(variavel,"Erro_de_ganho",k_gain)
        if inst.curvatura_mm:
            # Erro residual de forma: 4·r·(1-r) × amplitude, r = p/P_FS.
            fr=ganho(pressao,"Fracao_de_escala",1/P_FS,235)
            inv=soma(cte("Um",1,325),"Complemento",fr,"+-")
            b=node("Curvatura_normalizada","Product",235,signs="**")
            liga(fr,b,"in")
            liga(inv,b,"in1")
            nl=ganho(b,"Amplitude_curvatura",4*SLOPE*inst.curvatura_mm/1000,235)
            dist=soma(dist,"Adiciona_curvatura",nl)
        v=soma(dist,"Saida_nominal",cte("Zero_ratiometrico",.1*VS))
        v=soma(v,"Erro_de_zero",cte("Deslocamento_zero",SLOPE*inst.zero_mm/1000))
        noise=ganho(seno,"Amplitude_interferente",SLOPE*inst.ruido_mm/1000,-220)
        v=soma(v,"Captacao_na_interface",noise)
        frac=h0*RHO_G/P_FS
        init=.1*VS+SLOPE*(h0*k_gain+inst.zero_mm/1000+
                                    4*frac*(1-frac)*inst.curvatura_mm/1000)
        if inst.fc_hz:
            v=passa(v,"Condicionamento_RC",inst.fc_hz,init)
        if inst.adc_bits:
            adc=node("Faixa_ADC","Limit",upper_limit=VS*(1-2**(-int(inst.adc_bits))),lower_limit=0)
            liga(v,adc)
            lsb=VS/2**int(inst.adc_bits)
            cod=ganho(adc,"Escala_ADC",1/lsb)
            arred=node("Quantizacao_ADC","Round",round_fn="round")
            liga(cod,arred)
            v=ganho(arred,"Reconstrucao_ADC",lsb)
        v=soma(v,"Retira_zero_e_corrige",
               cte("Zero_e_correcao",.1*VS+SLOPE*inst.correcao_mm/1000),"+-")
        hmed=ganho(v,"Converte_volts_para_m",1/SLOPE)
        probe(hmed,"real_h",0)

    scope=m.get_item("Captura")
    m.set_property_value(m.prop(scope,"selected_signals"),CANAIS)
    signals={}
    for k,n in enumerate(CANAIS):
        page=3 if n=="u_ensaio" else (1 if ("1" in n) else 2)
        color=["#233C55","#233C55","#505050","#008394","#008394","#C77221","#C77221","#233C55","#233C55"][k]
        signals[n]={"viewports":[page],"type":"analog",
                    "color":{str(page):color},"display":{str(page):"solid"}}
    m.set_property_value(m.prop(scope,"signals_data"),json.dumps(
        {"signals":signals,"viewports":{str(i):dict(log_scale_x=False,log_scale_y=False,y_axis_db=False)
                                         for i in range(1,5)},
         "plot_settings":dict(layout="Vertical",background_color="white",legend_visible=True)}))
    output=Path(output).resolve()
    output.parent.mkdir(parents=True,exist_ok=True)
    if not m.save_as(str(output)):
        raise RuntimeError("Modelo E03 não pôde ser salvo.")
    return output
