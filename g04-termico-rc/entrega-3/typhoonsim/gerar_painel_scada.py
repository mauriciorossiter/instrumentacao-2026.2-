"""Gera instrumento_estatico_generico.cus com a API do Typhoon HIL.

Execute com o interpretador instalado pelo Typhoon HIL Control Center 2026.2:
    typhoon-python gerar_painel_scada.py

O arquivo .cus sera salvo na mesma pasta deste script.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from typhoon.api.scada import panel
import typhoon.api.scada.const as api_const


SIGNALS = (
    ("Entrada_x", "Entrada x"),
    ("Saida_ideal", "Saida ideal"),
    ("Saida_desvio_zero", "Saida com desvio de zero"),
    ("Saida_sensibilidade", "Saida com erro de sensibilidade"),
    ("Saida_real", "Saida real"),
    ("Erro_total", "Erro total"),
)


def set_optional(widget, property_name, value, warnings):
    """Aplica uma propriedade visual sem impedir a criacao do painel."""
    try:
        panel.set_property_value(widget, property_name, value)
    except Exception as exc:  # A disponibilidade pode variar entre revisoes 2026.x.
        warnings.append(f"{property_name}: {exc}")


def configure_scope(scope, capture_mode=False):
    """Configura Scope/Capture e usa a propriedade legada como fallback."""
    panel.set_property_value(scope, "state", "Capture" if capture_mode else "Scope")
    panel.set_property_value(scope, "scope_legend", True)
    panel.set_property_value(scope, "scope_layout", "Vertical")
    panel.set_property_value(scope, "time_base", 1.0)

    scope_signals = []
    for signal_name, _ in SIGNALS:
        viewport = [2] if signal_name == "Erro_total" else [1]
        scope_signals.append(
            {
                "Name": signal_name,
                "Type": "Analog",
                "Viewports": viewport,
                "Scale": "Auto",
                "Offset": 0,
                "Coupling": False,
            }
        )

    try:
        panel.set_property_value(scope, "scope_signals", scope_signals)
    except Exception:
        # Compatibilidade com instalacoes em que a propriedade unificada ainda
        # nao esteja disponivel.
        legacy_signals = []
        for signal_name, _ in SIGNALS:
            viewport = [2] if signal_name == "Erro_total" else [1]
            legacy_signals.append([signal_name, viewport, "Auto", 0, False])
        panel.set_property_value(scope, "scope_analog_signals", legacy_signals)


def build_panel(output_path: Path, force: bool = False, capture_mode: bool = False) -> Path:
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        if not force:
            raise FileExistsError(
                f"O arquivo ja existe: {output_path}. "
                "Use --force para substitui-lo conscientemente."
            )
        output_path.unlink()

    warnings = []
    panel.create_new_panel()

    # Leituras instantaneas: seis displays na faixa superior.
    for index, (signal_name, label) in enumerate(SIGNALS):
        display = panel.create_widget(
            widget_type=api_const.WT_DIGITAL,
            parent=None,
            name=f"Display {signal_name}",
            position=[20 + index * 190, 20],
        )
        panel.set_property_value(display, "signals", signal_name)
        set_optional(display, "size", [175, 105], warnings)
        set_optional(display, "use_label", True, warnings)
        set_optional(display, "label", label, warnings)
        set_optional(display, "decimals", 3, warnings)

    # Cinco curvas de entrada/saida no viewport 1 e o erro no viewport 2.
    scope = panel.create_widget(
        widget_type=api_const.WT_CAPTURE_SCOPE,
        parent=None,
        name="Comparacao das caracteristicas estaticas",
        position=[20, 145],
    )
    panel.set_property_value(scope, "size", [1125, 560])
    configure_scope(scope, capture_mode=capture_mode)
    set_optional(scope, "scope_background", "white", warnings)

    panel.save_panel_as(str(output_path))

    print(f"Painel criado com sucesso: {output_path}")
    if warnings:
        print("Avisos de propriedades visuais opcionais:")
        for warning in warnings:
            print(f"  - {warning}")
    return output_path


def parse_args(argv):
    default_output = Path(__file__).resolve().with_name(
        "instrumento_estatico_generico.cus"
    )
    parser = argparse.ArgumentParser(
        description="Gera o painel HIL SCADA do instrumento estatico."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output,
        help="Caminho do .cus a criar.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Permite substituir um .cus ja existente.",
    )
    parser.add_argument(
        "--capture",
        action="store_true",
        help="Abre o widget em Capture para facilitar a exportacao da evidencia.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        build_panel(args.output, force=args.force, capture_mode=args.capture)
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
