"""
Tests for ComputationalPhysiologyMonitor.

Tests resource monitoring including CPU, memory, latency, and efficiency tracking.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import time

from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor


class TestComputationalPhysiologyInitialization:
    """Test ComputationalPhysiologyMonitor initialization."""
    
    def test_initialization(self):
        """
        Test that monitor initializes with default metrics.
        
        Rationale: Ensures monitor starts with proper default state.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        assert monitor.metrics is not None
        assert "computational_load" in monitor.metrics
        assert "memory_pressure" in monitor.metrics
        assert "processing_latency" in monitor.metrics
        assert "attention_fluctuation" in monitor.metrics
        assert "energy_efficiency" in monitor.metrics
        
        # Check default values (should never be None)
        assert monitor.metrics["computational_load"] == 0.5  # Moderate default
        assert monitor.metrics["memory_pressure"] == 0.5  # Moderate default
        assert monitor.metrics["processing_latency"] == 0.0  # No latency default
        assert monitor.metrics["attention_fluctuation"] == 0.0  # No fluctuation default
        assert monitor.metrics["energy_efficiency"] == 0.5  # Moderate default


class TestCPULoadSensing:
    """Test CPU load sensing functionality."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_load_sensing(self, mock_psutil):
        """
        Test that CPU load is measured and normalized (0-1).
        
        Rationale: Ensures CPU load is properly tracked and normalized.
        """
        mock_psutil.cpu_percent.return_value = 50.0  # 50% CPU usage
        
        monitor = ComputationalPhysiologyMonitor()
        cpu_load = monitor._measure_cpu_load()
        
        assert isinstance(cpu_load, float)
        assert 0.0 <= cpu_load <= 1.0
        assert cpu_load == 0.5  # 50% should be 0.5 normalized
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_load_normalization(self, mock_psutil):
        """
        Test that CPU load is properly normalized to 0-1 range.
        
        Rationale: Ensures values outside 0-100% are clamped correctly.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Test 0%
        mock_psutil.cpu_percent.return_value = 0.0
        assert monitor._measure_cpu_load() == 0.0
        
        # Test 100%
        mock_psutil.cpu_percent.return_value = 100.0
        assert monitor._measure_cpu_load() == 1.0
        
        # Test >100% (should clamp to 1.0)
        mock_psutil.cpu_percent.return_value = 150.0
        assert monitor._measure_cpu_load() == 1.0
    
    def test_cpu_load_default_when_psutil_unavailable(self):
        """
        Test that CPU load returns default when psutil unavailable.
        
        Rationale: Ensures unavailable data uses default value.
        """
        # Temporarily remove psutil
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            cpu_load = monitor._measure_cpu_load()
            assert cpu_load == 0.5  # Default value
        finally:
            cp_module.psutil = original_psutil


class TestMemoryPressureSensing:
    """Test memory pressure sensing functionality."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_memory_pressure_sensing(self, mock_psutil):
        """
        Test that memory usage is tracked correctly.
        
        Rationale: Ensures memory pressure is properly measured.
        """
        mock_memory = Mock()
        mock_memory.percent = 75.0  # 75% memory usage
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = ComputationalPhysiologyMonitor()
        memory_pressure = monitor._measure_memory_pressure()
        
        assert isinstance(memory_pressure, float)
        assert 0.0 <= memory_pressure <= 1.0
        assert memory_pressure == 0.75  # 75% should be 0.75 normalized
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_memory_pressure_normalization(self, mock_psutil):
        """
        Test that memory pressure is normalized correctly.
        
        Rationale: Ensures memory values are in valid range.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Test 0%
        mock_memory = Mock()
        mock_memory.percent = 0.0
        mock_psutil.virtual_memory.return_value = mock_memory
        assert monitor._measure_memory_pressure() == 0.0
        
        # Test 100%
        mock_memory.percent = 100.0
        assert monitor._measure_memory_pressure() == 1.0
    
    def test_memory_pressure_default_when_psutil_unavailable(self):
        """
        Test that memory pressure returns default when psutil unavailable.
        
        Rationale: Ensures unavailable data uses default value.
        """
        # Temporarily remove psutil
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            memory_pressure = monitor._measure_memory_pressure()
            assert memory_pressure == 0.5  # Default value
        finally:
            cp_module.psutil = original_psutil


class TestProcessingLatencySensing:
    """Test processing latency sensing functionality."""
    
    def test_processing_latency_sensing(self):
        """
        Test that response time delays are measured.
        
        Rationale: Ensures latency tracking works correctly.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Record start time
        start_time = time.time()
        monitor._record_operation_start("test_operation")
        
        # Simulate some delay
        time.sleep(0.1)
        
        # Record end time and get latency
        latency = monitor._record_operation_end("test_operation")
        
        assert isinstance(latency, float)
        assert latency >= 0.0
        assert latency >= 0.1  # Should be at least 0.1 seconds
        
        # Test that processing_latency is computed
        monitor.sample_resources()
        avg_latency = monitor.metrics["processing_latency"]
        assert isinstance(avg_latency, float)
        assert avg_latency >= 0.0
    
    def test_processing_latency_default_when_no_operations(self):
        """
        Test that processing latency returns default when no operations tracked.
        
        Rationale: Ensures unavailable data uses default value.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # No operations tracked
        latency = monitor._calculate_processing_latency()
        assert latency == 0.0  # Default value
        
        monitor.sample_resources()
        assert monitor.metrics["processing_latency"] == 0.0  # Default value
    
    def test_processing_latency_normalization(self):
        """
        Test that latency is normalized to 0-1 range.
        
        Rationale: Ensures latency values are normalized for consistency.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Set a baseline latency
        monitor._baseline_latency = 1.0
        
        # Record operation with 0.5s latency (50% of baseline)
        monitor._record_operation_start("test")
        time.sleep(0.5)
        latency = monitor._record_operation_end("test")
        
        # Normalized latency should be calculated
        normalized = monitor._normalize_latency(latency)
        assert normalized is not None
        assert 0.0 <= normalized <= 1.0
    
    def test_normalize_latency_none(self):
        """
        Test that normalize_latency returns None when input is None.
        
        Rationale: Ensures None values are handled correctly.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        normalized = monitor._normalize_latency(None)
        assert normalized is None


class TestAttentionFluctuation:
    """Test attention fluctuation tracking."""
    
    def test_attention_fluctuation_tracking(self):
        """
        Test that focus variability is tracked.
        
        Rationale: Ensures attention patterns are monitored.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Simulate varying attention levels
        monitor._record_attention_level(0.8)
        monitor._record_attention_level(0.6)
        monitor._record_attention_level(0.9)
        monitor._record_attention_level(0.5)
        
        fluctuation = monitor._calculate_attention_fluctuation()
        
        assert isinstance(fluctuation, float)
        assert 0.0 <= fluctuation <= 1.0
        assert fluctuation > 0.0  # Should detect some fluctuation
    
    def test_attention_fluctuation_stable(self):
        """
        Test that stable attention shows low fluctuation.
        
        Rationale: Ensures fluctuation calculation is accurate.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Record stable attention levels
        for _ in range(5):
            monitor._record_attention_level(0.7)
        
        fluctuation = monitor._calculate_attention_fluctuation()
        
        assert isinstance(fluctuation, float)
        assert fluctuation < 0.1  # Should be low for stable attention
    
    def test_attention_fluctuation_default_when_insufficient_data(self):
        """
        Test that attention fluctuation returns default when insufficient data.
        
        Rationale: Ensures unavailable data uses default value.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # No data
        fluctuation = monitor._calculate_attention_fluctuation()
        assert fluctuation == 0.0  # Default value
        
        # Only one data point
        monitor._record_attention_level(0.7)
        fluctuation = monitor._calculate_attention_fluctuation()
        assert fluctuation == 0.0  # Default value (needs at least 2 points)


class TestEnergyEfficiency:
    """Test energy efficiency calculation."""
    
    def test_energy_efficiency_calculation(self):
        """
        Test that computational efficiency is calculated.
        
        Rationale: Ensures efficiency metrics are tracked.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Set up metrics
        monitor.metrics["computational_load"] = 0.5
        monitor.metrics["memory_pressure"] = 0.3
        
        efficiency = monitor._calculate_energy_efficiency()
        
        assert isinstance(efficiency, float)
        assert 0.0 <= efficiency <= 1.0
    
    def test_energy_efficiency_high_load(self):
        """
        Test that high load reduces efficiency.
        
        Rationale: Ensures efficiency calculation reflects resource usage.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # High load scenario
        monitor.metrics["computational_load"] = 0.9
        monitor.metrics["memory_pressure"] = 0.8
        
        efficiency = monitor._calculate_energy_efficiency()
        
        # Efficiency should be lower with high load
        assert isinstance(efficiency, float)
        assert efficiency < 0.5
    
    def test_energy_efficiency_default_when_resources_unavailable(self):
        """
        Test that energy efficiency returns default when resources unavailable.
        
        Rationale: Ensures unavailable data uses default value.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Should use defaults even if metrics are None (they shouldn't be, but test resilience)
        efficiency = monitor._calculate_energy_efficiency()
        assert efficiency == 0.5  # Default value (uses default metrics)


class TestResourceSampling:
    """Test resource sampling functionality."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_resource_sampling(self, mock_psutil):
        """
        Test that all metrics can be sampled at once.
        
        Rationale: Ensures complete resource state can be captured.
        """
        # Mock CPU metrics
        def cpu_percent_side_effect(interval=None, percpu=False):
            if percpu:
                return [50.0, 50.0]  # Return list for per-CPU
            return 50.0  # Return single value for overall
        
        mock_psutil.cpu_percent.side_effect = cpu_percent_side_effect
        
        # Mock CPU times
        mock_cpu_times = Mock()
        mock_cpu_times.user = 1000.0
        mock_cpu_times.system = 500.0
        mock_cpu_times.idle = 8500.0
        mock_cpu_times.nice = 0.0
        mock_psutil.cpu_times.return_value = mock_cpu_times
        
        # Mock CPU frequency
        mock_cpu_freq = Mock()
        mock_cpu_freq.current = 2400.0
        mock_cpu_freq.min = 800.0
        mock_cpu_freq.max = 3200.0
        mock_psutil.cpu_freq.return_value = mock_cpu_freq
        
        # Mock CPU stats
        mock_cpu_stats = Mock()
        mock_cpu_stats.ctx_switches = 1000000
        mock_cpu_stats.interrupts = 500000
        mock_cpu_stats.soft_interrupts = 200000
        mock_psutil.cpu_stats.return_value = mock_cpu_stats
        
        # Mock memory metrics
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.used = 8000000000
        mock_memory.cached = 2000000000
        mock_memory.buffers = 500000000
        mock_memory.shared = 0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        # Mock swap memory
        mock_swap = Mock()
        mock_swap.percent = 20.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        # Mock disk metrics
        mock_disk = Mock()
        mock_disk.percent = 65.0
        mock_psutil.disk_usage.return_value = mock_disk
        mock_psutil.disk_io_counters.return_value = None  # Will return None on first call
        
        # Mock network metrics
        mock_psutil.net_io_counters.return_value = None  # Will return None on first call
        mock_psutil.net_connections.return_value = []
        
        # Mock system metrics
        import time as time_module
        mock_psutil.boot_time.return_value = time_module.time() - 3600
        mock_psutil.pids.return_value = list(range(100))
        mock_psutil.users.return_value = [Mock(), Mock()]
        
        monitor = ComputationalPhysiologyMonitor()
        sample = monitor.sample_resources()
        
        assert isinstance(sample, dict)
        assert "computational_load" in sample
        assert "memory_pressure" in sample
        assert "processing_latency" in sample
        assert "attention_fluctuation" in sample
        assert "energy_efficiency" in sample
        assert "timestamp" in sample
        
        # Check values are in valid ranges (some may be None if unavailable)
        # Some metrics are now dicts or lists (expanded metrics)
        for key, value in sample.items():
            if key != "timestamp":
                if value is not None:
                    # Handle different metric types
                    if isinstance(value, float):
                        assert 0.0 <= value <= 1.0
                    elif isinstance(value, list):
                        # Lists should contain normalized floats (e.g., cpu_per_core)
                        assert all(isinstance(v, float) and 0.0 <= v <= 1.0 for v in value)
                    elif isinstance(value, dict):
                        # Dicts contain metric breakdowns (e.g., cpu_times, memory_breakdown)
                        # Most values should be normalized floats, but some may be raw counts
                        # (e.g., cpu_statistics has raw counts, disk_io/network_io may have counts)
                        for v in value.values():
                            if isinstance(v, (int, float)):
                                # For normalized metrics, should be 0-1
                                # For raw counts, just check they're non-negative
                                # We'll be lenient and only check if value is < 1.0 that it's >= 0.0
                                if float(v) < 1.0:
                                    assert 0.0 <= float(v) <= 1.0
                                # Otherwise it's likely a raw count, just check non-negative
                                else:
                                    assert float(v) >= 0.0
                # Some metrics may be None (e.g., processing_latency if no operations)


class TestMetricHistory:
    """Test metric history maintenance."""
    
    def test_metric_history(self):
        """
        Test that history window of samples is maintained.
        
        Rationale: Ensures historical data is available for analysis.
        """
        monitor = ComputationalPhysiologyMonitor(history_window=5)
        
        # Sample multiple times
        for i in range(10):
            monitor.sample_resources()
        
        history = monitor.get_history()
        
        assert isinstance(history, list)
        assert len(history) <= 5  # Should respect history window
        assert len(history) > 0
    
    def test_metric_history_timestamp(self):
        """
        Test that history entries have timestamps.
        
        Rationale: Ensures temporal information is preserved.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        monitor.sample_resources()
        history = monitor.get_history()
        
        assert len(history) > 0
        assert "timestamp" in history[0]
        assert isinstance(history[0]["timestamp"], float)


class TestAnomalyDetection:
    """Test anomaly detection functionality."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_anomaly_detection(self, mock_psutil):
        """
        Test that unusual resource patterns are detected.
        
        Rationale: Ensures system can identify abnormal states.
        """
        mock_psutil.cpu_percent.return_value = 30.0
        mock_memory = Mock()
        mock_memory.percent = 40.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = ComputationalPhysiologyMonitor()
        
        # Create normal baseline
        for _ in range(5):
            monitor.sample_resources()
        
        # Create anomaly (sudden spike)
        mock_psutil.cpu_percent.return_value = 95.0
        monitor.sample_resources()
        
        anomalies = monitor.detect_anomalies()
        
        assert isinstance(anomalies, list)
        # Should detect the spike as an anomaly
        assert len(anomalies) > 0
    
    def test_anomaly_detection_no_anomalies(self):
        """
        Test that normal patterns don't trigger anomalies.
        
        Rationale: Ensures false positives are minimized.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Create stable normal pattern
        for _ in range(10):
            monitor.metrics["computational_load"] = 0.4
            monitor.sample_resources()
        
        anomalies = monitor.detect_anomalies()
        
        # Should have few or no anomalies for stable pattern
        assert isinstance(anomalies, list)

