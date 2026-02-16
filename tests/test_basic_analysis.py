import unittest

from src.basic_analysis import (
    EventThresholds,
    LineContext,
    detect_threshold_events,
    estimate_fault_distance_km,
    summarize_signal_metrics,
)


class TestBasicAnalysis(unittest.TestCase):
    def test_metrics(self):
        summary = summarize_signal_metrics({"VA": [1.0, -1.0, 1.0, -1.0]})
        self.assertEqual(summary[0]["signal"], "VA")
        self.assertAlmostEqual(summary[0]["rms"], 1.0, places=6)
        self.assertAlmostEqual(summary[0]["peak"], 1.0, places=6)

    def test_events(self):
        thresholds = EventThresholds(overcurrent_a=500.0, overvoltage_pu=1.2, undervoltage_pu=0.95)
        events = detect_threshold_events(
            voltage_map={"VA": [100.0, 130.0, 90.0]},
            current_map={"IA": [100.0, 200.0, 700.0]},
            nominal_voltage_v=100.0,
            thresholds=thresholds,
        )
        event_types = sorted(e["type"] for e in events)
        self.assertEqual(event_types, ["sobrecorrente", "sobretensao", "subtensao"])

    def test_distance(self):
        line = LineContext(line_length_km=10.0, voltage_class_kv=138.0, positive_seq_impedance_ohm_per_km=1.0)
        distance = estimate_fault_distance_km([100.0, 100.0, 100.0], [1.0, 1.0, 1.0], line)
        self.assertAlmostEqual(distance, 10.0, places=6)


if __name__ == "__main__":
    unittest.main()
