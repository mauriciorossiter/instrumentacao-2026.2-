"""Compõe o relatório PDF a partir das métricas e figuras da entrega."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)
from PIL import Image as PILImage

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
DADOS=BASE/"simulacao/dados"
FIG=HERE/"figuras"
E2=BASE.parent/"e2-equivalente-eletrico/relatorio/figuras/circuito-equivalente.png"
FONT=Path("C:/Windows/Fonts")
for name,file in [("Cal","calibri.ttf"),("CalB","calibrib.ttf")]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily("Cal",normal="Cal",bold="CalB")
navy,teal,gray,light=map(colors.HexColor,["#143B4B","#08798C","#405765","#E9F3F6"])
styles={
    "tiny":ParagraphStyle("tiny",fontName="Cal",fontSize=9.5,leading=12,textColor=gray,spaceAfter=4),
    "p":ParagraphStyle("p",fontName="Cal",fontSize=11.5,leading=15.1,textColor=navy,spaceAfter=8),
    "cap":ParagraphStyle("cap",fontName="Cal",fontSize=9.5,leading=12,textColor=gray,spaceBefore=4,spaceAfter=9),
    "title":ParagraphStyle("title",fontName="CalB",fontSize=29,leading=31,textColor=navy,spaceAfter=10),
    "h":ParagraphStyle("h",fontName="CalB",fontSize=19,leading=22,textColor=navy,spaceAfter=9),
    "sh":ParagraphStyle("sh",fontName="CalB",fontSize=14,leading=17,textColor=teal,spaceBefore=8,spaceAfter=4),
    "k":ParagraphStyle("k",fontName="CalB",fontSize=10,leading=14,textColor=teal,spaceAfter=10),
    "td":ParagraphStyle("td",fontName="Cal",fontSize=10,leading=12.5,textColor=navy),
    "th":ParagraphStyle("th",fontName="CalB",fontSize=10,leading=12.5,textColor=colors.white)
}
story=[]
WIDTH=503

def p(text,style="p"):
    story.append(Paragraph(text,styles[style]))

def table(rows,widths,pad=5):
    z=Table([[Paragraph(str(x),styles["td" if j else "th"]) for x in row]
             for j,row in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign="LEFT")
    z.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),navy),("VALIGN",(0,0),(-1,-1),"TOP"),
                           ("ROWBACKGROUNDS",(0,1),(-1,-1),[light,colors.white]),
                           ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
                           ("TOPPADDING",(0,0),(-1,-1),pad),("BOTTOMPADDING",(0,0),(-1,-1),pad)]))
    story.extend([z,Spacer(1,9)])

def fig(path,width,caption):
    with PILImage.open(path) as im: w,h=im.size
    story.append(Image(str(path),width=width,height=width*h/w))
    p(caption,"cap")

def page(k,h):
    if story: story.append(PageBreak())
    p(k,"k");p(h,"h")

def num(value,n=2):
    return "—" if value is None else f"{value:.{n}f}".replace(".",",")

def load(preset):
    return json.loads((DADOS/f"{preset}.json").read_text(encoding="utf-8"))["metricas"]

def link(url,caption):
    return '<link color="#08798c" href="'+escape(url)+'">'+caption+"</link>"

MAPA=json.loads((BASE/"simulacao/mapa.json").read_text(encoding="utf-8"))
from functools import lru_cache
@lru_cache
def dados(n):
    return json.loads((DADOS/f"{n}.json").read_text(encoding="utf-8"))


def numero_t(t):
    return "—" if t is None else num(t,1)


p("ECOM060 INSTRUMENTAÇÃO ELETRÔNICA  /  UFAL 2026.2  /  GRUPO 01","k")
p("Controle de nível<br/>em malha fechada","title")
p("Fase 2, Entrega 04","h")
p("Pablo Munih Silva de Carvalho, Pedro Henrique Balbino Rocha, Rafael José Amaral Saleme e Raniel Ferreira Athayde<br/>Professor Maurício Beltrão Rossiter","tiny")
p("R1  /  Demanda e critérios de desempenho","sh")
p("O objetivo é manter o nível de T2 próximo do setpoint e variar a bomba dentro da faixa de operação. A E02 fornece a planta e a E03 fornece os dois caminhos de leitura. O PI recebe h2 medido. O Scope registra também h2 da planta e o nível de T1.")
fig(FIG/"realimentacao.png",493,"Figura 1. Malha implementada com blocos nativos do TyphoonSim. O distúrbio soma vazão na entrada da planta, após o limitador da bomba.")
table([["Critério","Limite","Condição ou motivação"],
  ["Erro estacionário","≤4 mm em módulo","Meta da E03, equivalente a 5% da excursão de 80 mm"],
  ["Acomodação","≤900 s","Entrada sustentada na faixa de ±4 mm após cada degrau"],
  ["Sobressinal","≤10%","Até 8 mm além do novo setpoint, no sentido da mudança"],
  ["Esforço e faixa física","≤1,50 L/s de desvio","Comando relativo a 10 L/s. Limites da bomba de 7 a 13 L/s. Ambos os níveis entre 0,10 e 1,20 m."],
  ["Rejeição","Pico ≤60 mm<br/>Retorno ≤1000 s","Vazão adicional permanente de 0,50 L/s. Retorno sustentado a 1,00 ±0,004 m."]],[116,127,260])
p("Os degraus de referência partem de 1,00 m e chegam a 1,08 m ou 0,92 m. O orçamento de tempo considera a dinâmica de dois tanques, cada um com 100 s no ponto nominal. Os limites são metas de projeto adotadas para comparar as configurações.","tiny")

page("R2  /  SINTONIA COM MEDIÇÃO IDEAL","Projeto do PI e previsão algébrica")
p("Considere u = q/10, com q em L/s. Linearizando os balanços não lineares em h1=h2=1 m, cada tanque tem τ=100 s. O ganho estático até h2 é 2 m por unidade de u.")
table([["Etapa","Resultado em segundos físicos"],
       ["Planta linearizada","G(s) = 2 / (1 + 100s)²"],
       ["Controlador","C(s) = 0,25 + 0,0025/s. Kp = 0,25 m⁻¹ e Ki = 0,0025 (m·s)⁻¹."],
       ["Método","Posicionamento do zero em −0,01 s⁻¹ para cancelar um polo nominal e obtenção de ζ≈0,707 no par dominante."],
       ["Polos internos","(s + 0,01)(s² + 0,01s + 0,00005). Polos −0,01 e −0,005 ± j0,005 s⁻¹."],
       ["Malha e margens","L(s) = 0,005/[s(1+100s)]. ωc ≈ 0,00455 rad/s e margem de fase ≈ 65,5°. O modelo ideal contínuo tem margem de ganho ilimitada."],
       ["Referência e distúrbio","T = L/(1+L) prevê sobressinal de 4,32% e acomodação aproximada de 600 s. G/(1+L) tem ganho DC nulo frente ao distúrbio aditivo."]],[128,375])
p("O PI soma o comando nominal unitário à ação proporcional e ao estado integral. Antes do disparo, o estado fica em zero. No TyphoonSim, o ganho que antecede o integrador vale 100·Ki para compensar a escala de tempo. O antiwindup realimenta o desvio entre os comandos antes e depois da saturação, com ganho de rastreio de 0,04 s⁻¹ na escala física.")
p("Verificação no circuito não linear","sh")
linhas=[["Ensaio ideal","Erro final (mm)","Acomodação (s)","Pico ou sobressinal","Esforço (L/s)"]]
for e,nom in [("subida","Subida"),("disturbio","Distúrbio"),("descida","Descida")]:
    z=dados(e+"-ideal");x=z["planta"]
    linhas.append([nom,num(x["erro_mm"],3),numero_t(x["acomodacao_s"]),
        num(x["pico_mm" if e=="disturbio" else "sobressinal_pct"])+(" mm" if e=="disturbio" else "%"),
        num(z["esforco_ls"],3)])
table(linhas,[103,94,101,113,92])
p("A medição ideal coincide com o estado da planta. Os três ensaios atendem aos limites, com ambos os níveis dentro da faixa. O pico de T2 no degrau de subida supera levemente a previsão linear. Como o pico cruza a banda de 5% do degrau, o instante da última entrada na faixa é posterior à aproximação de sintonia.","tiny")

page("R3  /  DEGRAUS DE REFERÊNCIA","Leitura e nível da planta com o mesmo PI")
fig(FIG/"subida.png",497,"Figura 2. Subida de 1,00 para 1,08 m. Em azul, nível da planta. Em laranja, leitura realimentada. A faixa azul clara representa ±4 mm em torno da referência tracejada.")
a=dados("subida-real"); z=dados("subida-calibrado")
p(f"No nominal, a leitura chega perto da referência (erro {num(a['medida']['erro_mm'])} mm), com T2 em patamar {num(abs(a['planta']['erro_mm']))} mm abaixo. A integração regula o sinal que entra no comparador. Por isso, o desvio de zero, o ganho e a curvatura da E03 se convertem em erro de nível.")
fig(FIG/"descida.png",497,"Figura 3. Descida de 1,00 para 0,92 m. O mesmo desvio leva o nível físico abaixo do alvo e aumenta o pico de ultrapassagem no sentido da descida.")
p("Nos gráficos, a entrada na faixa visível e o erro de regime são propriedades distintas. O tempo de acomodação considera todo o registro após o disparo, incluindo novas saídas da faixa.","tiny")

page("R3  /  REJEIÇÃO DE PERTURBAÇÃO","Balanço de vazão e métricas dos três ensaios")
fig(FIG/"disturbio.png",490,"Figura 4. A entrada recebe 0,50 L/s adicionais. A bomba reduz seu comando para compensar a perturbação. Com a leitura nominal, o erro físico permanece mesmo após essa compensação.")
linhas=[["Ensaio e perfil","Erro final M / P<br/>(mm)","Acomodação M / P<br/>(s)","Pico M / P<br/>(% ou mm)","Esforço<br/>(L/s)"]]
for e,nom in [("subida","Subida"),("disturbio","Distúrbio"),("descida","Descida")]:
    for perfil,lab in [("ideal","ideal"),("real","real"),("calibrado","calibrado")]:
        z=dados(e+"-"+perfil);a,b=z["medida"],z["planta"]
        pico="pico_mm" if e=="disturbio" else "sobressinal_pct"
        linhas.append([f"{nom} {lab}",f"{num(a['erro_mm'])} / {num(b['erro_mm'])}",
            f"{numero_t(a['acomodacao_s'])} / {numero_t(b['acomodacao_s'])}",
            f"{num(a[pico],1)} / {num(b[pico],1)}",num(z["esforco_ls"],3)])
table(linhas,[121,93,110,107,72],pad=4)
p("M = leitura realimentada, P = nível da planta. Pico em mm no distúrbio e em porcentagem do degrau nos demais. O travessão indica ausência de acomodação sustentada na captura de 2500 s físicos. O erro final é a média assinada dos últimos 100 s. O esforço é o maior desvio do comando da bomba em relação aos 10 L/s.","tiny")

def faixa(c):
    if c is None:
        return "Atendeu"
    if c["anterior"] is None:
        return f"≤{c['primeira_falha']:g}".replace(".",",")
    return f"({c['anterior']:g}; {c['primeira_falha']:g}]".replace(".",",")

def mapa_tabela(ensaio):
    rows=[["Efeito e grandeza","Erro final","Acomodação","Pico","Esforço / faixa"]]
    nomes={"zero_mm":"Zero (mm)","tau_s":"Tomada (s)","ruido_mm":"Interferência (mm)"}
    for nome,pares in MAPA["limiares_na_grade"][ensaio].items():
        for can,rot in [("planta","P"),("medida","M")]:
            x=pares[can]
            rows.append([f"{nomes[nome]} · {rot}",faixa(x["erro"]),faixa(x["acomodacao"]),
                         faixa(x["pico"]),f"{faixa(x['esforco'])} / {faixa(x['faixa'])}"])
    table(rows,[124,74,82,74,149],pad=3.5)

page("R4  /  VARREDURA DE INTENSIDADE","Primeira falha no degrau de subida")
fig(FIG/"mapa-subida.png",488,"Figura 5. Linhas vermelhas marcam os critérios. Triângulos em 2550 s indicam rodadas sem acomodação na janela de 2500 s.")
mapa_tabela("subida")
p("P = planta e M = leitura. Cada intervalo indica a última intensidade anterior testada e a primeira falha observada. “Atendeu” indica atendimento em toda a grade. A classificação se refere aos valores ensaiados. Uma faixa de tolerância pode produzir cruzamentos em tempos diferentes mesmo com erros de patamar semelhantes.","tiny")
p("Com erro de zero b, a leitura em regime é aproximadamente r e o nível é aproximadamente r−b. A tomada acrescenta uma defasagem de atan(ωcτ). Com τ=30 s, T2 já apresenta 11,59% de sobressinal. A 0,8 Hz a planta atenua a oscilação do comando. Uma interferência de 15 mm deixa cerca de 3,66 mm de oscilação em regime na leitura, mas já viola o prazo de acomodação porque se soma ao transiente.")

page("R4  /  REJEIÇÃO DE PERTURBAÇÃO","Sensibilidade durante a compensação da vazão")
fig(FIG/"mapa-disturbio.png",488,"Figura 6. Mesmos níveis de intensidade, com setpoint fixo em 1,00 m e vazão adicional. Pico em milímetros, com limite de 60 mm.")
mapa_tabela("disturbio")
p("A curva ideal rejeita o degrau de entrada porque o integrador reduz o comando até que a vazão total equilibre a descarga. Com τ=60 s, a correção tardia eleva o pico físico a 61,50 mm e o retorno a 1094 s. A leitura filtrada registra pico de 57,98 mm, dentro do limite de 60 mm. O atraso pode mascarar uma excursão real da planta.")
mg={float(x["tau_s"]):x["fase_graus"] for x in MAPA["margens"]}
p(f"Na análise linear da tomada isolada, a margem de fase segue {num(mg[0],1)}° no ideal, {num(mg[60],1)}° com τ=60 s e {num(mg[400],1)}° com τ=400 s. Para o seno de 0,8 Hz, o RC de 0,2 Hz prevê fração residual de 1/√17, cerca de 24,3%. A média final dos casos que ainda oscilam é um indicador da janela, pois a análise linear prevê erro assintótico nulo para a tomada isolada.","tiny")

page("R5  /  AÇÃO DE PROJETO","Calibração da leitura antes do PI")
p("A correção por dois pontos usa 0,10 e 1,20 m como referências. A lei nominal da cadeia simulada fornece as duas leituras de calibração. Aplicamos a transformação afim antes do comparador e repetimos os três ensaios com o mesmo PI.")
from math import isfinite
# Coeficientes reconstituídos da lei estática da E03 em unidades de nível.
H=16000/9810
def sens(h):
    return 1.003*h+.006+.003*4*h/H*(1-h/H)
coef=1.10/(sens(1.20)-sens(.10))
offset=.10-coef*sens(.10)
p(f"<b>Correção calculada</b>   h corrigido = {num(coef,6)}·h medido {num(offset,6)} m. O ajuste remove o erro afim nos dois pontos e deixa efeitos residuais de curvatura, dinâmica, interferência e ADC.")
fig(FIG/"calibracao.png",495,"Figura 7. Erro físico no degrau de subida. A origem de cada curva é a mesma planta em equilíbrio a 1 m. O eixo foi ampliado para mostrar a entrada na banda e o patamar.")
linhas=[["Ensaio","|Erro de T2| antes / após","Acomodação após","Esforço antes / após"]]
for e,nom in [("subida","Subida"),("disturbio","Distúrbio"),("descida","Descida")]:
    a,z=dados(e+"-real"),dados(e+"-calibrado")
    linhas.append([nom,f"{num(abs(a['planta']['erro_mm']))} / {num(abs(z['planta']['erro_mm']))} mm",
        f"{numero_t(z['planta']['acomodacao_s'])} s",
        f"{num(a['esforco_ls'],3)} / {num(z['esforco_ls'],3)} L/s"])
table(linhas,[109,147,110,137])
p("O perfil nominal não acomoda o nível físico em nenhum dos três ensaios. Com a correção, o nível e a leitura atendem às metas. A correção usa um ganho e uma soma, sem memória adicional. Na subida, o esforço aumenta em relação à cadeia nominal porque a bomba agora precisa elevar o tanque até mais perto do alvo.")
p("A contrapartida em bancada é obter duas referências confiáveis e repetir a calibração quando o conjunto mudar. As leituras de calibração usadas aqui vêm do modelo, e o resultado quantifica o efeito esperado no controle simulado.","tiny")

page("R6  /  SÍNTESE E REPETIBILIDADE","Como repetir os resultados")
p("Para manter o nível em regime, o erro de zero é o efeito mais direto porque permanece na grandeza controlada. Durante mudanças, a tomada lenta reduz o amortecimento. A captação de alta frequência aparece primeiro na leitura e no comando, com pouca variação física na planta nesta faixa.")
for passo in [
    "<b>1.</b> Abra o TyphoonSim 2026.3 ativado. Mantenha as pastas das Entregas 2, 3 e 4 no mesmo diretório da Fase 2.",
    "<b>2.</b> Abra <b>typhoonsim/modelo.tse</b>, execute e abra o Scope Captura. Compare ref_m, med_m e h2_m. O caso salvo é subida-real. A leitura converge para cerca de 1,080 m e a planta para cerca de 1,068 m.",
    "<b>3.</b> Abra <b>typhoonsim/painel.cus</b> no SCADA Standalone e ative as macros. Se necessário, informe a pasta typhoonsim no campo de caminho. Execute subida-real e subida-calibrado. No segundo, confirme T2 em aproximadamente 1,0795 m.",
    "<b>4.</b> Execute os presets de distúrbio e descida. Use zero-mm-6, tau-s-60 ou ruido-mm-40 para isolar efeitos na subida. Os presets com prefixo d- repetem a sequência com distúrbio.",
    "<b>5.</b> Para gerar todos os dados, rode <b>python typhoonsim/rodar.py --grupo todos --saida CAMINHO</b> e <b>python simulacao/graficos.py --capturas CAMINHO</b>. A API oficial cria os blocos nativos e chama o solver offline, que calcula a planta e o controlador. Os scripts também exportam os dados, métricas e figuras.",
    "<b>6.</b> Confira o disparo após a pré-carga de 0,25 s elétrico. A aquisição é a cada 1 ms elétrico, equivalente a 0,1 s físico. Compare o resumo das métricas com a tabela e os intervalos no mapa.json."
    ]: p(passo)
p("Fontes","sh")
for fonte in [
    "ECOM060. Fase 2, Entrega 04, Malha Fechada: Desempenho do Controle com Instrumentação Real. Orientação da atividade.",
    "Equipe G01. Entregas 02 e 03 da Fase 2. Equivalente elétrico e instrumentação piezoresistiva, com parâmetros e capturas no mesmo repositório.",
    "Typhoon HIL. "+link("https://typhoon-hil.com/documentation/typhoon-hil-software-manual/References/lpf.html","Low-Pass Filter")+" e "+link("https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/typhoonsim.html","TyphoonSim")+" (manual oficial)."
    ]: p(fonte,"tiny")

def rodape(c,d):
    c.saveState()
    c.setStrokeColor(light);c.line(46,39,549,39)
    c.setFont("Cal",9);c.setFillColor(gray)
    c.drawString(46,25,"G01 / Fase 2, Entrega 04 / Controle em malha fechada")
    c.drawRightString(549,25,str(d.page))
    c.restoreState()

SimpleDocTemplate(str(HERE/"relatorio.pdf"),pagesize=A4,leftMargin=46,rightMargin=46,
 topMargin=46,bottomMargin=54,title="G01 - Controle de nível em malha fechada",
 author="Equipe 01 - ECOM060 UFAL").build(story,onFirstPage=rodape,onLaterPages=rodape)
