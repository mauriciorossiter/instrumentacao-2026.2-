"""Abre o SCADA Standalone incluido no TyphoonSim, sem Control Center."""
from pathlib import Path
import os
import shutil
import subprocess
HERE=Path(__file__).resolve().parent

if __name__=='__main__':
    instalacao=Path(os.environ.get('TYPHOONPATH',r'C:\Program Files\TyphoonSim 2026.3'))
    exe=instalacao/'typhoon_hil.exe'
    if not exe.exists():
        path=shutil.which('typhoon_hil.exe')
        if not path:raise SystemExit('Configurar TYPHOONPATH para a pasta da instalacao TyphoonSim.')
        exe=Path(path)
    subprocess.Popen([str(exe),'sa_hs','--panel',str(HERE/'painel-offline.cus'),'--start'],cwd=HERE)
