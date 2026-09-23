# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Capitulo 5, Secao 5.4.3
Funcoes de densidade espectral de potencia -- analise e figuras do relatorio.

Reaproveita o arquivo de dados JA ENTREGUE no Capitulo 3 (Secao 3.3, Limiar):
  ../../e3-geracao-dados/dados/Equipe_08_Limiar.csv
Nao gera nenhum dado novo no TyphoonSim (conforme Orientacao - Cap. 5, item 4).

Sinal de "ruido" analisado:
  e[n] = y_instrumento[n] - x_referencia[n]
isto e', o desvio entre a leitura do instrumento e a grandeza de referencia
conhecida (livre de ruido) que a excitou -- o "erro do canal de medicao" no
instante n. E' o unico sinal de ruido diretamente extraivel deste dataset,
ja que o proprio arquivo não contem uma coluna de ruido isolado.

Produz:
  figs/sinal_erro_tempo.pdf         e[n] no dominio do tempo (registro completo)
  figs/autocorrelacao.pdf           autocorrelacao amostral de e[n]
  figs/periodograma_welch.pdf       periodograma bruto x metodo de Welch
  figs/wiener_khinchin.pdf          FT{autocorrelacao} sobreposta ao periodograma
  figs/repouso_subserie.pdf         subserie em x=0 (repouso), 30 realizacoes
  resultados_dsp.json               todos os numeros citados no relatorio
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import signal
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

AQUI = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(AQUI, '..', '..', 'e3-geracao-dados', 'dados', 'Equipe_08_Limiar.csv')
FIG = os.path.join(AQUI, '..', 'DensidadeEspectral_Latex', 'figs')
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({'font.size': 10, 'axes.grid': True, 'grid.alpha': .3,
                      'figure.dpi': 160, 'savefig.bbox': 'tight',
                      'axes.spines.top': False, 'axes.spines.right': False})
AZUL = '#1f4e79'
CINZA = '#888888'
VERM = '#a83232'

# ---------------------------------------------------------------------------
# 0. Carga dos dados (Equipe 08, Capitulo 3, caracteristica "Limiar")
# ---------------------------------------------------------------------------
df = pd.read_csv(CSV)
FS = 60.0                       # Hz, taxa de amostragem do ensaio (metadados Cap. 3)
N_STEPS = 100                    # passos por varredura (protocolo Limiar)
PASSOS = N_STEPS + 1             # 101 amostras por varredura
M_SWEEPS = len(df) // PASSOS
assert len(df) == M_SWEEPS * PASSOS

t = df['tempo'].to_numpy()
x = df['x_referencia'].to_numpy()
y = df['y_instrumento'].to_numpy()
e = y - x                        # sinal de erro/ruido do canal
N = len(e)

resultados = {}
resultados['dataset_origem'] = 'Equipe_08_Limiar.csv (Capitulo 3, Secao 3.3, Equipe 08)'
resultados['Fs_Hz'] = FS
resultados['N_amostras'] = int(N)
resultados['M_varreduras'] = int(M_SWEEPS)
resultados['amostras_por_varredura'] = int(PASSOS)
resultados['duracao_total_s'] = float(N / FS)

# ---------------------------------------------------------------------------
# 1. Estatisticas descritivas do sinal de erro e[n]
# ---------------------------------------------------------------------------
resultados['e_media'] = float(np.mean(e))
resultados['e_desvio_padrao'] = float(np.std(e, ddof=1))
resultados['e_min'] = float(np.min(e))
resultados['e_max'] = float(np.max(e))

fig, ax = plt.subplots(figsize=(7.2, 3.6))
ax.plot(t, e, lw=0.6, color=AZUL)
ax.axhline(0, color=CINZA, lw=0.8, ls='--')
ax.set_xlabel('tempo  [s]')
ax.set_ylabel(r'$e[n] = y_{\mathrm{instrumento}} - x_{\mathrm{referencia}}$  [graus]')
ax.set_title('Sinal de erro do canal de medição — registro completo (30 varreduras)')
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'sinal_erro_tempo.pdf'))
plt.close(fig)

# ---------------------------------------------------------------------------
# 2. Autocorrelacao amostral (estimador enviesado, forma classica de livro-texto)
#    R[k] = (1/N) sum_n e[n] e[n+k]
# ---------------------------------------------------------------------------
MAXLAG = 250
e0 = e - np.mean(e)
autocorr_full = np.correlate(e0, e0, mode='full') / N
mid = len(autocorr_full) // 2
R = autocorr_full[mid:mid + MAXLAG + 1]
rho = R / R[0]

bound = 1.96 / np.sqrt(N)        # banda de 95% para ruido branco (lags > 0)
lags_fora = int(np.sum(np.abs(rho[1:]) > bound))
resultados['acf_banda_95_branco'] = float(bound)
resultados['acf_lags_fora_da_banda_ate_250'] = lags_fora
resultados['acf_rho_lag1'] = float(rho[1])
resultados['acf_primeiro_lag_dentro_da_banda'] = int(np.argmax(np.abs(rho[1:]) < bound) + 1)

fig, ax = plt.subplots(figsize=(7.2, 3.8))
lags = np.arange(MAXLAG + 1)
ax.stem(lags, rho, linefmt=AZUL, markerfmt=' ', basefmt=CINZA)
ax.axhline(bound, color=VERM, lw=0.9, ls='--', label=r'banda 95% ($\pm 1{,}96/\sqrt{N}$)')
ax.axhline(-bound, color=VERM, lw=0.9, ls='--')
ax.set_xlabel('atraso $k$  [amostras]')
ax.set_ylabel(r'$\hat\rho[k] = \hat R[k]/\hat R[0]$')
ax.set_title('Autocorrelação amostral normalizada de $e[n]$')
ax.legend(loc='upper right', fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'autocorrelacao.pdf'))
plt.close(fig)

# ---------------------------------------------------------------------------
# 3. Periodograma bruto x metodo de Welch
# ---------------------------------------------------------------------------
f_pgram, Pxx_pgram = signal.periodogram(e0, fs=FS, window='boxcar', scaling='density')
NPERSEG = 256
NOVERLAP = 128
f_welch, Pxx_welch = signal.welch(e0, fs=FS, window='hann', nperseg=NPERSEG,
                                   noverlap=NOVERLAP, scaling='density')
n_segmentos = int(np.floor((N - NOVERLAP) / (NPERSEG - NOVERLAP)))
resultados['welch_nperseg'] = NPERSEG
resultados['welch_noverlap'] = NOVERLAP
resultados['welch_n_segmentos'] = n_segmentos
resultados['welch_resolucao_Hz'] = float(FS / NPERSEG)
resultados['pgram_resolucao_Hz'] = float(FS / N)

def flatness(Pxx):
    Pxx = Pxx[Pxx > 0]
    return float(np.exp(np.mean(np.log(Pxx))) / np.mean(Pxx))

resultados['spectral_flatness_periodograma'] = flatness(Pxx_pgram[1:])
resultados['spectral_flatness_welch'] = flatness(Pxx_welch[1:])

# picos espectrais mais proeminentes no espectro de Welch (excluindo DC)
idx_sorted = np.argsort(Pxx_welch[1:])[::-1] + 1
top_picos = [(float(f_welch[i]), float(Pxx_welch[i])) for i in idx_sorted[:5]]
resultados['welch_top5_picos_Hz_potencia'] = top_picos
resultados['welch_potencia_media_faixa_alta'] = float(
    np.mean(Pxx_welch[f_welch > 10.0]))
resultados['welch_potencia_media_faixa_baixa'] = float(
    np.mean(Pxx_welch[(f_welch > 0) & (f_welch < 2.0)]))

fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.semilogy(f_pgram, Pxx_pgram, color=CINZA, lw=0.7, alpha=.8, label='periodograma bruto')
ax.semilogy(f_welch, Pxx_welch, color=AZUL, lw=1.6, label='Welch (%d segmentos, %d amostras/seg.)' %
            (n_segmentos, NPERSEG))
ax.set_xlabel('frequência  [Hz]')
ax.set_ylabel(r'DEP  [graus$^2$/Hz]')
ax.set_title('Densidade espectral de potência de $e[n]$ — periodograma × Welch')
ax.legend(loc='upper right', fontsize=8)
ax.set_xlim(0, FS / 2)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'periodograma_welch.pdf'))
plt.close(fig)

# ---------------------------------------------------------------------------
# 4. Verificacao numerica do teorema de Wiener-Khinchin via estimador de
#    Blackman-Tukey: S_BT(f) = FT{ w[k] . R[k] }, k=-M..M, com R[k] a MESMA
#    autocorrelacao amostral do item 2 (dominio do tempo, calculo
#    independente do periodograma/Welch, que trabalham direto sobre e[n]).
#    Comparar S_BT(f) com o periodograma e com Welch fecha o ciclo
#    tempo -> frequencia -> tempo pedido pela Orientacao.
# ---------------------------------------------------------------------------
M = 200                                    # atraso maximo mantido na janela (< N/10)
R_trunc = R[:M + 1]                        # reaproveita R[k] ja calculado no item 2
lag_window = np.hanning(2 * M + 1)         # janela de atraso (Blackman-Tukey classico)
R_sym = np.concatenate([R_trunc[::-1][:-1], R_trunc])   # k = -M..M
R_janelada = R_sym * lag_window

NFFT = 4096
S_BT_full = np.fft.rfft(np.fft.ifftshift(R_janelada), n=NFFT) / FS
S_BT = np.abs(S_BT_full)
f_BT = np.fft.rfftfreq(NFFT, d=1.0 / FS)

fig, ax = plt.subplots(figsize=(7.2, 4.2))
ax.semilogy(f_pgram, Pxx_pgram, color=CINZA, lw=0.6, alpha=.55, label='periodograma bruto de $e[n]$')
ax.semilogy(f_welch, Pxx_welch, color=AZUL, lw=1.5, label='Welch (média de %d segmentos)' % n_segmentos)
ax.semilogy(f_BT, S_BT, color=VERM, lw=1.3, ls='--',
            label=r'Blackman--Tukey: $\mathcal{F}\{w[k]\,\hat R[k]\}$, $M=%d$' % M)
ax.set_xlabel('frequência  [Hz]')
ax.set_ylabel(r'DEP  [graus$^2$/Hz]')
ax.set_title('Verificação de Wiener–Khinchin: $S(f)=\\mathcal{F}\\{R[k]\\}$ (três estimadores independentes)')
ax.legend(loc='upper right', fontsize=8)
ax.set_xlim(0, FS / 2)
fig.tight_layout()
fig.savefig(os.path.join(FIG, 'wiener_khinchin.pdf'))
plt.close(fig)

# concordancia grosseira entre Welch e Blackman-Tukey (mesma resolucao efetiva)
S_BT_interp = np.interp(f_welch, f_BT, S_BT)
corr_welch_bt = float(np.corrcoef(np.log(S_BT_interp + 1e-12), np.log(Pxx_welch + 1e-12))[0, 1])
resultados['wiener_khinchin_M_lags'] = M
resultados['wiener_khinchin_correlacao_log_welch_x_BT'] = corr_welch_bt

# ---------------------------------------------------------------------------
# 5. Subserie em repouso (x_referencia = 0): 30 realizacoes independentes de
#    ruido, uma por varredura -- amostragem "lenta" (uma amostra por sweep)
# ---------------------------------------------------------------------------
idx_repouso = np.arange(0, N, PASSOS)     # k=0 de cada varredura
e_repouso = e[idx_repouso]
Fs_repouso = FS / PASSOS

resultados['repouso_N'] = int(len(e_repouso))
resultados['repouso_Fs_Hz'] = float(Fs_repouso)
resultados['repouso_media'] = float(np.mean(e_repouso))
resultados['repouso_desvio_padrao'] = float(np.std(e_repouso, ddof=1))

er0 = e_repouso - np.mean(e_repouso)
Nr = len(er0)
acr_full = np.correlate(er0, er0, mode='full') / Nr
midr = len(acr_full) // 2
Rr = acr_full[midr:midr + 10]
rho_r = Rr / Rr[0]
bound_r = 1.96 / np.sqrt(Nr)
resultados['repouso_acf_banda_95'] = float(bound_r)
resultados['repouso_acf_lag1'] = float(rho_r[1])
resultados['repouso_fora_da_banda'] = int(np.sum(np.abs(rho_r[1:]) > bound_r))

f_r, Pxx_r = signal.periodogram(er0, fs=Fs_repouso, window='boxcar', scaling='density')
resultados['repouso_flatness'] = flatness(Pxx_r[1:]) if len(Pxx_r) > 2 else None

fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.4))
axes[0].plot(np.arange(Nr), e_repouso, 'o-', ms=4, lw=0.9, color=AZUL)
axes[0].axhline(np.mean(e_repouso), color=CINZA, ls='--', lw=0.8)
axes[0].set_xlabel('índice da varredura $m$')
axes[0].set_ylabel(r'$e[m\cdot 101]$  [graus]')
axes[0].set_title('(a) repouso, 30 realizações')

axes[1].stem(np.arange(10), rho_r, linefmt=AZUL, markerfmt=' ', basefmt=CINZA)
axes[1].axhline(bound_r, color=VERM, ls='--', lw=0.9)
axes[1].axhline(-bound_r, color=VERM, ls='--', lw=0.9)
axes[1].set_xlabel('atraso $k$ [varreduras]')
axes[1].set_ylabel(r'$\hat\rho[k]$')
axes[1].set_title('(b) autocorrelação (repouso)')

axes[2].plot(f_r, Pxx_r, 'o-', ms=4, lw=0.9, color=AZUL)
axes[2].set_xlabel('frequência [Hz]')
axes[2].set_ylabel(r'DEP [graus$^2$/Hz]')
axes[2].set_title('(c) periodograma (repouso)')

fig.tight_layout()
fig.savefig(os.path.join(FIG, 'repouso_subserie.pdf'))
plt.close(fig)

# ---------------------------------------------------------------------------
# 6. Parametros de projeto do canal simulado (conhecidos pela Equipe 08 por
#    ser a equipe geradora -- usados aqui apenas como referencia de validacao,
#    NAO como atalho para o exercicio de limiar/resolucao de outras equipes)
# ---------------------------------------------------------------------------
Q_DEG = 360.0 / 2**12
SIGMA_DEG = 0.02
DELTA_X = Q_DEG / 10.0
resultados['ref_projeto_quantum_Q_deg'] = Q_DEG
resultados['ref_projeto_sigma_ruido_deg'] = SIGMA_DEG
resultados['ref_projeto_incremento_x_deg'] = DELTA_X
resultados['ref_projeto_amostras_por_quantum'] = float(Q_DEG / DELTA_X)
resultados['ref_projeto_freq_cruzamento_quantum_Hz'] = float(FS / (Q_DEG / DELTA_X))
resultados['ref_projeto_freq_repeticao_varredura_Hz'] = float(FS / PASSOS)
resultados['ref_projeto_var_quantizacao_teorica'] = float(Q_DEG**2 / 12)
resultados['ref_projeto_var_ruido_teorica'] = float(SIGMA_DEG**2)

with open(os.path.join(AQUI, 'resultados_dsp.json'), 'w', encoding='utf-8') as fp:
    json.dump(resultados, fp, indent=2, ensure_ascii=False)

print('OK - figuras em', FIG)
print('OK - resultados em', os.path.join(AQUI, 'resultados_dsp.json'))
for k, v in resultados.items():
    print(' ', k, '=', v)
