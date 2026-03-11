import pytest

np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")

from src.comtrade_analyzer import (
    EventThresholds,
    LineContext,
    build_analysis_report,
    detect_threshold_events,
    estimate_fault_distance_km,
    summarize_signal_metrics,
)


def test_summarize_signal_metrics_basic():
    df = pd.DataFrame({"VA": [1.0, -1.0, 1.0, -1.0], "IA": [0.0, 2.0, 0.0, -2.0]})
    out = summarize_signal_metrics(df, ["VA", "IA"])

    assert list(out["signal"]) == ["VA", "IA"]
    va_rms = out.loc[out["signal"] == "VA", "rms"].iloc[0]
    assert np.isclose(va_rms, 1.0)


def test_detect_threshold_events():
    df = pd.DataFrame({"VA": [100.0, 130.0, 90.0], "IA": [100.0, 200.0, 700.0]})
    thresholds = EventThresholds(overcurrent_a=500.0, overvoltage_pu=1.2, undervoltage_pu=0.95)

    events = detect_threshold_events(
        df,
        voltage_cols=["VA"],
        current_cols=["IA"],
        nominal_voltage_v=100.0,
        thresholds=thresholds,
    )

    event_types = sorted(events["type"].tolist())
    assert event_types == ["sobrecorrente", "sobretensao", "subtensao"]


def test_estimate_fault_distance_clamped_to_line_length():
    va = np.array([100.0, 100.0, 100.0])
    ia = np.array([1.0, 1.0, 1.0])
    line = LineContext(line_length_km=10.0, voltage_class_kv=138.0, positive_seq_impedance_ohm_per_km=1.0)

    distance = estimate_fault_distance_km(va, ia, line)
    assert np.isclose(distance, 10.0)


def test_build_analysis_report_includes_key_sections():
    metrics = pd.DataFrame([{"signal": "VA", "rms": 100.0, "peak": 120.0, "dc": 1.0}])
    events = pd.DataFrame([{"signal": "VA", "type": "sobretensao", "index": 15, "value": 1.3}])
    line = LineContext(line_length_km=50.0, voltage_class_kv=230.0, positive_seq_impedance_ohm_per_km=0.4)

    report = build_analysis_report(metrics, events, 12.5, line)

    assert "Distância estimada da falta" in report
    assert "Eventos detectados" in report
    assert "sobretensao" in report
