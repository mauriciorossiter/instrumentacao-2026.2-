"""Desenho tecnico do circuito e graficos cientificos da previsao numerica."""
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
HERE=Path(__file__).resolve().parent
OUT=HERE/'figuras'; OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(HERE.parent/'simulacao'))
from equivalente import CASOS, alinhar, original


def circuito():
    fig,ax=plt.subplots(figsize=(12,5.3))
    ax.set(xlim=(.1,12),ylim=(-.2,5)); ax.axis('off')
    navy='#15364c'; gray='#718392'; teal='#087b8a'
    def line(xs,ys,c=navy,lw=1.8):ax.plot(xs,ys,color=c,lw=lw)
    def txt(x,y,s,size=11,c=navy,**kw):ax.text(x,y,s,ha='center',va='center',fontsize=size,color=c,**kw)
    def arrow(x,y,dx,dy,c=navy):ax.annotate('',(x+dx,y+dy),(x,y),arrowprops=dict(arrowstyle='->',lw=1.7,color=c))
    def source(x,y,label,up=True,c=navy,controlled=False):
        line([x,x],[1,y-.38],c);line([x,x],[y+.38,3.8],c)
        patch=Polygon([(x,y-.38),(x+.38,y),(x,y+.38),(x-.38,y)],fill=False,edgecolor=c,lw=1.8) if controlled else Circle((x,y),.38,fill=False,edgecolor=c,lw=1.8)
        ax.add_patch(patch)
        arrow(x,y-.2 if up else y+.2,0,.4 if up else -.4,c)
        txt(x-.55 if x<2 else x+.72,y,label,10,c)
    line([1,5.9],[3.8,3.8]);line([6.7,11],[3.8,3.8]);line([1,11],[1,1])
    source(1,2.4,r'$i_{in}$')
    for x,j in [(3,1),(8.2,2)]:
        line([x,x],[3.8,2.6]);line([x-.33,x+.33],[2.6,2.6]);line([x-.33,x+.33],[2.42,2.42]);line([x,x],[2.42,1])
        ax.plot(x,3.8,'o',color=navy,ms=5)
        txt(x,4.2,fr'$N{j}:\ v_{j}=10h_{j}$',13)
        txt(x-.6,1.7,fr'$C_{j}$'+'\n500 µF',11)
    ax.add_patch(Polygon([(5.9,3.8),(6.3,4.08),(6.7,3.8),(6.3,3.52)],fill=False,edgecolor=teal,lw=1.8))
    arrow(6.06,3.8,.46,0,teal)
    txt(6.3,4.55,r'$i_{12}=G_1\sqrt{v_1}$',13,teal)
    txt(6.3,3.12,'fonte controlada por V1',10,teal)
    source(11,2.4,r'$i_2$',up=False,c=teal,controlled=True)
    txt(10.7,4.55,r'$i_2=G_2\sqrt{v_2}$',12,teal)
    source(4.4,2.25,r'$i_{pre,1}$',c=gray)
    source(9.5,2.25,r'$i_{pre,2}$',c=gray)
    line([6.3,6.3],[1,.75]);line([5.98,6.62],[.75,.75]);line([6.08,6.52],[.63,.63]);line([6.18,6.42],[.51,.51])
    txt(6.3,.25,'Terra comum',10)
    txt(6.3,-.08,'Pré-carga: sat ±100 mA de 2(Vref − V); desligada durante o ensaio',10,gray)
    fig.tight_layout(pad=.4)
    for ext in ['png','svg']:fig.savefig(OUT/f'circuito-equivalente.{ext}',dpi=190,bbox_inches='tight',facecolor='white')
    plt.close(fig)


def sensibilidade():
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=False)
    for ax,names,title in [(axes[0],['r4-k2-1','r4-k2-2','r4-k2-3'],'Variação de k2'),
                           (axes[1],['r4-q-0p5','r4-q-0p75','r4-q-1'],'Variação de q0')]:
        for name in names:
            arr=np.loadtxt(HERE.parent/f'simulacao/dados/offline/{name}.csv',delimiter=',',skiprows=1)
            t,h=alinhar(arr);c=CASOS[name]
            label=f'k2 × {c.g2:g}' if 'k2' in name else f'q0 × {c.qrel:g}'
            line=ax.plot(t,h[:,1],label=label)[0]
            ref=original(c,t)
            ax.plot(t,ref[:,1],'--',color=line.get_color(),alpha=.7,lw=1)
        ax.set(xlabel='tempo original [s]',ylabel='h2 [m]',title=title,xlim=(0,900));ax.grid(alpha=.25);ax.legend(fontsize=9)
    fig.suptitle('TyphoonSim offline - sensibilidade com degrau de 5%\nContínuo: circuito; tracejado: EDOs da E01',fontsize=11)
    fig.tight_layout();fig.savefig(OUT/'offline-sensibilidade.png',dpi=160);plt.close(fig)


if __name__=='__main__':circuito();sensibilidade()
