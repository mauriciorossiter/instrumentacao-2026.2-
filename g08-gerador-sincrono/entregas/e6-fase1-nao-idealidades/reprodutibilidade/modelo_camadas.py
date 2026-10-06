# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Definicao unica das camadas nao ideais, importada por:
    camadas.py         (gabarito Python, figuras e numeros do relatorio)
    monta_modelo.py    (gera o codigo C da C function 'potenciometro' do TyphoonSim)
    analisa_typhoon.py (aplica as mesmas metricas aos dados do TyphoonSim)

Cadeia (ordem fisica):
  theta_ref (eixo) -> [folga/backlash] -> theta_c (cursor) -> [resolucao] -> x_q
  -> sensor de ordem zero (x_q . VREF) -> [ruido de contato: dR_c . I_cursor]
  -> v_cursor -> MESMO circuito da Entrega 01 -> I_LOOP

As funcoes abaixo e o codigo C de C_POT fazem as mesmas operacoes, na mesma ordem, para que
o gabarito e a simulacao sejam comparaveis amostra a amostra.
"""
import numpy as np

import parametros as P


# =====================================================================
# R6 - camada estatica
# =====================================================================

def folga(theta, b=P.FOLGA_GRAUS):
    """Folga mecanica (backlash) entre eixo e cursor - operador de folga ('play').
    O cursor so se move quando o eixo encosta num dos lados da folga:
      subindo:  theta_c = theta          (calibracao feita na subida)
      descendo: theta_c = theta + b      (depois de percorrer a folga inteira)
    Na reversao o cursor fica parado enquanto o eixo percorre b graus (zona morta).
    Forma fechada usada nas tres implementacoes (Python, C e blocos nativos Min/Max do Typhoon):
        theta_c[k] = max( theta[k], min(theta[k] + b, theta_c[k-1]) )
    (subindo, o max escolhe theta; descendo alem da folga, o min escolhe theta + b;
     dentro da folga, fica theta_c[k-1])."""
    theta = np.asarray(theta, dtype=float)
    y = np.empty_like(theta)
    yk = theta[0]                      # 1a chamada: cursor encostado no eixo
    for k, th in enumerate(theta):
        yk = max(th, min(th + b, yk))
        y[k] = yk
    return np.clip(y, 0.0, P.THETA_FS)


def resolucao(theta_c, n=P.N_PASSOS, fase=P.FASE_ESPIRA):
    """Resolucao do fio enrolado: o cursor so assume N posicoes discretas (uma por espira),
    deslocadas de 'fase' passo em relacao ao zero. Cada posicao vale para o cursor a menos
    de meio passo dela (erro simetrico de +-1/2 passo):
      x_q = (floor(x.N + 1/2 - fase) + fase) / N      (igual ao C).
    Limitado a [0, 1], como no potenciometro da E01: com a fase de 1/4, a ultima posicao da
    escada cairia 0,18 grau alem do fim da trilha, onde o cursor nao chega."""
    x = np.asarray(theta_c, dtype=float) / P.THETA_FS
    return np.clip((np.floor(x * n + 0.5 - fase) + fase) / n, 0.0, 1.0)


# =====================================================================
# R8 - camada espectral: gerador de ruido 1/f reproduzivel em C
# =====================================================================

class GeradorRosa:
    """Ruido 1/f ('rosa'), deterministico e reproduzivel em C:
      - branco: soma de 12 uniformes de um LCG de 32 bits (Numerical Recipes), menos 6
        -> aproximadamente gaussiano, media 0, variancia 1 (Irwin-Hall);
      - rosa: filtro de Paul Kellet ('refined'), 7 polos reais escalonados.
    Todas as operacoes sao exatas em double (1664525 . 2^32 < 2^53), entao Python e C
    produzem a mesma sequencia."""
    A, C, M = 1664525.0, 1013904223.0, 4294967296.0

    def __init__(self, semente=P.SEMENTE):
        self.s = float(semente)
        self.b = [0.0] * 7

    def branco(self):
        g = 0.0
        for _ in range(12):
            self.s = (self.A * self.s + self.C) % self.M
            g += self.s / self.M
        return g - 6.0

    def proximo(self):
        w = self.branco()
        b = self.b
        b[0] = 0.99886 * b[0] + w * 0.0555179
        b[1] = 0.99332 * b[1] + w * 0.0750759
        b[2] = 0.96900 * b[2] + w * 0.1538520
        b[3] = 0.86650 * b[3] + w * 0.3104856
        b[4] = 0.55000 * b[4] + w * 0.5329522
        b[5] = -0.7616 * b[5] - w * 0.0168980
        rosa = b[0] + b[1] + b[2] + b[3] + b[4] + b[5] + b[6] + w * 0.5362
        b[6] = w * 0.115926
        return rosa

    def serie(self, n):
        return np.array([self.proximo() for _ in range(n)])


# Coeficientes do filtro 1/f de Kellet, na forma paralela usada pelos blocos nativos do Typhoon:
#   H(z) = sum_i G_i / (1 - P_i z^-1)  +  DIRETO  +  ATRASO . z^-1
# (e exatamente o que GeradorRosa.proximo calcula, termo a termo)
KELLET_P = [0.99886, 0.99332, 0.96900, 0.86650, 0.55000, -0.7616]
KELLET_G = [0.0555179, 0.0750759, 0.1538520, 0.3104856, 0.5329522, -0.0168980]
KELLET_DIRETO = 0.5362
KELLET_ATRASO = 0.115926


def filtro_kellet(w):
    """Aplica o filtro 1/f a uma sequencia de ruido branco w (mesma conta dos blocos nativos).
    Usado para conferir o filtro do TyphoonSim a partir do ruido branco que ele mesmo sorteou."""
    w = np.asarray(w, dtype=float)
    b = np.zeros(6); y = np.empty_like(w); w_ant = 0.0
    for k, wk in enumerate(w):
        for i in range(6):
            b[i] = KELLET_P[i] * b[i] + KELLET_G[i] * wk
        y[k] = b.sum() + KELLET_DIRETO * wk + KELLET_ATRASO * w_ant
        w_ant = wk
    return y


N_AMOSTRAS = int(round(P.T_SIM / P.DT_SINAL)) + 1          # 20001 amostras a 1 ms
ROSA_BRUTO = GeradorRosa().serie(N_AMOSTRAS)
K_ENR = float(P.ENR_POT / np.max(np.abs(ROSA_BRUTO)))     # pico de |dR_c| = ENR maximo (100 ohm)
DRC = K_ENR * ROSA_BRUTO                                   # ohm, realizacao do gabarito (no TyphoonSim o Random Source sorteia outra)


# =====================================================================
# cadeia completa (circuito da Entrega 01 sem alteracao)
# =====================================================================

def io_transmissor(x, R0=P.R0, Rin=P.RIN, vref=P.VREF):
    """Lei da Entrega 01 (Eq. 2), com o cursor bufferizado [A]."""
    return P.GANHO_XTR * (x * vref / Rin + vref / R0)


def cadeia(theta, camadas, dR=None):
    """Aplica as camadas pedidas e o circuito da Entrega 01.
    camadas: subconjunto de {'folga', 'resolucao', 'ruido'}.
    Retorna dict com theta_c, x_q, v_cursor [V] e I_mA [mA]."""
    th_c = folga(theta) if 'folga' in camadas else np.clip(theta, 0, P.THETA_FS)
    xq = resolucao(th_c) if 'resolucao' in camadas else th_c / P.THETA_FS
    v = xq * P.VREF                                  # sensor de ordem zero (R7)
    if 'ruido' in camadas:
        # ENR so existe com o cursor deslizando sobre a trilha (definicao do ENR)
        movendo = np.r_[False, np.diff(th_c) != 0]
        v = v + (DRC if dR is None else dR) * P.I_CURSOR * movendo
    I = io_transmissor(v / P.VREF)
    return dict(theta_c=th_c, x_q=xq, v_cursor=v, I_mA=1e3 * I)


CASOS = {
    'ideal':     set(),
    'estatica':  {'folga', 'resolucao'},
    'espectral': {'ruido'},
    'completa':  {'folga', 'resolucao', 'ruido'},
}


# =====================================================================
# metricas (as mesmas para o gabarito e para o TyphoonSim)
# =====================================================================

def metricas(t, th, I):
    """Criterios de R2 (Entrega 01) + histerese e zona morta na reversao.
    t [s], th = theta_ref [graus], I = corrente de laco [mA]."""
    sub = t <= P.T_VARREDURA / 2 + (t[1] - t[0]) / 2
    des = ~sub
    x = th / P.THETA_FS
    i0 = np.interp(0.0, th[sub], I[sub]); i1 = np.interp(P.THETA_FS, th[sub], I[sub])
    reta = i0 + (i1 - i0) * x
    e_lin = 100 * (I - reta) / (i1 - i0)
    e_tot = 100 * (I - (4 + 16 * x)) / 16.0
    grade = np.linspace(0.02, 0.98, 48001) * P.THETA_FS
    o = np.argsort(th[des])
    Isub = np.interp(grade, th[sub], I[sub]); Ides = np.interp(grade, th[des][o], I[des][o])
    th_med = P.THETA_FS * (I - 4.0) / 16.0
    # zona morta: quanto o eixo volta, depois do pico, ate a leitura mudar.
    # Limiar de 10 nA: bem acima do ruido de contato (~1e-4 nA) e bem abaixo de um
    # passo de resolucao (3,2 uA), para nao confundir ruido com movimento.
    kp = int(np.argmax(th))
    mud = np.nonzero(np.abs(I[kp:] - I[kp]) > 1e-5)[0]
    zm = float(th[kp] - th[kp + mud[0]]) if len(mud) else float('nan')
    return dict(
        erro_lin_subida_pcFS=float(np.max(np.abs(e_lin[sub]))),
        erro_lin_banda_pcFS=float(np.max(np.abs(e_lin))),
        erro_total_pcFS=float(np.max(np.abs(e_tot))),
        histerese_pcFS=float(100 * np.max(np.abs(Ides - Isub)) / 16.0),
        histerese_graus=float(P.THETA_FS * np.max(np.abs(Ides - Isub)) / 16.0),
        erro_angulo_graus=float(np.max(np.abs(th_med - th))),
        zona_morta_reversao_graus=zm,
        atende=bool(np.max(np.abs(e_lin)) < 100 * P.ERRO_LIN_MAX
                    and np.max(np.abs(e_tot)) < 100 * P.ERRO_LIN_MAX),
    ), e_lin, e_tot


# =====================================================================
# contrafactual R8: potenciometro eletrico SEM buffer (modelo_r8_sem_buffer.tse)
# =====================================================================
CASOS_R8 = {
    'r8_sem_buffer':           {'folga', 'resolucao', 'ruido'},
    'r8_sem_buffer_sem_ruido': {'folga', 'resolucao'},
}


def cadeia_sem_buffer(theta, camadas, dR=None):
    """Mesmas camadas, mas o cursor alimenta R_IN direto (sem OPA333). A trilha e dois
    resistores (R_inf = Rp.x, R_sup = Rp.(1-x), cada um >= R_MIN) e o contato fica em serie
    com o cursor (R_c = R_C0 + dR_c, so com o cursor em movimento) - igual ao C_POT_E.
    Circuito: I_IN = V_th/(R_th + R_c + R_IN) + VREF/R0, com o Thevenin do cursor."""
    th_c = folga(theta) if 'folga' in camadas else np.clip(theta, 0, P.THETA_FS)
    xq = resolucao(th_c) if 'resolucao' in camadas else th_c / P.THETA_FS
    R_inf = np.maximum(P.R_POT * xq, P.R_MIN_POT)
    R_sup = np.maximum(P.R_POT * (1.0 - xq), P.R_MIN_POT)
    Rc = np.full_like(xq, P.R_C0)
    if 'ruido' in camadas:
        movendo = np.r_[False, np.diff(th_c) != 0]
        Rc = Rc + (DRC if dR is None else dR) * movendo
    V_th = P.VREF * R_inf / (R_inf + R_sup)
    R_th = R_inf * R_sup / (R_inf + R_sup)
    I_rin = V_th / (R_th + Rc + P.RIN)
    I = P.GANHO_XTR * (I_rin + P.VREF / P.R0)
    return dict(theta_c=th_c, x_q=xq, v_cursor=I_rin * P.RIN, R_c=Rc, I_mA=1e3 * I)
