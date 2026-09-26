# -*- coding: utf-8 -*-
"""Esquematico da cadeia projetada (fig-01), desenhado com schemdraw."""
import os
import schemdraw
import schemdraw.elements as elm
import matplotlib
matplotlib.use('Agg')

import parametros as P
from estilo import DIR_PNG, DIR_PDF, AZUL, LARANJA, TINTA2

schemdraw.config(fontsize=10, lw=1.1)


def kohm(r):
    return ('%.3g k$\\Omega$' % (r / 1e3)).replace('.', ',')


with schemdraw.Drawing(show=False) as d:
    # ---------------- lado do sensor (flutua em IRET)
    vref = d.add(elm.SourceV().up())
    d.add(elm.Label().at((vref.center[0] - 1.0, vref.center[1]))
          .label('$V_{REF}$\n2,5 V\n(XTR115)', fontsize=9))
    d.add(elm.Line().right(2.2))
    topo = d.add(elm.Dot())
    pot = d.add(elm.Potentiometer().down().color(LARANJA))
    d.add(elm.Label().at((pot.center[0] - 1.05, pot.center[1]))
          .label('3590S\n10 k$\\Omega$', color=LARANJA, fontsize=9))
    d.add(elm.Line().left(2.2))
    base = d.add(elm.Dot())
    d.add(elm.Line().to(vref.start))
    d.add(elm.Ground().at(base.center).label('IRET', loc='right', fontsize=8))

    # cursor -> buffer OPA333
    d.add(elm.Line().at(pot.tap).right(0.6))
    op = d.add(elm.Opamp(leads=True).anchor('in2').label('OPA333', loc='center', fontsize=8))
    d.add(elm.Line().at(op.out).right(0.4))
    no_out = d.add(elm.Dot())
    d.add(elm.Line().up(1.5))
    d.add(elm.Line().tox(op.in1[0] - 0.3))
    d.add(elm.Line().toy(op.in1))
    d.add(elm.Line().tox(op.in1))
    d.add(elm.Line().at(no_out.center).right(0.2))
    rin = d.add(elm.Resistor().right(2.6).label('$R_{IN}$\n' + kohm(P.RIN)))
    no_iin = d.add(elm.Dot())

    # R0 a partir de VREF
    d.add(elm.Line().at(topo.center).up(2.6))
    d.add(elm.Line().tox(rin.start))
    d.add(elm.Resistor().tox(no_iin.center).label('$R_0$\n' + kohm(P.R0)))
    d.add(elm.Line().toy(no_iin.center))

    # XTR115 como bloco
    d.add(elm.Line().at(no_iin.center).right(0.8).label('$I_{IN}$', loc='top', fontsize=9))
    xtr = d.add(elm.Ic(pins=[elm.IcPin(name='IIN', side='left', slot='1/1', lblsize=9),
                             elm.IcPin(name='V+', side='top', slot='1/1', anchorname='VP', lblsize=9),
                             elm.IcPin(name='IO', side='bottom', slot='1/1', lblsize=9)],
                       size=(3.0, 2.4), edgepadW=0.5)
                .anchor('IIN').label('XTR115\n$I_O = 100\\,I_{IN}$', loc='center', fontsize=9)
                .color(AZUL))

    # ---------------- laço 4-20 mA
    d.add(elm.Line().at(xtr.IO).down(1.0))
    d.add(elm.Resistor().right(3.0).label('$R_{cabo}$\n%.0f $\\Omega$' % P.R_CABO))
    a = d.add(elm.Dot())
    rl = d.add(elm.Resistor().down(2.4).label('$R_L$ 250 $\\Omega$\n(1–5 V)', loc='bottom'))
    b = d.add(elm.Dot())
    d.add(elm.Ground())
    d.add(elm.Line().at(b.center).right(2.2))
    vl = d.add(elm.SourceV().up())
    d.add(elm.Label().at((vl.center[0] + 1.0, vl.center[1])).label('$V_{LOOP}$\n24 V', fontsize=9))
    d.add(elm.Line().toy(xtr.VP[1] + 1.2))
    d.add(elm.Line().tox(xtr.VP))
    d.add(elm.Line().toy(xtr.VP))
    fig = d.draw(show=False)
    os.makedirs(DIR_PNG, exist_ok=True)
    fig.save(os.path.join(DIR_PNG, 'fig-01-esquematico.png'), dpi=200)
    fig.save(os.path.join(DIR_PDF, 'fig-01-esquematico.pdf'))
print('ok')
