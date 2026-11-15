# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 2, Entrega 02: roda os ensaios no Virtual HIL (VHIL) e captura as sondas.

Substitui o roda_typhoon.py quando o TyphoonSim offline nao tem licenca ("appropriate license is not
available"). Usa os MESMOS ensaios e a mesma funcao aplica() do roda_typhoon.py: para cada ensaio,
ajusta o .tse (degrau temporizado, instantes da falta, D, X), compila, carrega no VHIL, roda e
captura as sondas com typhoon.test.capture.

Diferencas em relacao a rodada offline:
  - os eventos (degrau, falta) sao deslocados para depois de T_MARGEM s de simulacao, para a captura
    ja estar rodando quando eles acontecem; o CSV sai com o tempo ja realinhado (t = 0 no evento,
    coluna Time) e com a coluna t_sim (tempo de simulacao aproximado);
  - o ensaio (b) (condicao inicial no capacitor em t = 0) e' capturado a partir do Start; perde so
    as primeiras dezenas de ms (a coluna t_sim diz onde a captura comecou).

Uso (Schematic Editor aberto, SCADA fechado ou com a simulacao parada):
    <python da API> roda_vhil.py                   (todos)
    <python da API> roda_vhil.py ensaio_a_degrau   (um so)
Saida: dados/<ensaio>.csv
"""
import math
import os
import sys
import time

from typhoon.api.schematic_editor import model
import typhoon.api.hil as hil
import inspect
from typhoon.test import capture as CAP

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, 'gabarito'))
sys.dont_write_bytecode = True
import parametros_e02 as P      # noqa: E402
import monta_modelo as MM       # noqa: E402
import roda_typhoon as RT       # noqa: E402  (ENSAIOS e aplica)

DADOS = os.path.join(AQUI, 'dados')
CPD = os.path.join(AQUI, 'equivalente_eletrico Target files', 'equivalente_eletrico.cpd')
T_MARGEM = 3.0          # s de simulacao antes do evento (a captura comeca ~1 s antes dele)
DUR_SENS = {'sens_D': 15.0, 'sens_X': 25.0}   # s capturados depois do degrau (VHIL ~8x mais lento)
TAXA = 1000.0           # amostras/s na captura
SONDAS = ['delta_graus', 'delta_omega', 'Pe_pu', 'Pm_pu', 'i_A', 'vC_V', 'vnl_V', 'Vm_V']


def prepara(nome):
    """Copia do ensaio com os eventos deslocados; devolve (ensaio, t_evento, t_fim)."""
    e = dict(RT.ENSAIOS[nome])
    if nome.startswith('sens_X'):
        # parte do novo equilibrio (vC0 no capacitor) em vez de esperar 80 s o transitorio inicial
        e['vC0'] = RT.vc0(math.degrees(math.asin(P.PM0/(P.P_MAX*P.X_TOT/e['X']))))
        e['t_deg'], e['tempo'] = 1.0, 1.0 + DUR_SENS['sens_X']
    elif nome.startswith('sens_D'):
        e['tempo'] = e['t_deg'] + DUR_SENS['sens_D']
    if e['falta'] is not None:
        ti, tc = e['falta']
        e['falta'] = (T_MARGEM, tc)
        t_ev, dur = T_MARGEM, e['tempo'] - ti
    elif e['t_deg'] is not None:
        t_ev = max(e['t_deg'], T_MARGEM)
        dur = e['tempo'] - e['t_deg']
        e['t_deg'] = t_ev
    else:
        # (b) condicao inicial no capacitor em t = 0: a captura comeca logo depois do Start e perde
        # so as primeiras dezenas de ms; o Time sai no tempo de simulacao (t_ev = 0)
        t_ev, dur = 0.0, 20.0
    e['tempo'] = t_ev + dur + 2.0
    return e, t_ev, dur


def espera_sim(t_alvo, limite=900.0):
    t0 = time.time()
    while hil.get_sim_time() < t_alvo:
        if time.time() - t0 > limite:
            raise RuntimeError('a simulacao nao chegou a t = %.1f s em %.0f s' % (t_alvo, limite))
        time.sleep(0.05)


def resultados_captura(duracao):
    """Espera a captura terminar e devolve o DataFrame (a assinatura muda entre versoes)."""
    if hasattr(CAP, 'wait_capture_finish'):
        try:
            CAP.wait_capture_finish(timeout=10*duracao + 60)
        except TypeError:
            CAP.wait_capture_finish()
    params = inspect.signature(CAP.get_capture_results).parameters
    kw = {}
    for nome in ('wait_capture', 'wait_capture_finish'):
        if nome in params:
            kw[nome] = True
    df = CAP.get_capture_results(**kw)
    if isinstance(df, dict):
        import pandas as pd
        df = pd.DataFrame(df)
    return df


def roda(nome):
    p = prepara(nome)
    if p is None:
        return
    e, t_ev, dur = p
    t0 = time.time()
    model.load(MM.TSE)
    RT.aplica(e)
    if not model.compile():
        raise RuntimeError('nao compilou: ' + nome)
    model.close_model()
    if not hil.load_model(file=CPD, vhil_device=True):
        raise RuntimeError('o VHIL nao carregou ' + CPD)
    hil.start_simulation()
    try:
        t_cap = t_ev - 1.0
        espera_sim(t_cap)
        t_ini = hil.get_sim_time()
        CAP.start_capture(duration=dur + 1.0, rate=TAXA, signals=SONDAS)
        df = resultados_captura(dur + 1.0)
    finally:
        hil.stop_simulation()
    df = df.reset_index()
    col_t = df.columns[0]
    t = df[col_t]
    t = t.dt.total_seconds() if hasattr(t, 'dt') else t.astype(float)
    df.insert(0, 't_sim', t + t_ini)
    df.insert(0, 'Time', df['t_sim'] - t_ev)
    df = df.drop(columns=[col_t])
    df.to_csv(os.path.join(DADOS, nome + '.csv'), index=False)
    print('%-30s pontos=%7d  inicio da captura em t_sim=%.3f s  %.0f s' % (nome, len(df), t_ini, time.time() - t0),
          flush=True)


if __name__ == '__main__':
    os.makedirs(DADOS, exist_ok=True)
    nomes = sys.argv[1:] or list(RT.ENSAIOS)
    try:
        for nome in nomes:
            roda(nome)
    finally:
        # devolve o .tse aos valores do painel e recompila, para o SCADA voltar a funcionar
        model.load(MM.TSE)
        RT.aplica(dict(vC0=0.0, t_deg=None, falta=None, D=P.D, X=P.X_TOT, tempo=121.0))
        model.save()
        model.compile()
        model.close_model()
        print('modelo devolvido aos valores do painel e recompilado', flush=True)
