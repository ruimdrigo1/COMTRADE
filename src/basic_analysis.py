from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable


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


def rms(values: Iterable[float]) -> float:
    vals = [float(v) for v in values]
    if not vals:
        return 0.0
    return sqrt(sum(v * v for v in vals) / len(vals))


def mean(values: Iterable[float]) -> float:
    vals = [float(v) for v in values]
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def peak_abs(values: Iterable[float]) -> float:
    vals = [abs(float(v)) for v in values]
    return max(vals) if vals else 0.0


def summarize_signal_metrics(signal_map: dict[str, list[float]]) -> list[dict[str, float | str]]:
    summary: list[dict[str, float | str]] = []
    for name, values in signal_map.items():
        summary.append(
            {
                "signal": name,
                "rms": rms(values),
                "peak": peak_abs(values),
                "dc": mean(values),
            }
        )
    return summary


def detect_threshold_events(
    voltage_map: dict[str, list[float]],
    current_map: dict[str, list[float]],
    nominal_voltage_v: float,
    thresholds: EventThresholds,
) -> list[dict[str, float | str | int]]:
    events: list[dict[str, float | str | int]] = []
    vbase = nominal_voltage_v if nominal_voltage_v > 0 else 1e-6

    for signal, values in voltage_map.items():
        pu_values = [abs(float(v)) / vbase for v in values]

        for i, pu in enumerate(pu_values):
            if pu > thresholds.overvoltage_pu:
                events.append({"signal": signal, "type": "sobretensao", "index": i, "value": pu})
                break

        for i, pu in enumerate(pu_values):
            if pu < thresholds.undervoltage_pu:
                events.append({"signal": signal, "type": "subtensao", "index": i, "value": pu})
                break

    for signal, values in current_map.items():
        amps = [abs(float(v)) for v in values]
        for i, amp in enumerate(amps):
            if amp > thresholds.overcurrent_a:
                events.append({"signal": signal, "type": "sobrecorrente", "index": i, "value": amp})
                break

    return events


def estimate_fault_distance_km(va: list[float], ia: list[float], line_context: LineContext) -> float:
    if not va or not ia:
        return 0.0

    current_rms = max(rms(ia), 1e-6)
    voltage_rms = rms(va)
    z_apparent = voltage_rms / current_rms

    z_line = max(line_context.positive_seq_impedance_ohm_per_km * line_context.line_length_km, 1e-6)
    fraction = min(max(z_apparent / z_line, 0.0), 1.0)
    return fraction * line_context.line_length_km
