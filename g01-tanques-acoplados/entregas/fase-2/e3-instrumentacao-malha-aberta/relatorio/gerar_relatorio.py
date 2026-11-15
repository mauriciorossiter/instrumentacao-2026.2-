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

DS="https://prod-edam.honeywell.com/content/dam/honeywell-edam/sps/siot/en-us/products/sensors/pressure-sensors/board-mount-pressure-sensors/trustability-hsc-series/documents/sps-siot-trustability-hsc-series-high-accuracy-board-mount-pressure-sensors-50099148-a-en-ciid-151133.pdf"

p("ECOM060 INSTRUMENTAÇÃO ELETRÔNICA  /  UFAL 2026.2  /  GRUPO 01","k")
p("Instrumentação em<br/>malha aberta","title")
p("<b>Fase 2, Entrega 03</b> · Medição ideal e real dos dois níveis","h")
p("Pablo Munih Silva de Carvalho, Pedro Henrique Balbino Rocha, Rafael José Amaral Saleme e Raniel Ferreira Athayde<br/>Professor Maurício Beltrão Rossiter","tiny")
p("R1  /  O que a planta exige da medição","sh")
p("Mantemos o circuito da E02. Os nós V1 e V2 representam h1 e h2 pela lei V = 10h. A instrumentação apenas observa ambos os nós e a bomba mantém o comando em malha aberta.")
fig(E2,483,"Figura 1. Equivalente elétrico da E02, usado como planta. As fontes em cinza só preparam a condição inicial.")
table([["Critério de projeto","Origem no modelo da E01","Valor"],
       ["Nível em T1 e T2","Faixa hidráulica adotada","0,10 a 1,20 m"],
       ["Pressão manométrica","p = ρgh, com ρ = 1000 kg/m³ e g = 9,81 m/s²","0,981 a 11,772 kPa"],
       ["Banda útil","τ nominal de 100 s; pulso de 30 s motiva 1/30 Hz","DC a cerca de 0,033 Hz"],
       ["Resolução","1% em q eleva h de 1 para 1,0201 m; alvo de 10 incrementos","≤2 mm"],
       ["Incerteza alvo","A alocação de 20% sobre os 20,1 mm do menor degrau dá 4,02 mm","U(k=2) ≤4 mm"]],[105,255,143])
p("Na linearização, fₚ = 1/(2πτ) = 0,00159 Hz em cada tanque, e a cascata de h2 tem corte de 0,00102 Hz. Mesmo na borda de 0,10 m, τ = 31,6 s e fₚ = 0,00503 Hz. A banda adotada inclui componentes mais rápidas do pulso sem tratar o degrau como limitado em frequência.","tiny")

page("R2–R3  /  MODELO E CONDICIONAMENTO","Da coluna de água até o valor em metros")
p("Cada tomada mede a pressão acima da atmosfera junto ao fundo. A pressão deforma um diafragma de silício e altera as resistências piezoresistivas da ponte; o ASIC interno excita, amplifica e compensa seu sinal. Usamos o <b>Honeywell TruStability HSC, faixa 160MG</b>, manométrico, analógico 10–90% e 5 V. Em bancada, prever interface de isolamento ou verificar a compatibilidade do líquido e da opção de porta antes de conectar.")
fig(FIG/"cadeia.png",495,"Figura 2. Mesma cadeia nos dois canais. Fluxo somente de observação; nenhuma realimentação para a planta.")
p("<b>Transferência:</b> p = 9810h; V = 5[0,1 + 0,8(p/16000)] = 0,5 + 2,4525h. Assim, o intervalo de interesse ocupa 0,745 a 3,443 V na saída. O ideal entrega h diretamente, com ganho 1.")
table([["Modelo / ajuste no SCADA","Valor nominal e por quê"],
       ["Zero, ganho e curvatura","Estimativas: +6 mm, +0,3% da leitura e +3 mm de amplitude. A curvatura normalizada 4r(1−r) multiplica a amplitude, com r = p/16000. Não são tolerâncias independentes da ficha."],
       ["Dinâmica da tomada","τ = 0,2 s como hipótese didática da montagem. O HSC tem resposta típica de 1 ms na ficha; não atribuímos os 0,2 s ao chip."],
       ["Interferência","Seno de 0,8 Hz, ±2 mm equivalentes (4,9 mV de pico) como captação periódica na interface. A mesma perturbação nos canais facilita comparar."],
       ["Alimentação e interface","5 V regulados, desacoplamento e referência do ADC da mesma fonte (insensibilidade inerente à variação comum de alimentação). Modelo nominal com referência fixa."],
       ["Filtro RC","Buffer seguido de R = 79,6 kΩ e C = 10 µF nominais (fc ≈ 0,2 Hz); filtra interferência e perde cerca de 1,35% a 0,033 Hz. Implementação por bloco Low-Pass Filter."],
       ["A/D e correção","12 bits/5 V, um LSB ≈0,498 mm. Após a leitura, remover 0,5 V, subtrair o zero calibrado equivalente e dividir por 2,4525 V/m. Correção calculada de zero; ganho e curvatura residuais permanecem."]],[113,390])
p("Ficha: ±0,25% FSS BFSL a 25 °C (≈4,08 mm), banda total ±1% FSS (≈16,31 mm), resolução de saída 0,03% FSS (≈0,489 mm). A quantização explícita simula o ADC externo; a resolução interna é considerada no orçamento e não replicada como outro quantizador. A excitação e o ganho interno do ASIC entram na transferência agregada.","tiny")

page("R4  /  ENSAIOS COM O MODELO NATIVO","Degrau e condição inicial")
fig(FIG/"degrau.png",497,"Figura 3. Degrau de +5%. A curva ideal cobre a da planta; o canal real exibe erro de leitura nos dois níveis.")
fig(FIG/"inicial.png",497,"Figura 4. Níveis iniciais de 1,15 m e 0,60 m. A dinâmica não troca o sentido da recuperação: T1 desce e T2 sobe.")
p("O ensaio começa após 0,25 s elétrico de pré-carga. Reconvertemos o tempo por t = 100(tₑ − 0,25) e comparamos a cada amostra as saídas em metros. As curvas mostradas ficam com zoom no transiente, mas as métricas usam a captura de 2000 s físicos.")

page("R4  /  MÉTRICAS E ISOLAMENTO","Pulso de vazão e comparação por tanque")
fig(FIG/"pulso.png",415,"Figura 5. Pulso de +20% por 30 s. O pico de T2 é posterior ao de T1 e o deslocamento de zero permanece após o pulso.")
rows=[["Ensaio","Tanque","Erro máx.<br/>mm / %","Δt50<br/>s","t10–90 ideal / real<br/>s","Marca ideal / real<br/>m"]]
for ens in ["degrau","inicial","pulso"]:
    for h,x in load(ens).items():
        a,b=x["ideal"],x["real"]
        rows.append([ens.capitalize(),h.upper(),f'{num(x["erro_max_mm"])} / {num(x["erro_rel_max_pct"])}',
            num(x["atraso_50_s"]),f'{num(a["tempo_10_90_s"],1)} / {num(b["tempo_10_90_s"],1)}',
            f'{num(a["h_caracteristico_m"],4)} / {num(b["h_caracteristico_m"],4)}'])
table(rows,[60,55,84,57,125,122])
p("A marca é patamar final para o degrau, leitura inicial para a recuperação e pico para o pulso. O atraso de medição é reportado como a diferença de cruzamentos a 50% da excursão de cada curva; limiares próprios evitam atribuir um erro de zero a atraso. Com quantização e interferência, Δt50 é uma diferença aparente e pode mudar de sinal. O erro relativo usa o nível instantâneo da planta.","tiny")
rows=[["Efeito isolado no degrau","T1: máx. (mm)","T2: máx. (mm)","T2: patamar (mm)"]]
for label,k in [("Tudo em bypass","referencia"),("Zero","zero-6mm"),("Ganho","so-ganho"),
 ("Curvatura","so-curvatura"),("Dinâmica","tau-0p2s"),("Interferência","so-interferencia"),("Filtro","so-filtro"),("ADC","so-adc")]:
    a=load(k)
    rows.append([label,num(a["h1"]["erro_max_mm"]),num(a["h2"]["erro_max_mm"]),num(a["h2"]["erro_final_mm"])])
table(rows,[172,110,110,111],pad=3.5)

page("R5  /  PREVISÃO E EXACERBAÇÃO","A mesma planta, com erros diferentes")
fig(FIG/"exacerbacao.png",497,"Figura 6. Resíduos em h2. Na interferência, subtraímos a rodada de referência com o mesmo RC e sem seno para isolar a contribuição.")
att=json.loads((BASE/"simulacao/atenuacao.json").read_text())
rows=[["Previsão registrada antes da execução","Observação na captura","Por que acontece"]]
rows.append(["Zero +6 / +20 / +60 mm: soma ao patamar.",
           "T2: "+" / ".join(num(load(f"zero-{v}mm")["h2"]["erro_final_mm"],1) for v in (6,20,60))+" mm.",
           "Uma constante não muda o formato da curva."])
rows.append(["τ = 0,2 / 10 / 60 s: atraso aumenta e o patamar se conserva.",
           "Δt50 de T2: "+" / ".join(num(load(f"tau-{v}s")["h2"]["atraso_50_s"],1) for v in ("0p2","10","60"))+" s.",
           "O bloco segue uma média exponencial; para τ pequeno, e ≈ −τ dh/dt."])
rows.append(["Seno ±2 / ±10 / ±40 mm: RC deixa passar 1/√17 ≈ 24,3% da amplitude.",
           "Amplitude em T2: "+" / ".join(num(att[str(v)]["amplitude_observada_mm"],2) for v in (2,10,40))+" mm.",
           "A frequência é quatro vezes fc; filtrar reduz a oscilação, mas não o erro de zero."])
table(rows,[170,165,168])
a=load("degrau")["h2"];b=load("zero-corrigido")["h2"]
p("Síntese e decisão de projeto","sh")
p(f"No nominal, <b>o desvio de zero é o maior efeito isolado persistente</b>; ganho e curvatura também desviam a leitura de patamar. Subtrair 6 mm reduz o viés de T2 no degrau de {num(a['erro_final_mm'])} para {num(b['erro_final_mm'])} mm. O resíduo ainda supera 4 mm, mesmo sem estimar uma incerteza experimental. Para indicações absolutas e limites de segurança, aferir zero, ganho e curvatura com coluna de referência; filtrar não corrige esses erros.")
p("Para detectar transientes, uma tomada obstruída ou com dinâmica muito lenta é mais crítica que um zero fixo: desloca o instante percebido e deforma a excursão. A perturbação periódica afeta limiares instantâneos; o RC a reduz, com contrapartida de atraso. Uma verificação experimental em vários níveis e temperaturas é necessária para demonstrar U(k=2).")
p("Execução: solver TyphoonSim offline; todas as curvas 'reais' são da cadeia simulada. Não se mediu um sensor físico.","tiny")

page("R6  /  REPETIBILIDADE","Como repetir os ensaios")
for desc in [
 "<b>1.</b> Abra TyphoonSim 2026.3 com licença ativa. Mantenha no mesmo repositório as pastas irmãs da E02 e E03; o gerador carrega a planta de <font name='CalB'>e2-equivalente-eletrico/typhoonsim/modelo-offline.tse</font>.",
 "<b>2.</b> Para inspecionar a montagem nominal, abra <b>typhoonsim/modelo.tse</b>, clique Run e abra o Scope Captura. V1/V2 são volts; h1_m, h2_m e caminhos ideal/real são metros.",
 "<b>3.</b> Abra <b>typhoonsim/painel.cus</b> no Standalone HIL SCADA e ative as macros. Se necessário, informe a pasta typhoonsim da E03 no campo Pasta dos scripts. Selecione o preset e clique Executar no TyphoonSim. Os controles valem na próxima rodada.",
 "<b>4.</b> Compare degrau, inicial e pulso com as Figuras 3 a 5. Use referência e os presets isolados; para a demonstração ao vivo, altere o zero de 6 para 60 mm em zero-6mm e repita.",
 "<b>5.</b> Para reprodução em lote com Python/API oficial, execute <b>python typhoonsim/executar.py --todos --saida CAMINHO</b> a partir da pasta da E03. Depois rode <b>python simulacao/graficos.py --capturas CAMINHO</b>. Os dados originais e parâmetros estão nos JSONs da entrega.",
 "<b>6.</b> Verifique no JSON a origem typhoonsim-offline. A CLI e a macro chamam o mesmo executador. O passo de processamento é 100 µs elétrico, a aquisição é 1 ms elétrico (0,1 s físico) e o solver para em 20,25 s elétricos."
 ]: p(desc)
p("Fontes e referência da montagem","sh")
for src in [
 "UFAL, ECOM060. Fase 2, Entrega 03: Instrumentação em Malha Aberta, orientação e anexo.",
 "G01. Entrega 01, Caracterização da planta, 2026; Entrega 02, Equivalente elétrico, 2026. Relatórios, modelos e resultados no mesmo repositório.",
 "Honeywell. "+link(DS,"TruStability HSC Series, datasheet 50099148, rev. B")+". Tabelas de operação analógica e faixas 160MG; guia de pedido e função 10–90%.",
 "Typhoon HIL. "+link("https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/concepts/typhoonsim.html","TyphoonSim")+", "+link("https://typhoon-hil.com/documentation/typhoon-hil-software-manual/References/lpf.html","Low-Pass Filter")+" e "+link("https://www.typhoon-hil.com/documentation/typhoon-hil-software-manual/References/typhoonsim_scope.html","Scope")+" (manual oficial)."
 ]: p(src,"tiny")

def rodape(c,d):
    c.saveState()
    c.setStrokeColor(light);c.line(46,39,549,39)
    c.setFont("Cal",9);c.setFillColor(gray)
    c.drawString(46,25,"G01 / Fase 2, Entrega 03 / Instrumentação em malha aberta")
    c.drawRightString(549,25,str(d.page))
    c.restoreState()

SimpleDocTemplate(str(HERE/"relatorio.pdf"),pagesize=A4,leftMargin=46,rightMargin=46,
 topMargin=46,bottomMargin=54,title="G01 - Instrumentação em malha aberta",
 author="Equipe 01 - ECOM060 UFAL").build(story,onFirstPage=rodape,onLaterPages=rodape)
