# -*- coding: utf-8 -*-
"""
ECOM060 - Grupo 08 - Fase 1, Entrega 03
Diagnostico: imprime os NOMES REAIS (de API) das propriedades e terminais dos blocos que o
gerador de ensaios usa, em especial o 'core/SCADA Input' (novo nesta entrega).
Se monta_modelo_e03.py falhar ou avisar "propriedade ... nao aplicada", rode e mande a saida:
    <python com typhoon_hil_api> inspeciona_blocos_e03.py > inspecao_e03.txt
"""
from typhoon.api.schematic_editor import model

BLOCOS = ['core/SCADA Input', 'core/Sign', 'core/Abs', 'core/Product', 'core/Clock',
          'core/Probe', 'core/Unit Delay', 'core/Min Max', 'core/Sum']

model.create_new_model('inspecao_e03')
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
            print('   prop  %-32s = %r' % (k, v))
    except Exception as e:
        print('   (propriedades) erro:', e)
    try:
        for t in model.get_items(parent=c, item_type='terminal'):
            print('   term  %s' % model.get_name(t))
    except Exception as e:
        print('   (terminais) erro:', e)
model.close_model()
