# Equipe 04 - Capítulo 5, seção 5.2: modulação em amplitude

**Correção da captura (18/09/2026).** O `.tse` é o mesmo da versão que superou o erro de `pre_compile`. O erro posterior de passo de captura (`2e-07 s` em vez de `100 us`) vinha do argumento de decimação `1` em `capturar_vhil.py`: o Capture registrava cada passo-base de 0,2 µs. O script agora lê o passo-base do modelo carregado e calcula automaticamente a decimação inteira. Para 0,2 µs, usa `500`, resultando em 100 µs por amostra. As versões anteriores continuam preservadas. A captura real ainda precisa ser repetida no computador com Typhoon.

Este projeto atende à orientação `ECOM060_Orientacao_Capitulo5.pdf`: modelo AM no TyphoonSim, três índices de modulação, formas de onda no tempo, bandas laterais no espectro e relatório autossuficiente. **A captura VHIL ainda não foi executada neste computador**, pois nele não há Typhoon HIL instalado. O PDF de prévia contém apenas previsões analíticas e não deve ser entregue como relatório experimental final.

## O que há no projeto

| Arquivo/pasta | Função |
| --- | --- |
| `Equipe_04_ModulacaoAM.tse` | Esquemático TyphoonSim: fonte, sequenciador, modulador e cinco probes. |
| `capturar_vhil.py` | Compila, carrega em Virtual HIL e captura 36 mil amostras a 10 kS/s. |
| `analisar_captura.py` | Valida o CSV VHIL e gera tabelas e gráficos para o LaTeX. |
| `montar_entrega_final.py` | Reúne PDF final, dados e scripts num ZIP depois da compilação no Overleaf. |
| `Equipe_04_ModulacaoAM.tex` | Relatório Overleaf. Detecta automaticamente se há resultados VHIL. |
| `gerar_referencia_analitica.py` e `referencia_analitica/` | Apenas curvas teóricas ilustrativas, nunca dados de simulação. |
| `diagrama_am.mmd` | Diagrama de blocos em Mermaid, para visualizar em mermaid.live. |
| `MANIFESTO_REQUISITOS.md` | Relação entre cada item da orientação e a evidência produzida. |

## Parâmetros e resultado esperado

- Portadora: `c(t)=cos(2*pi*500*t)`, pico de 1 V.
- Mensagem normalizada: `m(t)=cos(2*pi*25*t)`.
- Modulador: `u(t)=1+mu*m(t)`, `s(t)=u(t)*c(t)`.
- Índices: `mu=0,5`, `1,0` e `1,5`, cada um por 0,4 s, com repetição.
- Passo: 100 µs; taxa de amostragem: 10 kS/s; Nyquist: 5 kHz.
- Bandas: 475 e 525 Hz. Cada pico lateral esperado tem amplitude `mu/2`, enquanto a portadora permanece com pico 1 V.
- Mínimo de `u(t)`: 0,5; 0; -0,5, respectivamente. Valor negativo identifica sobremodulação e inversão de fase.

## Execução no computador com Typhoon HIL

1. Extraia todo o ZIP do projeto numa pasta local, sem modificar o `.tse` depois de capturar. Instale/abra o Typhoon HIL Control Center que você usou nas atividades anteriores. Use TyphoonSim/Virtual HIL, não o dispositivo físico. O modelo seleciona HIL404 Base 1, como na atividade anterior. A versão projetada é 2026.2.
2. Abra `Equipe_04_ModulacaoAM.tse` no Schematic Editor. Confira visualmente os dois blocos `C function`, as conexões e os cinco probes: `mensagem_norm`, `portadora`, `indice_modulacao`, `envoltoria_assinada`, `sinal_am`. A compilação manual é opcional; o script do passo 4 também compila. Se a validação falhar, copie a mensagem completa antes de modificar o modelo.
3. Abra o terminal/console com o Python do Typhoon HIL. No Windows PowerShell, entre na pasta extraída usando `Set-Location 'CAMINHO_DA_PASTA'`. Confirme que `typhoon-python` funciona. Se o comando não estiver no PATH, use o terminal Python incluído no Typhoon HIL Control Center e seu caminho do executável; não execute com um Python sem o pacote `typhoon`.
4. Rode `typhoon-python capturar_vhil.py`. O script compila, carrega o modelo em VHIL, inicia a simulação e usa **Capture** para registrar os cinco sinais no mesmo eixo temporal. Ele exibirá o passo-base, a decimação calculada e o passo previsto; no seu caso, esperamos `2e-07 s`, `500` e `0.0001 s`. Por padrão, o limite de espera é 300 segundos de relógio; se o VHIL estiver lento, rode `typhoon-python capturar_vhil.py --timeout 600`. Não use `read_analog_signals` em polling: isso pode subamostrar a portadora de 500 Hz e invalidar a FFT.
5. O script informa um caminho como `capturas/captura_AAAAMMDD_HHMMSS`. Nessa pasta estarão `Equipe_04_ModulacaoAM_captura.csv` e `Equipe_04_ModulacaoAM_metadados.json`. Confirme nos metadados: origem `TyphoonSim/Virtual HIL`, `decimacao_capture` de 500 se o passo-base for 0,2 µs, aproximadamente 10.000 amostras/s, 36.000 linhas e índices 0,5, 1,0 e 1,5. Os hashes do CSV, `.tse` e `.cpd` são registrados.
6. Execute `typhoon-python analisar_captura.py capturas/captura_AAAAMMDD_HHMMSS`, substituindo pelo nome real informado no passo 5. Serão criados `resultados_vhil/medidas.tex`, `resultados_vhil/resumo.json` e seis CSVs de figuras. O analisador recusa captura incompleta, modelo alterado ou hash de CSV divergente.

**Nenhum painel `.cus` é necessário** para essa aquisição. Para inspeção adicional no HIL SCADA, carregue o `.cpd` em modo VHIL, crie um painel novo e adicione um widget Capture/Scope com os cinco probes. Configure amostragem de 10 kS/s e uma janela de ao menos 3,6 s; essas imagens são opcionais. Os dados usados no relatório vêm do script, com taxa e origem verificadas.

## Compilar a versão final no Overleaf

1. Crie um projeto no Overleaf e envie a pasta do projeto com sua estrutura preservada; após a aquisição, inclua também a pasta `resultados_vhil/`. Se fizer upload via ZIP, confira se `Equipe_04_ModulacaoAM.tex` está na raiz do projeto.
2. Defina `Equipe_04_ModulacaoAM.tex` como **Main document**. Selecione XeLaTeX ou pdfLaTeX; os dois são compatíveis com o fonte. Compile. O título deve mostrar **“Resultados experimentais VHIL incluídos”**. Se continuar mostrando “Prévia técnica”, `resultados_vhil/medidas.tex` não está na posição correta ou não foi enviado.
3. Verifique no PDF: tabela medida de três índices, gráfico temporal capturado, FFTs capturadas, hashes, discussão e conclusão sem ressalva de pendência. Confira especificamente que o espectro mostra 475, 500 e 525 Hz e que `u_min` é negativo no caso `mu=1,5`.
4. Baixe o PDF e salve exatamente como `Equipe_04_ModulacaoAM.pdf`, nome solicitado pelo professor. Não use o PDF de prévia.
5. Ponha esse PDF na pasta do projeto e execute `typhoon-python montar_entrega_final.py Equipe_04_ModulacaoAM.pdf capturas/captura_AAAAMMDD_HHMMSS`, usando o nome real da pasta. O script validará hashes e arquivos e criará `Entrega_Final_Equipe_04_ModulacaoAM.zip`. Confira o PDF visualmente antes de enviar; o script não interpreta seu conteúdo.

## O que enviar ao professor

O enunciado pede **um PDF por equipe** e os dados ou scripts auxiliares novos. Para a Equipe 04, envie:

1. `Equipe_04_ModulacaoAM.pdf` **após incluir a captura VHIL**;
2. `Equipe_04_ModulacaoAM.tse`;
3. `Equipe_04_ModulacaoAM_captura.csv` e `Equipe_04_ModulacaoAM_metadados.json` da mesma pasta de captura;
4. `capturar_vhil.py` e `analisar_captura.py`.

Você pode reunir os itens 2-4 num ZIP de anexos se a plataforma de entrega permitir. O `.cpd` e o `.cus` não são exigidos pelo enunciado. O `.tex`, `diagrama_am.mmd` e os CSVs teóricos podem ser anexados como material suplementar, mas não substituem os cinco itens acima.

## Se algo falhar

- **“unknown type name real”**: só os terminais Typhoon usam `real`; as variáveis C do projeto usam `double` ou `int`. Confirme que não houve edição manual no `C function`.
- **`pre_compile`: `'NoneType' object has no attribute 'value'` em `Fontes e regimes AM`**: confirme que abriu este `.tse` corrigido, não o arquivo do primeiro ZIP. O bloco não deve conter `#include` nem constantes no campo *Arbitrary definitions*. Se persistir, salve o arquivo novamente pelo Schematic Editor e envie o traceback completo ou o arquivo `.tse` salvo para inspeção.
- **Probe não encontrado**: abra o modelo compilado e confira os nomes públicos exatos acima. Recompile se editou o `.tse`.
- **Capture não inicia**: feche outra captura no HIL SCADA e inicie novamente o script. Use VHIL ativo, não `offlineMode`.
- **Passo de captura `2e-07 s`**: você está usando o script anterior, cuja decimação era 1. Use o `capturar_vhil.py` deste pacote. A decimação correta é 500 quando o passo-base é 0,2 µs. Não faça FFT de leituras por polling.
- **Tempo limite excedido**: use `--timeout 600` e confira se a simulação está em execução. Não gere dados fictícios para contornar a falha.
- **Overleaf ainda mostra “Prévia”**: suba todos os arquivos de `resultados_vhil/` e confira o caminho relativo ao `.tex` principal.

As funções de compilação, carregamento e Capture estão documentadas nas [APIs oficiais do Typhoon HIL](https://www.typhoon-hil.com/documentation/typhoon-hil-api-documentation/typhoon_api.html). O ZIP atual foi validado estruturalmente e o LaTeX de prévia compila, mas a compilação do `.tse` e a captura precisam ser confirmadas no Typhoon instalado.
