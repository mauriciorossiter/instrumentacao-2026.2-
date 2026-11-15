"""Analisa sinais da mesma rodada do TyphoonSim em metros e segundos físicos."""
import numpy as np


def cruzar(t, x, alvo, sentido):
    i = np.flatnonzero(sentido * (x - alvo) >= 0)
    if not i.size:
        return None
    j = int(i[0])
    if not j or x[j] == x[j-1]:
        return float(t[j])
    return float(t[j-1] + (t[j]-t[j-1]) * (alvo-x[j-1])/(x[j]-x[j-1]))


def medir(t, x, caso):
    inicial = float(np.mean(x[t<0])) if np.any(t<0) else float(x[0])
    sel = t >= 0
    t, x = t[sel], x[sel]
    final = float(np.mean(x[t > t[-1]-60]))
    if caso == "pulso":
        j = int(np.argmax(x))
        alvo = inicial + (x[j] - inicial) * np.array([.1, .5, .9])
        janela = slice(0, j+1)
        marca_t, marca_m = float(t[j]), float(x[j])
    elif caso == "inicial":
        # Esta métrica descreve a recuperação de cada nível até seu próprio patamar.
        alvo = inicial + (final - inicial) * np.array([.1, .5, .9])
        janela = slice(None)
        marca_t, marca_m = 0.0, float(x[0])
    else:
        alvo = inicial + (final - inicial) * np.array([.1, .5, .9])
        janela = slice(None)
        marca_t, marca_m = None, final
    d = 1 if alvo[-1] >= inicial else -1
    valores = [cruzar(t[janela], x[janela], a, d) for a in alvo]
    tr = valores[2] - valores[0] if valores[2] is not None and valores[0] is not None else None
    return {"h_inicial_m": inicial, "h_final_m": final,
            "h_caracteristico_m": marca_m, "t_caracteristico_s": marca_t,
            "t50_s": valores[1], "tempo_10_90_s": tr}


def comparar(t, ref, ideal, real, caso):
    if not np.allclose(ref, ideal, rtol=0, atol=2e-6):
        raise RuntimeError(f"Ideal difere da referência em {np.max(np.abs(ref-ideal))*1000:g} mm")
    ativo = t >= 0
    linhas = {}
    for j in range(2):
        a, b = ref[:,j], real[:,j]
        erro = (b-a)[ativo]
        va, vb = medir(t,a,caso), medir(t,b,caso)
        ca, cb = va["t50_s"], vb["t50_s"]
        linhas["h"+str(j+1)] = {
            "ideal": va, "real": vb,
            "erro_max_mm": 1000 * float(np.max(np.abs(erro))),
            "erro_rel_max_pct": 100 * float(np.max(np.abs(erro)/np.abs(a[ativo]))),
            "rmse_mm": 1000 * float(np.sqrt(np.mean(erro**2))),
            "erro_final_mm": 1000 * (vb["h_final_m"] - va["h_final_m"]),
            "atraso_50_s": cb-ca if ca is not None and cb is not None else None,
        }
    return linhas
