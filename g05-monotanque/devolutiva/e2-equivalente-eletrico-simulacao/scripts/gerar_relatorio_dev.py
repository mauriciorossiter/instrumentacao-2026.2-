# -*- coding: utf-8 -*-
# Relatorio da devolutiva da Fase 2 / Entrega 02 (G05, Monotanque): equivalente eletrico v2.
# Le 4_dados/resultados_dev.json e as figuras de 2_entrega/relatorio/figuras.
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image as PI
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIG = os.path.join(BASE, "2_entrega", "relatorio", "figuras")
OUT = os.path.join(BASE, "2_entrega", "devolutiva", "e2-equivalente-eletrico.pdf")
EQD = os.path.join(os.environ.get("TEMP", HERE), "eq_rel_dev"); os.makedirs(EQD, exist_ok=True)
R = json.load(open(os.path.join(BASE, "4_dados", "resultados_dev.json"), encoding="utf-8"))
PR = R["param"]

F = "C:/Windows/Fonts/"
for n, f_ in [("TNR", "times.ttf"), ("TNR-B", "timesbd.ttf"), ("TNR-I", "timesi.ttf"), ("TNR-BI", "timesbi.ttf")]:
    pdfmetrics.registerFont(TTFont(n, F + f_))
registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")
body = ParagraphStyle("body", fontName="TNR", fontSize=10.3, leading=13.2, alignment=TA_JUSTIFY, spaceAfter=4)
h1 = ParagraphStyle("h1", fontName="TNR-B", fontSize=12.5, leading=15, spaceBefore=9, spaceAfter=4, keepWithNext=1)
h2 = ParagraphStyle("h2", fontName="TNR-B", fontSize=10.6, leading=13, spaceBefore=5, spaceAfter=2, keepWithNext=1)
title = ParagraphStyle("t", fontName="TNR", fontSize=17, leading=21, alignment=TA_CENTER)
subt = ParagraphStyle("s", fontName="TNR-I", fontSize=10.3, leading=13, alignment=TA_CENTER)
cell = ParagraphStyle("cell", fontName="TNR", fontSize=9.2, leading=11.4, alignment=TA_CENTER)
cellL = ParagraphStyle("cellL", parent=cell, alignment=0)
cellH = ParagraphStyle("cellH", parent=cell, fontName="TNR-B")
cap = ParagraphStyle("c", fontName="TNR", fontSize=8.9, leading=10.8, alignment=TA_CENTER, spaceBefore=2, spaceAfter=6)
item = ParagraphStyle("item", parent=body, leftIndent=14, firstLineIndent=-10, spaceAfter=2)
W = 17.0 * cm
SB = '<sub rise="2" size="7">'


def f(v, d=2):
    if v is None or v != v:
        return "—"
    v = 0.0 if abs(v) < 0.5 * 10 ** -d else v
    return f"{v:,.{d}f}".replace(",", " ").replace(".", ",").replace("-", "−")


def dif(x, ref, d=2):
    return f(100 * (x - ref) / ref, d) + " %"


def P(t, st=body):
    return Paragraph(str(t).replace("<sub>", SB), st)


NT = [0]


def tabela(rows, widths, left_cols=(0,), cap_txt=None):
    data = [[P(cc, cellH if i == 0 else (cellL if j in left_cols else cell)) for j, cc in enumerate(r)]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="CENTER", repeatRows=1)
    t.setStyle(TableStyle([("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black),
                           ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black),
                           ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 2),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    NT[0] += 1
    return KeepTogether([P(f"<b>Tabela {NT[0]}:</b> {cap_txt}", cap), t, Spacer(1, 6)])


NF = [0]


def figura(nome, legenda, w=W):
    NF[0] += 1
    p = os.path.join(FIG, nome)
    iw, ih = PI.open(p).size
    return KeepTogether([Image(p, width=w, height=w * ih / iw), P(f"<b>Figura {NF[0]}:</b> {legenda}", cap)])


NE = [0]


def eq(tex, h=0.42 * cm):
    NE[0] += 1
    p = os.path.join(EQD, f"eq{NE[0]}.png")
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, "$" + tex.replace(r"\frac", r"\dfrac") + "$", fontsize=13, math_fontfamily="stix")
    fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.02, transparent=True)
    plt.close(fig)
    iw, ih = PI.open(p).size
    hh = h * ih / 52
    if hh * iw / ih > W - 1.4 * cm:
        hh = (W - 1.4 * cm) * ih / iw
    t = Table([[Image(p, width=hh * iw / ih, height=hh), P(f"({NE[0]})", ParagraphStyle("n", parent=body,
                                                                                         alignment=2))]],
              colWidths=[W - 1.2 * cm, 1.2 * cm])
    t.setStyle(TableStyle([("ALIGN", (0, 0), (0, 0), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return KeepTogether([Spacer(1, 2), t, Spacer(1, 3)])


st = []
st += [P("Equivalente elétrico do Monotanque no TyphoonSim", title), Spacer(1, 3),
       P("ECOM060 – Instrumentação Eletrônica · Fase 2, Entrega 02 (versão final) · UFAL 2026.2", subt),
       P("Prof. Maurício Beltrão Rossiter", subt),
       P("Equipe G05: Carlos Vinicius, Pedro Resende e Nelson Moreira", subt), Spacer(1, 8)]
pol = PR["polos"]
OP, LI, BO, IN, V, AR, KK = R["op"], R["lin"], R["bode"], R["inercia"], R["val"], R["area"], R["k"]
st.append(P("<b>Ponto de partida.</b> O modelo, os parâmetros e os resultados da Entrega 01 são a referência: "
            "A dh/dt = q<sub>i</sub> − k√h − q<sub>d</sub>, com A = 0,50 m², k = 0,010 m²·⁵/s, h<sub>0</sub> = 0,50 m e "
            "q<sub>i0</sub> = k√h<sub>0</sub> = 7,071 L/s; constante de tempo local τ = 2A√h<sub>0</sub>/k = 70,71 s. "
            "O equivalente foi construído a partir da física do escoamento: o que guarda a água (o tanque), o que a "
            "empurra para fora (a pressão da coluna), o que a freia (a resistência ao escoamento) e o que a faz resistir a "
            "mudar de velocidade (a massa de água no tubo de saída). Cada efeito tem um elemento elétrico próprio. Os "
            "ensaios foram executados no HIL virtual (VHIL) do TyphoonSim com o painel SCADA e sobrepostos à Entrega 01 e "
            "ao modelo de referência resolvido em Python (SciPy). Arquivos: pasta <i>devolutiva/e2-equivalente-eletrico-simulacao/</i> (modelo .tse, painel "
            ".cus e <i>instrucoes.md</i>)."))

# ====================================================================================== R1
st.append(P("R1. Analogia e escalonamento", h1))
st.append(P("(a) Modelo físico e correspondência entre os domínios", h2))
st.append(P("O tanque é regido pela conservação da massa. A água que está <i>dentro do tubo de saída</i> tem massa "
            "ρ·l·a e é acelerada pela diferença entre a pressão no fundo do tanque (ρgh) e a pressão perdida no "
            "orifício: é a segunda lei de Newton aplicada à coluna de líquido. Dividindo por ρga, tudo fica em metros de "
            "coluna d’água (o último termo é a perda no orifício):"))
st.append(eq(r"A\,\frac{dh}{dt}=q_i-q-q_d \qquad\qquad I_h\,\frac{dq}{dt}=h-\frac{q\,|q|}{k^2},\qquad "
             r"I_h=\frac{l}{g\,a}", h=0.6 * cm))
st.append(P(f"Em regime (dq/dt = 0) a segunda equação dá q = k√h, a lei de Torricelli da Entrega 01, que é o caso "
            f"limite sem inércia. Com C<sub>d</sub> = 0,60, o orifício tem área a = k/(C<sub>d</sub>√(2g)) = "
            f"{f(PR['a_or'] * 1e4, 1)} cm² (d = {f(PR['d_or'] * 100, 1)} cm); um tubo de saída de l = {f(PR['l_tubo'], 0)} m "
            f"(estimativa da equipe: o dossiê não informa o comprimento) tem inertância I<sub>h</sub> = l/(g·a) = "
            f"{f(PR['I_h'], 1)} s²/m². O escoamento é turbulento (Re = {f(PR['Re'], 0)}), por isso a perda é quadrática na "
            "vazão e já inclui o atrito do tubo curto (k é o coeficiente agregado da E01)."))
st.append(P("Na analogia adotada, a variável de esforço é a que se iguala entre elementos em paralelo e a de fluxo é a "
            "que se soma num nó: nível (pressão ρgh) ↔ tensão e vazão ↔ corrente (Tabela 1, Figura 1)."))
st.append(tabela([
    ["Papel", "Hidráulico", "Elétrico", "Elemento no TyphoonSim"],
    ["Esforço", "nível h (pressão ρgh)", "tensão v", "Voltage Measurement"],
    ["Fluxo", "vazão q", "corrente i", "Current Measurement"],
    ["Armazena energia potencial", "tanque: V = A·h", "capacitância: Q = C·v", "Capacitor"],
    ["Armazena energia cinética", "massa no tubo: I<sub>h</sub> = l/(g·a)", "indutância: v = L·di/dt", "Inductor"],
    ["Dissipa energia", "orifício: h = q|q|/k²", "resistência de saída R + e(i)",
     "Resistor + Signal Controlled Voltage Source"],
    ["Fonte manipulada", "bomba q<sub>i</sub>", "fonte de corrente", "Signal Controlled Current Source"],
    ["Fonte de distúrbio", "consumo q<sub>d</sub>", "fonte de corrente", "Signal Controlled Current Source"]],
    [3.8 * cm, 4.2 * cm, 4.2 * cm, 4.8 * cm], left_cols=(0,), cap_txt="Analogia tanque ↔ circuito."))
st.append(P("A bomba é uma fonte de corrente por razão física: a água entra por cima e cai livre na superfície, então a "
            "vazão da bomba não sente o nível (a fonte ideal de corrente é o elemento cuja corrente não depende da "
            "tensão). O consumo q<sub>d</sub> é tratado como uma bomba dosadora, pelo mesmo motivo."))
st.append(figura("fig-01-tanque-e-circuito-v2.png", "O tanque com tubo de saída e o circuito equivalente: capacitor "
                 "(tanque), indutor (inércia da água no tubo), resistor (escoamento) e a fonte da parte não linear do "
                 "orifício."))
st.append(P("(b) Equações do circuito e equivalência com a Entrega 01", h2))
st.append(P("A lei das correntes no nó do nível e a lei das tensões no ramo de saída dão:"))
st.append(eq(r"C\,\frac{dv}{dt_c}=i_i-i_o-i_d \qquad\qquad L\,\frac{di_o}{dt_c}=v-R\,i_o-e(i_o)", h=0.5 * cm))
st.append(P("Com v = k<sub>v</sub>h, i = k<sub>i</sub>q e t = k<sub>t</sub>t<sub>c</sub>, as duas equações viram as "
            "Equações (1), sem aproximação, desde que C = A·k<sub>i</sub>/(k<sub>v</sub>k<sub>t</sub>), "
            "L = I<sub>h</sub>·k<sub>v</sub>/(k<sub>i</sub>k<sub>t</sub>) e R·i + e(i) = i|i|/K<sub>e</sub>², com "
            "K<sub>e</sub> = k·k<sub>i</sub>/√k<sub>v</sub>. A resistência de saída foi separada em uma parte linear, "
            "que é um resistor do circuito, e uma parte que só existe porque o orifício não é linear (R·i é o resistor; "
            "e(i) é a fonte comandada):"))
st.append(eq(r"v_{or}(i)=\frac{i\,|i|}{K_e^2}=R\,i+e(i),\qquad e(i)=\frac{i\,|i|}{K_e^2}-R\,i,\qquad "
             r"R=\frac{2\sqrt{V_0}}{K_e}=1{,}414\ \Omega", h=0.6 * cm))
st.append(P("R é a resistência incremental do orifício no ponto de operação (a resistência de escoamento turbulento, "
            "R = 2h<sub>0</sub>/q<sub>0</sub>), e é ela que decide a constante de tempo. A fonte e(i) corrige o que a reta "
            "não acompanha: vale −5 V em 0,5 m e varia pouco perto do equilíbrio. No painel, a opção <i>linearizado</i> "
            "troca e(i) pela tangente em h<sub>op</sub>, e então <b>só o resistor</b> faz o papel do orifício, como no "
            "modelo linear clássico de nível (Ogata, cap. 4)."))
st.append(P("(c) Fatores de escala e faixas", h2))
st.append(tabela([
    ["Fator", "Valor", "Leitura", "Justificativa"],
    ["k<sub>v</sub> (nível → tensão)", "10 V/m", "1 V = 10 cm", "0,10–1,20 m vira 1–12 V, a faixa (±10 V) dos sinais "
                                                                  "de instrumentação e das entradas analógicas de HIL"],
    ["k<sub>i</sub> (vazão → corrente)", "1000 A/(m³/s)", "1 A = 1 L/s", "o painel lê L/s direto nos amperímetros"],
    ["k<sub>t</sub> (tempo)", "100", "1 s = 100 s", "τ = 70,7 s vira 0,707 s: um ensaio cabe numa demonstração ao "
                                                    "vivo; o passo de 20 µs equivale a 2 ms no tanque"]],
    [3.6 * cm, 2.4 * cm, 2.2 * cm, 8.8 * cm], left_cols=(0, 3), cap_txt="Fatores de escala."))
st.append(tabela([
    ["Variável", "Faixa no tanque", "Faixa no circuito", "Observação"],
    ["nível h ↔ tensão no capacitor", "0,10 a 1,20 m (2,0 m no ensaio de k)", "1 a 12 V (20 V)",
     "acima de 12 V o tanque transbordaria"],
    ["bomba q<sub>i</sub>", "0 a 40 L/s", "0 a 40 A", "40 A só na preparação; nominal 7,071 A"],
    ["saída q (corrente no indutor)", "0 a 11 L/s", "0 a 11 A", "q = k√h em regime"],
    ["parte não linear e(i)", "—", "−5 a 0 V", "mínimo −5 V em 7,07 A; 0 V em 0 A"],
    ["consumo q<sub>d</sub>", "−5 a 20 L/s", "−5 a 20 A", "padrão 0"],
    ["tempo dos ensaios", "350 a 2000 s", "3,5 a 20 s", "início do ensaio em 100 s ↔ 1 s"]],
    [4.4 * cm, 4.2 * cm, 3.0 * cm, 5.4 * cm], left_cols=(0, 3), cap_txt="Faixas de tensão e corrente."))
st.append(P("(d) Parâmetros do circuito", h2))
st.append(eq(r"C=\frac{k_i}{k_v k_t}A=0{,}5\ \mathrm{F},\qquad L=\frac{k_v}{k_i k_t}I_h="
             + f"{PR['L'] * 1000:.2f}".replace(".", "{,}") + r"\ \mathrm{mH},\qquad K_e=\frac{k_i}{\sqrt{k_v}}k="
             r"3{,}162\ \mathrm{A/\sqrt{V}},\qquad V_0=5\ \mathrm{V},\quad I_0=7{,}071\ \mathrm{A}", h=0.55 * cm))
st.append(P("(e) Ganho estático, polos e constantes de tempo", h2))
st.append(P("Linearizando em h<sub>0</sub>, o circuito é um RLC; o nível e a vazão de saída respondem à bomba por"))
st.append(eq(r"\frac{H(s)}{Q_i(s)}=\frac{R+I_h s}{A I_h s^2+A R s+1},\qquad \frac{Q_o(s)}{Q_i(s)}="
             r"\frac{1}{A I_h s^2+A R s+1},\qquad \omega_n=\frac{1}{\sqrt{A I_h}},\quad \zeta=\frac{R}{2}"
             r"\sqrt{\frac{A}{I_h}}", h=0.6 * cm))
st.append(tabela([
    ["Grandeza", "Entrega 01 (R2)", "Circuito, convertido ao tanque", "No circuito"],
    ["Ganho estático (nível)", "141,4 s/m²", "141,4 s/m² (× k<sub>i</sub>/k<sub>v</sub>)", "R = 1,414 Ω"],
    ["Polo do tanque", "−0,01414 s⁻¹", f"{f(pol[1], 5)} s⁻¹ (÷ k<sub>t</sub>)", f"{f(pol[1] * 100, 3)} rad/s"],
    ["Constante de tempo dominante", "70,71 s", f"{f(-1 / pol[1], 2)} s (× k<sub>t</sub>)", f"{f(-1 / pol[1] / 100, 4)} s"],
    ["Polo da inércia", "— (desprezada)", f"{f(pol[0], 3)} s⁻¹", f"{f(pol[0] * 100, 1)} rad/s"],
    ["Zero do nível", "—", f"{f(PR['zero'], 3)} s⁻¹", f"{f(PR['zero'] * 100, 1)} rad/s"],
    ["Frequência natural ω<sub>n</sub>", "—", f"{f(PR['wn'], 4)} rad/s", f"{f(PR['wn'] * 100, 2)} rad/s"],
    ["Amortecimento ζ", "—", f"{f(PR['zeta'], 2)}", f"{f(PR['zeta'], 2)}"]],
    [4.6 * cm, 3.4 * cm, 5.0 * cm, 4.0 * cm], cap_txt="Ganho, polos e constantes de tempo (linearização em 0,5 m)."))
st.append(P(f"Com ζ ≈ {f(PR['zeta'], 1)} o sistema é fortemente sobreamortecido: o polo da inércia é "
            f"{f(pol[0] / pol[1], 0)} vezes mais rápido que o do tanque e o zero do nível praticamente o cancela. O polo "
            f"dominante fica {f(100 * (pol[1] / -0.0141421 - 1), 2)} % mais rápido que o da E01, e é essa a diferença "
            "esperada nos tempos característicos. A hipótese da E01 de que a inércia não pesa no nível fica confirmada com "
            "números; a inércia continua visível na vazão de saída (R3) e domina se o tubo for longo (R4)."))
st.append(P("Como o orifício não é linear, R e τ dependem do ponto de operação. A Figura 2 mostra a característica "
            "tensão × corrente da saída medida no circuito e a resistência em função do nível, e a Tabela 6 dá os "
            "valores em cinco pontos."))
st.append(figura("fig-02-caracteristica-resistencia.png", "Esquerda: corrente na saída em função da tensão do "
                 "capacitor, medida durante a drenagem livre, com os pontos de equilíbrio e a reta do resistor. "
                 "Direita: resistências secante e incremental; os quadrados são Δh/Δq medidos com degraus de 2 %."))
st.append(tabela([["h<sub>op</sub> [m]", "q [L/s]", "R<sub>secante</sub> [s/m²]", "R incremental teórica [s/m²] (Ω)",
                   "Δh/Δq VHIL [s/m²]", "τ = A·R [s]", "t<sub>63</sub> VHIL [s]", "ζ"]] +
                 [[f(o["h"], 2), f(o["q"], 2), f(o["R_sec"], 1), f"{f(o['R_inc'], 1)} ({f(o['R_ohm'], 3)})",
                   f(o["R_vhil"], 1), f(o["tau_lin"], 1), f(o["t63_vhil"], 1), f(o["zeta"], 1)] for o in OP],
                 [1.6 * cm, 1.5 * cm, 2.0 * cm, 3.3 * cm, 2.3 * cm, 1.8 * cm, 2.1 * cm, 1.2 * cm],
                 left_cols=(), cap_txt="Resistência de escoamento e constante de tempo em cinco pontos de operação."))
st.append(P(f"A curva medida coincide com q = k√h em toda a faixa, de 1,2 m ao tanque vazio. A resistência incremental "
            f"cresce com √h, de {f(OP[0]['R_inc'], 0)} s/m² em 0,2 m a {f(OP[-1]['R_inc'], 0)} s/m² em 1,1 m; por isso um "
            f"único resistor representa o orifício só perto de um nível, e τ = A·R vai de {f(OP[0]['tau_lin'], 0)} s a "
            f"{f(OP[-1]['tau_lin'], 0)} s na faixa de operação (Figura 3). Os valores Δh/Δq do VHIL ficam cerca de 1 % "
            "acima da teoria porque um degrau de 2 % já sente a curvatura de √h."))
st.append(figura("fig-03-pontos-de-operacao.png", "Degrau de +2 % na bomba a partir de cinco níveis de equilíbrio "
                 "(resposta normalizada). Pontilhado: modelo de referência."))

# ====================================================================================== R2
st.append(P("R2. Implementação com a biblioteca nativa", h1))
st.append(P("O circuito usa só componentes da biblioteca core do Typhoon HIL Control Center 2026.2, sem bloco C "
            "function. Os elementos de potência são três: um capacitor, um indutor e um resistor. O orifício é a única "
            "parte sem par direto na biblioteca (não existe resistor não linear de dois terminais com v = i|i|/K²); por "
            "isso ele é o resistor R mais a fonte de tensão comandada e(i), calculada a partir da corrente medida no "
            "próprio ramo com blocos nativos. A tabela de pontos (Look-Up-Table Controlled Voltage Source) foi "
            "descartada porque não permite mudar k ao vivo no SCADA."))
st.append(tabela([
    ["Parte do modelo", "Elemento nativo (nome na biblioteca)", "Qtd.", "Observação"],
    ["Tanque (área A)", "Capacitor", "1", "C = A em F; pole shift ignore ligado"],
    ["Inércia da água no tubo", "Inductor", "1", "L = 2,71 mH por metro; pole shift ignore ligado"],
    ["Resistência de escoamento", "Resistor", "1", "R = 1,414 Ω"],
    ["Parte não linear do orifício", "Signal Controlled Voltage Source; Abs; Product; Mathematical function (square, "
                                     "reciprocal, sqrt); Gain; Sum; Signal switch", "1 + blocos",
     "subsistema Parte_nao_linear; modo linearizado"],
    ["Bomba q<sub>i</sub> e consumo q<sub>d</sub>", "Signal Controlled Current Source", "2", "comandadas pelo gerador "
                                                                                           "e pelo SCADA"],
    ["Medidores ideais", "Voltage Measurement; Current Measurement", "1 + 3", "nível, q<sub>i</sub>, q, q<sub>d</sub>"],
    ["Gerador de ensaios e preparação", "Integrator; Signal switch; Multiport signal switch; Sum; Product; Gain; "
                                        "Limit; Constant; Trigonometric function", "—", "degrau, condição inicial, "
                                                                                       "drenagem, senoide"],
    ["Interface", "SCADA Input; Probe; Scope", "10 + 7 + 1", "comandos e leituras do painel"],
    ["Código externo", "nenhum (C function não utilizada)", "0", "—"]],
    [3.8 * cm, 6.6 * cm, 1.8 * cm, 4.8 * cm], left_cols=(0, 1, 3), cap_txt="Inventário de elementos."))
st.append(P("<b>Área e tubo.</b> A área e o comprimento do tubo são parâmetros de construção, como num tanque real: ficam "
            "em <i>Model Initialization</i> (variáveis <i>A</i> e <i>l_tubo</i>) e mudam o valor do único capacitor e do "
            "indutor ao recompilar. Parâmetros de operação (válvula k, consumo, modo do orifício, nível de operação e "
            "ensaio) mudam ao vivo no SCADA."))
st.append(P("<b>Condição inicial.</b> A cada disparo há uma preparação de 100 s (1 s no circuito) em que a própria bomba "
            "leva o tanque ao nível inicial do ensaio: vazão de equilíbrio do nível desejado mais um termo proporcional "
            "ao erro (K<sub>p</sub> = 50 A/V, limitada a 0–40 L/s). O ensaio começa em equilíbrio, inclusive com a "
            "corrente certa no indutor, e os tempos são contados a partir daí. Não há fonte de pré-carga nem contator "
            "no circuito."))
st.append(P("<b>Cuidados de implementação.</b> (1) No capacitor e no indutor o simulador aplica por padrão um "
            "deslocamento de polos (<i>pole shifting</i>) que equivale a uma resistência parasita e desloca o equilíbrio; "
            "a opção <i>pole shift ignore</i> foi ativada nos dois. (2) Como e(i) usa a corrente do passo anterior, todos "
            "os blocos rodam no passo do circuito (20 µs), o que mantém a malha estável mesmo com o tubo de 0,1 m."))

# ====================================================================================== R3
st.append(P("R3. Validação contra o domínio original", h1))
st.append(P("<b>Critério de concordância.</b> Cada grandeza característica deve diferir da Entrega 01 em no máximo 1 %. "
            "A margem é uma ordem de grandeza menor que a incerteza dos próprios parâmetros físicos (o coeficiente de "
            "descarga é conhecido a ±5 %), de modo que nenhuma decisão de instrumentação mudaria por causa dela. "
            "Os ensaios foram executados com o tubo de 1 m e repetidos com 0,1 m, para separar o efeito da inércia."))
st.append(figura("fig-04-validacao-entrega01.png", "Os três ensaios da Entrega 01 no circuito, com tubo de 1 m e de "
                 "0,1 m, sobrepostos ao modelo da Entrega 01."))
lin = []
for pre, rot in (("", "1 m"), ("l0p1_", "0,1 m")):
    a, b, b2, c = V[pre + "a"], V[pre + "b"], V[pre + "b2"], V[pre + "c"]
    lin += [[f"(a) t<sub>63</sub>, tubo {rot}", f(a["t63_e01"], 2) + " s", f(a["t63"], 2) + " s", dif(a["t63"], a["t63_e01"])],
            [f"(a) t<sub>s</sub> (±2 %), tubo {rot}", f(a["ts2_e01"], 1) + " s", f(a["ts2"], 1) + " s",
             dif(a["ts2"], a["ts2_e01"])],
            [f"(a) nível final, tubo {rot}", f(a["hf_e01"], 4) + " m", f(a["hf"], 4) + " m", dif(a["hf"], a["hf_e01"], 3)],
            [f"(b) t<sub>63</sub> da volta de 1,0 m, tubo {rot}", f(b["t63_e01"], 2) + " s", f(b["t63"], 2) + " s",
             dif(b["t63"], b["t63_e01"])],
            [f"(b) drenagem até h<sub>mín</sub>, tubo {rot}", f(b2["t_hmin_e01"], 2) + " s", f(b2["t_hmin"], 2) + " s",
             dif(b2["t_hmin"], b2["t_hmin_e01"])],
            [f"(c) amplitude, tubo {rot}", f(c["amp_e01"] * 1000, 2) + " mm", f(c["amp"] * 1000, 2) + " mm",
             dif(c["amp"], c["amp_e01"])],
            [f"(c) fase, tubo {rot}", f(c["fase_e01"], 2) + "°", f(c["fase"], 2) + "°", dif(c["fase"], c["fase_e01"])]]
lin.append(["Sobressinal (a)", "0 %", "0 %", "polos reais (ζ ≈ 9,6)"])
st.append(tabela([["Grandeza característica", "Entrega 01", "Circuito (VHIL)", "Diferença"]] + lin,
                 [6.8 * cm, 3.2 * cm, 3.4 * cm, 3.6 * cm], left_cols=(0,),
                 cap_txt="Grandezas características: Entrega 01 × equivalente elétrico (escala do tanque)."))
st.append(P("Com o tubo de 0,1 m o circuito reproduz a E01 (diferenças de até 0,1 %). Com o tubo de 1 m todas as "
            "diferenças ficam dentro do critério e têm causa física conhecida, o polo dominante 0,3 % mais rápido "
            "(R1e), e não erro numérico. Fora do equilíbrio (volta de 1,0 m e drenagem até h<sub>mín</sub>) a "
            "concordância se mantém. A única discrepância maior está no fim da drenagem: a água que ainda corre no tubo "
            f"continua saindo quando o nível chega a zero, e o nível do circuito vai a "
            f"{f(-1000 * R['dren_tubo']['1']['h_min'], 1)} mm abaixo de zero. No tanque real o orifício passaria a "
            "aspirar ar; esse regime não é modelado, nem na E01 nem aqui, e fica fora da faixa de operação."))
st.append(P("<b>Fora do ponto de equilíbrio: só o resistor × orifício completo.</b> Os degraus de ±20 % e ±50 % "
            "foram repetidos com o orifício linearizado, em que só o resistor R faz o papel do orifício (Figura 4, "
            "Tabela 9)."))
st.append(figura("fig-05-linear-x-nao-linear.png", "Degraus de ±20 % e ±50 % na bomba a partir de 0,5 m, com o "
                 "orifício completo (contínuo) e só com o resistor R (tracejado). Pontilhado: Entrega 01."))
st.append(tabela([["Degrau", "h final teórico [m]", "h final não linear [m]", "h final só R [m]",
                   "erro do linear em Δh", "t<sub>63</sub> não linear [s]", "t<sub>63</sub> só R [s]"]] +
                 [[f"{o['pct']:+d} %", f(o["hf_teo"], 4), f(o["hf_nl"], 4), f(o["hf_lin"], 4),
                   f(o["erro_hf_pct"], 1) + " %", f(o["t63_nl"], 1), f(o["t63_lin"], 1)] for o in LI],
                 [1.6 * cm, 2.5 * cm, 2.7 * cm, 2.3 * cm, 2.6 * cm, 2.6 * cm, 2.4 * cm], left_cols=(),
                 cap_txt="Erro do modelo linear (resistor) contra o não linear."))
st.append(P("Com o resistor sozinho as respostas para cima e para baixo são espelhadas e têm a mesma constante de tempo "
            "(70,5 s). Com o orifício real, subir é mais lento e chega mais longe que descer, porque a resistência "
            "aumenta com o nível. O erro do linear na variação de nível é de cerca de 10 % para ±20 % e de 20 a 33 % para "
            "±50 %. No degrau de −50 % o resistor sozinho esvazia o tanque (0 m), enquanto o orifício real para em "
            "0,125 m. Critério prático: para variações de poucos por cento em torno de 0,5 m (o controle regulatório "
            "das próximas entregas) o resistor basta; para partidas, drenagem e grandes perturbações, a parte não "
            "linear é indispensável."))
st.append(P("<b>Resposta em frequência.</b> Senoides de ±10 % na bomba foram aplicadas de 0,2 a 1000 vezes a frequência "
            "de canto, medindo o nível (tensão no capacitor) e a vazão de saída (corrente no indutor)."))
st.append(figura("fig-06-resposta-em-frequencia.png", "Resposta em frequência medida no VHIL e teoria linearizada. "
                 "Esquerda: nível. Direita: vazão de saída. Tracejado vertical: os dois polos."))
b1 = min(BO, key=lambda b: abs(b["w_rel"] - 1))
st.append(P(f"Na frequência de canto o ganho do nível é {f(b1['H'], 1)} s/m² (teoria 100,0) com fase "
            f"{f(b1['fase_H'], 1)}° (teoria −45,0°). O nível se comporta como primeira ordem em toda a faixa, porque o zero "
            f"({f(-PR['zero'], 3)} s⁻¹) praticamente cancela o polo da inércia. A vazão de saída mostra o segundo polo: "
            f"acima de {f(-pol[0], 2)} rad/s a queda passa de −20 para −40 dB/década e a fase vai a −180°. É a assinatura "
            "da inércia, visível só na corrente do indutor. Os pontos do VHIL concordam com a teoria em todas as "
            "frequências (amplitude dentro de 0,1 %, fase dentro de 1°)."))

# ====================================================================================== R4
st.append(P("R4. Sensibilidade no equivalente", h1))
st.append(P("Foram variados os dois parâmetros do R5 da Entrega 01, a área A e o coeficiente k da válvula, e um "
            "terceiro que só existe no equivalente com inércia: o comprimento do tubo. Previsão da E01: A muda só a "
            "velocidade (t<sub>63</sub> proporcional a A) e não o nível final; k muda os dois (h* = (q<sub>i</sub>/k)²)."))
st.append(figura("fig-07-sensibilidade.png", "Esquerda: área (valor do capacitor). Direita: válvula k alterada no "
                 "SCADA, com a bomba em q<sub>i0</sub>. Pontilhado: Entrega 01."))
st.append(tabela([["A [m²] = C [F]", "t<sub>63</sub> E01 [s]", "t<sub>63</sub> VHIL [s]", "Diferença",
                   "t<sub>63</sub>/t<sub>63</sub>(0,5 m²)", "h final VHIL [m]"]] +
                 [[f(o["A"], 2), f(o["t63_e01"], 2), f(o["t63"], 2), dif(o["t63"], o["t63_e01"]),
                   f(o["t63"] / AR[1]["t63"], 3), f(o["hf"], 3)] for o in AR],
                 [2.8 * cm, 2.6 * cm, 2.6 * cm, 2.4 * cm, 3.2 * cm, 2.8 * cm], left_cols=(),
                 cap_txt="Sensibilidade à área."))
st.append(tabela([["k [m²·⁵/s]", "h* = (q<sub>i0</sub>/k)² [m]", "h final VHIL [m]", "t<sub>63</sub> E01 [s]",
                   "t<sub>63</sub> VHIL [s]", "passa de 1,2 m em"]] +
                 [[f(o["k"], 4), f(o["h_teo"], 4), f(o["hf"], 4), f(o["t63_e01"], 1), f(o["t63"], 1),
                   (f(o["t_transb"], 1) + " s (E01: " + f(o["t_transb_e01"], 1) + " s)"
                    if o["t_transb"] == o["t_transb"] else "não transborda")] for o in KK],
                 [2.2 * cm, 3.0 * cm, 2.6 * cm, 2.4 * cm, 2.4 * cm, 4.2 * cm], left_cols=(),
                 cap_txt="Sensibilidade ao coeficiente da válvula."))
st.append(P("O equivalente responde a A e k como o sistema original: dobrar a capacitância dobra o tempo "
            "(t<sub>63</sub> na razão 0,5 : 1 : 2 : 4) sem mudar o destino, e k decide o destino (k/2 leva o nível a "
            "2,0 m e transborda em 148 s; 2k o baixa a 0,125 m). As diferenças em relação à E01 ficam abaixo de 1,6 %; "
            "as maiores (k = 0,02, t<sub>63</sub> de só 24 s) vêm do polo da inércia, que pesa mais quando o tanque é "
            "rápido."))
st.append(figura("fig-08-inercia-do-liquido.png", "Degrau de +20 % com tubos de 0,1 a 1000 m (o mesmo circuito "
                 "recompilado com outro L). Pontilhado: modelo de referência."))
st.append(tabela([["l [m]", "L [mH]", "ω<sub>n</sub> [rad/s]", "ζ", "sobressinal q teórico (linear)",
                   "sobressinal q VHIL", "sobressinal h VHIL", "t<sub>63</sub> nível VHIL [s]"]] +
                 [[f(o["l"], 1 if o["l"] < 1 else 0), f(o["L"] * 1000, 3 if o["l"] < 1 else 2), f(o["wn"], 4),
                   f(o["zeta"], 2), f(o["ov_qo_teo_lin"], 1) + " %", f(o["ov_qo_vhil"], 1) + " %",
                   f(o["ov_h_vhil"], 1) + " %", f(o["t63_vhil"], 1)] for o in IN],
                 [1.4 * cm, 1.6 * cm, 2.0 * cm, 1.4 * cm, 2.8 * cm, 2.4 * cm, 2.4 * cm, 2.6 * cm], left_cols=(),
                 cap_txt="Sensibilidade ao comprimento do tubo (inertância)."))
st.append(P(f"Com tubo de até 1 m a inércia muda o t<sub>63</sub> do nível em menos de 0,3 %. Com 10 m a diferença já é "
            f"de {f(100 * (IN[2]['t63_vhil'] - IN[0]['t63_vhil']) / IN[0]['t63_vhil'], 1)} %; com 100 m (ζ ≈ 1, "
            f"amortecimento crítico) o nível sobe {f(-100 * (IN[3]['t63_vhil'] - IN[0]['t63_vhil']) / IN[0]['t63_vhil'], 0)} % "
            "mais rápido no início, porque a água que já corre no tubo demora a frear. Com 1000 m ζ cai para 0,3: a "
            "coluna de água ganha velocidade, passa do ponto e o sistema oscila como um tubo em U, com sobressinal na "
            "vazão e no nível (a mesma física do golpe de aríete). O sobressinal medido da vazão (30 %) é menor que o da "
            "fórmula linear (37 %) porque o degrau de 20 % já sente a não linearidade. Em todos os casos o VHIL "
            "acompanha o modelo de referência. <b>Conclusão:</b> o equivalente responde a A e k como o sistema "
            "original, e o comprimento do tubo mostra até onde vale a hipótese de inércia desprezível da E01."))

# ====================================================================================== R5
st.append(P("R5. Roteiro de repetibilidade", h1))
st.append(P("Ferramenta: Typhoon HIL Control Center 2026.2 (TyphoonSim/VHIL, sem hardware). Arquivos na pasta "
            "<i>devolutiva/e2-equivalente-eletrico-simulacao/</i>: <i>monotanque_equivalente_v2.tse</i> e <i>painel_monotanque_v2.cus</i>."))
for i, s_ in enumerate([
    "Abrir o Typhoon HIL Control Center 2026.2 → Schematic Editor → Ctrl + O → <i>monotanque_equivalente_v2.tse</i>.",
    "Na seta de <i>Compile and (re)load model in HIL SCADA</i>, escolher <b>Compile and (re)load model in SCADA VHIL "
    "MODE</b> e esperar <i>Compilation finished successfully</i>.",
    "No HIL SCADA, abrir <i>painel_monotanque_v2.cus</i>, conferir VIRTUAL HIL MODE e ACTIVE, clicar em Lock e em "
    "Start. Valores padrão: ensaio (a), h<sub>op</sub> = 0,5 m, degrau 20 %, h(0) = 1,0 m, amplitude 10 %, "
    "frequência 1, orifício não linear, k = 0,01, q<sub>d</sub> = 0.",
    "Em cada ensaio o nível vai ao valor inicial em 1 s de gráfico (100 s de tanque) e então o ensaio começa.",
    f"Ensaio (a), DISPARAR: h de 0,500 a 0,720 m; 63 % em ≈ {f(V['a']['t63'], 1)} s depois do início.",
    "Ensaio (b) bomba ligada: de 1,0 m volta a 0,500 m. Drenagem livre: chega a 0,10 m em ≈ 68 s e esvazia em ≈ 95 s.",
    "Ensaio (c): oscilação de ±0,071 m em torno de 0,50 m, atrasada ≈ 45° da bomba.",
    "Resistência de saída = <i>Linearizado</i> e ensaio (a): h vai a 0,700 m (só o resistor), em vez de 0,720 m.",
    "Pontos de operação: ensaio (a), degrau 2 % e h<sub>op</sub> = 0,2 / 0,8 m: t<sub>63</sub> ≈ "
    f"{f(OP[0]['t63_vhil'], 0)} / {f(OP[3]['t63_vhil'], 0)} s.",
    "Válvula: degrau 0 e k = 0.005: h → 2,0 m, passa de 1,2 m em ≈ "
    f"{f(KK[0]['t_transb'], 0)} s. Voltar k = 0.01.",
    "Área ou tubo: Stop, no Schematic Editor abrir Model → Model Initialization, mudar <i>A</i> ou <i>l_tubo</i> e "
    "recompilar (passo 2). Ex.: A = 2 → t<sub>63</sub> ≈ " + f(AR[-1]["t63"], 0) + " s; l_tubo = 1000 → o nível "
    "passa de 0,72 m e oscila."]):
    st.append(P(f"{i + 1}. {s_}", item))
st.append(P("As figuras deste relatório são refeitas com <i>rodar_tudo.sh</i> (ensaios no VHIL) e "
            "<i>analisar_dev.py</i> (referências e figuras), descritos em <i>e2-equivalente-eletrico-simulacao/instrucoes.md</i>."))

st.append(P("Referências", h1))
for r_ in ["OGATA, K. <i>Engenharia de Controle Moderno</i>. 5. ed. São Paulo: Pearson, 2010 (cap. 4: sistemas de "
           "nível de líquido, resistência e capacitância hidráulicas).",
           "FOX, R. W.; McDONALD, A. T.; PRITCHARD, P. J. <i>Introdução à Mecânica dos Fluidos</i>. 8. ed. Rio de "
           "Janeiro: LTC, 2014 (escoamento em orifícios, perdas e escoamento transiente em tubos).",
           "DOEBELIN, E. O. <i>System Dynamics: Modeling, Analysis, Simulation, Design</i>. New York: Marcel Dekker, "
           "1998 (inertância e analogias fluido-elétricas).",
           "TYPHOON HIL. <i>Typhoon HIL Software Manual</i>, versão 2026.2: Capacitor, Inductor, Resistor, "
           "Signal Controlled Sources.",
           "G05. <i>Caracterização do Monotanque no domínio hidráulico</i>. ECOM060, Fase 2, Entrega 01, UFAL, 2026."]:
    st.append(P(r_, item))


def rodape(cv_, doc):
    cv_.saveState(); cv_.setFont("TNR", 8.5)
    cv_.drawCentredString(A4[0] / 2, 1.2 * cm, f"{doc.page}")
    cv_.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.8 * cm, title="G05 - Fase 2, Entrega 02 - Equivalente eletrico (versao final)",
                        author="Equipe G05")
doc.build(st, onFirstPage=rodape, onLaterPages=rodape)
print("ok", OUT, NF[0], "figuras", NT[0], "tabelas")
