# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, E03 e E04: confere a FIACAO do modelo do TyphoonSim contra o gabarito Python,
sem o TyphoonSim.

Uma API falsa (so' as funcoes que typhoonsim/monta_modelo.py usa) grava os blocos, as propriedades e as
ligacoes que o script cria. Depois o diagrama gravado e' executado bloco a bloco, com a semantica documentada
de cada bloco nativo (Sum, Gain, Product, Unit Delay, Signal switch, Round, Hysteresis Function, Discrete
Transfer Function, Rate Transition...), e o estagio de potencia da E02 e' resolvido com os valores de R, L e C
lidos do proprio diagrama. Se a fiacao estiver certa, as sondas coincidem com sistema.simula().

O que isto NAO confere: a implementacao interna de cada bloco no TyphoonSim (isso so' a corrida no Windows,
com compara_typhoon.py). O Random Source recebe aqui a mesma sequencia do gabarito.
Uso:  python confere_fiacao.py      (~1 min)
"""
import json
import math
import os
import sys
import types

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, '..'))
sys.dont_write_bytecode = True


# ============================================================ API falsa
class Comp:
    def __init__(self, tipo, nome):
        self.tipo, self.nome, self.props = tipo, nome, {}


class FakeModel(types.ModuleType):
    def __init__(self):
        super().__init__('model')
        self.comps, self.ligacoes = {}, []

    def create_new_model(self, nome=None):
        self.comps, self.ligacoes = {}, []

    def create_component(self, tipo, name=None, **kw):
        c = Comp(tipo, name)
        self.comps[name] = c
        return c

    def prop(self, c, k):
        return (c, k)

    def set_property_value(self, p, v):
        p[0].props[p[1]] = v

    def get_property_value(self, p):
        return p[0].props.get(p[1])

    def term(self, c, nome):
        return (c.nome, nome)

    def create_connection(self, a, b):
        self.ligacoes.append((a, b))

    def get_item(self, nome):
        return self.comps[nome]

    def set_position(self, *a, **k):
        pass

    set_rotation = set_model_property_value = set_position

    def save_as(self, *a):
        pass

    def compile(self):
        return True

    def close_model(self):
        pass


FAKE = FakeModel()
pkg = types.ModuleType('typhoon'); api = types.ModuleType('typhoon.api'); se = types.ModuleType('typhoon.api.schematic_editor')
se.model = FAKE
sys.modules.update({'typhoon': pkg, 'typhoon.api': api, 'typhoon.api.schematic_editor': se})
import monta_modelo as MM   # noqa: E402
import parametros_e34 as P  # noqa: E402
import sistema as S         # noqa: E402
import circuito as C2       # noqa: E402
from ensaios_e34 import ENSAIOS  # noqa: E402

CIRCUITO = {'core/Voltage Source', 'core/Current Measurement', 'core/Inductor', 'core/Resistor', 'core/Capacitor',
            'core/Signal Controlled Voltage Source', 'core/Voltage Measurement', 'core/Ground'}


def num(v):
    if isinstance(v, (int, float)):
        return float(v)
    return float(eval(str(v), {'inf': math.inf}))


# ============================================================ execucao do diagrama gravado
def executa(T, ruido):
    comps, lig = FAKE.comps, FAKE.ligacoes
    # cada terminal de entrada aponta para o terminal de saida que o alimenta
    fonte = {}
    for a, b in lig:
        ca, cb = comps[a[0]], comps[b[0]]
        a_saida = a[1] == 'out' and ca.tipo not in CIRCUITO or (ca.tipo in ('core/Voltage Measurement', 'core/Current Measurement') and a[1] == 'out')
        b_saida = b[1] == 'out' and cb.tipo not in CIRCUITO or (cb.tipo in ('core/Voltage Measurement', 'core/Current Measurement') and b[1] == 'out')
        if a_saida and not b_saida:
            fonte[b] = a
        elif b_saida and not a_saida:
            fonte[a] = b
    sinal = [c for c in comps.values() if c.tipo not in CIRCUITO and c.tipo not in ('core/Probe', 'core/Scope')]
    taxa = {c.nome: num(c.props.get('execution_rate', P.TS_M)) for c in sinal}
    estado_saida = {'core/Unit Delay'}
    # ordem topologica (atrasos sao fontes)
    dep = {}
    for c in sinal:
        ent = [t for (n, t) in fonte if n == c.nome]
        dep[c.nome] = [] if c.tipo in estado_saida else [fonte[(c.nome, t)][0] for t in ent if comps[fonte[(c.nome, t)][0]].tipo not in CIRCUITO]
    ordem, visto = [], set()

    def visita(n, pilha=()):
        if n in visto:
            return
        if n in pilha:
            raise RuntimeError('laco algebrico em ' + n)
        for d in dep[n]:
            visita(d, pilha + (n,))
        visto.add(n); ordem.append(n)
    for c in sinal:
        visita(c.nome)
    # circuito
    R = num(comps['R_amortec'].props['resistance']); L = num(comps['L_inercia'].props['inductance'])
    Cc = num(comps['C_sincron'].props['capacitance'])
    Phi, Gam = C2.discretiza(R, L, Cc, P.TS_SP)
    iL, vC = 0.0, num(comps['C_sincron'].props['initial_voltage'])
    val = {}
    st = {c.nome: num(c.props.get('init_value', 0)) for c in sinal if c.tipo == 'core/Unit Delay'}
    hst = {c.nome: (num(c.props['high_out']) if c.props.get('init_state') == 'high' else num(c.props['low_out']))
           for c in sinal if c.tipo == 'core/Hysteresis Function'}
    dtf = {c.nome: [0.0, 0.0] for c in sinal if c.tipo == 'core/Discrete Transfer Function'}
    rt = {c.nome: num(c.props.get('init_value', 0)) for c in sinal if c.tipo == 'core/Rate Transition'}
    sondas = {c.nome: [] for c in comps.values() if c.tipo == 'core/Probe'}
    ts_sondas = []
    n20 = int(round(T/P.TS_SP)); passo = int(round(P.TS_M/P.TS_SP))
    k100 = 0

    def ent(nome, t='in'):
        f = fonte[(nome, t)]
        if f[0] == 'V_vC':
            return vC
        if f[0] == 'I_dw':
            return iL
        return val[f[0]]
    for k in range(n20 + 1):
        t = k*P.TS_SP
        lento = (k % passo == 0)
        for n in ordem:
            c = comps[n]; p = c.props; tp = c.tipo
            if taxa[n] > P.TS_SP*1.5 and not lento:
                continue
            if tp == 'core/Constant':
                y = num(p['value'])
            elif tp == 'core/SCADA Input':
                y = num(p['def_value'])
            elif tp == 'core/Gain':
                y = num(p['gain'])*ent(n)
            elif tp == 'core/Sum':
                sg = p['signs']; y = 0.0
                for j, s in enumerate(sg):
                    x = ent(n, 'in' if j == 0 else 'in%d' % j)
                    y += x if s == '+' else -x
            elif tp == 'core/Product':
                sg = p.get('signs', '**'); y = 1.0
                for j, s in enumerate(sg):
                    x = ent(n, 'in' if j == 0 else 'in%d' % j)
                    y = y*x if s == '*' else y/x
            elif tp == 'core/Unit Delay':
                y = st[n]
            elif tp == 'core/Min Max':
                a, b = ent(n, 'in'), ent(n, 'in1')
                y = min(a, b) if p['operation'] == 'min' else max(a, b)
            elif tp == 'core/Signal switch':
                # terminais conferidos no codigo C da 2026.2: in = entrada 1, in1 = entrada 2, in2 = controle
                ctrl = ent(n, 'in2'); th = num(p['threshold'])
                y = ent(n, 'in') if ctrl > th else ent(n, 'in1')
            elif tp == 'core/Round':
                x = ent(n); f = p['round_fn']
                y = math.floor(x) if f == 'floor' else (math.ceil(x) if f == 'ceil' else (float(round(x)) if f == 'round' else float(int(x))))
            elif tp == 'core/Mathematical function':
                x = ent(n); f = p['mathematical_fn']
                y = math.sqrt(x) if f == 'sqrt' else math.exp(x)
            elif tp == 'core/Trigonometric function':
                f = p['trigonometric_fn']
                y = math.atan2(ent(n, 'in'), ent(n, 'in1')) if f == 'atan2' else getattr(math, f)(ent(n))   # 2026.2: atan2(in, in1)
            elif tp == 'core/Limit':
                y = min(max(ent(n), num(p['lower_limit'])), num(p['upper_limit']))
            elif tp == 'core/Step':
                y = num(p['final_value']) if t >= num(p['step_time']) - 1e-12 else num(p['initial_value'])
            elif tp == 'core/Clock':
                # o Clock soma o passo e reinicia quando passa de reset_at: periodo = passos inteiros acima de reset_at
                per = math.ceil(num(p['reset_at'])/P.TS_M - 1e-6)*P.TS_M
                y = t - math.floor(t/per + 1e-9)*per
            elif tp == 'core/Random Source':
                y = ruido[k100] if ruido is not None else 0.0
            elif tp == 'core/Hysteresis Function':
                x = ent(n)
                if x > num(p['up_thr']):
                    hst[n] = num(p['high_out'])
                elif x < num(p['low_thr']):
                    hst[n] = num(p['low_out'])
                y = hst[n]
            elif tp == 'core/Discrete Transfer Function':
                b = eval(p['b_coeff']); a = eval(p['a_coeff'])
                x = ent(n); x1, y1 = dtf[n]
                y = (b[0]*x + b[1]*x1 - a[1]*y1)/a[0]
                dtf[n] = [x, y]
            elif tp == 'core/Rate Transition':
                y = ent(n)
            else:
                raise RuntimeError('bloco sem semantica: ' + tp)
            val[n] = y
        if lento:
            for nome in sondas:
                f = fonte[(nome, 'in')]
                sondas[nome].append(vC if f[0] == 'V_vC' else val[f[0]])
            ts_sondas.append(t)
            for n in st:
                st[n] = ent(n)
            k100 += 1
        # circuito: V_m - v_nl aplicado ao R-L-C por 20 us
        u = ent('V_m', 'in') - ent('v_nl', 'in')
        iL, vC = (Phi[0, 0]*iL + Phi[0, 1]*vC + Gam[0]*u, Phi[1, 0]*iL + Phi[1, 1]*vC + Gam[1]*u)
    return np.array(ts_sondas), {k: np.array(v) for k, v in sondas.items()}


def confere(nome, T=1.6):
    ens, cfg = ENSAIOS[nome]
    ens = dict(ens, T=T)
    MM.monta(tempo=T, ens=ens, cfg=cfg)
    MM.aplica_eventos(ens)
    n = int(round(T/P.TS_M))
    rng = np.random.default_rng(cfg['semente'])
    ruido = (rng.standard_normal(n + 1)).tolist() if cfg['sigma'] > 0 else None
    t, sd = executa(T, ruido)
    g = S.simula(ens, dict(cfg, decim=1))
    m = min(len(t), len(g['t']))
    pares = (('V_ideal', g['V_id']), ('V_real', g['V_re']), ('f_ideal', g['f_id']), ('f_real', g['f_re']),
             ('Efd', g['Efd']), ('delta_graus', np.degrees(g['delta'])), ('upss', g['upss']))
    out = {}
    for sonda, ref in pares:
        d = sd[sonda][:m] - ref[:m]
        out[sonda] = float(np.max(np.abs(d)))
    return out


if __name__ == '__main__':
    res = {}
    for nome in ('e03_c', 'e04_real_r', 'e04_R5_p'):
        res[nome] = confere(nome)
        print('%-12s ' % nome + '  '.join('%s %.1e' % (k, v) for k, v in res[nome].items()), flush=True)
    with open(os.path.join(AQUI, 'confere_fiacao.json'), 'w', encoding='utf-8') as fh:
        json.dump(res, fh, indent=1)
