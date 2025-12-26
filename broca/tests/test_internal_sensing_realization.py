import pytest
import time
import numpy as np
from broca.internal_sensing.framework import InternalSensingFramework
from broca.internal_sensing.response_analyzer import ResponseAnalyzer
from broca.internal_sensing.cognitive_state import CognitiveStateMonitor
from broca.internal_sensing.affective_state import ComputationalAffectMonitor

def test_informational_surprise_logic():
    """Test that semantic novelty triggers surprise."""
    # Low surprise: high overlap
    exp1 = "Melbourne weather"
    real1 = "The weather in Melbourne is sunny."
    surprise_low = ResponseAnalyzer.calculate_informational_surprise(exp1, real1)
    
    # High surprise: low overlap
    exp2 = "Melbourne weather"
    real2 = "The stock market in Tokyo is up."
    surprise_high = ResponseAnalyzer.calculate_informational_surprise(exp2, real2)
    
    assert surprise_high > surprise_low
    assert 0.0 <= surprise_low <= 1.0
    assert 0.0 <= surprise_high <= 1.0

def test_semantic_distance_logic():
    """Test cosine distance calculation for embeddings."""
    emb1 = [1.0, 0.0, 0.0]
    emb2 = [1.0, 0.0, 0.0] # Same
    emb3 = [0.0, 1.0, 0.0] # Orthogonal
    emb4 = [-1.0, 0.0, 0.0] # Opposite
    
    dist_same = ResponseAnalyzer.calculate_semantic_distance(emb1, emb2)
    dist_ortho = ResponseAnalyzer.calculate_semantic_distance(emb1, emb3)
    dist_opp = ResponseAnalyzer.calculate_semantic_distance(emb1, emb4)
    
    assert dist_same == 0.0
    assert dist_ortho == 0.5
    assert dist_opp == 1.0

def test_vader_sentiment_analysis():
    """Test VADER sentiment analysis integration."""
    text_pos = "I am so happy and excited about this progress!"
    text_neg = "This is terrible, I am very frustrated and sad."
    
    scores_pos = ResponseAnalyzer.analyze_sentiment_vader(text_pos)
    scores_neg = ResponseAnalyzer.analyze_sentiment_vader(text_neg)
    
    if scores_pos and scores_neg:
        assert scores_pos['compound'] > 0.5
        assert scores_neg['compound'] < -0.5

def test_logical_reversal_coherence():
    """Test that mid-stream corrections reduce coherence."""
    monitor = CognitiveStateMonitor()
    
    # Need at least 2 steps for coherence to be calculated
    monitor.record_reasoning_step('s1', {'premise': 'A', 'conclusion': 'B'})
    monitor.record_reasoning_step('s1a', {'premise': 'A', 'conclusion': 'B'})  # Consistent step
    coh_perfect = monitor.states['conceptual_coherence']
    
    # Reversal step
    monitor.record_reasoning_step('s2', {'premise': 'C', 'conclusion': 'Wait, actually I was wrong, it is D.'})
    coh_reversal = monitor.states['conceptual_coherence']
    
    # Perfect coherence should be high (1.0 or close)
    assert coh_perfect >= 0.8
    # Coherence with reversal should be reduced
    assert coh_reversal < 1.0

def test_thought_analysis_metrics():
    """Test that reasoning content analysis extracts uncertainty and depth."""
    thoughts = "I am not sure about this. Maybe it is X, but could be Y. Let me re-evaluate."
    metrics = ResponseAnalyzer.analyze_thoughts(thoughts)
    
    assert metrics['uncertainty'] > 0
    assert metrics['conflict'] > 0
    assert metrics['depth'] > 0

def test_dynamic_curiosity_and_pleasure():
    """Test that curiosity scales with surprise and pleasure with certainty."""
    affect = ComputationalAffectMonitor()
    
    # Set baseline
    affect.update_surprise(0.1)
    affect.compute_curiosity_drive(uncertainty=0.1, interest=0.1)
    curiosity_low = affect.affective_states['curiosity_drive']
    
    # Increase surprise
    affect.update_surprise(0.9)
    affect.compute_curiosity_drive(uncertainty=0.1, interest=0.1)
    curiosity_high = affect.affective_states['curiosity_drive']
    
    assert curiosity_high > curiosity_low
    
    # Test pleasure
    affect.update_certainty_affect(0.1)
    affect.update_coherence_pleasure(0.8)
    pleasure_low = affect.affective_states['coherence_pleasure']
    
    affect.update_certainty_affect(0.9)
    affect.update_coherence_pleasure(0.8)
    pleasure_high = affect.affective_states['coherence_pleasure']
    
    assert pleasure_high > pleasure_low

def test_error_risk_prediction():
    """Test that error risk increases with load and low confidence."""
    framework = InternalSensingFramework()
    
    # Low risk state
    framework.interoception.cognition.record_confidence('r1', 0.9)
    framework.interoception.physiology.metrics['computational_load'] = 0.1
    framework.interoception.cognition.states['conceptual_coherence'] = 0.9
    
    risk_low = framework.interoception.prediction.predict_error_probability(
        framework.interoception.cognition,
        framework.interoception.physiology,
        framework.interoception.affect
    )
    
    # High risk state
    framework.interoception.cognition.record_confidence('r2', 0.1)
    framework.interoception.physiology.metrics['computational_load'] = 0.9
    framework.interoception.cognition.states['conceptual_coherence'] = 0.1
    
    risk_high = framework.interoception.prediction.predict_error_probability(
        framework.interoception.cognition,
        framework.interoception.physiology,
        framework.interoception.affect
    )
    
    assert risk_high > risk_low

def test_integrated_surprise_flow():
    """Test the full flow from tool result to surprise in report."""
    framework = InternalSensingFramework()
    
    # Establish baseline
    framework.sample_internal_state()
    
    # Record a surprising tool result
    framework.record_informational_surprise("Expected A", "Found something completely different like ZZZ")
    
    # Bypass rate limiter
    framework._last_sample_time = 0
    
    state = framework.sample_internal_state()
    report = framework.generate_interoceptive_report()
    
    assert state['affective']['surprise'] > 0
    assert "Surprise:" in report
