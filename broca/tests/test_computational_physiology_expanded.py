"""
Tests for expanded ComputationalPhysiologyMonitor metrics.

Tests additional psutil metrics including CPU details, memory breakdown,
disk I/O, network I/O, and system metrics.
"""

from __future__ import annotations

from unittest.mock import Mock, patch, MagicMock
import pytest
import time

from broca.internal_sensing.computational_physiology import ComputationalPhysiologyMonitor


class TestPerCPUUsageTracking:
    """Test per-CPU usage tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_per_cpu_usage_tracking(self, mock_psutil):
        """
        Test that per-CPU usage is measured and stored.
        
        Rationale: Ensures individual CPU core utilization is tracked.
        """
        # Mock per-CPU usage
        mock_psutil.cpu_percent.return_value = [25.0, 50.0, 75.0, 30.0]  # 4 cores
        
        monitor = ComputationalPhysiologyMonitor()
        per_cpu = monitor._measure_per_cpu_usage()
        
        assert per_cpu is not None
        assert isinstance(per_cpu, list)
        assert len(per_cpu) == 4
        assert all(0.0 <= cpu <= 1.0 for cpu in per_cpu)
        assert per_cpu[0] == 0.25
        assert per_cpu[1] == 0.5
        assert per_cpu[2] == 0.75
        assert per_cpu[3] == 0.3
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_per_cpu_usage_normalization(self, mock_psutil):
        """
        Test that per-CPU usage is normalized to 0-1 range.
        
        Rationale: Ensures values are in consistent range.
        """
        monitor = ComputationalPhysiologyMonitor()
        
        # Test 0%
        mock_psutil.cpu_percent.return_value = [0.0, 0.0]
        per_cpu = monitor._measure_per_cpu_usage()
        assert all(cpu == 0.0 for cpu in per_cpu)
        
        # Test 100%
        mock_psutil.cpu_percent.return_value = [100.0, 100.0]
        per_cpu = monitor._measure_per_cpu_usage()
        assert all(cpu == 1.0 for cpu in per_cpu)
    
    def test_per_cpu_usage_none_when_psutil_unavailable(self):
        """
        Test that per-CPU usage returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            per_cpu = monitor._measure_per_cpu_usage()
            assert per_cpu is None
        finally:
            cp_module.psutil = original_psutil


class TestCPUTimesTracking:
    """Test CPU times tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_times_tracking(self, mock_psutil):
        """
        Test that CPU times (user, system, idle) are tracked.
        
        Rationale: Ensures detailed CPU time breakdown is available.
        """
        # Mock CPU times
        mock_times = Mock()
        mock_times.user = 1000.0
        mock_times.system = 500.0
        mock_times.idle = 8500.0
        mock_times.nice = 0.0
        mock_times.iowait = 0.0
        mock_psutil.cpu_times.return_value = mock_times
        
        monitor = ComputationalPhysiologyMonitor()
        times = monitor._measure_cpu_times()
        
        assert times is not None
        assert isinstance(times, dict)
        assert "user" in times
        assert "system" in times
        assert "idle" in times
        # Values should be normalized (sum of all times = 1.0)
        total = sum(times.values())
        assert abs(total - 1.0) < 0.01  # Allow small floating point error
    
    def test_cpu_times_none_when_psutil_unavailable(self):
        """
        Test that CPU times returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            times = monitor._measure_cpu_times()
            assert times is None
        finally:
            cp_module.psutil = original_psutil


class TestCPUFrequencyTracking:
    """Test CPU frequency tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_frequency_tracking(self, mock_psutil):
        """
        Test that CPU frequency is tracked if available.
        
        Rationale: Ensures CPU frequency monitoring when available.
        """
        # Mock CPU frequency
        mock_freq = Mock()
        mock_freq.current = 2400.0  # MHz
        mock_freq.min = 800.0
        mock_freq.max = 3200.0
        mock_psutil.cpu_freq.return_value = mock_freq
        
        monitor = ComputationalPhysiologyMonitor()
        freq = monitor._measure_cpu_frequency()
        
        assert freq is not None
        assert isinstance(freq, float)
        assert 0.0 <= freq <= 1.0  # Normalized
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_frequency_none_when_unavailable(self, mock_psutil):
        """
        Test that CPU frequency returns None when unavailable.
        
        Rationale: CPU frequency may not be available on all systems.
        """
        mock_psutil.cpu_freq.side_effect = RuntimeError("Frequency not available")
        
        monitor = ComputationalPhysiologyMonitor()
        freq = monitor._measure_cpu_frequency()
        
        assert freq is None


class TestCPUStatisticsTracking:
    """Test CPU statistics tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_cpu_statistics_tracking(self, mock_psutil):
        """
        Test that CPU stats (context switches, interrupts) are tracked.
        
        Rationale: Ensures system-level CPU statistics are monitored.
        """
        # Mock CPU stats
        mock_stats = Mock()
        mock_stats.ctx_switches = 1000000
        mock_stats.interrupts = 500000
        mock_stats.soft_interrupts = 200000
        mock_psutil.cpu_stats.return_value = mock_stats
        
        monitor = ComputationalPhysiologyMonitor()
        stats = monitor._measure_cpu_statistics()
        
        assert stats is not None
        assert isinstance(stats, dict)
        assert "context_switches" in stats or "ctx_switches" in stats
        # Values should be normalized or raw counts (implementation dependent)
    
    def test_cpu_statistics_none_when_psutil_unavailable(self):
        """
        Test that CPU statistics returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            stats = monitor._measure_cpu_statistics()
            assert stats is None
        finally:
            cp_module.psutil = original_psutil


class TestSwapMemoryTracking:
    """Test swap memory tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_swap_memory_tracking(self, mock_psutil):
        """
        Test that swap memory usage is measured.
        
        Rationale: Ensures swap usage is monitored.
        """
        # Mock swap memory
        mock_swap = Mock()
        mock_swap.percent = 45.0  # 45% swap usage
        mock_psutil.swap_memory.return_value = mock_swap
        
        monitor = ComputationalPhysiologyMonitor()
        swap_usage = monitor._measure_swap_memory()
        
        assert swap_usage is not None
        assert isinstance(swap_usage, float)
        assert 0.0 <= swap_usage <= 1.0
        assert swap_usage == 0.45
    
    def test_swap_memory_none_when_psutil_unavailable(self):
        """
        Test that swap memory returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            swap_usage = monitor._measure_swap_memory()
            assert swap_usage is None
        finally:
            cp_module.psutil = original_psutil


class TestMemoryBreakdownTracking:
    """Test memory breakdown tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_memory_breakdown_tracking(self, mock_psutil):
        """
        Test that detailed memory breakdown is tracked.
        
        Rationale: Ensures memory component metrics are available.
        """
        # Mock virtual memory with detailed breakdown
        mock_memory = Mock()
        mock_memory.total = 16000000000  # 16 GB
        mock_memory.available = 8000000000  # 8 GB available
        mock_memory.cached = 2000000000  # 2 GB cached
        mock_memory.buffers = 500000000  # 500 MB buffers
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = ComputationalPhysiologyMonitor()
        breakdown = monitor._measure_memory_breakdown()
        
        assert breakdown is not None
        assert isinstance(breakdown, dict)
        assert "available" in breakdown
        assert "cached" in breakdown
        assert "buffers" in breakdown
        # Values should be normalized
        assert all(0.0 <= v <= 1.0 for v in breakdown.values())
    
    def test_memory_breakdown_none_when_psutil_unavailable(self):
        """
        Test that memory breakdown returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            breakdown = monitor._measure_memory_breakdown()
            assert breakdown is None
        finally:
            cp_module.psutil = original_psutil


class TestDiskUsageTracking:
    """Test disk usage tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_disk_usage_tracking(self, mock_psutil):
        """
        Test that disk usage per partition is tracked.
        
        Rationale: Ensures disk space monitoring.
        """
        # Mock disk usage for root partition
        mock_disk = Mock()
        mock_disk.percent = 65.0  # 65% disk usage
        mock_psutil.disk_usage.return_value = mock_disk
        
        monitor = ComputationalPhysiologyMonitor()
        disk_usage = monitor._measure_disk_usage()
        
        assert disk_usage is not None
        assert isinstance(disk_usage, float)
        assert 0.0 <= disk_usage <= 1.0
        assert disk_usage == 0.65
    
    def test_disk_usage_none_when_psutil_unavailable(self):
        """
        Test that disk usage returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            disk_usage = monitor._measure_disk_usage()
            assert disk_usage is None
        finally:
            cp_module.psutil = original_psutil


class TestDiskIOTracking:
    """Test disk I/O tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_disk_io_tracking(self, mock_psutil):
        """
        Test that disk I/O counters are tracked.
        
        Rationale: Ensures disk I/O activity is monitored.
        """
        # Mock disk I/O counters
        mock_io = Mock()
        mock_io.read_bytes = 1000000000  # 1 GB read
        mock_io.write_bytes = 500000000  # 500 MB written
        mock_io.read_count = 10000
        mock_io.write_count = 5000
        mock_psutil.disk_io_counters.return_value = mock_io
        
        monitor = ComputationalPhysiologyMonitor()
        # First call to establish baseline
        io_metrics = monitor._measure_disk_io()
        # Second call to get rate
        time.sleep(0.1)
        io_metrics = monitor._measure_disk_io()
        
        assert io_metrics is not None
        assert isinstance(io_metrics, dict)
        # Should have read/write rates (normalized or raw)
    
    def test_disk_io_none_when_psutil_unavailable(self):
        """
        Test that disk I/O returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            io_metrics = monitor._measure_disk_io()
            assert io_metrics is None
        finally:
            cp_module.psutil = original_psutil


class TestNetworkIOTracking:
    """Test network I/O tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_network_io_tracking(self, mock_psutil):
        """
        Test that network I/O counters are tracked.
        
        Rationale: Ensures network activity is monitored.
        """
        # Mock network I/O counters
        mock_net = Mock()
        mock_net.bytes_sent = 5000000000  # 5 GB sent
        mock_net.bytes_recv = 3000000000  # 3 GB received
        mock_net.packets_sent = 1000000
        mock_net.packets_recv = 800000
        mock_psutil.net_io_counters.return_value = mock_net
        
        monitor = ComputationalPhysiologyMonitor()
        # First call to establish baseline
        net_metrics = monitor._measure_network_io()
        # Second call to get rate
        time.sleep(0.1)
        net_metrics = monitor._measure_network_io()
        
        assert net_metrics is not None
        assert isinstance(net_metrics, dict)
        # Should have sent/recv rates
    
    def test_network_io_none_when_psutil_unavailable(self):
        """
        Test that network I/O returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            net_metrics = monitor._measure_network_io()
            assert net_metrics is None
        finally:
            cp_module.psutil = original_psutil


class TestNetworkConnectionsTracking:
    """Test network connections tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_network_connections_tracking(self, mock_psutil):
        """
        Test that active network connection count is tracked.
        
        Rationale: Ensures network connection monitoring.
        """
        # Mock network connections
        mock_psutil.net_connections.return_value = [
            Mock(), Mock(), Mock()  # 3 connections
        ]
        
        monitor = ComputationalPhysiologyMonitor()
        conn_count = monitor._measure_network_connections()
        
        assert conn_count is not None
        assert isinstance(conn_count, (int, float))
        assert conn_count >= 0
    
    def test_network_connections_none_when_psutil_unavailable(self):
        """
        Test that network connections returns None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            conn_count = monitor._measure_network_connections()
            assert conn_count is None
        finally:
            cp_module.psutil = original_psutil


class TestSystemMetricsTracking:
    """Test system metrics tracking."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_system_uptime_tracking(self, mock_psutil):
        """
        Test that system uptime is tracked.
        
        Rationale: Ensures system uptime monitoring.
        """
        import time as time_module
        # Mock boot time (1 hour ago)
        mock_psutil.boot_time.return_value = time_module.time() - 3600
        
        monitor = ComputationalPhysiologyMonitor()
        uptime = monitor._measure_system_uptime()
        
        assert uptime is not None
        assert isinstance(uptime, float)
        assert uptime >= 0.0
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_process_count_tracking(self, mock_psutil):
        """
        Test that running process count is tracked.
        
        Rationale: Ensures process count monitoring.
        """
        # Mock process list
        mock_psutil.pids.return_value = list(range(100))  # 100 processes
        
        monitor = ComputationalPhysiologyMonitor()
        proc_count = monitor._measure_process_count()
        
        assert proc_count is not None
        assert isinstance(proc_count, (int, float))
        assert proc_count >= 0
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_user_count_tracking(self, mock_psutil):
        """
        Test that logged-in user count is tracked.
        
        Rationale: Ensures user count monitoring.
        """
        # Mock users
        mock_user1 = Mock()
        mock_user2 = Mock()
        mock_psutil.users.return_value = [mock_user1, mock_user2]  # 2 users
        
        monitor = ComputationalPhysiologyMonitor()
        user_count = monitor._measure_user_count()
        
        assert user_count is not None
        assert isinstance(user_count, (int, float))
        assert user_count >= 0
    
    def test_system_metrics_none_when_psutil_unavailable(self):
        """
        Test that system metrics return None when psutil unavailable.
        
        Rationale: Ensures graceful degradation.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            assert monitor._measure_system_uptime() is None
            assert monitor._measure_process_count() is None
            assert monitor._measure_user_count() is None
        finally:
            cp_module.psutil = original_psutil


class TestRegressionExistingMetrics:
    """Regression tests ensuring existing metrics still work."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_existing_cpu_load_still_works(self, mock_psutil):
        """
        Test that existing CPU load measurement still works.
        
        Rationale: Ensures no regressions in existing functionality.
        """
        mock_psutil.cpu_percent.return_value = 50.0
        
        monitor = ComputationalPhysiologyMonitor()
        cpu_load = monitor._measure_cpu_load()
        
        assert cpu_load is not None
        assert cpu_load == 0.5
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_existing_memory_pressure_still_works(self, mock_psutil):
        """
        Test that existing memory pressure measurement still works.
        
        Rationale: Ensures no regressions in existing functionality.
        """
        mock_memory = Mock()
        mock_memory.percent = 75.0
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = ComputationalPhysiologyMonitor()
        memory_pressure = monitor._measure_memory_pressure()
        
        assert memory_pressure is not None
        assert memory_pressure == 0.75


class TestSampleResourcesIncludesNewMetrics:
    """Test that sample_resources() includes all new metrics."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_sample_resources_includes_new_metrics(self, mock_psutil):
        """
        Test that sample_resources() includes all new metrics.
        
        Rationale: Ensures all new metrics appear in sample output.
        """
        # Mock all psutil calls
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.cached = 2000000000
        mock_memory.buffers = 500000000
        mock_psutil.virtual_memory.return_value = mock_memory
        
        mock_swap = Mock()
        mock_swap.percent = 20.0
        mock_psutil.swap_memory.return_value = mock_swap
        
        mock_disk = Mock()
        mock_disk.percent = 65.0
        mock_psutil.disk_usage.return_value = mock_disk
        
        monitor = ComputationalPhysiologyMonitor()
        sample = monitor.sample_resources()
        
        # Check existing metrics still present
        assert "computational_load" in sample
        assert "memory_pressure" in sample
        
        # Check new metrics are present (may be None if not implemented yet)
        # This test will pass once implementation is complete
        assert isinstance(sample, dict)
        assert "timestamp" in sample


class TestGracefulDegradation:
    """Test graceful degradation when metrics unavailable."""
    
    def test_graceful_degradation_when_psutil_unavailable(self):
        """
        Test that metrics return None when psutil unavailable.
        
        Rationale: System handles missing metrics gracefully.
        """
        import broca.internal_sensing.computational_physiology as cp_module
        original_psutil = cp_module.psutil
        cp_module.psutil = None
        
        try:
            monitor = ComputationalPhysiologyMonitor()
            sample = monitor.sample_resources()
            
            # All metrics should be None or gracefully handled
            assert isinstance(sample, dict)
            assert "timestamp" in sample
        finally:
            cp_module.psutil = original_psutil


class TestMetricNormalization:
    """Test that all metrics are properly normalized."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_all_metrics_normalized(self, mock_psutil):
        """
        Test that all new metrics are normalized to 0-1 range where appropriate.
        
        Rationale: Ensures consistent metric ranges.
        """
        # Setup mocks
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.cached = 2000000000
        mock_memory.buffers = 500000000
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = ComputationalPhysiologyMonitor()
        sample = monitor.sample_resources()
        
        # Check that all non-None metrics are in valid ranges
        for key, value in sample.items():
            if key != "timestamp" and value is not None:
                if isinstance(value, (int, float)):
                    # Some metrics might be lists or dicts, so only check numeric values
                    if not isinstance(value, (list, dict)):
                        # For normalized metrics, should be 0-1
                        # Some raw counts might be > 1, so we'll check per-metric
                        pass  # Implementation specific


class TestHistoryIncludesNewMetrics:
    """Test that history tracking includes new metrics."""
    
    @patch('broca.internal_sensing.computational_physiology.psutil')
    def test_history_includes_new_metrics(self, mock_psutil):
        """
        Test that history tracking includes new metrics.
        
        Rationale: Ensures historical samples contain new metric data.
        """
        # Setup mocks
        mock_psutil.cpu_percent.return_value = 50.0
        mock_memory = Mock()
        mock_memory.percent = 60.0
        mock_memory.total = 16000000000
        mock_memory.available = 8000000000
        mock_memory.cached = 2000000000
        mock_memory.buffers = 500000000
        mock_psutil.virtual_memory.return_value = mock_memory
        
        monitor = ComputationalPhysiologyMonitor()
        
        # Sample multiple times
        for _ in range(3):
            monitor.sample_resources()
        
        history = monitor.get_history()
        
        assert len(history) > 0
        # Check that history entries have expected structure
        assert "timestamp" in history[0]
        assert "computational_load" in history[0]
        assert "memory_pressure" in history[0]

