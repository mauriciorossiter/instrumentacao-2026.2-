# Previsões antes das capturas

A planta da E02 está linearizada em h1 = h2 = 1 m e q0 = 10 L/s. O comando é
adimensional, u = q/q0. Como ambos os tanques têm τ = 100 s e o ganho de
nível em regime por unidade de u vale 2 m, G(s) = 2/(1+100s)².

## Especificação de projeto

Os setpoints 1,08 e 0,92 m representam mudanças operacionais em torno de 1 m.
A margem de leitura de 4 mm vem da E03 e equivale a 5% do degrau de 80 mm.
Acomodação em 900 s corresponde a nove constantes nominais e deixa margem
diante da previsão de segunda ordem. O tanque deve permanecer de 0,10 a 1,20 m.
Para conter excursões de nível e da bomba, admitimos até 10% de sobressinal do
degrau e até 1,50 L/s de desvio do comando em relação aos 10 L/s nominais.
Os limites físicos simulados da bomba são 7 a 13 L/s. Para perturbação
permanente aditiva de +0,5 L/s na entrada, o pico absoluto de afastamento
de 1 m deve ser ≤60 mm, com retorno sustentado à faixa de ±4 mm em ≤1000 s.
São metas de projeto da equipe, pois a atividade não fornece limites para a aplicação.

## Sintonia e previsão

PI = 0,25 + 0,0025/s. O zero em −0,01 s⁻¹ simplifica a sintonia local.
A equação característica é (s+0,01)(s²+0,01s+0,00005).
Os polos são −0,01 e −0,005±j0,005 s⁻¹. Para a referência ideal, ζ≈0,707,
sobressinal previsto de 4,32% e tempo aproximado de 600 s a 5%.
O termo integral zera o erro estacionário da grandeza realimentada.
O ganho de malha cruza 0 dB perto de 0,00455 rad/s, com margem de fase
de aproximadamente 65,5° e margem de ganho ilimitada no modelo ideal contínuo.
A rejeição de perturbação tem função δh₂/δd = G/(1+G·PI) e ganho DC zero.

## Características isoladas na subida

- **Zero**. Se a leitura vale h+b, a integração impõe h≈r−b. A fronteira
  algébrica do erro estacionário de 4 mm ocorre em |b|=4 mm. A leitura
  ainda pode ficar no setpoint. A acomodação do nível também pode falhar
  nessa mesma fronteira. Os dois sinais serão avaliados.
- **Tomada lenta**. Acrescenta 1/(1+τs) à leitura. No cruzamento da nova
  malha, subtrai-se atan(ωcτ) da fase. Ao aumentar τ, espera-se menor
  amortecimento e eventual violação de pico ou acomodação, ainda com
  erro em regime nulo para o sensor isolado.
- **Interferência**. Seno a 0,8 Hz e RC de 0,2 Hz. A amplitude de leitura
  residual é aproximadamente 0,243A em escala de nível. Compare com
  4 mm a partir de A≈16,5 mm. A planta atenua fortemente essa frequência
  (|G(j2π·0,8)|≈8×10⁻⁶ m/pu), embora o PI varie o comando.

A correção proposta é afim de dois pontos (0,10 m e 1,20 m), obtidos da lei
estática nominal da cadeia E03 em bancada simulada. O cálculo pode remover
zero e inclinação efetivos, com curvatura e quantização residuais. Não adiciona
um filtro nem altera os ganhos do PI.


## Rejeição de perturbação na mesma grade

Repetiremos a grade com referência fixa em 1 m e +0,50 L/s depois da
bomba. O offset desloca o nível antes de o PI compensar a entrada extra.
Para offset positivo, o desvio inicial de nível provocado pelo distúrbio é
parcialmente compensado no pico, mas permanece o erro −b em regime.
A tomada lenta retarda a redução de vazão do PI e deve elevar o pico
ou prolongar a recuperação. A interferência provoca oscilação na leitura,
e a inércia da planta deve conservar o retorno do nível físico quando o
seno já impede o retorno sustentado da leitura à banda de ±4 mm.
