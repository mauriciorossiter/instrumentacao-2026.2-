# Como rodar a simulação no Typhoon HIL (Entrega final, G04)

Guia passo a passo para reproduzir, na sua máquina, a demonstração contínua do relatório *Instrumentação não ideal e seus efeitos no controle*: a planta térmica do IGBT controlada por um PI, com três caminhos de medição (ideal, real sem compensação, real com compensação).

## 0. Pré-requisitos

- **Typhoon HIL Control Center versão 2026.3** (a usada pela equipe). Outras versões (2026.2, 2026.4) não foram testadas e podem exigir ajustes.
- Não precisa de equipamento físico: tudo roda em **VHIL** (virtual HIL), com a configuração **HIL404, configuração 6**.
- Python/typhoon-python já vêm com a instalação do Typhoon. Não é preciso instalar nada extra.

## 1. Arquivos desta pasta

| Arquivo | Para que serve |
|---|---|
| `G04_Final_continuo.tse` | Esquemático da **demonstração contínua**: a malha roda sem parar, com referência periódica de 0,8 s (sobe 10 K aos 20 ms de cada ciclo). **É este que você usa.** |
| `G04_Final_degrau.tse` | Variante com um único degrau, usada nos ensaios em lote que geraram as tabelas do relatório. Não é necessária para a demonstração. |
| `G04_Final_Continuo.cus` | Painel do SCADA (botões, displays e gráfico/Capture). |
| `painel_continuo.py` | Código Python chamado pelos botões do painel. **Precisa ficar na mesma pasta do `.cus`.** |

### Sobre o `painel_continuo.py` (importante)

- **O que ele faz:** não inicializa a simulação nem define os parâmetros do teste. Esses valores já estão no modelo (`.tse`). O `.py` é chamado **quando você clica nos botões do painel**: os botões de modo (IDEAL, REAL, COMPENSADO) alteram os sinais `Medicao_real_on` e `Correcao_on`, os botões TAU alteram `Tau_sensor_s`, e o texto "Caminho ativo" do painel é atualizado.
- **Onde ele deve estar:** na **mesma pasta do `G04_Final_Continuo.cus`**. O painel executa `add_to_python_path(get_settings_dir_path())` antes do `import painel_continuo`, ou seja, procura o módulo na pasta de onde o `.cus` foi carregado. Quem usou o painel ao vivo só mexeu na interface do Typhoon, mas o arquivo precisava estar nessa pasta.
- **É necessário?** Para tudo funcionar do jeito esperado, sem erro nenhum, **sim**. Todos os botões do painel (inclusive CAPTURAR PROXIMO DEGRAU) importam esse módulo, e sem ele dão erro de importação. Provavelmente seria possível rodar a simulação sem ele (iniciar a malha, ajustar `Medicao_real_on` e `Correcao_on` à mão no SCADA e armar o Capture direto pelo gráfico), mas isso não foi testado e seria desnecessariamente mais trabalhoso. Use o arquivo.

Mantenha os quatro arquivos juntos numa pasta local sua (de preferência com caminho sem acentos nem espaços, só por precaução).

## 2. Passo a passo

### Passo 1: abrir o esquemático
1. Abra o **Typhoon HIL Control Center 2026.3**.
2. Abra o **Schematic Editor** e carregue `G04_Final_continuo.tse` (File > Open).

### Passo 2: compilar e carregar no VHIL
1. No Schematic Editor, rode a ação **Compile and (re)load model in SCADA VHIL MODE** (menu de simulação ou barra de ferramentas).
2. O Typhoon compila o modelo e gera os arquivos de destino (o `.cpd`) e abre o **HIL SCADA** com o modelo carregado em **VHIL normal**.
3. Na primeira vez a compilação pode demorar, pois o cache de bibliotecas é reconstruído. Espere terminar sem erros antes de seguir.

> Não use *External Mode*. Este painel depende do Capture/Scope nativo.

### Passo 3: abrir o painel no SCADA
1. No HIL SCADA, abra o painel: **File > Load panel** e escolha `G04_Final_Continuo.cus`.
2. Confirme que `painel_continuo.py` está na mesma pasta. Se não estiver, os botões darão erro de importação (`No module named painel_continuo`).

### Passo 4: iniciar a simulação
1. Clique no botão **Play** (Start simulation) do SCADA.
2. A malha passa a rodar sem parar. O modelo **não é recarregado** quando você usa os botões.
3. Os displays digitais (Referência, Planta, Indicação bruta, Feedback, Comando) começam a atualizar. Eles servem só de acompanhamento instantâneo. As medições "de verdade" vêm do gráfico de Capture.

### Passo 5: escolher o caminho de medição
Clique em **um** dos três botões:

| Botão | O que muda |
|---|---|
| **IDEAL** | O PI realimenta a temperatura verdadeira da planta (sensor perfeito). |
| **REAL SEM COMPENSACAO** | O PI realimenta a indicação do instrumento não ideal. A indicação chega à referência, mas a temperatura real fica abaixo. |
| **REAL COM COMPENSACAO** | Igual ao anterior, mas com a correção estática de dois pontos. A planta volta para perto da referência. |

O mesmo PI e a mesma planta são usados nos três casos. Só a seleção de medição muda. O texto na parte de baixo do painel mostra o caminho ativo.

### Passo 6: capturar
1. Depois de escolher o caminho, **espere dois ciclos de 0,8 s de modelo e aguarde o "Captured data ready" no Message Log**.
2. Clique em **CAPTURAR PROXIMO DEGRAU**. Isso arma o Capture, que dispara na próxima subida da referência (303,15 K) e grava a 100 kS/s.

### Passo 7: ver o gráfico
1. Dê **duplo clique no ícone do Capture/Scope** (o quadradinho do widget "Dinamica", no canto superior esquerdo do painel) para abrir a janela do gráfico.
2. Use o modo **Capture**.
3. Quando a captura terminar, crie o gráfico na tela do Capture com os sinais **Referencia_K**, **T_planta_K**, **T_medida_K** e **Feedback_K**:
   - `T_planta_K` é a verdade do modelo;
   - `T_medida_K` é a indicação bruta do instrumento;
   - `Feedback_K` é o que entra no PI (ideal, real ou corrigido, conforme o botão).
4. Espere a conclusão indicada no gráfico antes de trocar de caminho.

### Passo 8 (opcional): comparar outro caminho
Repita os passos 5 a 7 para os outros botões. Para comparar o efeito do atraso do sensor, volte a **REAL SEM COMPENSACAO** e use os botões **TAU 3.0 ms / 15.0 ms / 60.0 ms**. Restaure **3 ms** antes de qualquer comparação nominal.

Esses botões mantêm os demais erros nominais ligados. Não são equivalentes aos ensaios isolados do Item 7 do relatório.

## 3. O que você deve observar

- **Ideal:** a temperatura da planta acompanha a referência.
- **Real sem compensação:** a indicação (`T_medida_K`/`Feedback_K`) chega à referência, mas `T_planta_K` fica cerca de 0,67 K abaixo. O PI regula o que lê, não a verdade.
- **Real com compensação:** `T_planta_K` volta para a referência, enquanto a indicação bruta mantém seu desvio.

## 4. Problemas comuns

| Sintoma | Causa provável / solução |
|---|---|
| Botões dão erro `No module named painel_continuo` | `painel_continuo.py` não está na mesma pasta do `.cus`. |
| O Capture fica esperando para sempre | Disparo sem dispositivo vinculado (`-1`). O fonte de disparo deve estar no **dispositivo 0**. O painel já vem corrigido; se você regenerar o painel, confira esse campo. |
| Captura demora muito | Em VHIL a simulação é mais lenta que o tempo real. Dois ciclos de 0,8 s de modelo podem levar dezenas de segundos de relógio. Espere. |
| Campo de horário (UTC) do disparo aparece como indisponível | Normal em VHIL. Não indica ausência de dados. |
| Erro ao compilar ou carregar | Confirme a versão 2026.3 e a configuração HIL404 / configuração 6. Execute só um programa Typhoon por vez. |

## 5. Ao terminar

Volte para o caminho **IDEAL**, salve o painel se tiver feito alterações e pare a simulação (botão **Stop**).
