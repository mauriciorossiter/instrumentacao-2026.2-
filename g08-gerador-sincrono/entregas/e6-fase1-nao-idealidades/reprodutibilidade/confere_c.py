# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Confere, SEM o TyphoonSim, que o que vai para os modelos .tse (monta_modelo.py) calcula o
mesmo que o gabarito Python (modelo_camadas.py):

  'nativo'   - a montagem da entrega. Os blocos nativos da E02 (folga, resolucao, chave,
               movimento, filtro 1/f em forma paralela, ganhos) sao EMULADOS aqui, operacao por
               operacao e na ordem do diagrama; a saida deles alimenta a C function da E01
               (C_POT_E01, compilada com gcc, texto identico ao do .tse). O Random Source e
               substituido pelo MESMO ruido branco do gabarito, para a comparacao ser exata.
  'r8'       - contrafactual sem buffer: as resistencias calculadas pelos blocos nativos.
  'c'        - plano B (camadas em C function), compilado com gcc.

Uso:  python confere_c.py        (precisa de gcc e numpy; nao precisa do Typhoon)
"""
import os
import subprocess
import sys
import tempfile
import types

import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
# monta_modelo importa a API do Typhoon no topo; aqui so precisamos dos textos C
sys.modules.setdefault('typhoon', types.ModuleType('typhoon'))
sys.modules.setdefault('typhoon.api', types.ModuleType('typhoon.api'))
mod_se = types.ModuleType('typhoon.api.schematic_editor'); mod_se.model = None
sys.modules.setdefault('typhoon.api.schematic_editor', mod_se)

import parametros as P
import monta_modelo as M
from modelo_camadas import (cadeia, cadeia_sem_buffer, CASOS, CASOS_R8, N_AMOSTRAS, GeradorRosa,
                            K_ENR, KELLET_P, KELLET_G, KELLET_DIRETO, KELLET_ATRASO)


def corpo(txt):
    return txt.split('/*Begin code section*/')[1].split('/*End code section*/')[0]


def declara(globais):
    out = []
    for d in globais.strip(';').split(';'):
        tipo, nome = d.split()
        out.append('%s %s;' % ('double' if tipo == 'real' else 'int', nome))
    return '\n'.join(out)


def programa(globais, init, codigo, entradas, saidas):
    """Le as entradas do stdin (uma linha por passo), roda o codigo do .tse e imprime
    theta_ref (calculado por C_REFERENCIA) e as saidas. Se 'theta' nao for lido do stdin,
    ele recebe theta_ref (ligacao direta, como no plano B)."""
    le = ''.join('scanf("%%lf", &%s); ' % e for e in entradas)
    imp = ','.join(['%.17g'] * (1 + len(saidas)))
    return r'''
#include <stdio.h>
#include <math.h>
%s
double THETA_FS_R, T_MEIO;
int main(void) {
    double t, theta_ref, vref = %r;
    double %s;
    int n;
    %s
    THETA_FS_R = %r; T_MEIO = %r;
    for (n = 0; n < %d; n++) {
        t = n * %r;
        { double THETA_FS = THETA_FS_R; %s }
        %s
        %s
        %s
        printf("%s\n", theta_ref, %s);
    }
    return 0;
}
''' % (declara(globais), P.VREF, ', '.join(sorted(set(entradas + saidas + ['theta']))), init, P.THETA_FS,
       P.T_VARREDURA / 2, N_AMOSTRAS, P.DT_SINAL, corpo(M.C_REFERENCIA),
       '' if 'theta' in entradas else 'theta = theta_ref;', le, corpo(codigo), imp, ', '.join(saidas))


def roda_c(fonte, dados_entrada, d):
    src = os.path.join(d, 'p.c'); exe = os.path.join(d, 'p')
    open(src, 'w').write(fonte)
    subprocess.run(['gcc', '-O0', '-std=c99', '-Wall', '-Wno-unused-variable', '-Wno-unused-but-set-variable',
                    '-o', exe, src, '-lm'], check=True)
    txt = '' if dados_entrada is None else '\n'.join(' '.join('%.17g' % v for v in l) for l in dados_entrada)
    out = subprocess.run([exe], input=txt, capture_output=True, text=True, check=True).stdout
    return np.loadtxt(out.splitlines(), delimiter=',')


def blocos_nativos(theta, flags, branco):
    """Emula os blocos nativos da E02, na ordem do diagrama de monta_modelo.monta().
    Retorna theta_c, theta_pot (entrada do potenciometro da E01) e dRc_ativo [ohm]."""
    b, k_res, k_r = P.FOLGA_GRAUS * flags[0], float(flags[1]), float(flags[2])
    g_n, c_a, c_f, g_q = P.N_PASSOS / P.THETA_FS, 0.5 - P.FASE_ESPIRA, P.FASE_ESPIRA, P.THETA_FS / P.N_PASSOS
    ud = 0.0; ud_m = 0.0; pol = np.zeros(6); w_ant = 0.0
    th_c = np.empty_like(theta); th_pot = np.empty_like(theta); dr = np.empty_like(theta)
    for k, th in enumerate(theta):
        y = max(th, min(th + b, ud)); ud = y                       # folga (Sum, Min, Max, Unit Delay)
        th_q = (np.floor(y * g_n + c_a) + c_f) * g_q                # resolucao (Gain, Sum, Round, Sum, Gain)
        th_p = y + (th_q - y) * k_res                              # chave (Sum +-, Product, Sum)
        w = branco[k]                                              # Random Source (aqui: o branco do gabarito)
        for i in range(6):                                         # 6 Discrete Transfer Function
            pol[i] = KELLET_P[i] * pol[i] + KELLET_G[i] * w
        rosa = pol.sum() + KELLET_ATRASO * w_ant + KELLET_DIRETO * w   # TF de atraso + Gain + Sum(8)
        w_ant = w
        mov = np.sign(abs(y - ud_m)); ud_m = y                     # Sum +-, Unit Delay, Abs, Sign
        th_c[k], th_pot[k], dr[k] = y, th_p, K_ENR * rosa * mov * k_r
    return th_c, th_pot, dr


t = np.arange(N_AMOSTRAS) * P.DT_SINAL
th = P.theta_ref(t)
g = GeradorRosa(); BRANCO = np.array([g.branco() for _ in range(N_AMOSTRAS)])   # o branco do gabarito
ok_geral = True
linhas = []
with tempfile.TemporaryDirectory() as d:
    # ---------------------------------------------------------------- 'nativo' (a entrega)
    for caso, flags in M.FLAGS.items():
        thc, thp, dr = blocos_nativos(th, flags, BRANCO)
        r = roda_c(programa(M.GLOBAIS_POT_E01, M.INIT_POT_E01, M.C_POT_E01, ['theta'], ['v_cursor']),
                   thp[:, None], d)
        v = r[:, 1] + dr * P.I_CURSOR                              # Gain I_cursor + Sum na saida da E01
        py = cadeia(th, CASOS[caso])
        dc = np.max(np.abs(thc - py['theta_c'])); dv = np.max(np.abs(v - py['v_cursor']))
        ok = dc < 1e-9 and dv < 1e-12
        ok_geral &= ok
        linhas.append(('nativo', caso, dc, dv, ok))
    # ---------------------------------------------------------------- contrafactual R8 (nativo)
    for caso, flags in M.FLAGS_R8.items():
        thc, thp, dr = blocos_nativos(th, flags, BRANCO)
        R_inf = np.minimum(np.maximum((P.R_POT / P.THETA_FS) * thp, P.R_MIN_POT), P.R_POT)
        R_c = P.R_C0 + dr
        py = cadeia_sem_buffer(th, CASOS_R8[caso])
        dR = max(np.max(np.abs(R_inf - np.maximum(P.R_POT * py['x_q'], P.R_MIN_POT))),
                 np.max(np.abs(R_c - py['R_c'])))
        dc = np.max(np.abs(thc - py['theta_c']))
        ok = dc < 1e-9 and dR < 1e-9
        ok_geral &= ok
        linhas.append(('r8', caso, dc, dR, ok))
    # ---------------------------------------------------------------- plano B ('c')
    for caso, flags in M.FLAGS.items():
        r = roda_c(programa(M.GLOBAIS_POT, M.init_pot(*flags), M.C_POT, [], ['v_cursor', 'theta_c', 'dRc']), None, d)
        py = cadeia(th, CASOS[caso])
        dv = np.max(np.abs(r[:, 1] - py['v_cursor'])); dc = np.max(np.abs(r[:, 2] - py['theta_c']))
        ok = np.max(np.abs(r[:, 0] - th)) < 1e-9 and dc < 1e-9 and dv < 1e-12
        ok_geral &= ok
        linhas.append(('c', caso, dc, dv, ok))

print('%-7s %-24s %-22s %-24s' % ('modo', 'caso', 'theta_cursor [grau]', 'v_cursor [V] / R [ohm]'))
for modo, caso, dc, dv, ok in linhas:
    print('%-7s %-24s %-22.1e %-12.1e %s' % (modo, caso, dc, dv, 'IGUAL' if ok else 'DIFERENTE'))
print('Typhoon (blocos nativos + C da E01) x Python:', 'todos os casos conferem' if ok_geral else 'HA DIFERENCAS')
sys.exit(0 if ok_geral else 1)
