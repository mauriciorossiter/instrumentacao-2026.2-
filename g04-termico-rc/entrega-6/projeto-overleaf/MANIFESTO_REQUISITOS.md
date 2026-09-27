# Rastreio da orientação do Capítulo 5 - Equipe 04

Esta versão mantém o `.tse` corrigido após a falha de `pre_compile` e corrige a decimação do script de Capture. O erro de passo informado pelo usuário ocorreu após a compilação, o carregamento e a obtenção do buffer, evidenciando que essa etapa do modelo passou no Typhoon do usuário. A captura válida a 10 kS/s e seus resultados ainda precisam ser obtidos. As versões anteriores foram preservadas.

| Exigência do professor | Onde está atendida | Estado em 18/09/2026 |
| --- | --- | --- |
| Seção 5.2 - modulação em amplitude | Relatório, seções 1-2; `Equipe_04_ModulacaoAM.tse` | Teoria e modelo preparados |
| Portadora + mensagem no TyphoonSim | `Fontes e regimes AM` no `.tse` | Compilação e carregamento superados; captura válida pendente |
| Bloco modulador implementado | `Modulador AM` no `.tse` | Compilação e carregamento superados; medição pendente |
| Sinal no domínio do tempo | Figura teórica no relatório; `resultados_vhil/tempo_mu*.csv` após captura | Figura teórica pronta; figura VHIL pendente |
| Domínio da frequência e bandas laterais | Derivação e figura teórica; `resultados_vhil/espectro_mu*.csv` após captura | Teoria pronta; FFT VHIL pendente |
| Variar índice, discutir sub- e sobremodulação | Casos 0,5; 1,0; 1,5; Tabela 1 e discussão do relatório | Completo teoricamente; confirmação VHIL pendente |
| Relatório autossuficiente em PDF | `Equipe_04_ModulacaoAM.tex` | Fonte atualizado; PDF final depende da captura |
| Identificação da equipe e livro-texto | Capa, bibliografia e seção 1 | Completo |
| Dados/scripts auxiliares novos anexados | `.tse`, scripts, CSV/JSON gerados | Scripts prontos; CSV/JSON VHIL pendentes |
| Nome `Equipe_04_ModulacaoAM.pdf` | Exportação final Overleaf, conforme README | Pendente da captura |

Não há `.cus` obrigatório na orientação. O `.cpd` é gerado pela compilação do `.tse` no computador com Typhoon HIL; não há `.cpd` anexado neste pacote.
