# -*- coding: utf-8 -*-
"""Le os JSON de resultados e escreve macros LaTeX (numeros.tex) para que texto e figuras batam."""
import json, sys, math

final, f2e1, f1e3, saida = sys.argv[1:5]
F = json.load(open(final, encoding="utf-8"))
E = json.load(open(f2e1, encoding="utf-8"))
P = json.load(open(f1e3, encoding="utf-8"))
L = []


def br(v, d=2):
    if v is None or (isinstance(v, float) and (math.isinf(v) or math.isnan(v))):
        return "---"
    return f"{v:.{d}f}".replace(".", "{,}")


def mac(nome, valor):
    L.append(f"\\newcommand{{\\{nome}}}{{{valor}}}")


# ---- final
mi = F["item5"]
mac("idEss", br(mi["ess"], 2)); mac("idTs", br(mi["ts"], 2)); mac("idOs", br(mi["os"], 1)); mac("idUmax", br(mi["umax"], 1))
re_, me = F["item6"]["real"], F["item6"]["medido"]
mac("reEss", br(re_["ess"], 1)); mac("reOs", br(re_["os"], 0)); mac("reUmax", br(re_["umax"], 1)); mac("reUrip", br(re_["u_rip"], 1))
mac("reYinf", br(re_["yinf"], 2)); mac("meEss", br(me["ess"], 1)); mac("meOs", br(me["os"], 0)); mac("meYinf", br(me["yinf"], 2))
dec = {d["caso"]: d for d in F["item6"]["decomposicao"]}
for chave, nome in (("semS", "sem desvio de S"), ("semRuido", "sem ruído/interferências"),
                    ("semLim", "sem limiar/resolução"), ("soLock", "só o lock-in (fc = 1 Hz)"),
                    ("fcDez", "lock-in com fc = 10 Hz, demais ligadas")):
    d = dec[nome]
    for k, nd in (("ess", 1), ("os", 0), ("umax", 1), ("u_rip", 2), ("ts", 2)):
        mac(f"dec{chave}{k.replace('_', '')}R", br(d["real"][k], nd))
        mac(f"dec{chave}{k.replace('_', '')}M", br(d["medido"][k], nd))
for i, d in enumerate(F["item4"]):
    tag = "abcdef"[i]
    mac(f"maRms{tag}", br(d["erro_rms_cm"], 2)); mac(f"maFim{tag}", br(d["erro_final_pct"], 1))
    mac(f"maRuido{tag}", br(d["ruido_final_cm"] * 10, 2))
pv = F["previsoes"]
mac("prevFc", br(pv["item7a_fc_minimo_para_sobressinal_10pct_Hz"], 1))
mac("prevFcMax", br(pv["item7a_fc_maximo_ripple_1N_Hz"], 1))
mac("prevSlo", br(pv["item7b_faixa_S_sobre_Snom_para_2pct"][0], 3)); mac("prevShi", br(pv["item7b_faixa_S_sobre_Snom_para_2pct"][1], 3))
mac("prevGm", br(pv["item7b_margem_ganho_fc10Hz_S_sobre_Snom"], 2))
mac("prevData", pv["gerado_em"])
j = F["item7"]["janela_fc_Hz"]; mac("simFcLo", br(j[0], 0)); mac("simFcHi", br(j[1], 0))
j = F["item7"]["janela_S_rel"]; mac("simSlo", br(j[0], 2)); mac("simShi", br(j[1], 2))
fcd = {d["fc"]: d for d in F["item7"]["fc"]}
for fc, tag in ((6, "Seis"), (6.5, "SeisMeio"), (7, "Sete"), (15, "Quinze"), (17, "Dezessete"), (5, "Cinco")):
    mac(f"fcOs{tag}", br(fcd[fc]["os"], 1)); mac(f"fcUrip{tag}", br(fcd[fc]["u_rip"], 2))
Sd = {d["S_rel"]: d for d in F["item7"]["S"]}
for s_, tag in ((0.98, "a"), (1.02, "b"), (1.03, "c"), (2.2, "d"), (2.5, "e"), (0.615, "f"), (1.715, "g")):
    mac(f"sEss{tag}", br(Sd[s_]["ess"], 2)); mac(f"sOs{tag}", br(Sd[s_]["os"], 1)); mac(f"sUrip{tag}", br(Sd[s_]["u_rip"], 2))
c8 = F["item8"]["cenarios"]
for i, d in enumerate(c8):
    tag = "abcd"[i]
    for k, nd in (("ess", 2), ("os", 1), ("ts", 2), ("umax", 1), ("u_rip", 2)):
        mac(f"cen{tag}{k.replace('_', '')}", br(d["real"][k], nd))
j = F["item8"]["janela_1Hz"]; mac("corUmLo", br(j[0], 2)); mac("corUmHi", br(j[1], 2))
j = F["item8"]["janela_085Hz"]; mac("corOitoLo", br(j[0], 2)); mac("corOitoHi", br(j[1], 2))
rb = {d["fc"]: d for d in F["item8"]["robustez_1Hz"]}
mac("corUmOsNove", br(rb[0.9]["os"], 1))
rr = {d["caso"]: d for d in F["ruido_residual"]}
mac("ruidoUm", br(rr["fc = 1 Hz"]["desvio_mm"], 3)); mac("ruidoDez", br(rr["fc = 10 Hz"]["desvio_mm"], 3))
mac("ruidoCorr", br(rr["fc = 1 Hz + correção"]["desvio_mm"], 3))
# ---- fase 2 / E01
R4 = {d["grandeza"]: d for d in E["R4"]}
for g, tag in (("Valor final [m]", "Vf"), ("Sobressinal [%]", "Os"), ("Tempo de pico [s]", "Tp"),
               ("Acomodação 2 % [s] (4/ζωn)", "Ts"), ("Período amortecido [s]", "Td"),
               ("ζ (decremento logarítmico)", "Zeta"), ("Pico do pulso [m]", "Pulso")):
    d = R4[g]
    nd = 4 if tag in ("Vf", "Pulso", "Zeta", "Tp", "Td") else 3
    mac(f"rq{tag}A", br(d["algebrica"], nd)); mac(f"rq{tag}S", br(d["simulada"], nd)); mac(f"rq{tag}D", br(d["dif_pct"], 3))
# ---- fase 1 / E03
cm = {d["camada"]: d for d in P["camadas"]}
mac("fiEst", br(cm["estática (S, limiar, resolução)"]["final_N"], 3))
mac("fiEstRms", br(cm["estática (S, limiar, resolução)"]["desvio_rms_N"], 3))
mac("fiDinRms", br(cm["dinâmica sem chopagem (passa-alta)"]["desvio_rms_N"], 3))
mac("fiEspRms", br(cm["espectral (ruído + 60 Hz + offset + deriva)"]["desvio_rms_N"] * 1000, 1))
mac("fiTodas", br(cm["todas (com chopagem)"]["final_N"], 3))
mac("fiPrevObt", br(P["previsao_teste_A1N"]["obtido"], 3))
mac("fiCalC", br(P["c"]["final_cal"], 3))
open(saida, "w", encoding="utf-8").write("\n".join(L) + "\n")
print(len(L), "macros")
