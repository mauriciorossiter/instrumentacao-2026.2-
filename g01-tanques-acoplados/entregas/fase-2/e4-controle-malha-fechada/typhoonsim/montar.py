"""Acopla um PI nativo à planta instrumentada da E03."""
import json
from dataclasses import replace
from pathlib import Path

from configuracao import EVENTOS, HERE, KP, KI, N, QMIN, QMAX, calibracao
from gerar_modelo import gerar as gerar_e3

CANAIS = ["ref_m", "med_m", "h2_m", "h1_m", "bomba_ls", "entrada_ls", "u_ensaio"]
DT = .0001


def montar(m, caso, output):
    caso.validar()
    # O gerador E03 só aceita tau <=100 s. Após montar o mesmo bloco,
    # a propriedade física é atualizada para os casos de falha maiores.
    inst=caso.instrumento
    submodelo=Path(output).with_name("base-e3.tse")
    gerar_e3(m,"degrau",replace(inst,tau_s=min(100,inst.tau_s)),submodelo)
    if not m.load(str(submodelo)):
        raise RuntimeError("Não abriu o modelo instrumentado.")
    m.delete_item(m.get_item("Escala_corrente"))
    if inst.tau_s>100:
        from math import pi
        for j in (1,2):
            prop=m.prop(m.get_item(f"Dinamica_tomada_T{j}"),"frequency")
            m.set_property_value(prop,N/(2*pi*inst.tau_s))
    for nome in ("D_deg","D_pul"):
        m.set_property_value(m.prop(m.get_item(nome),"def_value"),0.)
    vref,dist=EVENTOS[caso.ensaio]

    def bloco(nome,tipo,x,y,**props):
        b=m.create_component("core/"+tipo,name=nome,position=(x,y))
        for k,v in dict(execution_rate=DT,**props).items():
            m.set_property_value(m.prop(b,k),v)
        return b

    def ligar(a,b,entrada="in"):
        m.create_connection(m.term(a,"out"),m.term(b,entrada))

    def constante(nome,v,x,y):
        return bloco(nome,"Constant",x,y,value=v)

    def ganho(nome,k,origem,x,y):
        b=bloco(nome,"Gain",x,y,gain=k)
        ligar(origem,b)
        return b

    def soma(nome,sinais,origens,x,y):
        b=bloco(nome,"Sum",x,y,signs=sinais)
        for i,o in enumerate(origens):
            ligar(o,b,"in" if i==0 else f"in{i}")
        return b

    def produto(nome,a,b,x,y):
        z=bloco(nome,"Product",x,y,signs="**")
        ligar(a,z)
        ligar(b,z,"in1")
        return z

    def probe(nome,origem,x,y):
        z=bloco(nome,"Probe",x,y,override_signal_name=True,signal_name=nome)
        ligar(origem,z)

    ativo=m.get_item("u_ensaio_calc")
    pre=m.get_item("precarga")
    real=m.get_item("Converte_volts_para_m_T2")
    y=10620
    if caso.perfil=="ideal":
        med=m.get_item("Ideal_unitario_T2")
    elif caso.perfil=="calibrado":
        a,b=calibracao(inst)
        med=soma("Correcao_afim","++",[ganho("Fator_calibrado",a,real,8850,y+310),
                        constante("Zero_calibrado",b,8850,y+420)],9070,y+310)
    else:
        med=real
    base=constante("Ponto_nominal",1,7250,y-160)
    delta=ganho("Amplitude_referencia",vref-1,ativo,7250,y)
    ref=soma("Referencia_m","++",[base,delta],7490,y)
    erro=soma("Erro_PI","+-",[ref,med],7740,y)
    habil=produto("Erro_com_disparo",erro,ativo,7970,y)
    prop=ganho("Kp_025",KP,habil,8200,y)
    inte=bloco("Estado_integral","Integrator",8720,y+150,
               show_reset="level",reset_type="synchronous",init_value="0")
    ligar(pre,inte,"reset")
    livre=soma("PI_mais_vazao_nominal","+++",[base,prop,inte],9020,y)
    limite=bloco("Limites_bomba","Limit",9250,y,lower_limit=QMIN,upper_limit=QMAX)
    ligar(livre,limite)
    # Antiwindup por rastreamento ativo somente quando o limitador opera.
    e_lim=soma("Retorno_antiwindup","+-",[limite,livre],9440,y+260)
    aw=ganho("Rastreio_saturacao",N*.04,e_lim,9240,y+300)
    ki=ganho("Ki_00025",N*KI,habil,8170,y+150)
    soma_i=soma("Derivada_estado_integral","++",[ki,aw],8460,y+150)
    ligar(soma_i,inte)
    passo=ganho("Disturbio_entrada",dist,ativo,9470,y+130)
    total=soma("Vazao_inclui_disturbio","++",[limite,passo],9630,y)
    i=ganho("Corrente_de_comando_A",.010,total,9890,y)
    ligar(i,m.get_item("I_in"))
    probe("ref_m",ref,7500,y-305)
    probe("med_m",med,9620,y+440)
    probe("bomba_ls",ganho("Bomba_em_L_s",10,limite,9520,y-200),9700,y-200)
    probe("entrada_ls",ganho("Entrada_em_L_s",10,total,9830,y+190),10010,y+190)
    scope=m.get_item("Captura")
    m.set_property_value(m.prop(scope,"selected_signals"),CANAIS)
    colors=["#59616b","#bf581b","#123c53","#067686","#3d729a","#8a7532","#555555"]
    signals={}
    for k,(n,c) in enumerate(zip(CANAIS,colors)):
        panel=1 if k<3 else 2 if k==3 else 3 if k<6 else 4
        signals[n]={"viewports":[panel],"type":"analog","color":{str(panel):c},
                    "display":{str(panel):"solid"}}
    m.set_property_value(m.prop(scope,"signals_data"),json.dumps(
        {"signals":signals,"viewports":{str(i):dict(log_scale_x=False,log_scale_y=False,y_axis_db=False)
                         for i in range(1,5)},"plot_settings":dict(layout="Vertical",
                         background_color="white",legend_visible=True)}))
    m.set_model_property_value("simulation_time",25.25)
    output=Path(output).resolve()
    if not m.save_as(str(output)):
        raise RuntimeError("TyphoonSim não salvou o circuito.")
    return output
