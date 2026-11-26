# -*- coding: utf-8 -*-
"""ECOM060 - G08 - Fase 2, E03 e E04: tabela dos ensaios rodados no TyphoonSim (typhoonsim/roda_typhoon.py)
e comparados com o gabarito (compara_typhoon.py). Python puro: nao precisa da API do Typhoon."""
import parametros_e34 as P
import sistema as S


def malha(fb, **kw):
    return S.cfg_padrao(malha='fechada', pss=True, fb_v=fb, fb_f=fb, **kw)


def regime(T=3.0):
    e = S.ensaio('r', T=T)
    e['nome'] = 'regime'
    e['dvref'] = lambda t: 0.0
    return e


# nome: (ensaio, configuracao)
ENSAIOS = {
    'e03_a': (S.ensaio('a'), S.cfg_padrao()),
    'e03_b': (S.ensaio('b'), S.cfg_padrao()),
    'e03_c': (S.ensaio('c'), S.cfg_padrao()),
    'e03_c_tau1': (S.ensaio('c'), S.cfg_padrao(tau_rms=1.0)),      # R5: exacerbacao do AD637
    'e03_b_N16': (S.ensaio('b'), S.cfg_padrao(n_cic=16.0)),        # R5: exacerbacao do frequencimetro
}
for fb in ('ideal', 'real'):
    for e in 'rpf':
        ENSAIOS['e04_%s_%s' % (fb, e)] = (S.ensaio(e), malha(fb))
    ENSAIOS['e04_%s_regime' % fb] = (regime(), malha(fb))
for e in 'rp':
    ENSAIOS['e04_R5_%s' % e] = (S.ensaio(e), malha('real', pf_bw=10.0))
ENSAIOS['e04_R5_regime'] = (regime(), malha('real', pf_bw=10.0))


# Entrega Final, item 4: cada caracteristica SOZINHA no ensaio (a), 6 s (captura opcional no VHIL; o relatorio usa o
# gabarito, validado pelas capturas e03_* e e04_*). Ruido e relogio so' agem dentro do frequencimetro: N = 1 neles.
def _so(ch):
    c = dict(P.NEUTRO)
    c[ch] = P.REAL[ch]
    if ch in ('sigma', 'fclk'):
        c['n_cic'] = 1.0
    return S.cfg_padrao(**c)


for _ch in ('eps_tp', 'tau_rms', 'nbits', 'sigma', 'n_cic', 'fclk'):
    ENSAIOS['fin_a_so_' + _ch] = (S.ensaio('a', T=6.0), _so(_ch))
