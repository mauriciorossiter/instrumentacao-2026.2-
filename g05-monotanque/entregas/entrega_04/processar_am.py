# -*- coding: utf-8 -*-
"""
Demodulacao de AM: deteccao de envoltoria x demodulacao sincrona.
Reproduz o sinal gerado pelo modulador_am.tse e compara os dois metodos,
incluindo a sensibilidade a erro de fase e de frequencia da portadora local
e o comportamento sob sobremodulacao (ma > 1).
Gera metricas_am.json e as figuras do relatorio.
"""
import numpy as np, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import signal

rng = np.random.default_rng(2025)

# ------------------------------------------------ parametros (= model_init .tse)
Ts   = 1e-5           # 100 kHz
fm1, fm2 = 50.0, 120.0
fc   = 2000.0
Ac   = 1.0
ma   = 0.5
sigma = 0.02
Tend = 0.2
t = np.arange(0.0, Tend, Ts)
wc = 2*np.pi*fc

# ------------------------------------------------ sinais base
m_norm = 0.7*np.sin(2*np.pi*fm1*t) + 0.3*np.sin(2*np.pi*fm2*t)   # em [-1,1]
carrier = np.cos(wc*t)
def make_am(ma, noise=True):
    env = 1.0 + ma*m_norm
    s = Ac*env*carrier
    if noise: s = s + rng.normal(0, sigma, t.size)
    return s, env
s_am, env_true = make_am(ma)

# ------------------------------------------------ filtro passa-baixas comum
# corte entre a banda da mensagem (<=120 Hz) e a portadora (2 kHz): 400 Hz
def lp(x, fcut=400.0, order=6):
    b, a = signal.butter(order, fcut/(0.5/Ts), btype="low")
    return signal.filtfilt(b, a, x)

# util: casa amplitude/nivel de um sinal recuperado ao m_norm de referencia
def align(rec, ref):
    # remove media e escala por minimos quadrados (rec ~ alfa*ref + beta)
    A = np.vstack([ref, np.ones_like(ref)]).T
    alfa, beta = np.linalg.lstsq(A, rec, rcond=None)[0]
    return (rec - beta)/alfa if abs(alfa) > 1e-12 else rec - beta

# regiao de regime (descarta transitorio do filtro)
reg = t > 0.02

def nrmse(rec, ref):
    r = align(rec, ref)
    return float(np.sqrt(np.mean((r[reg]-ref[reg])**2)) / (ref[reg].max()-ref[reg].min()))

# ============================================================ 1) ENVOLTORIA
# retificacao de onda completa + passa-baixas
env_detect = lp(np.abs(s_am))
env_msg = align(env_detect, m_norm)      # recuperada (nivel/escala ajustados)

# ============================================================ 2) SINCRONA (ideal)
# multiplica por portadora local em fase e filtra
sync_ideal = lp(s_am * (2*np.cos(wc*t)))
sync_msg = align(sync_ideal, m_norm)

res = {}
res["fc"]=fc; res["fm1"]=fm1; res["fm2"]=fm2; res["ma"]=ma; res["sigma"]=sigma
res["nrmse_envoltoria"] = nrmse(env_detect, m_norm)
res["nrmse_sincrona_ideal"] = nrmse(sync_ideal, m_norm)

# ============================================================ 3) SENSIB. A FASE
fases = np.linspace(0, 90, 46)          # graus
fidel_fase = []
gan_fase = []
mr = m_norm[reg]-m_norm[reg].mean()
for phi in np.radians(fases):
    d = lp(s_am * (2*np.cos(wc*t + phi)))
    A = np.vstack([m_norm, np.ones_like(m_norm)]).T
    alfa = np.linalg.lstsq(A, d, rcond=None)[0][0]
    gan_fase.append(alfa)
    dr = d[reg]-d[reg].mean()
    fidel_fase.append(float(np.dot(dr,mr)/(np.linalg.norm(dr)*np.linalg.norm(mr)+1e-12)))
fidel_fase = np.array(fidel_fase); gan_fase = np.array(gan_fase)
res["fidelidade_fase90"] = float(fidel_fase[-1])
res["ganho_fase0"] = float(gan_fase[0])
res["ganho_fase60"] = float(gan_fase[np.argmin(np.abs(fases-60))])
res["ganho_fase90"] = float(gan_fase[-1])

# ============================================================ 4) SENSIB. A FREQ
dfs = np.array([0.0, 1.0, 2.0, 5.0, 10.0, 20.0])   # Hz de erro na portadora local
# sob batimento o alinhamento LS degenera; usamos correlacao normalizada
# (fidelidade): 1.0 = recuperacao perfeita, 0 = sem correlacao com a mensagem
fidel_freq = []
for df in dfs:
    d = lp(s_am * (2*np.cos(2*np.pi*(fc+df)*t)))
    dr, mr = d[reg]-d[reg].mean(), m_norm[reg]-m_norm[reg].mean()
    fidel_freq.append(float(np.dot(dr,mr)/(np.linalg.norm(dr)*np.linalg.norm(mr)+1e-12)))
fidel_freq = np.array(fidel_freq)
res["fidelidade_freq"] = {float(k): float(v) for k, v in zip(dfs, fidel_freq)}

# demodulacao sincrona com erro de frequencia de 5 Hz (para figura)
# escala pelo ganho nominal 0.5 (nao por LS, que degenera sob batimento)
sync_df5 = lp(s_am*(2*np.cos(2*np.pi*(fc+5)*t))) / ma
# envoltoria teorica do batimento: |cos(2*pi*df*t)| modulando a mensagem
beat = m_norm*np.cos(2*np.pi*5*t)

# ============================================================ 5) SOBREMODULACAO
ma_over = 1.5
s_over, env_over = make_am(ma_over)
env_over_detect = lp(np.abs(s_over))
sync_over = lp(s_over*(2*np.cos(wc*t)))
# referencia sobremodulada normalizada (a mensagem "verdadeira" continua m_norm)
res["nrmse_env_sobremod"] = nrmse(env_over_detect, m_norm)
res["nrmse_sync_sobremod"] = nrmse(sync_over, m_norm)

json.dump(res, open("/home/claude/out/metricas_am.json","w"), indent=1)
for k,v in res.items(): print(f"{k:26s} {v}")

# ============================================================ FIGURAS
plt.rcParams.update({"font.size":8,"axes.grid":True,"grid.alpha":0.3,
                     "figure.dpi":170,"savefig.bbox":"tight",
                     "axes.spines.top":False,"axes.spines.right":False})
AZ,VM,CZ,VD = "#1f4e79","#c00000","#808080","#2e7d32"

# Fig 1 - sinal AM no tempo com envoltoria
fig,ax=plt.subplots(figsize=(6.6,3.0))
w1=(t>=0.05)&(t<=0.09)
ax.plot(t[w1], s_am[w1], color="#9dc3e6", lw=0.5, label="sinal AM  s(t)")
ax.plot(t[w1], (Ac*env_true)[w1], color=VM, lw=1.3, label="envoltória  1 + ma·m(t)")
ax.plot(t[w1], -(Ac*env_true)[w1], color=VM, lw=1.3)
ax.set_xlabel("Tempo t [s]"); ax.set_ylabel("Amplitude")
ax.legend(fontsize=7, loc="upper right")
ax.set_title("Sinal AM gerado (ma = 0,5) e sua envoltória", fontsize=8.5, loc="left")
fig.savefig("/home/claude/out/am_fig1_sinal.png"); plt.close(fig)

# Fig 2 - recuperacao pelos dois metodos (ideal)
fig,ax=plt.subplots(figsize=(6.6,3.0))
w2=(t>=0.05)&(t<=0.11)
ax.plot(t[w2], m_norm[w2], color=CZ, lw=2.0, label="mensagem original m(t)")
ax.plot(t[w2], env_msg[w2], color=AZ, lw=1.0, label="envoltória")
ax.plot(t[w2], sync_msg[w2], color=VD, lw=1.0, ls="--", label="síncrona (fase ideal)")
ax.set_xlabel("Tempo t [s]"); ax.set_ylabel("Amplitude (normalizada)")
ax.legend(fontsize=7, loc="upper right")
ax.set_title("Recuperação da mensagem: ambos os métodos com portadora ideal",
             fontsize=8.5, loc="left")
fig.savefig("/home/claude/out/am_fig2_recuperacao.png"); plt.close(fig)

# Fig 3 - sensibilidade a erro de fase
fig,ax=plt.subplots(1,2,figsize=(6.8,2.9))
ax[0].plot(fases, gan_fase, color=AZ, lw=1.5, label="ganho medido")
ax[0].plot(fases, np.cos(np.radians(fases))*gan_fase[0], color=VM, lw=1.0, ls="--",
           label="cos(Δφ)")
ax[0].set_xlabel("Erro de fase Δφ [graus]"); ax[0].set_ylabel("Ganho recuperado")
ax[0].legend(fontsize=7); ax[0].set_title("(a) Ganho ∝ cos(Δφ)", fontsize=8, loc="left")
ax[1].plot(fases, fidel_fase, color=VD, lw=1.5)
ax[1].axhline(0, color="k", lw=0.5)
ax[1].set_xlabel("Erro de fase Δφ [graus]"); ax[1].set_ylabel("Fidelidade (correlação)")
ax[1].set_ylim(-0.1,1.05)
ax[1].set_title("(b) Fidelidade da recuperação", fontsize=8, loc="left")
fig.suptitle("Demodulação síncrona: sensibilidade ao erro de fase da portadora local",
             fontsize=8.5, x=0.02, ha="left")
fig.tight_layout()
fig.savefig("/home/claude/out/am_fig3_fase.png"); plt.close(fig)

# Fig 4 - erro de frequencia: batimento
fig,ax=plt.subplots(figsize=(6.6,2.8))
w4=(t>=0.02)&(t<=0.2)
ax.plot(t[w4], m_norm[w4], color=CZ, lw=1.8, label="mensagem original m(t)")
ax.plot(t[w4], sync_df5[w4], color=VM, lw=0.9, label="síncrona com Δf = 5 Hz")
# a envelope +/- do batimento evidencia o periodo de 1/Δf = 0,2 s
ax.plot(t[w4],  np.abs(np.cos(2*np.pi*5*t[w4]))*1.2, color=VD, lw=1.0, ls=":",
        label="fator de batimento  |cos(2πΔf·t)|")
ax.plot(t[w4], -np.abs(np.cos(2*np.pi*5*t[w4]))*1.2, color=VD, lw=1.0, ls=":")
ax.set_ylim(-3,3)
ax.set_xlabel("Tempo t [s]"); ax.set_ylabel("Amplitude (normalizada)")
ax.legend(fontsize=7, loc="upper right")
ax.set_title("Erro de frequência: o descasamento produz batimento na saída",
             fontsize=8.5, loc="left")
fig.savefig("/home/claude/out/am_fig4_freq.png"); plt.close(fig)

# Fig 5 - sobremodulacao
fig,ax=plt.subplots(1,2,figsize=(6.8,2.9),sharey=True)
w5=(t>=0.05)&(t<=0.11)
for a_,titulo,rec in [(ax[0],"(a) Envoltória",env_over_detect),
                      (ax[1],"(b) Síncrona",sync_over)]:
    a_.plot(t[w5], m_norm[w5], color=CZ, lw=1.6, label="mensagem")
    a_.plot(t[w5], align(rec,m_norm)[w5], color=VM, lw=0.9, label="recuperada")
    a_.set_xlabel("Tempo t [s]"); a_.legend(fontsize=7)
    a_.set_title(titulo, fontsize=8, loc="left")
ax[0].set_ylabel("Amplitude (norm.)")
fig.suptitle("Sobremodulação (ma = 1,5): envoltória distorce, síncrona preserva",
             fontsize=8.5, x=0.02, ha="left")
fig.tight_layout()
fig.savefig("/home/claude/out/am_fig5_sobremod.png"); plt.close(fig)
print("\nfiguras geradas.")
