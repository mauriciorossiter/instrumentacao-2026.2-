import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# 1. CONFIGURAÇÕES
# ============================================================

# Nome do arquivo CSV exportado pelo TyphoonSim
ARQUIVO_CSV = "pulso_typhoonsim.csv"

# Pasta onde os gráficos serão salvos
PASTA_SAIDA = Path("resultados_fourier")

# Frequência máxima mostrada nos gráficos do espectro
# Para o nosso pulso de 50 ms, 200 Hz é suficiente
FREQ_MAX_GRAFICO = 200


# ============================================================
# 2. LEITURA DO CSV
# ============================================================

print("=" * 70)
print("ANÁLISE DA TRANSFORMADA DE FOURIER - TYPHOONSIM")
print("=" * 70)

print("\nLendo arquivo...")

df = pd.read_csv(ARQUIVO_CSV)

# Verificação das colunas
if "Time" not in df.columns:
    raise ValueError("A coluna 'Time' não foi encontrada no CSV.")

if "Probe1" not in df.columns:
    raise ValueError("A coluna 'Probe1' não foi encontrada no CSV.")

# Converter para NumPy
t = df["Time"].to_numpy(dtype=float)
x = df["Probe1"].to_numpy(dtype=float)


# ============================================================
# 3. PARÂMETROS DA AQUISIÇÃO
# ============================================================

N = len(x)

# Diferença entre amostras
dt = np.mean(np.diff(t))

# Frequência de amostragem
fs = 1 / dt

# Duração total da janela
T_janela = t[-1] - t[0]

# Resolução espectral
delta_f = fs / N

# Frequência de Nyquist
f_nyquist = fs / 2


print("\n--- PARÂMETROS DA AQUISIÇÃO ---")
print(f"Número de amostras N       = {N:,}")
print(f"Intervalo de amostragem dt = {dt:.3e} s")
print(f"Frequência de amostragem   = {fs:,.2f} Hz")
print(f"Janela de observação       = {T_janela:.6f} s")
print(f"Resolução espectral Δf     = {delta_f:.6f} Hz")
print(f"Frequência de Nyquist      = {f_nyquist:,.2f} Hz")


# ============================================================
# 4. IDENTIFICAÇÃO DO PULSO
# ============================================================

# Consideramos que o pulso é aproximadamente diferente de zero
# e que o restante do sinal está próximo de zero.

amplitude = np.max(np.abs(x))

# Limite para distinguir pulso de zero
limiar = amplitude * 0.5

indices_pulso = np.where(np.abs(x) > limiar)[0]

if len(indices_pulso) == 0:
    raise ValueError("Não foi possível identificar o pulso.")

indice_inicio = indices_pulso[0]
indice_fim = indices_pulso[-1]

t_inicio = t[indice_inicio]
t_fim = t[indice_fim]

# Duração aproximada
tau = t_fim - t_inicio + dt

print("\n--- CARACTERÍSTICAS DO PULSO ---")
print(f"Amplitude A               = {amplitude:.6f}")
print(f"Início do pulso           = {t_inicio:.6f} s")
print(f"Fim do pulso              = {t_fim:.6f} s")
print(f"Duração do pulso τ        = {tau:.6f} s")
print(f"Largura esperada          = {1/tau:.2f} Hz")


# ============================================================
# 5. CRIAÇÃO DA PASTA DE RESULTADOS
# ============================================================

PASTA_SAIDA.mkdir(exist_ok=True)


# ============================================================
# 6. GRÁFICO DO SINAL NO DOMÍNIO DO TEMPO
# ============================================================

plt.figure(figsize=(10, 5))

plt.plot(t, x)

plt.xlabel("Tempo (s)")
plt.ylabel("Amplitude")
plt.title("Pulso retangular capturado no TyphoonSim")
plt.grid(True)

plt.tight_layout()

plt.savefig(
    PASTA_SAIDA / "01_pulso_tempo.png",
    dpi=300
)

plt.show()


# ============================================================
# 7. GRÁFICO AMPLIADO DO PULSO
# ============================================================

# Mostra apenas uma região ao redor do pulso
margem = max(0.01, tau)

t_min_zoom = max(t[0], t_inicio - margem)
t_max_zoom = min(t[-1], t_fim + margem)

indices_zoom = (
    (t >= t_min_zoom) &
    (t <= t_max_zoom)
)

plt.figure(figsize=(10, 5))

plt.plot(
    t[indices_zoom],
    x[indices_zoom]
)

plt.xlabel("Tempo (s)")
plt.ylabel("Amplitude")
plt.title("Detalhe do pulso retangular")
plt.grid(True)

plt.tight_layout()

plt.savefig(
    PASTA_SAIDA / "02_pulso_detalhe.png",
    dpi=300
)

plt.show()


# ============================================================
# 8. FFT
# ============================================================

print("\nCalculando FFT...")

# FFT do sinal
X_fft = np.fft.fft(x)

# Frequências associadas
frequencias = np.fft.fftfreq(N, d=dt)

# ============================================================
# IMPORTANTE:
# A FFT é uma soma discreta.
#
# Para aproximar a Transformada de Fourier contínua:
#
# X(f) ≈ dt * FFT{x[n]}
#
# ============================================================

X_continua = dt * X_fft

# Shift para colocar frequência zero no centro
frequencias_shift = np.fft.fftshift(frequencias)
X_shift = np.fft.fftshift(X_continua)

# Módulo
modulo_X = np.abs(X_shift)


# ============================================================
# 9. ESPECTRO COMPLETO
# ============================================================

plt.figure(figsize=(11, 5))

plt.plot(
    frequencias_shift,
    modulo_X
)

plt.xlabel("Frequência (Hz)")
plt.ylabel(r"$|X(f)|$")
plt.title("Espectro de magnitude - FFT do sinal do TyphoonSim")
plt.grid(True)

plt.xlim(-FREQ_MAX_GRAFICO, FREQ_MAX_GRAFICO)

plt.tight_layout()

plt.savefig(
    PASTA_SAIDA / "03_espectro_fft.png",
    dpi=300
)

plt.show()


# ============================================================
# 10. TRANSFORMADA ANALÍTICA DO PULSO
# ============================================================

# Para um pulso retangular:
#
# X(f) = A * τ * sinc(f * τ)
#
# ATENÇÃO:
# np.sinc(z) = sin(pi*z)/(pi*z)
#
# portanto essa função já corresponde à definição
# normalizada da sinc utilizada na transformada.

frequencias_teoricas = np.linspace(
    -FREQ_MAX_GRAFICO,
    FREQ_MAX_GRAFICO,
    10000
)

X_teorico = (
    amplitude
    * tau
    * np.sinc(frequencias_teoricas * tau)
)

modulo_teorico = np.abs(X_teorico)


# ============================================================
# 11. COMPARAÇÃO FFT × TEORIA
# ============================================================

# Selecionar somente as frequências de interesse
indices_espectro = (
    np.abs(frequencias_shift) <= FREQ_MAX_GRAFICO
)

plt.figure(figsize=(11, 6))

# FFT experimental
plt.plot(
    frequencias_shift[indices_espectro],
    modulo_X[indices_espectro],
    label="FFT - TyphoonSim"
)

# Solução analítica
plt.plot(
    frequencias_teoricas,
    modulo_teorico,
    "--",
    label=r"Teoria: $|A\tau\,sinc(f\tau)|$"
)

plt.xlabel("Frequência (Hz)")
plt.ylabel(r"$|X(f)|$")
plt.title("Comparação entre FFT e Transformada de Fourier analítica")

plt.legend()
plt.grid(True)

plt.xlim(-FREQ_MAX_GRAFICO, FREQ_MAX_GRAFICO)

plt.tight_layout()

plt.savefig(
    PASTA_SAIDA / "04_fft_vs_teoria.png",
    dpi=300
)

plt.show()


# ============================================================
# 12. COMPARAÇÃO SOMENTE DE 0 A 200 Hz
# ============================================================

indices_positivos = (
    (frequencias_shift >= 0) &
    (frequencias_shift <= FREQ_MAX_GRAFICO)
)

plt.figure(figsize=(11, 6))

plt.plot(
    frequencias_shift[indices_positivos],
    modulo_X[indices_positivos],
    label="FFT - TyphoonSim"
)

plt.plot(
    frequencias_teoricas[frequencias_teoricas >= 0],
    modulo_teorico[frequencias_teoricas >= 0],
    "--",
    label="Transformada analítica"
)

plt.xlabel("Frequência (Hz)")
plt.ylabel(r"$|X(f)|$")
plt.title("Espectro de magnitude - região positiva")

plt.legend()
plt.grid(True)

plt.xlim(0, FREQ_MAX_GRAFICO)

plt.tight_layout()

plt.savefig(
    PASTA_SAIDA / "05_espectro_positivo.png",
    dpi=300
)

plt.show()


# ============================================================
# 13. IDENTIFICAÇÃO DOS ZEROS TEÓRICOS
# ============================================================

print("\n--- ZEROS TEÓRICOS DO ESPECTRO ---")

print(
    "Para um pulso retangular, os zeros ocorrem aproximadamente em:"
)

for k in range(1, 6):

    f_zero = k / tau

    print(
        f"k = {k}: f = ±{f_zero:.2f} Hz"
    )


# ============================================================
# 14. VALOR TEÓRICO EM f = 0
# ============================================================

valor_dc_teorico = amplitude * tau

# Procurar a amostra mais próxima de 0 Hz
indice_dc = np.argmin(np.abs(frequencias_shift))

valor_dc_fft = modulo_X[indice_dc]

print("\n--- COMPONENTE EM 0 Hz ---")

print(
    f"Teórico |X(0)| = Aτ = {valor_dc_teorico:.6f}"
)

print(
    f"FFT      |X(0)| = {valor_dc_fft:.6f}"
)


# ============================================================
# 15. RESUMO FINAL
# ============================================================

print("\n" + "=" * 70)
print("RESUMO DA ANÁLISE")
print("=" * 70)

print(f"Amostras:               {N:,}")
print(f"Frequência de amostra:  {fs:,.2f} Hz")
print(f"Janela temporal:        {T_janela:.6f} s")
print(f"Resolução espectral:    {delta_f:.6f} Hz")
print(f"Nyquist:                {f_nyquist:,.2f} Hz")
print(f"Amplitude do pulso:     {amplitude:.6f}")
print(f"Duração do pulso:       {tau:.6f} s")
print(f"Primeiro zero teórico:  ±{1/tau:.2f} Hz")

print("\nGráficos salvos em:")
print(PASTA_SAIDA.resolve())

print("\nAnálise concluída.")