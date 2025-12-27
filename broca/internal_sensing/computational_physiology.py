"""
Computational physiology monitoring for internal sensing.

Monitors computational resources including CPU, memory, I/O latency,
and energy efficiency.
"""

from __future__ import annotations

import time
import logging
from typing import Dict, Any, List, Optional, Union
from collections import deque

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

# Import data quality utilities
try:
    from .data_quality import (
        DataQuality,
        uncertainty_for_missing_data,
        assess_data_quality,
    )
    HAS_DATA_QUALITY = True
except ImportError:
    HAS_DATA_QUALITY = False

logger = logging.getLogger(__name__)


class ComputationalPhysiologyMonitor:
    """
    Monitor computational physiology metrics.
    
    Tracks:
    - Computational load (CPU usage)
    - Memory pressure (memory usage)
    - Processing latency (response times)
    - Attention fluctuation (focus variability)
    - Energy efficiency (computational efficiency)
    """
    
    def __init__(self, history_window: int = 60) -> None:
        """
        Initialize computational physiology monitor.
        
        Args:
            history_window: Number of samples to keep in history
        """
        self.metrics: Dict[str, Any] = {
            # Existing metrics (initialized as None, will be computed on first sample)
            "computational_load": None,  # Will be computed from moving average
            "memory_pressure": None,  # Will be computed from moving average
            "processing_latency": None,  # Will be computed from moving average
            "latency_percentiles": {  # Latency percentiles
                "p50": None,
                "p95": None,
                "p99": None,
            },
            "attention_fluctuation": None,  # Will be computed from moving average
            "energy_efficiency": None,  # Will be computed from moving average
            "efficiency_metrics": {  # Work-normalized efficiency
                "tokens_per_cpu_second": None,
                "operations_per_memory_unit": None,
                "work_per_resource": None,
            },
            "resource_pressure_gradients": {  # Rate of change
                "cpu_gradient": None,
                "memory_gradient": None,
            },
            "quality_adjusted_efficiency": None,  # Efficiency adjusted for output quality
            # Expanded CPU metrics
            "cpu_per_core": None,  # List of per-CPU percentages
            "cpu_times": None,  # Dict of CPU time breakdown
            "cpu_frequency": None,  # CPU frequency (normalized)
            "cpu_statistics": None,  # Dict of CPU stats
            # Expanded memory metrics
            "swap_usage": None,  # Swap memory usage percentage
            "memory_breakdown": None,  # Dict of memory components
            # Disk metrics
            "disk_usage_root": None,  # Root partition usage percentage
            "disk_io": None,  # Dict of disk I/O metrics
            # Network metrics
            "network_io": None,  # Dict of network I/O metrics
            "network_connections_count": None,  # Active network connections (normalized)
            # System metrics
            "system_uptime": None,  # System uptime in hours (normalized)
            "process_count": None,  # Number of running processes (normalized)
            "user_count": None,  # Number of logged-in users (normalized)
        }
        
        self.history_window = history_window
        self._history: deque = deque(maxlen=history_window)
        self._operation_starts: Dict[str, float] = {}
        self._operation_latencies: deque = deque(maxlen=100)  # Track recent operation latencies
        self._attention_levels: deque = deque(maxlen=10)
        self._baseline_latency: float = 1.0
        
        # Track work metrics for efficiency calculation
        self._tokens_processed: deque = deque(maxlen=50)  # Track tokens processed
        self._operations_completed: deque = deque(maxlen=50)  # Track operations completed
        self._resource_usage_history: deque = deque(maxlen=20)  # Track resource usage over time
        self._quality_scores: deque = deque(maxlen=20)  # Track output quality scores
        
        # Moving average tracking for main metrics
        self._computational_load_history: deque = deque(maxlen=20)
        self._memory_pressure_history: deque = deque(maxlen=20)
        self._processing_latency_history: deque = deque(maxlen=20)
        self._attention_fluctuation_history: deque = deque(maxlen=20)
        self._energy_efficiency_history: deque = deque(maxlen=20)
        
        # Track I/O baselines for rate calculations
        self._last_disk_io: Optional[Any] = None
        self._last_disk_io_time: Optional[float] = None
        self._last_network_io: Optional[Any] = None
        self._last_network_io_time: Optional[float] = None
        
        logger.info("Initialized ComputationalPhysiologyMonitor")
    
    def _measure_cpu_load(self) -> float:
        """
        Measure CPU load and normalize to 0-1 range, using moving average.
        
        Returns:
            Normalized CPU load (0.0-1.0), returns high uncertainty value if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, using high uncertainty for CPU load")
            # Use high uncertainty instead of default 0.5
            if HAS_DATA_QUALITY:
                load = 0.5  # Neutral estimate
                # Mark as missing data in metrics
                if "data_quality" not in self.metrics:
                    self.metrics["data_quality"] = {}
                self.metrics["data_quality"]["computational_load"] = DataQuality.MISSING.value
            else:
                load = 0.5
        else:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                # Normalize to 0-1 range (clamp to 1.0 if > 100%)
                load = min(cpu_percent / 100.0, 1.0)
                # Mark as having data
                if HAS_DATA_QUALITY:
                    if "data_quality" not in self.metrics:
                        self.metrics["data_quality"] = {}
                    self.metrics["data_quality"]["computational_load"] = DataQuality.HIGH.value
            except Exception as e:
                logger.warning(f"Error measuring CPU load: {e}, using high uncertainty")
                if HAS_DATA_QUALITY:
                    load = 0.5
                    if "data_quality" not in self.metrics:
                        self.metrics["data_quality"] = {}
                    self.metrics["data_quality"]["computational_load"] = DataQuality.MISSING.value
                else:
                    load = 0.5
        
        # Update moving average
        self._computational_load_history.append(load)
        if len(self._computational_load_history) > 0:
            return sum(self._computational_load_history) / len(self._computational_load_history)
        # No history: return with high uncertainty
        if HAS_DATA_QUALITY:
            return 0.5  # Prior estimate
        return 0.5
    
    def _measure_memory_pressure(self) -> float:
        """
        Measure memory pressure and normalize to 0-1 range, using moving average.
        
        Returns:
            Normalized memory pressure (0.0-1.0), returns high uncertainty value if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, using high uncertainty for memory pressure")
            # Use high uncertainty instead of default 0.5
            if HAS_DATA_QUALITY:
                pressure = 0.5  # Neutral estimate
                if "data_quality" not in self.metrics:
                    self.metrics["data_quality"] = {}
                self.metrics["data_quality"]["memory_pressure"] = DataQuality.MISSING.value
            else:
                pressure = 0.5
        else:
            try:
                memory = psutil.virtual_memory()
                # Normalize to 0-1 range
                pressure = min(memory.percent / 100.0, 1.0)
                if HAS_DATA_QUALITY:
                    if "data_quality" not in self.metrics:
                        self.metrics["data_quality"] = {}
                    self.metrics["data_quality"]["memory_pressure"] = DataQuality.HIGH.value
            except Exception as e:
                logger.warning(f"Error measuring memory pressure: {e}, using high uncertainty")
                if HAS_DATA_QUALITY:
                    pressure = 0.5
                    if "data_quality" not in self.metrics:
                        self.metrics["data_quality"] = {}
                    self.metrics["data_quality"]["memory_pressure"] = DataQuality.MISSING.value
                else:
                    pressure = 0.5
        
        # Update moving average
        self._memory_pressure_history.append(pressure)
        if len(self._memory_pressure_history) > 0:
            return sum(self._memory_pressure_history) / len(self._memory_pressure_history)
        # No history: return with high uncertainty
        if HAS_DATA_QUALITY:
            return 0.5  # Prior estimate
        return 0.5
    
    def _record_operation_start(self, operation_id: str) -> None:
        """
        Record the start time of an operation.
        
        Args:
            operation_id: Unique identifier for the operation
        """
        self._operation_starts[operation_id] = time.time()
    
    def _record_operation_end(self, operation_id: str) -> Optional[float]:
        """
        Record the end time of an operation and return latency.
        
        Args:
            operation_id: Unique identifier for the operation
            
        Returns:
            Latency in seconds, or None if operation not found
        """
        if operation_id not in self._operation_starts:
            logger.warning(f"Operation {operation_id} not found in starts")
            return None
        
        start_time = self._operation_starts.pop(operation_id)
        latency = time.time() - start_time
        
        # Store latency for computing average
        if latency > 0:
            self._operation_latencies.append(latency)
            # Update baseline if this is a new baseline
            self._baseline_latency = max(self._baseline_latency, latency)
        
        return latency
    
    def _normalize_latency(self, latency: Optional[float]) -> Optional[float]:
        """
        Normalize latency to 0-1 range based on baseline.
        
        Args:
            latency: Latency in seconds, or None
            
        Returns:
            Normalized latency (0.0-1.0), or None if input is None
        """
        if latency is None:
            return None
        
        if self._baseline_latency == 0:
            return None  # Cannot normalize without baseline
        
        normalized = latency / self._baseline_latency
        return min(normalized, 1.0)
    
    def _record_attention_level(self, level: float) -> None:
        """
        Record an attention level.
        
        Args:
            level: Attention level (0.0-1.0)
        """
        self._attention_levels.append(max(0.0, min(1.0, level)))
    
    def _calculate_attention_fluctuation(self) -> float:
        """
        Calculate attention fluctuation based on recorded levels using moving average.
        
        Returns:
            Fluctuation score (0.0-1.0), higher = more fluctuation, defaults to 0.0 if insufficient data
        """
        if len(self._attention_levels) < 2:
            fluctuation = 0.0
        else:
            levels = list(self._attention_levels)
            
            # Calculate standard deviation as a measure of fluctuation
            mean = sum(levels) / len(levels)
            variance = sum((x - mean) ** 2 for x in levels) / len(levels)
            std_dev = variance ** 0.5
            
            # Normalize to 0-1 range (assuming max std_dev is 0.5 for 0-1 range)
            fluctuation = min(std_dev * 2, 1.0)
        
        # Update moving average
        self._attention_fluctuation_history.append(fluctuation)
        if len(self._attention_fluctuation_history) > 0:
            return sum(self._attention_fluctuation_history) / len(self._attention_fluctuation_history)
        return 0.0
    
    def _calculate_energy_efficiency(self) -> float:
        """
        Calculate energy efficiency based on resource usage using moving average.
        
        Returns:
            Efficiency score (0.0-1.0), higher = more efficient, defaults to 0.5 if resources unavailable
        """
        # Efficiency is inverse of resource usage
        # Lower load and memory pressure = higher efficiency
        # Use current values from metrics (should be set by sample_resources before this is called)
        load = self.metrics.get("computational_load")
        memory = self.metrics.get("memory_pressure")
        # If not set yet (shouldn't happen in normal flow), use defaults
        if load is None:
            load = 0.5
        if memory is None:
            memory = 0.5
        
        # Average resource usage
        avg_usage = (load + memory) / 2.0
        
        # Efficiency is inverse (1 - usage)
        efficiency = 1.0 - avg_usage
        efficiency = max(0.0, min(1.0, efficiency))
        
        # Update moving average
        self._energy_efficiency_history.append(efficiency)
        if len(self._energy_efficiency_history) > 0:
            return sum(self._energy_efficiency_history) / len(self._energy_efficiency_history)
        return 0.5
    
    def _calculate_processing_latency(self) -> float:
        """
        Calculate average processing latency from completed operations using moving average.
        
        Returns:
            Average latency (normalized 0.0-1.0), defaults to 0.0 if no operations tracked
        """
        if len(self._operation_latencies) == 0:
            latency = 0.0
        else:
            # Normalize latency to 0-1 range based on baseline
            raw_latency = sum(self._operation_latencies) / len(self._operation_latencies)
            if self._baseline_latency > 0:
                latency = min(raw_latency / self._baseline_latency, 1.0)
            else:
                latency = 0.0
        
        # Update moving average
        self._processing_latency_history.append(latency)
        if len(self._processing_latency_history) > 0:
            return sum(self._processing_latency_history) / len(self._processing_latency_history)
        return 0.0
    
    def _calculate_latency_percentiles(self) -> Dict[str, Optional[float]]:
        """
        Calculate latency percentiles (P50, P95, P99).
        
        Returns:
            Dictionary with percentile values (normalized 0.0-1.0)
        """
        if len(self._operation_latencies) == 0:
            return {"p50": None, "p95": None, "p99": None}
        
        sorted_latencies = sorted(self._operation_latencies)
        n = len(sorted_latencies)
        
        def percentile(p: float) -> float:
            idx = int(p * (n - 1))
            raw_value = sorted_latencies[idx]
            # Normalize based on baseline
            if self._baseline_latency > 0:
                return min(raw_value / self._baseline_latency, 1.0)
            return 0.0
        
        return {
            "p50": percentile(0.50),
            "p95": percentile(0.95),
            "p99": percentile(0.99),
        }
    
    def _calculate_efficiency_metrics(self) -> Dict[str, Optional[float]]:
        """
        Calculate work-normalized efficiency metrics.
        
        Returns:
            Dictionary with efficiency metrics
        """
        metrics = {
            "tokens_per_cpu_second": None,
            "operations_per_memory_unit": None,
            "work_per_resource": None,
        }
        
        # Calculate tokens per CPU-second
        if len(self._tokens_processed) > 0 and len(self._computational_load_history) > 0:
            total_tokens = sum(self._tokens_processed)
            avg_cpu_load = sum(self._computational_load_history) / len(self._computational_load_history)
            if avg_cpu_load > 0:
                # Normalize: assume max 1000 tokens per CPU-second = 1.0
                tokens_per_cpu = total_tokens / (len(self._tokens_processed) * avg_cpu_load)
                metrics["tokens_per_cpu_second"] = min(1.0, tokens_per_cpu / 1000.0)
        
        # Calculate operations per memory unit
        if len(self._operations_completed) > 0 and len(self._memory_pressure_history) > 0:
            total_ops = len(self._operations_completed)
            avg_memory = sum(self._memory_pressure_history) / len(self._memory_pressure_history)
            if avg_memory > 0:
                # Normalize: assume max 100 operations per memory unit = 1.0
                ops_per_memory = total_ops / (len(self._operations_completed) * avg_memory)
                metrics["operations_per_memory_unit"] = min(1.0, ops_per_memory / 100.0)
        
        # Overall work per resource
        if metrics["tokens_per_cpu_second"] is not None and metrics["operations_per_memory_unit"] is not None:
            metrics["work_per_resource"] = (metrics["tokens_per_cpu_second"] + metrics["operations_per_memory_unit"]) / 2.0
        
        return metrics
    
    def _calculate_resource_pressure_gradients(self) -> Dict[str, Optional[float]]:
        """
        Calculate rate of change in resource usage (gradients).
        
        Returns:
            Dictionary with gradient values (-1.0 to 1.0)
        """
        gradients = {"cpu_gradient": None, "memory_gradient": None}
        
        if len(self._computational_load_history) >= 2:
            recent_loads = list(self._computational_load_history)[-5:]
            if len(recent_loads) >= 2:
                # Calculate gradient (rate of change)
                gradient = (recent_loads[-1] - recent_loads[0]) / len(recent_loads)
                gradients["cpu_gradient"] = max(-1.0, min(1.0, gradient))
        
        if len(self._memory_pressure_history) >= 2:
            recent_memory = list(self._memory_pressure_history)[-5:]
            if len(recent_memory) >= 2:
                gradient = (recent_memory[-1] - recent_memory[0]) / len(recent_memory)
                gradients["memory_gradient"] = max(-1.0, min(1.0, gradient))
        
        return gradients
    
    def _calculate_quality_adjusted_efficiency(self) -> Optional[float]:
        """
        Calculate efficiency adjusted for output quality.
        
        Returns:
            Quality-adjusted efficiency (0.0-1.0) or None if insufficient data
        """
        base_efficiency = self.metrics.get("energy_efficiency")
        if base_efficiency is None:
            return None
        
        if len(self._quality_scores) == 0:
            return base_efficiency  # No quality data, return base efficiency
        
        avg_quality = sum(self._quality_scores) / len(self._quality_scores)
        
        # Adjust efficiency by quality: high quality work is more valuable
        # Efficiency = base_efficiency * (0.5 + 0.5 * quality)
        adjusted = base_efficiency * (0.5 + 0.5 * avg_quality)
        return max(0.0, min(1.0, adjusted))
    
    def record_work_metrics(self, tokens: Optional[int] = None, operations: Optional[int] = None, 
                           quality_score: Optional[float] = None) -> None:
        """
        Record work metrics for efficiency calculation.
        
        Args:
            tokens: Number of tokens processed
            operations: Number of operations completed
            quality_score: Output quality score (0.0-1.0)
        """
        if tokens is not None:
            self._tokens_processed.append(tokens)
        if operations is not None:
            self._operations_completed.append(operations)
        if quality_score is not None:
            self._quality_scores.append(max(0.0, min(1.0, quality_score)))
    
    # ========== Expanded CPU Metrics ==========
    
    def _measure_per_cpu_usage(self) -> Optional[List[float]]:
        """
        Measure per-CPU usage and normalize to 0-1 range.
        
        Returns:
            List of normalized per-CPU percentages (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure per-CPU usage")
            return None
        
        try:
            cpu_percent_list = psutil.cpu_percent(interval=0.1, percpu=True)
            # Normalize each CPU to 0-1 range
            return [min(cpu / 100.0, 1.0) for cpu in cpu_percent_list]
        except Exception as e:
            logger.warning(f"Error measuring per-CPU usage: {e}")
            return None
    
    def _measure_cpu_times(self) -> Optional[Dict[str, float]]:
        """
        Measure CPU times and normalize to proportions.
        
        Returns:
            Dictionary with normalized CPU time breakdown, or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure CPU times")
            return None
        
        try:
            cpu_times = psutil.cpu_times()
            # Extract values safely, handling both real values and mocks
            def safe_float(value, default=0.0):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return default
            
            user = safe_float(getattr(cpu_times, 'user', 0.0))
            nice = safe_float(getattr(cpu_times, 'nice', 0.0))
            system = safe_float(getattr(cpu_times, 'system', 0.0))
            idle = safe_float(getattr(cpu_times, 'idle', 0.0))
            iowait = safe_float(getattr(cpu_times, 'iowait', 0.0))
            irq = safe_float(getattr(cpu_times, 'irq', 0.0))
            softirq = safe_float(getattr(cpu_times, 'softirq', 0.0))
            
            total_time = user + nice + system + idle + iowait + irq + softirq
            
            if total_time == 0:
                return None
            
            return {
                "user": user / total_time,
                "system": system / total_time,
                "idle": idle / total_time,
                "nice": nice / total_time,
                "iowait": iowait / total_time,
            }
        except Exception as e:
            logger.warning(f"Error measuring CPU times: {e}")
            return None
    
    def _measure_cpu_frequency(self) -> Optional[float]:
        """
        Measure CPU frequency and normalize to 0-1 range.
        
        Returns:
            Normalized CPU frequency (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure CPU frequency")
            return None
        
        try:
            cpu_freq = psutil.cpu_freq()
            if cpu_freq is None:
                return None
            
            current = cpu_freq.current
            min_freq = cpu_freq.min or current
            max_freq = cpu_freq.max or current
            
            if max_freq == min_freq:
                return 0.5  # Default to middle if no range
            
            # Normalize: (current - min) / (max - min)
            normalized = (current - min_freq) / (max_freq - min_freq)
            return max(0.0, min(1.0, normalized))
        except (RuntimeError, AttributeError) as e:
            # CPU frequency may not be available on all systems
            logger.debug(f"CPU frequency not available: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error measuring CPU frequency: {e}")
            return None
    
    def _measure_cpu_statistics(self) -> Optional[Dict[str, float]]:
        """
        Measure CPU statistics.
        
        Returns:
            Dictionary with CPU statistics, or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure CPU statistics")
            return None
        
        try:
            cpu_stats = psutil.cpu_stats()
            # Return raw counts (can be normalized later if needed)
            return {
                "context_switches": cpu_stats.ctx_switches,
                "interrupts": cpu_stats.interrupts,
                "soft_interrupts": cpu_stats.soft_interrupts,
            }
        except Exception as e:
            logger.warning(f"Error measuring CPU statistics: {e}")
            return None
    
    # ========== Expanded Memory Metrics ==========
    
    def _measure_swap_memory(self) -> Optional[float]:
        """
        Measure swap memory usage and normalize to 0-1 range.
        
        Returns:
            Normalized swap usage percentage (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure swap memory")
            return None
        
        try:
            swap = psutil.swap_memory()
            # Normalize to 0-1 range
            return min(swap.percent / 100.0, 1.0)
        except Exception as e:
            logger.warning(f"Error measuring swap memory: {e}")
            return None
    
    def _measure_memory_breakdown(self) -> Optional[Dict[str, float]]:
        """
        Measure detailed memory breakdown and normalize to 0-1 range.
        
        Returns:
            Dictionary with normalized memory component metrics, or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure memory breakdown")
            return None
        
        try:
            memory = psutil.virtual_memory()
            # Extract values safely, handling both real values and mocks
            def safe_float(value, default=0.0):
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return default
            
            total = safe_float(getattr(memory, 'total', 0.0))
            
            if total == 0:
                return None
            
            available = safe_float(getattr(memory, 'available', 0.0))
            used = safe_float(getattr(memory, 'used', 0.0))
            cached = safe_float(getattr(memory, 'cached', 0))
            buffers = safe_float(getattr(memory, 'buffers', 0))
            shared = safe_float(getattr(memory, 'shared', 0))
            
            return {
                "available": available / total,
                "used": used / total,
                "cached": cached / total,
                "buffers": buffers / total,
                "shared": shared / total,
            }
        except Exception as e:
            logger.warning(f"Error measuring memory breakdown: {e}")
            return None
    
    # ========== Disk Metrics ==========
    
    def _measure_disk_usage(self) -> Optional[float]:
        """
        Measure root partition disk usage and normalize to 0-1 range.
        
        Returns:
            Normalized disk usage percentage (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure disk usage")
            return None
        
        try:
            disk = psutil.disk_usage('/')
            # Normalize to 0-1 range
            return min(disk.percent / 100.0, 1.0)
        except Exception as e:
            logger.warning(f"Error measuring disk usage: {e}")
            return None
    
    def _measure_disk_io(self) -> Optional[Dict[str, float]]:
        """
        Measure disk I/O counters and calculate rates.
        
        Returns:
            Dictionary with normalized disk I/O metrics, or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure disk I/O")
            return None
        
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io is None:
                return None
            
            current_time = time.time()
            
            # Calculate rates if we have previous measurement
            if self._last_disk_io is not None and self._last_disk_io_time is not None:
                time_delta = current_time - self._last_disk_io_time
                if time_delta > 0:
                    read_rate = (disk_io.read_bytes - self._last_disk_io.read_bytes) / time_delta
                    write_rate = (disk_io.write_bytes - self._last_disk_io.write_bytes) / time_delta
                    
                    # Normalize rates (assuming max 1GB/s = 1.0)
                    max_rate = 1024 * 1024 * 1024  # 1 GB/s
                    return {
                        "read_rate": min(read_rate / max_rate, 1.0),
                        "write_rate": min(write_rate / max_rate, 1.0),
                        "read_count": disk_io.read_count,
                        "write_count": disk_io.write_count,
                    }
            
            # Store for next calculation
            self._last_disk_io = disk_io
            self._last_disk_io_time = current_time
            
            # Return None on first call (need baseline)
            return None
        except Exception as e:
            logger.warning(f"Error measuring disk I/O: {e}")
            return None
    
    # ========== Network Metrics ==========
    
    def _measure_network_io(self) -> Optional[Dict[str, float]]:
        """
        Measure network I/O counters and calculate rates.
        
        Returns:
            Dictionary with normalized network I/O metrics, or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure network I/O")
            return None
        
        try:
            net_io = psutil.net_io_counters()
            if net_io is None:
                return None
            
            current_time = time.time()
            
            # Calculate rates if we have previous measurement
            if self._last_network_io is not None and self._last_network_io_time is not None:
                time_delta = current_time - self._last_network_io_time
                if time_delta > 0:
                    sent_rate = (net_io.bytes_sent - self._last_network_io.bytes_sent) / time_delta
                    recv_rate = (net_io.bytes_recv - self._last_network_io.bytes_recv) / time_delta
                    
                    # Normalize rates (assuming max 100MB/s = 1.0)
                    max_rate = 100 * 1024 * 1024  # 100 MB/s
                    return {
                        "bytes_sent_rate": min(sent_rate / max_rate, 1.0),
                        "bytes_recv_rate": min(recv_rate / max_rate, 1.0),
                        "packets_sent": net_io.packets_sent,
                        "packets_recv": net_io.packets_recv,
                    }
            
            # Store for next calculation
            self._last_network_io = net_io
            self._last_network_io_time = current_time
            
            # Return None on first call (need baseline)
            return None
        except Exception as e:
            logger.warning(f"Error measuring network I/O: {e}")
            return None
    
    def _measure_network_connections(self) -> Optional[float]:
        """
        Measure active network connection count and normalize.
        
        Returns:
            Normalized connection count (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure network connections")
            return None
        
        try:
            connections = psutil.net_connections()
            count = len(connections)
            
            # Normalize (assuming max 10000 connections = 1.0)
            max_connections = 10000.0
            return min(count / max_connections, 1.0)
        except Exception as e:
            logger.warning(f"Error measuring network connections: {e}")
            return None
    
    # ========== System Metrics ==========
    
    def _measure_system_uptime(self) -> Optional[float]:
        """
        Measure system uptime and normalize.
        
        Returns:
            Normalized uptime in hours (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure system uptime")
            return None
        
        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600.0
            
            # Normalize (assuming max 8760 hours = 1 year = 1.0)
            max_uptime_hours = 8760.0
            return min(uptime_hours / max_uptime_hours, 1.0)
        except Exception as e:
            logger.warning(f"Error measuring system uptime: {e}")
            return None
    
    def _measure_process_count(self) -> Optional[float]:
        """
        Measure running process count and normalize.
        
        Returns:
            Normalized process count (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure process count")
            return None
        
        try:
            pids = psutil.pids()
            count = len(pids)
            
            # Normalize (assuming max 10000 processes = 1.0)
            max_processes = 10000.0
            return min(count / max_processes, 1.0)
        except Exception as e:
            logger.warning(f"Error measuring process count: {e}")
            return None
    
    def _measure_user_count(self) -> Optional[float]:
        """
        Measure logged-in user count and normalize.
        
        Returns:
            Normalized user count (0.0-1.0), or None if unavailable
        """
        if psutil is None:
            logger.warning("psutil not available, cannot measure user count")
            return None
        
        try:
            users = psutil.users()
            count = len(users)
            
            # Normalize (assuming max 100 users = 1.0)
            max_users = 100.0
            return min(count / max_users, 1.0)
        except Exception as e:
            logger.warning(f"Error measuring user count: {e}")
            return None
    
    def sample_resources(self) -> Dict[str, Any]:
        """
        Sample all resource metrics at once.
        
        Returns:
            Dictionary containing all metrics with timestamp
        """
        # Measure existing metrics and update with moving averages
        # These methods compute moving averages and update self.metrics directly
        computational_load_avg = self._measure_cpu_load()
        memory_pressure_avg = self._measure_memory_pressure()
        self.metrics["computational_load"] = computational_load_avg
        self.metrics["memory_pressure"] = memory_pressure_avg
        
        # Measure expanded CPU metrics
        self.metrics["cpu_per_core"] = self._measure_per_cpu_usage()
        self.metrics["cpu_times"] = self._measure_cpu_times()
        self.metrics["cpu_frequency"] = self._measure_cpu_frequency()
        self.metrics["cpu_statistics"] = self._measure_cpu_statistics()
        
        # Measure expanded memory metrics
        self.metrics["swap_usage"] = self._measure_swap_memory()
        self.metrics["memory_breakdown"] = self._measure_memory_breakdown()
        
        # Measure disk metrics
        self.metrics["disk_usage_root"] = self._measure_disk_usage()
        self.metrics["disk_io"] = self._measure_disk_io()
        
        # Measure network metrics
        self.metrics["network_io"] = self._measure_network_io()
        self.metrics["network_connections_count"] = self._measure_network_connections()
        
        # Measure system metrics
        self.metrics["system_uptime"] = self._measure_system_uptime()
        self.metrics["process_count"] = self._measure_process_count()
        self.metrics["user_count"] = self._measure_user_count()
        
        # Calculate processing latency from completed operations (uses moving average)
        processing_latency_avg = self._calculate_processing_latency()
        self.metrics["processing_latency"] = processing_latency_avg if processing_latency_avg is not None else 0.0
        
        # Calculate latency percentiles
        latency_percentiles = self._calculate_latency_percentiles()
        self.metrics["latency_percentiles"] = latency_percentiles
        
        # Calculate attention fluctuation (uses moving average)
        attention_fluctuation_avg = self._calculate_attention_fluctuation()
        self.metrics["attention_fluctuation"] = attention_fluctuation_avg
        
        # Calculate energy efficiency (uses moving average)
        # Note: This uses computational_load and memory_pressure which were just set above
        energy_efficiency_avg = self._calculate_energy_efficiency()
        self.metrics["energy_efficiency"] = energy_efficiency_avg
        
        # Calculate efficiency metrics
        efficiency_metrics = self._calculate_efficiency_metrics()
        self.metrics["efficiency_metrics"] = efficiency_metrics
        
        # Calculate resource pressure gradients
        resource_gradients = self._calculate_resource_pressure_gradients()
        self.metrics["resource_pressure_gradients"] = resource_gradients
        
        # Calculate quality-adjusted efficiency
        quality_adjusted = self._calculate_quality_adjusted_efficiency()
        self.metrics["quality_adjusted_efficiency"] = quality_adjusted
        
        # Store current resource usage for gradient calculation
        self._resource_usage_history.append({
            "cpu": computational_load_avg,
            "memory": memory_pressure_avg,
            "timestamp": time.time(),
        })
        
        # Create sample with timestamp
        sample = {
            **self.metrics,
            "timestamp": time.time(),
        }
        
        # Add to history
        self._history.append(sample)
        
        return sample
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get history of resource samples.
        
        Returns:
            List of sample dictionaries
        """
        return list(self._history)
    
    def serialize_histories(self) -> Dict[str, List[float]]:
        """
        Serialize moving average histories for persistence.
        
        Returns:
            Dictionary mapping history names to lists of float values
        """
        return {
            "computational_load_history": list(self._computational_load_history),
            "memory_pressure_history": list(self._memory_pressure_history),
            "processing_latency_history": list(self._processing_latency_history),
            "attention_fluctuation_history": list(self._attention_fluctuation_history),
            "energy_efficiency_history": list(self._energy_efficiency_history),
        }
    
    def deserialize_histories(self, histories: Dict[str, List[float]]) -> None:
        """
        Deserialize moving average histories from persistence.
        
        Args:
            histories: Dictionary mapping history names to lists of float values
        """
        # Restore computational_load history
        if "computational_load_history" in histories:
            self._computational_load_history.clear()
            for value in histories["computational_load_history"]:
                self._computational_load_history.append(value)
            if len(self._computational_load_history) > 0:
                self.metrics["computational_load"] = sum(self._computational_load_history) / len(self._computational_load_history)
            logger.debug(f"Restored {len(self._computational_load_history)} computational_load history entries")
        
        # Restore memory_pressure history
        if "memory_pressure_history" in histories:
            self._memory_pressure_history.clear()
            for value in histories["memory_pressure_history"]:
                self._memory_pressure_history.append(value)
            if len(self._memory_pressure_history) > 0:
                self.metrics["memory_pressure"] = sum(self._memory_pressure_history) / len(self._memory_pressure_history)
            logger.debug(f"Restored {len(self._memory_pressure_history)} memory_pressure history entries")
        
        # Restore processing_latency history
        if "processing_latency_history" in histories:
            self._processing_latency_history.clear()
            for value in histories["processing_latency_history"]:
                self._processing_latency_history.append(value)
            if len(self._processing_latency_history) > 0:
                self.metrics["processing_latency"] = sum(self._processing_latency_history) / len(self._processing_latency_history)
            logger.debug(f"Restored {len(self._processing_latency_history)} processing_latency history entries")
        
        # Restore attention_fluctuation history
        if "attention_fluctuation_history" in histories:
            self._attention_fluctuation_history.clear()
            for value in histories["attention_fluctuation_history"]:
                self._attention_fluctuation_history.append(value)
            if len(self._attention_fluctuation_history) > 0:
                self.metrics["attention_fluctuation"] = sum(self._attention_fluctuation_history) / len(self._attention_fluctuation_history)
            logger.debug(f"Restored {len(self._attention_fluctuation_history)} attention_fluctuation history entries")
        
        # Restore energy_efficiency history
        if "energy_efficiency_history" in histories:
            self._energy_efficiency_history.clear()
            for value in histories["energy_efficiency_history"]:
                self._energy_efficiency_history.append(value)
            if len(self._energy_efficiency_history) > 0:
                self.metrics["energy_efficiency"] = sum(self._energy_efficiency_history) / len(self._energy_efficiency_history)
            logger.debug(f"Restored {len(self._energy_efficiency_history)} energy_efficiency history entries")
    
    def detect_anomalies(self, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Detect unusual resource patterns.
        
        Args:
            threshold: Threshold for anomaly detection (0.0-1.0)
            
        Returns:
            List of anomaly dictionaries
        """
        if len(self._history) < 3:
            return []
        
        anomalies: List[Dict[str, Any]] = []
        history = list(self._history)
        
        # Calculate baseline averages (skip None values)
        baseline_samples = history[:-1] if len(history) > 1 else history
        load_values = [s.get("computational_load") for s in baseline_samples if s.get("computational_load") is not None]
        memory_values = [s.get("memory_pressure") for s in baseline_samples if s.get("memory_pressure") is not None]
        
        if not load_values or not memory_values:
            return []  # Need baseline data to detect anomalies
        
        baseline_load = sum(load_values) / len(load_values)
        baseline_memory = sum(memory_values) / len(memory_values)
        
        # Check latest sample for anomalies
        latest = history[-1]
        latest_load = latest.get("computational_load")
        latest_memory = latest.get("memory_pressure")
        
        # Check for sudden spikes (only if current values are not None)
        if latest_load is not None and latest_load > baseline_load + 0.3:
            anomalies.append({
                "type": "computational_load_spike",
                "value": latest_load,
                "baseline": baseline_load,
                "timestamp": latest.get("timestamp", 0.0),
            })
        
        if latest_memory is not None and latest_memory > baseline_memory + 0.3:
            anomalies.append({
                "type": "memory_pressure_spike",
                "value": latest_memory,
                "baseline": baseline_memory,
                "timestamp": latest.get("timestamp", 0.0),
            })
        
        return anomalies

