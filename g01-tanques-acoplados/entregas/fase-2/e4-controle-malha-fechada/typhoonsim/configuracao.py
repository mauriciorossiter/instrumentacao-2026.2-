"""Ganhos, critérios e cenários fixados antes das capturas."""
from pathlib import Path
import sys
from dataclasses import dataclass, replace
import math

HERE = Path(__file__).resolve().parent
E3 = HERE.parents[1] / "e3-instrumentacao-malha-aberta" / "typhoonsim"
sys.path.insert(0, str(E3))
from parametros import NOMINAL, IDEAL, H_FS, N

KP = .25  # variação relativa da vazão por metro
KI = .0025  # variação relativa da vazão por metro e segundo físico
QMIN, QMAX = .70, 1.30
ERRO_MM, TEMPO_S, SOBRESSINAL_PCT = 4., 900., 10.
PICO_DIST_MM, RECUPERACAO_S = 60., 1000.
ESFORCO_LS = 1.50
HMIN, HMAX = .10, 1.20
EVENTOS = {"subida":(1.08,0.), "disturbio":(1.,.05), "descida":(.92,0.)}
GRADE = {"zero_mm":(0,2,4,6,15,30,60),
         "tau_s":(.2,10,30,60,90,140,220,400),
         "ruido_mm":(2,10,15,20,40,60,100)}


@dataclass(frozen=True)
class Caso:
    ensaio: str
    perfil: str
    instrumento: object

    def validar(self):
        if self.ensaio not in EVENTOS or self.perfil not in ("ideal","real","calibrado"):
            raise ValueError("Ensaio ou perfil desconhecido.")
        # A grade inclui falhas deliberadamente maiores que a faixa original da E03.
        tau = self.instrumento.tau_s
        if not math.isfinite(tau) or not (tau == 0 or .05 <= tau <= 500):
            raise ValueError("Constante da tomada: 0 para bypass ou 0,05–500 s.")
        replace(self.instrumento, tau_s=min(100,tau)).validar()


def nome_grade(campo, valor, ensaio="subida"):
    nome=f"{campo}-{valor:g}".replace("_","-").replace(".","p")
    return nome if ensaio=="subida" else "d-"+nome


CASOS = {f"{ensaio}-{perfil}": Caso(ensaio,perfil,NOMINAL)
         for ensaio in EVENTOS for perfil in ("ideal","real","calibrado")}
for campo, valores in GRADE.items():
    for v in valores:
        # Todos os outros efeitos ficam em bypass. Para interferência, conserva-se
        # o RC de 0,2 Hz da E03, pois a perturbação entra antes do filtro.
        base=replace(IDEAL,fc_hz=.2) if campo=="ruido_mm" else IDEAL
        CASOS[nome_grade(campo,v)] = Caso("subida","real",replace(base,**{campo:v}))
        CASOS[nome_grade(campo,v,"disturbio")] = Caso("disturbio","real",replace(base,**{campo:v}))


def medicao_estatica(h, inst=NOMINAL):
    r=h/H_FS
    return ((1+inst.ganho_pct/100)*h+(inst.zero_mm-inst.correcao_mm)/1000
            +4*r*(1-r)*inst.curvatura_mm/1000)


def calibracao(inst):
    h_a,h_b=.10,1.20
    m_a,m_b=medicao_estatica(h_a,inst),medicao_estatica(h_b,inst)
    a=(h_b-h_a)/(m_b-m_a)
    return a,h_a-a*m_a


def margem_fase(tau=0., tau_rc=0.):
    # Há um só cruzamento de unidade. Bisecção em frequência física.
    def l(w):
        s=1j*w
        return .005/(s*(1+100*s)*(1+tau*s)*(1+tau_rc*s))
    lo,hi=1e-6,1.
    for _ in range(70):
        mid=(lo+hi)/2
        if abs(l(mid))>1: lo=mid
        else: hi=mid
    w=(lo+hi)/2
    fase=90-math.degrees(sum(math.atan(w*t) for t in (100,tau,tau_rc)))
    return w,fase
