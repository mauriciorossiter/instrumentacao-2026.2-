"""Planta térmica em SI. Parâmetros do fabricante, sem instrumentação."""
from pathlib import Path
import json
import math

ROOT=Path(__file__).resolve().parent
R4=[.492466,.884411,.589157,.073673]  # K/W, Fig.21
TAU4=[.0002,.00054,.0021,.031658]  # s
C4=[t/r for t,r in zip(TAU4,R4)]  # J/K
R2=[1.116866866999197,.922840133000803]
TAU2=[.0002878723810835251,.002021156766960753]
TC=298.15  # K (25 degC)
POWER=10.  # W
STEP=0.002  # s
OFF=0.012  # s
DT=2e-6  # RK4. Rede térmica nativa usa DT/4 = 0,5 us.
RECORD=10e-6  # s
SOURCE='https://www.infineon.com/dgdl/Infineon-IKD04N60RF-DS-v02_06-EN.pdf?fileId=db3a30433c5c92fb013c5d6c806d00dc'

def scenarios():
    cases={}
    for order in [4,2]:
        r=R4 if order==4 else R2
        c=C4 if order==4 else [t/q for t,q in zip(TAU2,R2)]
        for trial in ['degrau','livre','pulso']:
            cases[f'{trial}_{order}r']=dict(r=list(r),c=list(c),trial=trial,duration=.25,tc=TC,power=POWER,step=STEP,off=OFF,group='nominal')
    # Um parâmetro por vez. Não se mantém tau artificialmente constante.
    for parameter,index in [('R1',0),('C1',0),('R4',3)]:
        for scale in [.2,1.,5.]:
            r=list(R4);c=list(C4)
            (r if parameter.startswith('R') else c)[index]*=scale
            cases[f'{parameter}_x{scale:g}']=dict(r=r,c=c,trial='degrau',duration=max(.25,STEP+8*max(a*b for a,b in zip(r,c))),tc=TC,power=POWER,step=STEP,off=OFF,group='sensibilidade',parameter=parameter,scale=scale)
    cases['potencia_100W']=dict(cases['degrau_4r'],power=100.,group='fora_validade')
    return cases

def tau(cfg):return [r*c for r,c in zip(cfg['r'],cfg['c'])]

def initial(cfg):
    return [cfg['power']*r if cfg['trial']=='livre' else 0. for r in cfg['r']]

def power(t,cfg):
    if cfg['trial']=='livre':return 0.
    return cfg['power'] if t>=cfg['step'] and (cfg['trial']!='pulso' or t<cfg['off']) else 0.

def exact(t,cfg):
    ts=tau(cfg)
    if cfg['trial']=='livre':return [x*math.exp(-t/ti) for x,ti in zip(initial(cfg),ts)]
    def response(edge):
        return [cfg['power']*r*(-math.expm1(-(t-edge)/ti)) if t>=edge else 0. for r,ti in zip(cfg['r'],ts)]
    y=response(cfg['step'])
    if cfg['trial']=='pulso':y=[a-b for a,b in zip(y,response(cfg['off']))]
    return y

def root_time(fraction,cfg):
    """Tempo relativo à borda para atingir fração do ganho estático."""
    total=sum(cfg['r']);low=0.;high=40*max(tau(cfg))
    for _ in range(100):
        mid=(low+high)/2
        reached=sum(r*(-math.expm1(-mid/ti)) for r,ti in zip(cfg['r'],tau(cfg)))
        if reached<fraction*total:low=mid
        else:high=mid
    return (low+high)/2

def algebra(cfg):
    return dict(gain_K_W=sum(cfg['r']),poles_s_1=[-1/t for t in tau(cfg)],tau_s=tau(cfg),
                T_equilibrio_K=cfg['tc']+(cfg['power'] if cfg['trial']=='degrau' else 0.)*sum(cfg['r']),
                referencia_tempos='Resposta ao degrau unitario; ganho e polos pertencem a planta',
                t10_s=root_time(.1,cfg),t90_s=root_time(.9,cfg),
                subida_10_90_s=root_time(.9,cfg)-root_time(.1,cfg),
                acomodacao_2pct_s=root_time(.98,cfg),sobressinal_pct=0.)

def save_json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def predictions():
    return {
      'R1':dict(pergunta='E se a resistência do ramo rápido cair para 20% ou subir para cinco vezes?',
                previsao='Com C1 fixa, aumentar R1 aumenta o ganho DC, aumenta tau1 e aproxima o polo1 de zero. A temperatura final sobe. Não há oscilação nem perda de estabilidade para R1>0.'),
      'C1':dict(pergunta='E se a capacidade térmica equivalente rápida cair para 20% ou subir cinco vezes?',
                previsao='Com R1 fixa, C1 altera tau1 e o polo1, mas não o ganho DC nem a temperatura de equilíbrio. Capacidade maior reduz a taxa inicial de aquecimento.'),
      'R4':dict(pergunta='E se a resistência do ramo lento cair para 20% ou subir cinco vezes?',
                previsao='Com C4 fixa, aumentar R4 amplia a cauda lenta e a temperatura final. Seu polo aproxima-se de zero. O ganho pode mudar menos que ao variar R1, mas o tempo de acomodação pode mudar muito.'),
      'potencia_100W':dict(pergunta='E se a potência subir de 10 para 100 W?',
                previsao='A equação linear prevê temperatura acima do limite de 175 graus Celsius. A estabilidade matemática permanece, mas a extrapolação não representa operação física admissível.')}

if __name__=='__main__':
    save_json(ROOT/'parametros.json',scenarios())
    save_json(ROOT/'previsoes_ANTES_da_simulacao.json',predictions())
