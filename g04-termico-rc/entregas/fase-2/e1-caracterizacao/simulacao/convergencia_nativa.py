"""Dois passos nativos adicionais. Preserva as execuções principais."""
from modelo import ROOT
import typhoon_modelo as gen
import executar_typhoon as run

if __name__=='__main__':
 for h,label in [(2e-6,'h2us'),(.2e-6,'h0p2us')]:
  folder=ROOT/'verificacao_nativa'/label;folder.mkdir(parents=True,exist_ok=True)
  gen.NATIVE_DT=h;gen.ROOT=folder;run.ROOT=folder
  run.run('degrau_4r')
