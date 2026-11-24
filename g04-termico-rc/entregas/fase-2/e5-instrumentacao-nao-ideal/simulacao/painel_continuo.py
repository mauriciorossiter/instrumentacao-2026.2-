"""Muda somente a instrumentacao, sem parar/recarregar o modelo nem alterar o PI."""
def select(hil,panel,mode):
 for k,v in {'Medicao_real_on':float(mode!='ideal'),'Correcao_on':float(mode=='compensado')}.items():
  if hil.set_scada_input_value(k,v) is False:raise RuntimeError('Falha em '+k)
 note=panel.get_widget_by_fqn('Estado')
 panel.set_property_value(note,'text','Caminho ativo: '+mode+'. Mesmo PI e mesma planta. Aguarde dois ciclos antes de comparar.\nCAPTURAR PROXIMO DEGRAU usa Capture nativo a 100 kS/s; o modelo continua rodando.\nT_planta_K = verdade do modelo; T_medida_K = indicacao bruta; Feedback_K = entrada do controlador.')
 return mode
def tau(hil,value):
 if hil.set_scada_input_value('Tau_sensor_s',float(value)) is False:raise RuntimeError('Falha ao alterar tau')
 return 'Tau = '+str(value)+' s; aguarde dois ciclos e capture novamente.'
