"""Monta ZIP final APOS obter captura VHIL e baixar PDF final do Overleaf.

Exemplo:
    typhoon-python montar_entrega_final.py Equipe_04_ModulacaoAM.pdf capturas/captura_AAAAMMDD_HHMMSS

O script nao gera dados nem altera o PDF: apenas confere arquivos e os agrega.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parent
PDF_NAME = "Equipe_04_ModulacaoAM.pdf"
DATA_NAME = "Equipe_04_ModulacaoAM_captura.csv"
METADATA_NAME = "Equipe_04_ModulacaoAM_metadados.json"
RESULT_FILES = [
    "medidas.tex", "resumo.json",
    *[f"tempo_mu{tag}.csv" for tag in ("05", "10", "15")],
    *[f"espectro_mu{tag}.csv" for tag in ("05", "10", "15")],
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="PDF final baixado do Overleaf")
    parser.add_argument("captura", type=Path, help="Pasta criada por capturar_vhil.py")
    args = parser.parse_args()
    pdf = args.pdf.resolve()
    capture = args.captura.resolve()
    if pdf.name != PDF_NAME or not pdf.is_file() or pdf.read_bytes()[:4] != b"%PDF":
        raise ValueError(f"Informe o PDF FINAL com nome exato {PDF_NAME}.")
    data = capture / DATA_NAME
    metadata_path = capture / METADATA_NAME
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("origem") != "TyphoonSim/Virtual HIL; API hil.start_capture":
        raise ValueError("A origem VHIL nao esta documentada.")
    if sha256(data) != metadata["sha256_dados"]:
        raise ValueError("Hash do CSV nao corresponde aos metadados.")
    model = ROOT / "Equipe_04_ModulacaoAM.tse"
    if sha256(model) != metadata["sha256_modelo"]:
        raise ValueError("O .tse nao e o mesmo que gerou a captura.")
    results = ROOT / "resultados_vhil"
    for name in RESULT_FILES:
        if not (results / name).is_file():
            raise ValueError(f"Falta resultado VHIL: {name}")
    summary = json.loads((results / "resumo.json").read_text(encoding="utf-8"))
    if summary.get("sha256_dados") != metadata["sha256_dados"]:
        raise ValueError("A analise VHIL pertence a outra captura.")

    destination = ROOT / "Entrega_Final_Equipe_04_ModulacaoAM.zip"
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.write(pdf, PDF_NAME)
        package.write(data, f"dados/{DATA_NAME}")
        package.write(metadata_path, f"dados/{METADATA_NAME}")
        for name in ("Equipe_04_ModulacaoAM.tse", "capturar_vhil.py", "analisar_captura.py"):
            package.write(ROOT / name, f"reprodutibilidade/{name}")
        for name in RESULT_FILES:
            package.write(results / name, f"resultados_vhil/{name}")
    print(f"ZIP final: {destination}")
    print("Confirme visualmente que o PDF nao contem o aviso de previa tecnica antes de enviar.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        sys.exit(1)
