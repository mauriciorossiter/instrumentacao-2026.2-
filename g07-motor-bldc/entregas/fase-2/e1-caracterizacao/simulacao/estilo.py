"""Ao importar: figuras com virgula decimal (ticks e textos) ao salvar."""
import re, matplotlib
from matplotlib.figure import Figure
from matplotlib.ticker import ScalarFormatter
class _VF(ScalarFormatter):
    def __call__(self, x, pos=None):
        return super().__call__(x, pos).replace('.', ',')
_re = re.compile(r'(\d)\.(\d)')
def _virgula(fig):
    for ax in fig.axes:
        for axis, sc in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
            if sc == 'linear':
                f = _VF(); f.set_useOffset(False); axis.set_major_formatter(f)
        txts = list(ax.texts) + [ax.title, ax.xaxis.label, ax.yaxis.label]
        leg = ax.get_legend()
        if leg: txts += leg.get_texts()
        for t in txts:
            t.set_text(_re.sub(r'\1,\2', t.get_text()))
_orig = Figure.savefig
def _savefig(self, *a, **k):
    _virgula(self); return _orig(self, *a, **k)
Figure.savefig = _savefig
