from broca.internal_sensing.integrated_interoception import IntegratedInteroception


class TestCalibratedSurpriseNoLag:
    def test_calibrated_surprise_updates_same_turn(self, monkeypatch):
        """
        Regression: calibrated_surprise should not be stuck at 0 and should not lag one step.

        We force a large prediction error on the first \"has _last_prediction\" update and ensure:
        - PredictiveInteroception calibrated history is updated during that call
        - Affective surprise reflects the newly computed calibrated surprise
        """
        inter = IntegratedInteroception()

        # Ensure the "previous prediction exists" path executes.
        inter._last_prediction = {
            "computational_load": 0.0,
            "memory_pressure": 0.0,
            "processing_latency": 0.0,
            "attention_fluctuation": 0.0,
            "energy_efficiency": 0.5,
            "timestamp": 0.0,
            "horizon": 1,
            "_prediction_id": "test_pred",
        }

        def fake_sample_resources():
            # Keep the monitor internally consistent: PredictiveInteroception.predict_resources()
            # reads from physiology.metrics (not just the return value of sample_resources()).
            inter.physiology.metrics["computational_load"] = 1.0
            inter.physiology.metrics["memory_pressure"] = 1.0
            inter.physiology.metrics["processing_latency"] = 0.0
            inter.physiology.metrics["attention_fluctuation"] = 0.0
            inter.physiology.metrics["energy_efficiency"] = 0.5
            return {
                "computational_load": 1.0,
                "memory_pressure": 1.0,
                "processing_latency": 0.0,
                "attention_fluctuation": 0.0,
                "energy_efficiency": 0.5,
                "timestamp": 1.0,
            }

        monkeypatch.setattr(inter.physiology, "sample_resources", fake_sample_resources)

        state = inter.generate_interoceptive_awareness()

        calibrated = inter.prediction.get_rl_surprise_signal()
        assert calibrated > 0.0

        # Affective surprise is driven by calibrated_surprise when provided.
        aff = state.get("affective", {})
        assert aff.get("surprise", 0.0) > 0.0


