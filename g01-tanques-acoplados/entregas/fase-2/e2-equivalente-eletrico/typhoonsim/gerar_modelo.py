"""Gera o equivalente dos tanques com componentes nativos do Typhoon 2026.3.

Executar com python gerar_modelo.py [--compilar].
Requer a API oficial typhoon-hil-api da mesma versao da instalacao.
"""
import argparse
import json
import math
from pathlib import Path

TS = 100e-6
DT = 1e-6
KV, KI, N = 10., 1., 100.
C = .5 * KI / (KV * N)
G = .01 * KI / math.sqrt(KV)
ROOT = Path(__file__).resolve().parent

INPUTS = {
    "precarga": (1., 0., 1., "0/1"),
    "Vref1": (10., 0., 12., "V"),
    "Vref2": (10., 0., 12., "V"),
    "Q_rel": (1., .1, 2., "pu"),
    "D_deg": (5., -30., 9., "%"),
    "D_pul": (0., 0., 20., "%"),
    "G1_rel": (1., .25, 4., "pu"),
    "G2_rel": (1., .25, 4., "pu"),
}


def gerar(compilar=False):
    from typhoon.api.schematic_editor import SchematicAPI, const
    m = SchematicAPI()
    m.create_new_model(name="g01_tanques_equivalente")
    for key, value in {"hil_device": "HIL404", "hil_configuration_id": 1,
                       "simulation_time_step": DT, "simulation_method": "exact",
                       "enb_pole_shift": False, "simulation_time": 20.5,
                       "max_sim_step": DT, "data_sampling_rate": .001,
                       "abs_tol": 1e-9, "rel_tol": 1e-7}.items():
        m.set_model_property_value(key, value)
    comps, inventory = {}, []

    def add(name, typ, xy, props=None, rotation=None):
        options = dict(name=name, position=xy)
        if rotation is not None:
            options["rotation"] = rotation
        c = m.create_component("core/" + typ, **options)
        comps[name] = c
        for key, value in (props or {}).items():
            m.set_property_value(m.prop(c, key), value)
        inventory.append({"nome": name, "biblioteca": "core/"+typ,
                          "propriedades": props or {}})
        return c

    def wire(a, b, pa="out", pb="in"):
        return m.create_connection(m.term(comps[a], pa), m.term(comps[b], pb))

    def connect(a, b):
        def resolve(x):
            if isinstance(x, tuple):
                return m.term(comps[x[0]], x[1])
            return nodes[x]
        return m.create_connection(resolve(a), resolve(b))

    # Fontes: corrente positiva de n_node para p_node.
    for name, xy, rot in [("I_in",(7540,8120),"right"),
                           ("Orificio_12",(8460,7920),"down"),
                           ("Orificio_2",(9300,8120),"left"),
                           ("I_pre1",(8200,8120),"right"),
                           ("I_pre2",(9040,8120),"right")]:
        add(name,"Signal Controlled Current Source",xy,{"execution_rate":TS},rot)
    add("C1","Capacitor",(7920,8120),{"capacitance":C,"initial_voltage":0.,"pole_shift_ignore":True},"right")
    add("C2","Capacitor",(8740,8120),{"capacitance":C,"initial_voltage":0.,"pole_shift_ignore":True},"right")
    for name,typ,xy,rot in [("V1","Voltage Measurement",(8060,8120),"right"),
                             ("V2","Voltage Measurement",(8890,8120),"right"),
                             ("Q_in","Current Measurement",(7720,7920),"up"),
                             ("Q_12","Current Measurement",(8580,7920),"up"),
                             ("Q_out","Current Measurement",(9300,8290),"right")]:
        add(name,typ,xy,{"sig_output":True,"execution_rate":TS,
                         "override_signal_name":True,"signal_name":name},rot)
    add("Terra","Ground",(8400,8410))
    nodes = {name:m.create_junction(name=name,kind=const.KIND_PE,position=xy)
             for name,xy in {"N1":(7920,7920),"N1_V":(8060,7920),
                            "N1_pre":(8200,7920),"N2":(8740,7920),
                            "N2_V":(8890,7920),"N2_pre":(9040,7920),
                            "G0":(7540,8370),"G1":(7920,8370),
                            "G1_V":(8060,8370),"G1_pre":(8200,8370),
                            "G_mid":(8400,8370),"G2":(8740,8370),
                            "G2_V":(8890,8370),"G2_pre":(9040,8370),
                            "Gout":(9300,8370)}.items()}
    for a,b in [(('I_in','p_node'),('Q_in','p_node')),(('Q_in','n_node'),'N1'),
                ('N1','N1_V'),('N1_V','N1_pre'),('N1_pre',('Orificio_12','n_node')),
                (('Orificio_12','p_node'),('Q_12','p_node')),(('Q_12','n_node'),'N2'),
                ('N2','N2_V'),('N2_V','N2_pre'),('N2_pre',('Orificio_2','n_node')),
                (('Orificio_2','p_node'),('Q_out','p_node')),(('Q_out','n_node'),'Gout'),
                (('I_in','n_node'),'G0'),('N1',('C1','p_node')),
                (('C1','n_node'),'G1'),('N1_V',('V1','p_node')),
                (('V1','n_node'),'G1_V'),('N1_pre',('I_pre1','p_node')),
                (('I_pre1','n_node'),'G1_pre'),('N2',('C2','p_node')),
                (('C2','n_node'),'G2'),('N2_V',('V2','p_node')),
                (('V2','n_node'),'G2_V'),('N2_pre',('I_pre2','p_node')),
                (('I_pre2','n_node'),'G2_pre'),('G_mid',('Terra','node'))]:
        connect(a,b)
    grounds=['G0','G1','G1_V','G1_pre','G_mid','G2','G2_V','G2_pre','Gout']
    for a,b in zip(grounds,grounds[1:]): connect(a,b)

    for j,(name,(default,lo,hi,unit)) in enumerate(INPUTS.items()):
        add(name,"SCADA Input",(7040,8600+j*140),
            {"def_value":default,"min":lo,"max":hi,"unit":unit,
             "signal_type":"real","execution_rate":TS})
    def sp(name,typ,xy,props=None):
        return add(name,typ,xy,{"execution_rate":TS,**(props or {})})
    sp("Um","Constant",(7260,8520),{"value":1.})
    sp("u_ensaio_calc","Sum",(7480,8600),{"signs":"+-"})
    wire("Um","u_ensaio_calc"); wire("precarga","u_ensaio_calc",pb="in1")
    sp("Tempo_ensaio","Integrator",(7700,8600),
       {"show_reset":"level","reset_type":"synchronous","init_value":"0"})
    wire("u_ensaio_calc","Tempo_ensaio"); wire("precarga","Tempo_ensaio",pb="reset")
    sp("Duracao_pulso","Constant",(7700,8760),{"value":.3})
    sp("Janela_pulso","Relational operator",(7940,8660),{"relational_op":"<"})
    wire("Tempo_ensaio","Janela_pulso"); wire("Duracao_pulso","Janela_pulso",pb="in1")
    sp("Pulso_ativo","Product",(8160,8660),{"signs":"**"})
    wire("u_ensaio_calc","Pulso_ativo"); wire("Janela_pulso","Pulso_ativo",pb="in1")
    for inp,base,y,gate in [("D_deg","Degrau",8920,"u_ensaio_calc"),
                            ("D_pul","Pulso",9080,"Pulso_ativo")]:
        sp(base+"_fracao","Gain",(7460,y),{"gain":.01}); wire(inp,base+"_fracao")
        sp(base+"_aplicado","Product",(7920,y),{"signs":"**"})
        wire(base+"_fracao",base+"_aplicado"); wire(gate,base+"_aplicado",pb="in1")
    sp("Soma_comando","Sum",(8240,8960),{"signs":"+++"})
    wire("Um","Soma_comando"); wire("Degrau_aplicado","Soma_comando",pb="in1")
    wire("Pulso_aplicado","Soma_comando",pb="in2")
    sp("Vazao_operacao","Product",(8460,8960),{"signs":"**"})
    wire("Soma_comando","Vazao_operacao"); wire("Q_rel","Vazao_operacao",pb="in1")
    sp("Escala_corrente","Gain",(8660,8960),{"gain":.010})
    wire("Vazao_operacao","Escala_corrente"); wire("Escala_corrente","I_in")

    for j in (1,2):
        x=7540+(j-1)*1000; y=9400
        sp("Vpositivo"+str(j),"Limit",(x,y),{"lower_limit":0.,"upper_limit":1e6})
        wire("V"+str(j),"Vpositivo"+str(j))
        sp("Raiz"+str(j),"Mathematical function",(x+180,y),{"mathematical_fn":"sqrt"})
        wire("Vpositivo"+str(j),"Raiz"+str(j))
        sp("Gnom"+str(j),"Gain",(x+360,y),{"gain":G}); wire("Raiz"+str(j),"Gnom"+str(j))
        sp("Coef_orificio"+str(j),"Product",(x+540,y),{"signs":"**"})
        wire("Gnom"+str(j),"Coef_orificio"+str(j)); wire("G"+str(j)+"_rel","Coef_orificio"+str(j),pb="in1")
        wire("Coef_orificio"+str(j),"Orificio_12" if j==1 else "Orificio_2")
        sp("Erro_pre"+str(j),"Sum",(x,9700),{"signs":"+-"})
        wire("Vref"+str(j),"Erro_pre"+str(j)); wire("V"+str(j),"Erro_pre"+str(j),pb="in1")
        sp("Ganho_pre"+str(j),"Gain",(x+180,9700),{"gain":2.}); wire("Erro_pre"+str(j),"Ganho_pre"+str(j))
        sp("Limite_pre"+str(j),"Limit",(x+360,9700),{"lower_limit":-.1,"upper_limit":.1})
        wire("Ganho_pre"+str(j),"Limite_pre"+str(j))
        sp("Ativa_pre"+str(j),"Product",(x+540,9700),{"signs":"**"})
        wire("Limite_pre"+str(j),"Ativa_pre"+str(j)); wire("precarga","Ativa_pre"+str(j),pb="in1")
        wire("Ativa_pre"+str(j),"I_pre"+str(j))
        sp("Escala_h"+str(j),"Gain",(x,9960),{"gain":.1}); wire("V"+str(j),"Escala_h"+str(j))
        sp("h"+str(j)+"_m","Probe",(x+180,9960),{"override_signal_name":True,"signal_name":"h"+str(j)+"_m"})
        wire("Escala_h"+str(j),"h"+str(j)+"_m")
    sp("u_ensaio","Probe",(8160,8520),{"override_signal_name":True,"signal_name":"u_ensaio"})
    wire("u_ensaio_calc","u_ensaio")
    path=ROOT/"modelo.tse"
    if not m.save_as(str(path)):
        raise RuntimeError("O Typhoon nao salvou o modelo.")
    (ROOT/"inventario.json").write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Modelo salvo: {path}; {len(inventory)} componentes nativos.",flush=True)
    if compilar:
        ok=m.compile()
        print("COMPILACAO:",ok,flush=True)
        if not ok:
            raise RuntimeError("Compilacao recusada pelo Typhoon; conferir console e licenca.")
    return path


if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--compilar",action="store_true")
    gerar(ap.parse_args().compilar)
