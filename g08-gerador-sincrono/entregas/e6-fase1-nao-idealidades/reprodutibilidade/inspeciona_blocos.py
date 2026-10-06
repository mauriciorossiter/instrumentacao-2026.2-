# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 02
Diagnostico: cria, num modelo vazio, cada bloco nativo usado pelo modo 'hibrido' e pelo
contrafactual R8 de monta_modelo.py e imprime os NOMES REAIS (de API) das propriedades e
dos terminais nesta versao do Typhoon. A documentacao publica so mostra os rotulos da
interface ('Round function', 'Operation'...), nao os nomes internos.

Uso (TyphoonSim + Schematic Editor abertos):
    <python com typhoon_hil_api> inspeciona_blocos.py  > inspecao.txt
Se monta_modelo.py cair no plano B (modo 'c'), mande o inspecao.txt.
"""
from typhoon.api.schematic_editor import model

BLOCOS = ['core/Constant', 'core/Sum', 'core/Min Max', 'core/Unit Delay', 'core/Round',
          'core/Gain', 'core/Variable Resistor', 'core/Random Source']

model.create_new_model('inspecao')
for tipo in BLOCOS:
    print('=' * 70)
    print(tipo)
    try:
        c = model.create_component(tipo)
    except Exception as e:
        print('   NAO EXISTE / nao criou:', e)
        continue
    try:
        for k, v in model.get_property_values(c).items():
            extra = ''
            try:
                combo = model.get_property_combo_values(model.prop(c, k))
                if combo:
                    extra = '   opcoes=%s' % (combo,)
            except Exception:
                pass
            print('   prop  %-32s = %r%s' % (k, v, extra))
    except Exception as e:
        print('   (propriedades) erro:', e)
    try:
        for t in model.get_items(parent=c, item_type='terminal'):
            print('   term  %s' % model.get_name(t))
    except Exception as e:
        print('   (terminais) erro:', e)
model.close_model()
