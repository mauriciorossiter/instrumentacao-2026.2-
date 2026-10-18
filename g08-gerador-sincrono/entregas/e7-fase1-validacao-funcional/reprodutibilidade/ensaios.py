# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03
Gabarito Python dos tres ensaios-padrao (R11) sobre a cadeia completa: E01 (potenciometro
Bourns 3590S -> OPA333 -> XTR115 -> laco 24 V -> 250 ohm) + camadas da E02 (folga, resolucao,
ordem zero e ruido de contato 1/f).

A funcao simula() repete, amostra a amostra e na mesma ordem, o que os blocos do modelo do
TyphoonSim fazem (monta_modelo_e03.py): gerador de ensaio nativo -> folga (Min Max + Unit Delay,
com a injecao da condicao inicial) -> resolucao (Round) -> potenciometro da E01 -> ruido
(so com o cursor em movimento) -> circuito da E01. O ruido usa a realizacao do gabarito da E02
(no TyphoonSim o Random Source sorteia outra).

Saidas:
  ../gabarito/gabarito_ensaio_{a,b,c}.csv       sinais de cada ensaio (cadeia completa)
  ../gabarito/resultados_ensaios.json           parametros, metricas e tabela por camada (R13)
  ../figuras/fig-15-e03-ensaios.png (+ .pdf)    sinal medido x referencia ideal (R12)
  ../figuras/fig-16-e03-camadas.png (+ .pdf)    desvio de cada camada, por ensaio (R13)

Conferencia: com o seletor em 0 (varredura da E01), simula() reproduz o gabarito_completa.csv
da E02 (a funcao confere_e02() roda no fim e imprime a diferenca maxima).

Uso:  python ensaios.py
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import parametros_e03 as E                          # noqa: E402  (traz o caminho da E02)
import parametros as P                              # noqa: E402  (E01 + E02, sem alteracao)
import modelo_camadas as MC                         # noqa: E402  (E02, sem alteracao)

DIR_GAB = os.path.abspath(os.path.join(AQUI, '..', 'gabarito'))
DIR_FIG = os.path.abspath(os.path.join(AQUI, '..', 'figuras'))
if os.environ.get('G08_TESTE'):
    DIR_GAB = DIR_FIG = os.environ['G08_TESTE']

DT = P.DT_SINAL
TODAS = ('folga', 'resolucao', 'ruido')


# =====================================================================================
# simulador amostra a amostra (espelho dos blocos do TyphoonSim)
# =====================================================================================

def simula(ensaio, camadas=TODAS, n=None, t_auto=E.T_DISPARO, d_scada=None,
           theta_base=E.THETA_BASE, amplitude=E.AMPLITUDE, theta0=E.THETA0,
           delta0=E.DELTA0, largura=E.LARGURA, drc=None):
    """Simula o modelo da E03 com o seletor em 'ensaio' (0..3) e as camadas pedidas.

    d_scada: serie 0/1 da chave de disparo do SCADA (None = sempre 0; o disparo vem de t_auto).
    Retorna dict de arrays (sem o atraso numerico; ver com_atraso()).
    """
    if n is None:
        n = int(round(E.T_JANELA / DT)) + 1
    drc = MC.DRC if drc is None else drc
    b = P.FOLGA_GRAUS if 'folga' in camadas else 0.0
    k_res = 1.0 if 'resolucao' in camadas else 0.0
    k_ruido = 1.0 if 'ruido' in camadas else 0.0
    e = [1.0 - np.sign(abs(ensaio - k)) for k in range(4)]   # indicadores do seletor

    out = {c: np.zeros(n) for c in ('t', 'disparo', 'pulso', 'theta_ref', 'theta_cursor',
                                    'theta_resolucao', 'dRc_ativo', 'v_cursor', 'I_mA', 'theta_med')}
    d_ant = c_ant = 0.0           # Unit Delays do gerador (init 0)
    mem = 0.0                     # folga_memoria (init 0)
    mov_ant = 0.0                 # mov_memoria (init 0)
    for k in range(n):
        t = k * DT
        # ---- disparo: chave do SCADA OU degrau automatico em t_auto
        d_auto = 0.5 * (np.sign(t - t_auto + DT / 2) + 1.0)
        d = max(0.0 if d_scada is None else float(d_scada[k]), d_auto)
        borda = max(d - d_ant, 0.0); d_ant = d
        c = d * (c_ant + DT); c_ant = c                      # tempo desde o disparo (DT na 1a amostra)
        p = d * 0.5 * (np.sign(largura + DT / 2 - c) + 1.0)  # pulso de 'largura' segundos
        # ---- referencia: soma dos ramos ponderada pelos indicadores
        r = (e[0] * float(P.theta_ref(t)) + e[1] * (theta_base + amplitude * d)
             + e[2] * theta0 + e[3] * (theta_base + amplitude * p))
        # ---- R6 folga (blocos nativos) + injecao da condicao inicial no estado do cursor
        th_c = max(r, min(r + b, mem))
        inj = borda * e[2]
        mem = th_c + inj * ((r + delta0) - th_c)
        # ---- cursor em movimento (ENR so com o eixo girando)
        movendo = np.sign(abs(th_c - mov_ant)); mov_ant = th_c
        # ---- R6 resolucao (Round floor) com chave
        th_q = (np.floor(th_c * P.N_PASSOS / P.THETA_FS + 0.5 - P.FASE_ESPIRA)
                + P.FASE_ESPIRA) * P.THETA_FS / P.N_PASSOS
        th_pot = th_c + k_res * (th_q - th_c)
        # ---- potenciometro da E01 (ordem zero, R7) + ruido de contato (R8)
        x = min(max(th_pot / P.THETA_FS, 0.0), 1.0)
        dR = drc[k % len(drc)] * movendo * k_ruido
        v = x * P.VREF + dR * P.I_CURSOR
        # ---- circuito da E01 (lei do XTR115 com os resistores comerciais) e receptor
        I = 1e3 * P.GANHO_XTR * (v / P.RIN + P.VREF / P.R0)
        for nome, val in (('t', t), ('disparo', d), ('pulso', p), ('theta_ref', r),
                          ('theta_cursor', th_c), ('theta_resolucao', th_pot), ('dRc_ativo', dR),
                          ('v_cursor', v), ('I_mA', I),
                          ('theta_med', P.THETA_FS * (I - 4.0) / 16.0)):
            out[nome][k] = val
    return out


def com_atraso(s, m=E.ATRASO_AMOSTRAS):
    """O que o TyphoonSim mostra: I_LOOP e theta_med atrasados de m amostras (as m primeiras
    saem com corrente nula, como na E01)."""
    I = np.r_[np.zeros(m), s['I_mA'][:-m]]
    return I, P.THETA_FS * (I - 4.0) / 16.0


# =====================================================================================
# metricas
# =====================================================================================

NOMES_ENS = {1: 'a', 2: 'b', 3: 'c'}
CASOS = {                       # camadas isoladas, para a tabela do R13
    'ideal (E01)': (),
    'folga': ('folga',),
    'resolucao': ('resolucao',),
    'ruido': ('ruido',),
    'estatica (folga + resolucao)': ('folga', 'resolucao'),
    'completa': TODAS,
}


def janela_estavel(s, margem=E.ATRASO_AMOSTRAS + 1):
    """Amostras longe de qualquer mudanca da referencia (exclui as transicoes do atraso)."""
    mud = np.r_[False, np.diff(s['theta_ref']) != 0]
    ok = np.ones(len(mud), bool)
    for k in np.nonzero(mud)[0]:
        ok[k:k + margem] = False
    ok[:margem] = False
    return ok


def metricas_ensaio(ens):
    ref = simula(ens, ())
    tab = {}
    for nome, cam in CASOS.items():
        s = simula(ens, cam)
        tab[nome] = float(np.max(np.abs(s['theta_med'] - ref['theta_med'])))
    s = simula(ens, TODAS)
    ok = janela_estavel(s)
    t = s['t']
    fim = t >= t[-1] - 0.5           # ultimo meio segundo: valor final, depois do ensaio
    antes = t < E.T_DISPARO - 0.01
    res = dict(
        desvio_por_camada_graus=tab,
        dinamica_R7_graus=0.0,       # ordem zero: tau = 0,88 us << 1 ms (e^-1136 na 1a amostra)
        erro_vs_referencia_max_graus=float(np.max(np.abs(s['theta_med'] - s['theta_ref'])[ok])),
        erro_vs_referencia_E01_max_graus=float(np.max(np.abs(ref['theta_med'] - ref['theta_ref'])[ok])),
        theta_med_antes_graus=float(np.mean(s['theta_med'][antes])),
        theta_med_final_graus=float(np.mean(s['theta_med'][fim])),
        theta_ref_final_graus=float(np.mean(s['theta_ref'][fim])),
        theta_med_final_E01_graus=float(np.mean(ref['theta_med'][fim])),
        I_final_mA=float(np.mean(s['I_mA'][fim])),
        residuo_final_vs_E01_graus=float(np.mean(s['theta_med'][fim] - ref['theta_med'][fim])),
        cursor_final_menos_eixo_graus=float(np.mean(s['theta_cursor'][fim] - s['theta_ref'][fim])),
    )
    return res


# =====================================================================================
# conferencia contra o gabarito da E02 (seletor em 0 = varredura da E01)
# =====================================================================================

def confere_e02():
    cands = [os.path.join(E.DIR_E02, 'gabarito_completa.csv')]
    arq = next((c for c in cands if os.path.exists(c)), None)
    if arq is None:
        print('   (conferencia E02 pulada: gabarito_completa.csv nao encontrado em %s)' % E.DIR_E02)
        return None
    g = np.genfromtxt(arq, delimiter=',', names=True)
    s = simula(0, TODAS, n=len(g), t_auto=E.T_AUTO_NUNCA)
    d = {
        'theta_ref': float(np.max(np.abs(s['theta_ref'] - g['theta_ref_graus']))),
        'theta_cursor': float(np.max(np.abs(np.clip(s['theta_cursor'], 0, P.THETA_FS) - g['theta_cursor_graus']))),
        'v_cursor': float(np.max(np.abs(s['v_cursor'] - g['v_cursor_V']))),
        'I_loop': float(np.max(np.abs(s['I_mA'] - g['I_loop_mA']))),
    }
    print('   conferencia contra gabarito_completa.csv da E02 (diferenca maxima): %s' % d)
    return d


# =====================================================================================
# saidas
# =====================================================================================

def grava_csv(ens, s):
    I_ty, th_ty = com_atraso(s)
    cab = ('t_s,theta_ref_graus,disparo,theta_cursor_graus,theta_resolucao_graus,v_cursor_V,'
           'I_loop_mA,theta_med_graus,I_loop_mA_typhoon,theta_med_graus_typhoon')
    M = np.column_stack([s['t'], s['theta_ref'], s['disparo'], s['theta_cursor'], s['theta_resolucao'],
                         s['v_cursor'], s['I_mA'], s['theta_med'], I_ty, th_ty])
    os.makedirs(DIR_GAB, exist_ok=True)
    np.savetxt(os.path.join(DIR_GAB, 'gabarito_ensaio_%s.csv' % NOMES_ENS[ens]), M, delimiter=',',
               header=cab, comments='', fmt='%.10g')


def num_br(v):
    """Numero curto com virgula decimal (figuras em portugues)."""
    if v != 0 and abs(v) < 1e-3:
        m, ex = ('%.1e' % v).split('e')
        return '%s×10$^{%d}$' % (m.replace('.', ','), int(ex))
    return ('%g' % float('%.2g' % v)).replace('.', ',')


def figura_ensaios(sims, refs):
    sys.path.insert(0, E.DIR_E02)
    import estilo as S
    S.aplica_estilo()
    g = lambda v: ('%g' % v).replace('.', ',')  # noqa: E731
    titulos = {1: '(a) degrau 0 → %s° em t = %s s' % (g(E.AMPLITUDE), g(E.T_DISPARO)),
               2: '(b) referência fixa em %s°; cursor deslocado +%s° em t = %s s'
                  % (g(E.THETA0), g(E.DELTA0), g(E.T_DISPARO)),
               3: '(c) pulso de %s° por %s s em t = %s s' % (g(E.AMPLITUDE), g(E.LARGURA), g(E.T_DISPARO))}
    fig, ax = plt.subplots(3, 2, figsize=(9.6, 7.6), gridspec_kw=dict(width_ratios=[1.15, 1]))
    for i, ens in enumerate((1, 2, 3)):
        s, r = sims[ens], refs[ens]
        _, th_ty = com_atraso(s)
        _, th_ty0 = com_atraso(r)
        t = s['t']; v = t > 0.004                  # sem as 2 amostras nulas do atraso numerico
        a = ax[i, 0]
        a.plot(t, s['theta_ref'], color=S.CINZA, lw=3.0, alpha=0.55, label='referência ideal (E01)')
        a.plot(t[v], th_ty[v], color=S.AZUL, lw=1.2, label='medido: cadeia completa')
        a.set_ylabel('ângulo [graus]')
        a.set_title(titulos[ens], loc='left', fontsize=9)
        a.set_ylim(-150, 2050)
        if i == 0:
            a.legend(loc='center right')
        # desvio contra a referencia: completa x ideal da E01 (transicoes do atraso cortadas)
        b = ax[i, 1]
        ok = janela_estavel(s)
        d1 = np.where(ok, th_ty - s['theta_ref'], np.nan)
        d0 = np.where(ok, th_ty0 - r['theta_ref'], np.nan)
        b.plot(t, d0, color=S.LARANJA, lw=1.4, label='cadeia ideal (E01, camadas desligadas)')
        b.plot(t, d1, color=S.AZUL, lw=1.4, label='cadeia completa (E01 + E02)')
        b.axvline(E.T_DISPARO, color=S.CINZA, lw=0.6, ls=':')
        b.set_ylabel('medido − referência [graus]')
        b.set_ylim(-3, 3)
        if i == 0:
            b.legend(loc='lower right', fontsize=7)
    for a in ax[-1]:
        a.set_xlabel('tempo [s]')
    fig.tight_layout()
    os.makedirs(DIR_FIG, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(DIR_FIG, 'fig-15-e03-ensaios.%s' % ext))
    plt.close(fig)


def figura_camadas(res):
    import estilo as S
    S.aplica_estilo()
    camadas = [('folga', 'R6 folga'), ('resolucao', 'R6 resolução'), ('ruido', 'R8 ruído 1/f')]
    cores = [S.AZUL, S.LARANJA, S.AQUA]
    fig, a = plt.subplots(figsize=(7.2, 3.0))
    y0 = np.arange(3)
    h = 0.24
    for j, ((chave, rot), cor) in enumerate(zip(camadas, cores)):
        vals = [res[NOMES_ENS[e]]['desvio_por_camada_graus'][chave] for e in (1, 2, 3)]
        yy = y0 + (j - 1) * h
        a.barh(yy, vals, height=h - 0.03, color=cor, label=rot)
        for yv, val in zip(yy, vals):
            if val <= 0:
                a.text(1.3e-7, yv, '0 (a subida não aciona a folga)', va='center', fontsize=7,
                       color=S.TINTA2)
            else:
                a.text(val * 1.25, yv, num_br(val) + '°', va='center', fontsize=7, color=S.TINTA2)
    a.set_xscale('log')
    a.set_xlim(1e-7, 20)
    a.set_yticks(y0)
    a.set_yticklabels(['(a) degrau', '(b) cond. inicial', '(c) pulso'])
    a.invert_yaxis()
    a.set_xlabel('desvio máximo contra a cadeia ideal da E01 [graus]   (R7 ordem zero: 0)')
    a.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7, frameon=False)
    a.grid(axis='y', visible=False)
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(DIR_FIG, 'fig-16-e03-camadas.%s' % ext))
    plt.close(fig)


def main():
    sims, refs, res = {}, {}, {}
    for ens in (1, 2, 3):
        sims[ens] = simula(ens, TODAS)
        refs[ens] = simula(ens, ())
        grava_csv(ens, sims[ens])
        res[NOMES_ENS[ens]] = metricas_ensaio(ens)
    conf = confere_e02()
    figura_ensaios(sims, refs)
    figura_camadas(res)
    saida = dict(
        parametros=dict(theta_base_graus=E.THETA_BASE, amplitude_graus=E.AMPLITUDE,
                        theta0_graus=E.THETA0, delta0_graus=E.DELTA0, largura_pulso_s=E.LARGURA,
                        t_disparo_s=E.T_DISPARO, janela_s=E.T_JANELA, dt_s=DT,
                        atraso_numerico_amostras=E.ATRASO_AMOSTRAS,
                        folga_graus=P.FOLGA_GRAUS, passo_resolucao_graus=P.PASSO_GRAUS),
        ensaios=res,
        conferencia_E02=conf,
    )
    os.makedirs(DIR_GAB, exist_ok=True)
    with open(os.path.join(DIR_GAB, 'resultados_ensaios.json'), 'w', encoding='utf-8') as f:
        json.dump(saida, f, indent=2, ensure_ascii=False)
    for k, r in res.items():
        print('ensaio (%s): ' % k + ', '.join('%s=%.3g' % (n, v) for n, v in r['desvio_por_camada_graus'].items()))
        print('            final: ref=%.2f  E01=%.3f  completa=%.3f graus (%.4f mA) | residuo=%.3f | cursor-eixo=%.3f'
              % (r['theta_ref_final_graus'], r['theta_med_final_E01_graus'], r['theta_med_final_graus'],
                 r['I_final_mA'], r['residuo_final_vs_E01_graus'], r['cursor_final_menos_eixo_graus']))


if __name__ == '__main__':
    main()
