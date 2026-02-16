from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class LineContext:
    line_length_km: float
    voltage_class_kv: float
    positive_seq_impedance_ohm_per_km: float


@dataclass
class EventThresholds:
    overcurrent_a: float
    overvoltage_pu: float
    undervoltage_pu: float


def _safe_rms(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(values))))


def estimate_dc_component(values: np.ndarray) -> float:
    if values.size == 0:
        return 0.0
    return float(np.mean(values))


def summarize_signal_metrics(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    rows = []
    for col in columns:
        values = df[col].to_numpy(dtype=float)
        rms = _safe_rms(values)
        peak = float(np.max(np.abs(values))) if values.size else 0.0
        dc = estimate_dc_component(values)
        rows.append({"signal": col, "rms": rms, "peak": peak, "dc": dc})
    return pd.DataFrame(rows)


def detect_threshold_events(
    df: pd.DataFrame,
    voltage_cols: list[str],
    current_cols: list[str],
    nominal_voltage_v: float,
    thresholds: EventThresholds,
) -> pd.DataFrame:
    events: list[dict[str, float | str]] = []
    for col in voltage_cols:
        pu = np.abs(df[col].to_numpy(dtype=float)) / max(nominal_voltage_v, 1e-6)
        if np.any(pu > thresholds.overvoltage_pu):
            idx = int(np.argmax(pu > thresholds.overvoltage_pu))
            events.append({"signal": col, "type": "sobretensao", "index": idx, "value": pu[idx]})
        if np.any(pu < thresholds.undervoltage_pu):
            idx = int(np.argmax(pu < thresholds.undervoltage_pu))
            events.append({"signal": col, "type": "subtensao", "index": idx, "value": pu[idx]})

    for col in current_cols:
        amp = np.abs(df[col].to_numpy(dtype=float))
        if np.any(amp > thresholds.overcurrent_a):
            idx = int(np.argmax(amp > thresholds.overcurrent_a))
            events.append(
                {"signal": col, "type": "sobrecorrente", "index": idx, "value": float(amp[idx])}
            )

    return pd.DataFrame(events)


def estimate_fault_distance_km(
    va: np.ndarray,
    ia: np.ndarray,
    line_context: LineContext,
) -> float:
    if va.size == 0 or ia.size == 0:
        return 0.0

    current_rms = max(_safe_rms(ia), 1e-6)
    voltage_rms = _safe_rms(va)
    z_apparent = voltage_rms / current_rms

    z_line = max(
        line_context.positive_seq_impedance_ohm_per_km * line_context.line_length_km,
        1e-6,
    )
    fraction = np.clip(z_apparent / z_line, 0.0, 1.0)
    return float(fraction * line_context.line_length_km)


def build_analysis_report(
    metrics_df: pd.DataFrame,
    events_df: pd.DataFrame,
    fault_distance_km: float,
    line_context: LineContext,
) -> str:
    out = StringIO()
    out.write("Resumo de análise de perturbação\n")
    out.write("-" * 40 + "\n")
    out.write(
        f"Linha: {line_context.line_length_km:.1f} km | Classe de tensão: {line_context.voltage_class_kv:.1f} kV\n"
    )
    out.write(f"Distância estimada da falta: {fault_distance_km:.2f} km\n\n")

    out.write("Métricas de sinais:\n")
    if metrics_df.empty:
        out.write("  Nenhuma métrica disponível.\n")
    else:
        for _, row in metrics_df.iterrows():
            out.write(
                f"  - {row['signal']}: RMS={row['rms']:.3f}, Pico={row['peak']:.3f}, DC={row['dc']:.3f}\n"
            )

    out.write("\nEventos detectados:\n")
    if events_df.empty:
        out.write("  Nenhum evento acima dos limiares configurados.\n")
    else:
        for _, row in events_df.iterrows():
            out.write(
                f"  - {row['type']} em {row['signal']} (amostra {int(row['index'])}, valor={row['value']:.3f})\n"
            )

    return out.getvalue()
