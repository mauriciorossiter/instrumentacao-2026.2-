"""Gera o relatorio a partir das capturas nativas offline e das EDOs da E01."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
FONT=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Arial',str(FONT/'arial.ttf')))
pdfmetrics.registerFont(TTFont('Arial-Bold',str(FONT/'arialbd.ttf')))
pdfmetrics.registerFontFamily('Arial',normal='Arial',bold='Arial-Bold',italic='Arial',boldItalic='Arial-Bold')
navy=colors.HexColor('#15364c');teal=colors.HexColor('#087b8a');light=colors.HexColor('#edf3f6')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyA',fontName='Arial',fontSize=10,leading=14,spaceAfter=7))
styles.add(ParagraphStyle(name='H1A',fontName='Arial-Bold',fontSize=20,leading=24,textColor=navy,spaceAfter=13))
styles.add(ParagraphStyle(name='H2A',fontName='Arial-Bold',fontSize=12,leading=16,textColor=teal,spaceBefore=8,spaceAfter=7))
styles.add(ParagraphStyle(name='SmallA',fontName='Arial',fontSize=8.1,leading=11,spaceAfter=5))
story=[]
def p(s,small=False):return Paragraph(s,styles['SmallA' if small else 'BodyA'])
def add(s):story.append(p(s))
def title(s):story.append(Paragraph(s,styles['H1A']))
def h(s):story.append(Paragraph(s,styles['H2A']))
def table(rows,widths,fs=8.4):
    th=ParagraphStyle('TH',parent=styles['SmallA'],textColor=colors.white,fontName='Arial-Bold')
    t=Table([[Paragraph(str(c),th if i==0 else styles['SmallA']) for c in r] for i,r in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,light]),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#b7c6cf'))]))
    story.extend([t,Spacer(1,8)])
def img(name,width=490):
    im=Image(str(HERE/'figuras'/name));im.drawHeight*=width/im.drawWidth;im.drawWidth=width
    story.extend([im,Spacer(1,6)])
def page():story.append(PageBreak())
records={n:json.loads((ROOT/f'simulacao/resultados-offline-{n}.json').read_text(encoding='utf-8')) for n in ['r3a','r3b','r3c','r4-k2-1','r4-k2-2','r4-k2-3','r4-q-0p5','r4-q-0p75','r4-q-1']}
labels={'h2_final_m':'h2 final (m)','Kef_s_m2':'Ganho efetivo (s/m²)','t63_s':'t63 (s)','tr_s':'tr 10-90% (s)','ts_s':'ts 2% (s)','sobressinal_pct':'Sobressinal (%)','h1_pico_m':'Pico h1 (m)','h1_t_pico_s':'Instante pico h1 (s)','h2_pico_m':'Pico h2 (m)','h2_t_pico_s':'Instante pico h2 (s)','tau1_s':'τ1 ajustado (s)'}
def mt(name,exclude=()):
    rows=[['Métrica','EDOs E01','TyphoonSim offline','Diferença (%)']]
    for m in records[name]['metricas']:
        if m['grandeza'] in exclude:continue
        fmt=lambda v:'n/a' if v is None else f'{v:.7g}'.replace('.',',')
        rows.append([labels[m['grandeza']],fmt(m['original']),fmt(m['equivalente']),fmt(m['diferenca_pct'])])
    table(rows,[160,110,110,110])


def valor(n,k):return next(m['equivalente'] for m in records[n]['metricas'] if m['grandeza']==k)

title('Equivalente elétrico dos tanques acoplados')
add('<b>ECOM060 | Equipe 01 | Fase 2 - Entrega 02</b><br/>Validação nativa e painel independente - 10/11/2026')
table([['Resultado','Evidência'],['9 de 9 ensaios aprovados','Circuito executado pelo solver nativo do TyphoonSim 2026.3. Cada CSV tem 20.251 amostras reais; erro máximo global de 0,684309 mm.'],['Controle pelo SCADA Standalone','Painel incluído no TyphoonSim, com presets, edição dos parâmetros, execução e gráfico. Testados pela interface: r3a, k2×2 e q0×0,5.'],['Modo utilizado','TyphoonSim offline + SCADA Standalone, sem Control Center e sem VHIL. A distinção em relação ao fluxo VHIL/SCADA do enunciado está explícita no roteiro.']],[155,335])
h('1. Planta de referência e correspondências (R1)')
add('Mantém-se a cascata não interagente da Entrega 01: a descarga do tanque 1 depende somente de h1. A1=A2=0,5 m²; k1=k2=0,010 m<super>5/2</super>/s; q0=0,010 m³/s; equilíbrio nominal h1=h2=1 m. A faixa especificada é 0,1 a 1,2 m.')
add('<b>A1 dh1/dt = qin - k1√h1<br/>A2 dh2/dt = k1√h1 - k2√h2</b>')
table([['Grandeza física','Representação elétrica'],['Esforço: pressão p=ρgh','v=kv·h=(kv/ρg)·p, com kv=10 V/m.'],['Fluxo: vazão q','i=ki·q, com ki=1 A/(m³/s).'],['Armazenamento: área A','Capacitor C=A·ki/(kv·N).'],['Dissipação: orifício k√h','Fonte controlada i=G√v, G=k·ki/√kv.'],['Fonte de vazão','Fonte de corrente. Não há elemento inercial na planta; nenhum indutor é necessário.']],[173,317])
add('Com t_original=N·t_elétrico e N=100, a regra da cadeia fornece dv/dt_elétrico=kv·N·dh/dt_original. Multiplicar por A·ki/(kv·N) recupera ki·A·dh/dt_original. Portanto <b>C1=C2=500 µF</b> e <b>G1=G2=0,00316227766017 A/√V</b>.')
add('No ponto nominal: 10 V representam 1 m; 10 mA representam 10 L/s. A faixa operacional equivale a 1..12 V. O maior comando de vazão dos ensaios é 12 mA. As fontes artificiais de pré-carga são limitadas separadamente a ±100 mA.')

page();title('Circuito, equilíbrio e polos')
img('circuito-equivalente.png')
story.append(p('Figura 1. Equivalente elétrico; cinza indica as fontes de inicialização, desligadas durante os ensaios. Medidores ideais de tensão ficam em paralelo e os de corrente em série.',True))
h('2. Equações e verificação da linearização (R1)')
add('<b>C1 dv1/dte = iin + ipre1 - G1√v1<br/>C2 dv2/dte = G1√v1 + ipre2 - G2√v2</b>')
add('Durante o ensaio, ipre1=ipre2=0. Em regime: vj0=(iin0/Gj)², correspondendo a hj0=(q0/kj)². A fonte entre os nós depende somente de V1; usar √(V1-V2) mudaria a planta. A equivalência é das variáveis e da dinâmica, sem exigir um circuito passivo entre os nós.')
add('No ponto nominal, gj=Gj/(2√vj0)=0,0005 S e Rj,inc=2000 Ω. Assim τj,e=Cj/gj=1 s. A função linearizada elétrica é 2000/(s+1)²; após reconversão, a hidráulica é 200/(100s+1)².')
table([['Grandeza linearizada','E01','Elétrico reconvertido','Diferença'],['Ganho estático','200 s/m²','200 s/m²','0%'],['Polos','-0,01; -0,01 (1/s)','-1/100; -1/100 (1/s)','0%'],['τ1 / τ2','100 / 100 s','100 / 100 s','0%'],['ωn / ζ','0,01 rad/s / 1','0,01 rad/s / 1','0%']],[140,120,155,75])
add('O t63 da cascata linear (~214,6 s) não é a constante individual de 100 s. Para o degrau finito de 5%, h2 final=1,05²=1,1025 m e o ganho efetivo é 205 s/m²: a diferença de 2,5% frente ao ganho infinitesimal de 200 s/m² decorre da não linearidade do equilíbrio.')

page();title('Implementação nativa (R2)')
add('O circuito foi construído com a biblioteca core do TyphoonSim 2026.3 / API 1.32.1. Todas as equações da planta são executadas pelo simulador; Python prepara ensaios e compara os dados. <b>Nenhuma C function foi necessária.</b>')
table([['Tipo nativo na biblioteca core','Quantidade / função'],['Capacitor','2; C1/C2, 500 µF, tensão inicial 0 V.'],['Signal Controlled Current Source','5; entrada, duas descargas e duas pré-cargas.'],['Voltage Measurement / Current Measurement','2 / 3; medidores ideais com saídas de sinal.'],['Ground','1; referência comum.'],['SCADA Input','8 no modelo para VHIL; na variante offline, precarga é substituída por Step.'],['Mathematical function / Limit','2 raízes quadradas / 4 limites de domínio e pré-carga.'],['Integrator / Relational operator','1 relógio com reset por nível / 1 comparação t&lt;0,3 s.'],['Constant / Sum / Product / Gain / Probe','2 / 4 / 8 / 9 / 3; comandos, escalas e monitoramento.'],['Step / Scope na variante offline','Disparo automático 1→0 em 0,25 s / leitura de V1, V2 e u_ensaio.']],[250,240])
add('modelo.tse tem 55 componentes; modelo-offline.tse tem 56, com a troca da entrada de pré-carga por Step e a adição de Scope. O inventário JSON registra o modelo de 55 blocos; as duas alterações da variante estão descritas acima e em gerar_offline.py.')
h('3. Configuração realmente executada')
add('TyphoonSim: solver DAE, integração BDF, passo máximo 100 µs, passo inicial 1 µs, SP a 100 µs, tolerâncias absoluta 1e-9 e relativa 1e-7. O campo data_sampling_rate recebe o intervalo de aquisição de <b>0,001 s</b>. A duração é 20,25 s, incluindo 0,25 s de pré-carga. O modelo para VHIL mantém HIL404/1 e passo elétrico de 1 µs, mas não foi executado em VHIL.')
add('A pré-carga aplica precarga·sat±0,1 A[2 A/V·(Vrefj-Vj)]. A liberação é automática em 0,25 s; o pulso dura 0,3 s elétrico = 30 s originais. O integrador é zerado por nível enquanto a pré-carga está ativa. O Scope precisa ser inicializado reabrindo o .tse salvo e lido explicitamente por seu nome Captura.')
add('O painel Standalone chama a API do Schematic Editor para configurar e executar um novo ensaio offline. O gráfico usa os dados reais do Scope. Ele não tenta carregar .cpd nem controlar uma simulação HIL. Entradas manuais com equilíbrio ou trajetória fora de 0,1..1,2 m são recusadas pelo executor.')

page();title('Validação nativa: degrau de 5% (R3a)')
add('As curvas tracejadas são dados do circuito executado no <b>TyphoonSim offline</b>. As curvas contínuas vêm das EDOs da E01, reavaliadas por RK45 com rtol=1e-9, atol=1e-11 e passo máximo 0,1 s. O CSV bruto conserva as tensões e o tempo elétricos.')
img('offline-r3a.png',455)
mt('r3a')
add('Conversão: h=V/10 e t=100te. O início é alinhado à primeira amostra de u_ensaio&gt;0,5. Erro pontual máximo medido: <b>0,089931 mm</b>. A aquisição de 1 ms corresponde a 0,1 s no domínio original.')
add('Critérios definidos antes dos ensaios: erro de nível ≤2 mm (0,2% de 1 m) e diferença absoluta relativa ≤1% em cada métrica não nula. Para referências nulas, tolerância absoluta de 1e-4 na unidade indicada. Todos os critérios desta captura foram atendidos; nenhuma previsão Python foi usada no lugar do CSV nativo.')

page();title('Resposta livre e pulso no TyphoonSim')
story.append(Table([[Image(str(HERE/'figuras/offline-r3b.png'),width=241,height=169),Image(str(HERE/'figuras/offline-r3c.png'),width=241,height=169)]],colWidths=[245,245]))
story.append(Spacer(1,9))
h('4. Condição inicial: h1=1,15 m; h2=0,60 m (R3b)')
mt('r3b')
add('A vazão permanece nominal. h2 ultrapassa levemente 1 m e retorna ao equilíbrio; τ1 foi ajustado na cauda de h1 entre 300 e 800 s. O maior erro de nível é <b>0,684309 mm</b>. Na primeira amostra após o disparo, h2=0,600684309 m; esse resíduo combina a pré-carga aproximada com o avanço até o primeiro registro do gatilho.')
h('5. Pulso de +20% por 30 s originais (R3c)')
mt('r3c')
add('Erro máximo: <b>0,359821 mm</b>. O pico de h1 é registrado em 29,9 s e o de h2 em 117,5 s. A maior diferença relativa entre as métricas de todos os ensaios é 0,3333%, no instante do pico de h1: 0,1 s de diferença sobre 30 s.')
add('As diferenças pequenas são compatíveis com o disparo registrado em malha de 1 ms elétrico, a execução discreta dos blocos de sinais a 100 µs, a pré-carga proporcional e a integração BDF frente à referência RK45. A lei √h é mantida em todos os ensaios, inclusive na condição inicial afastada do equilíbrio; não houve substituição por resistores linearizados.')

page();title('Sensibilidade no equivalente (R4)')
add('Foram executados k2×{1,2,3} e q0×{0,5;0,75;1}, com degrau de 5%. Cada caso começa no próprio equilíbrio, Vrefj=10(Q_rel/Gj_rel)². Os ajustes de k2×2 e q0×0,5 também foram selecionados e executados pela interface SCADA Standalone; os registros scada-*.json identificam essas ações.')
img('offline-sensibilidade.png',490)
rows=[['Parâmetro','h2 inicial (m)','h2 final (m)','τ2 linear (s)','ts medido (s)']]
for n,label in [('r4-k2-1','k2 × 1'),('r4-k2-2','k2 × 2'),('r4-k2-3','k2 × 3'),('r4-q-0p5','q0 × 0,5'),('r4-q-0p75','q0 × 0,75'),('r4-q-1','q0 × 1')]:
    e=records[n]['entradas'];q=e['Q_rel'];g=e['G2_rel']
    values=[f'{(q/g)**2:.6g}',f'{valor(n,"h2_final_m"):.6g}',f'{100*q/g**2:.6g}',f'{valor(n,"ts_s"):.3f}']
    rows.append([label,*[v.replace('.',',') for v in values]])
table(rows,[105,93,98,94,100])
add('Aumentar k2 reduz h2 quadraticamente e τ2=2A2·q0/k2², mantendo τ1 nominal. Reduzir q0 reduz ambos os níveis quadraticamente e as constantes de tempo linearmente. As tendências dos dados nativos coincidem com as da E01. Os nove casos passaram: erro máximo global 0,684309 mm e maior diferença relativa de métrica 0,3333%.')
add('O painel altera os parâmetros entre execuções offline completas; não modifica uma planta HIL em tempo real. Para uma futura cadeia de instrumentação, sensores e filtros também precisarão ter as constantes de tempo escaladas. Manter automaticamente um filtro de 20 Hz mudaria a dinâmica relativa da cadeia.')

page();title('Reprodução sem Control Center (R5)')
table([['Passo','Procedimento'],['1. Abrir o painel','Executar typhoonsim/iniciar_painel_offline.py. O launcher abre o SCADA Standalone incluído no TyphoonSim com painel-offline.cus. Alternativa: abrir esse painel manualmente e iniciar o modo de execução.'],['2. Conferir arquivos','O campo Pasta aponta para a pasta typhoonsim desta entrega. Se o material for movido, conferir o caminho antes da execução. modelo-offline.tse permite abrir e rodar diretamente o caso r3a no editor.'],['3. Escolher o ensaio','Clicar no preset da tabela de instrucoes.md. O preset atualiza Q_rel, G1_rel, G2_rel, degrau, pulso e tensões iniciais.'],['4. Ajustar parâmetros','Para valores manuais, confirmar cada campo com Enter. Ao alterar q ou k, clicar Recalcular equilibrio; para R3b, usar as tensões específicas do preset.'],['5. Executar','Clicar Executar ensaio. O painel prepara o .tse, reabre-o para inicializar o Scope, roda 20,25 s e lê V1/V2/u_ensaio. Aguardar a mensagem final antes de iniciar outro ensaio.'],['6. Conferir resultados','O gráfico e o status mostram a captura concluída. CSVs reais: simulacao/dados/offline. Tabelas: simulacao/resultados-offline.md. Figuras: relatorio/figuras/offline-*.png.'],['7. Repetir por script','No Python com typhoon-hil-api 1.32.1 e os requisitos instalados: python typhoonsim/executar_offline.py. São reproduzidos os nove ensaios.']],[92,398])
h('6. Arquivos, proveniência e limite do modo utilizado')
add('A validação desta versão foi feita no TyphoonSim 2026.3, por API Python 1.32.1 e também pela interface SCADA Standalone. As equações do circuito são nativas; os scripts externos apenas configuram, acionam, exportam e confrontam com a E01. Os CSVs têm 20.251 linhas de dados, de 0 a 20,25 s elétricos. O sinal de disparo é registrado em 0,251 s na malha de aquisição.')
add('<b>Distinção em relação ao enunciado:</b> o procedimento usa SCADA Standalone como interface para o solver offline. Não foi executado Virtual HIL nem o HIL SCADA regular. O pacote também conserva modelo.tse, painel.cus e executar_vhil.py para esse fluxo, caso seja exigida demonstração específica em VHIL. Não se apresenta o modo offline como captura de VHIL.')
add('Os arquivos intermediários, executáveis, caches e backups permanecem em pastas ignoradas. A revisão dos guias e o roteiro detalhado acompanham a entrega. Apresentação: sete minutos de exposição e três de perguntas, com participação de todos os integrantes.')
h('Referências')
for name,ref in [('Disciplina','ECOM060_Fase2_Entrega02_Orientacao.pdf e relatório/modelo da Fase 2, Entrega 01.'),('TyphoonSim','https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/typhoonsim.html'),('SCADA Standalone','https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/standalone_scada.html'),('Schematic Editor API','https://www.typhoon-hil.com/documentation/typhoon-hil-api-documentation/schematic_api.html')]:
    story.append(p(f'<b>{name}.</b> {escape(ref)}',True))

def footer(canvas,doc):
    canvas.setStrokeColor(teal);canvas.line(52,45,543,45)
    canvas.setFont('Arial',7.5);canvas.setFillColor(navy)
    canvas.drawString(52,32,'G01 | Fase 2 - Entrega 02 | TyphoonSim offline + SCADA Standalone (sem VHIL)')
    canvas.drawRightString(543,32,str(doc.page))

if __name__=='__main__':
    doc=SimpleDocTemplate(str(HERE/'relatorio.pdf'),pagesize=A4,rightMargin=52,leftMargin=52,
                          topMargin=47,bottomMargin=60,title='G01 - Fase 2, Entrega 02 - Equivalente eletrico',author='Equipe 01')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(HERE/'relatorio.pdf')
