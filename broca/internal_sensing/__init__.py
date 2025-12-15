"""
Internal sensing system for computational interoception.

Provides multi-layered monitoring of internal states including:
- Computational physiology (resources, latency, efficiency)
- Cognitive states (confidence, coherence, attention)
- Affective states (valence, arousal, curiosity)
- Predictive interoception (forecasting future states)
- Integrated interoceptive awareness
"""

from .computational_physiology import ComputationalPhysiologyMonitor
from .cognitive_state import CognitiveStateMonitor
from .affective_state import ComputationalAffectMonitor
from .predictive_interoception import PredictiveInteroception
from .integrated_interoception import IntegratedInteroception
from .framework import InternalSensingFramework

__all__ = [
    "ComputationalPhysiologyMonitor",
    "CognitiveStateMonitor",
    "ComputationalAffectMonitor",
    "PredictiveInteroception",
    "IntegratedInteroception",
    "InternalSensingFramework",
]

