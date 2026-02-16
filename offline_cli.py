from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.basic_analysis import (
    EventThresholds,
    LineContext,
    detect_threshold_events,
    estimate_fault_distance_km,
    summarize_signal_metrics,
)


def parse_csv(path: Path) -> dict[str, list[float]]:
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames or []
        data: dict[str, list[float]] = {c: [] for c in columns}
        for row in reader:
            for c in columns:
                data[c].append(float(row[c]))
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Análise offline (sem dependências externas) para sinais exportados em CSV")
    parser.add_argument("--csv", required=True, help="CSV com colunas de sinais (ex.: time, VA, VB, VC, IA, IB, IC)")
    parser.add_argument("--voltage", nargs="+", default=["VA"], help="Nomes dos canais de tensão")
    parser.add_argument("--current", nargs="+", default=["IA"], help="Nomes dos canais de corrente")
    parser.add_argument("--line-km", type=float, default=100.0)
    parser.add_argument("--kv", type=float, default=230.0)
    parser.add_argument("--z1", type=float, default=0.4)
    parser.add_argument("--overcurrent", type=float, default=500.0)
    parser.add_argument("--overvoltage", type=float, default=1.1)
    parser.add_argument("--undervoltage", type=float, default=0.8)

    args = parser.parse_args()
    data = parse_csv(Path(args.csv))

    selected = {k: data[k] for k in (args.voltage + args.current) if k in data}
    metrics = summarize_signal_metrics(selected)

    voltage_map = {k: data[k] for k in args.voltage if k in data}
    current_map = {k: data[k] for k in args.current if k in data}

    thresholds = EventThresholds(args.overcurrent, args.overvoltage, args.undervoltage)
    nominal_voltage_v = (args.kv * 1000.0) / (3**0.5)
    events = detect_threshold_events(voltage_map, current_map, nominal_voltage_v, thresholds)

    line = LineContext(args.line_km, args.kv, args.z1)
    distance = 0.0
    if args.voltage and args.current and args.voltage[0] in data and args.current[0] in data:
        distance = estimate_fault_distance_km(data[args.voltage[0]], data[args.current[0]], line)

    print("Resumo offline de análise")
    print("=" * 32)
    print(f"Distância estimada da falta: {distance:.2f} km")
    print("\nMétricas:")
    for row in metrics:
        print(f"- {row['signal']}: RMS={row['rms']:.3f} | Pico={row['peak']:.3f} | DC={row['dc']:.3f}")

    print("\nEventos:")
    if not events:
        print("- Nenhum evento acima dos limiares")
    for e in events:
        print(f"- {e['type']} em {e['signal']} (amostra {e['index']}, valor={e['value']:.3f})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
