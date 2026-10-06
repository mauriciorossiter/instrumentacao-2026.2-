#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================================
 PARTE B - Curva de calibracao do sensor com zona morta
 ECOM060 - Instrumentacao Eletronica - UFAL - 2026.2 - Equipe 2 (Zona morta)
============================================================================

Aplica a Secao 3.2 do Aguirre (Fundamentos de Instrumentacao) aos dados
brutos exportados do TyphoonSim (arquivo CSV com Time, RawOutput,
OriginalInput, DeadZoneOutput).

IDEIA-GUIA
----------
A Secao 3.2 pressupoe que a curva de calibracao fe seja uma FUNCAO INVERTIVEL
de valor unico (Eq. 3.21). A zona morta VIOLA isso: para cada entrada x existem
duas saidas possiveis, dependendo do sentido da varredura (subida x descida).
A caracteristica estatica e um PARALELOGRAMO com dois ramos de inclinacao ~1,
deslocados de +-Zx/2 em relacao a bissetriz ideal y_id = x.

Por isso ajustamos a reta de calibracao (Eq. 3.22, y = p + alpha*x) a CADA RAMO
separadamente, por minimos quadrados (Eq. 3.25 e 3.26), com as incertezas do
ajuste (Eq. 3.27 a 3.29). A largura da zona morta e a separacao HORIZONTAL entre
os dois ramos, que deve coincidir com o Zx = 5 parametrizado no modelo.

Equacoes do Aguirre usadas aqui:
  3.22  y = p + alpha*x           (reta de calibracao)
  3.25  alpha_hat  (minimos quadrados, inclinacao)
  3.26  p_hat      (minimos quadrados, intercepto)
  3.27  s(alpha)^2 (variancia da inclinacao)
  3.28  s(p)^2     (variancia do intercepto)
  3.29  s(y,x)^2   (variancia do erro de ajuste; nu = N - 2)
  3.31  banda de confianca simplificada  y_hat +- t * s(y,x)/sqrt(N)
============================================================================
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------------------------------------
# 0) PARAMETROS
# ---------------------------------------------------------------------------
CSV = "HIL_260906_220904"   # arquivo de dados brutos do TyphoonSim
COL_X = "OriginalInput"     # x_referencia (entrada limpa, antes de fe)
COL_Y = "DeadZoneOutput"    # y_instrumento (saida apos zona morta, com ruido)
ZX_NOMINAL = 5.0            # largura da zona morta parametrizada no modelo
T_STUDENT_95 = 1.960        # fator t p/ 95% e nu grande (Tabela 3.1 do livro);
                            # com N ~ 7e4 amostras a distribuicao t ~ normal.

# ---------------------------------------------------------------------------
# 1) CARREGAR OS DADOS
# ---------------------------------------------------------------------------
df = pd.read_csv(CSV)
x = df[COL_X].to_numpy()
y = df[COL_Y].to_numpy()
print(f"Amostras carregadas: {len(df)}")
print(f"Entrada x: [{x.min():.3f}, {x.max():.3f}]")
print(f"Saida  y: [{y.min():.3f}, {y.max():.3f}]")

# ---------------------------------------------------------------------------
# 2) SEPARAR OS RAMOS (subida x descida)
# ---------------------------------------------------------------------------
# A zona morta tem "memoria": o ramo depende do SENTIDO da varredura, isto e,
# do sinal da derivada dx/dt. Usamos np.gradient para estimar dx/dt.
dxdt = np.gradient(x)

# Nos vertices da triangular a saida fica "presa" (congelada) enquanto a entrada
# percorre a largura Zx. Esses trechos NAO pertencem a parte ativa da reta e
# distorcem o ajuste (achatam a inclinacao). Selecionamos apenas o REGIME ATIVO,
# onde a saida ja acompanha a entrada, deslocada de +-Zx/2.
# Criterio: no regime ativo, (y - x) ~ -Zx/2 na subida e +Zx/2 na descida.
offset = y - x
TOL = 0.6  # tolerancia em torno de +-Zx/2 (absorve o ruido de medicao)

mask_subida  = (dxdt > 0) & (np.abs(offset - (-ZX_NOMINAL/2)) < TOL)
mask_descida = (dxdt < 0) & (np.abs(offset - (+ZX_NOMINAL/2)) < TOL)

print(f"\nAmostras no ramo de SUBIDA (ativo):  {mask_subida.sum()}")
print(f"Amostras no ramo de DESCIDA (ativo): {mask_descida.sum()}")

# ---------------------------------------------------------------------------
# 3) AJUSTE POR MINIMOS QUADRADOS (Eq. 3.25 e 3.26)
# ---------------------------------------------------------------------------
def minimos_quadrados(xi, yi):
    """
    Ajusta y = p + alpha*x por minimos quadrados, retornando os parametros e
    suas incertezas EXATAMENTE pelas formulas do Aguirre (Eq. 3.25-3.29).
    """
    N = len(xi)
    Sx  = xi.sum()
    Sy  = yi.sum()
    Sxx = (xi*xi).sum()
    Sxy = (xi*yi).sum()
    denom = N*Sxx - Sx**2

    # Eq. 3.25 (inclinacao) e Eq. 3.26 (intercepto)
    alpha = (N*Sxy - Sx*Sy) / denom
    p     = (Sy*Sxx - Sxy*Sx) / denom

    # Eq. 3.29: variancia do erro de ajuste, nu = N - 2 (reta)
    residuos = yi - (p + alpha*xi)
    nu = N - 2
    s_yx2 = (residuos**2).sum() / nu
    s_yx  = np.sqrt(s_yx2)

    # Eq. 3.27 e 3.28: variancias dos parametros
    s_alpha2 = N * s_yx2 / denom
    s_p2     = s_yx2 * Sxx / denom
    s_alpha  = np.sqrt(s_alpha2)
    s_p      = np.sqrt(s_p2)

    return dict(N=N, alpha=alpha, p=p, s_yx=s_yx,
                s_alpha=s_alpha, s_p=s_p, residuos=residuos)

fit_sub = minimos_quadrados(x[mask_subida],  y[mask_subida])
fit_des = minimos_quadrados(x[mask_descida], y[mask_descida])

def relatorio(nome, f):
    print(f"\n--- Ramo {nome} ---")
    print(f"  N = {f['N']}")
    print(f"  alpha (sensibilidade) = {f['alpha']:.4f} +- {f['s_alpha']:.2e}   [Eq. 3.25 / 3.27]")
    print(f"  p     (intercepto)    = {f['p']:.4f} +- {f['s_p']:.2e}   [Eq. 3.26 / 3.28]")
    print(f"  s(y,x) (desvio do ajuste) = {f['s_yx']:.4f}   [Eq. 3.29]")

relatorio("SUBIDA",  fit_sub)
relatorio("DESCIDA", fit_des)

# ---------------------------------------------------------------------------
# 4) MEDIR A LARGURA DA ZONA MORTA (separacao HORIZONTAL entre os ramos)
# ---------------------------------------------------------------------------
# Para uma mesma saida y, os dois ramos correspondem a entradas diferentes.
# Invertendo cada reta:  x = (y - p)/alpha.  A separacao horizontal e:
#   Zx_medido = x_descida(y) - x_subida(y)
# Como as retas sao praticamente paralelas (mesmo alpha), essa separacao e
# constante e pode ser avaliada em y = 0 (centro da escala):
#   x_sub(0) = -p_sub/alpha_sub ;  x_des(0) = -p_des/alpha_des
x_sub_0 = -fit_sub['p'] / fit_sub['alpha']
x_des_0 = -fit_des['p'] / fit_des['alpha']
Zx_medido = x_sub_0 - x_des_0   # subida esta a direita, descida a esquerda -> positivo

# Incerteza de Zx por propagacao (Eq. 3.15). Como alpha ~ 1 e as incertezas de p
# dominam, uma aproximacao de 1a ordem util e:
#   u(Zx) ~ sqrt( (s_p_sub/alpha_sub)^2 + (s_p_des/alpha_des)^2 )
u_Zx = np.sqrt( (fit_sub['s_p']/fit_sub['alpha'])**2
              + (fit_des['s_p']/fit_des['alpha'])**2 )

print("\n============================================================")
print(" LARGURA DA ZONA MORTA MEDIDA (separacao horizontal)")
print("============================================================")
print(f"  x_subida(y=0)  = {x_sub_0:+.4f}")
print(f"  x_descida(y=0) = {x_des_0:+.4f}")
print(f"  Zx_medido = {Zx_medido:.4f} +- {u_Zx:.2e}")
print(f"  Zx_nominal = {ZX_NOMINAL:.4f}")
print(f"  erro relativo = {100*abs(Zx_medido-ZX_NOMINAL)/ZX_NOMINAL:.3f} %")

# ---------------------------------------------------------------------------
# 5) GRAFICO 1 - Caracteristica estatica (paralelogramo) + retas ajustadas
# ---------------------------------------------------------------------------
# Subamostra para o scatter nao ficar pesado no PDF/PNG
step = max(1, len(x)//6000)
xs, ys = x[::step], y[::step]

fig, ax = plt.subplots(figsize=(7.5, 6.2))
ax.scatter(xs, ys, s=3, c="#c0392b", alpha=0.25, label="dados (y_instrumento)")

xx = np.linspace(x.min(), x.max(), 200)
ax.plot(xx, fit_sub['p'] + fit_sub['alpha']*xx, 'b-', lw=2,
        label=f"reta subida:  y = {fit_sub['p']:.3f} + {fit_sub['alpha']:.3f}x")
ax.plot(xx, fit_des['p'] + fit_des['alpha']*xx, 'g-', lw=2,
        label=f"reta descida: y = {fit_des['p']:+.3f} + {fit_des['alpha']:.3f}x")
ax.plot(xx, xx, 'k--', lw=1, alpha=0.6, label="instrumento ideal y_id = x")

# Cota horizontal de Zx em y = 0
ax.annotate("", xy=(x_sub_0, 0), xytext=(x_des_0, 0),
            arrowprops=dict(arrowstyle="<->", color="black", lw=1.5))
ax.text((x_sub_0+x_des_0)/2, 0.4, f"Zx = {Zx_medido:.3f}",
        ha="center", fontsize=11)

ax.set_xlabel("entrada x  (x_referencia)")
ax.set_ylabel("saida y  (y_instrumento)")
ax.set_title("Curva de calibracao do sensor com zona morta (Secao 3.2)")
ax.legend(fontsize=8, loc="upper left")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig("parteB_fig1_caracteristica.png", dpi=150)
print("\n[figura salva] parteB_fig1_caracteristica.png")

# ---------------------------------------------------------------------------
# 6) GRAFICO 2 - Banda de confianca de 95% (Eq. 3.31) no ramo de subida
# ---------------------------------------------------------------------------
# Banda simplificada (Eq. 3.31):  y_hat +- t * s(y,x)/sqrt(N)
f = fit_sub
banda = T_STUDENT_95 * f['s_yx'] / np.sqrt(f['N'])
y_hat = f['p'] + f['alpha']*xx

fig2, ax2 = plt.subplots(figsize=(7.5, 5.2))
ax2.scatter(x[mask_subida][::step], y[mask_subida][::step],
            s=3, c="#2980b9", alpha=0.25, label="dados (subida)")
ax2.plot(xx, y_hat, 'k-', lw=2, label="reta ajustada")
ax2.fill_between(xx, y_hat-banda, y_hat+banda, color="orange", alpha=0.4,
                 label=f"banda 95% (+-{banda:.4f})  [Eq. 3.31]")
ax2.set_xlabel("entrada x")
ax2.set_ylabel("saida y")
ax2.set_title("Ramo de subida: reta de calibracao e banda de confianca 95%")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)
fig2.tight_layout()
fig2.savefig("parteB_fig2_banda.png", dpi=150)
print("[figura salva] parteB_fig2_banda.png")

# ---------------------------------------------------------------------------
# 7) RESUMO FINAL
# ---------------------------------------------------------------------------
print("\n============================================================")
print(" RESUMO DA CALIBRACAO (Secao 3.2)")
print("============================================================")
print(f"  Sensibilidade (alpha) ~ 1  -> subida={fit_sub['alpha']:.4f}  descida={fit_des['alpha']:.4f}")
print(f"  Interceptos: subida p={fit_sub['p']:+.4f}  descida p={fit_des['p']:+.4f}")
print(f"  (esperado +-Zx/2 = +-{ZX_NOMINAL/2:.2f} em relacao a bissetriz)")
print(f"  Zx medido = {Zx_medido:.4f} +- {u_Zx:.2e}   (nominal {ZX_NOMINAL})")
print("============================================================")