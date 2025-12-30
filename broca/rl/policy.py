"""PolicyRanker skeleton for BrocaOS RL integration.

Provides a simple interface to load a policy model and rank tools given a context.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional


class PolicyRanker:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.action_map = None

    def load_model(self, model_path: Optional[str] = None):
        path = model_path or self.model_path
        # Placeholder: load model from disk
        self.model = {"path": path}
        # Try sklearn model
        try:
            import joblib
            mpath = path or 'models/rl/policy_bc.pkl'
            self.model = joblib.load(mpath)
            # load action map
            try:
                am = {}
                with open('data/rl/action_map.csv') as f:
                    next(f)
                    for l in f:
                        k,v = l.strip().split(',',1)
                        am[int(v)] = k
                self.action_map = am
            except Exception:
                self.action_map = None
        except Exception:
            # keep fallback
            self.model = {"path": path}

    def rank_tools(self, context: Dict[str, Any], tools: List[Any]) -> List[Dict[str, Any]]:
        """Return a list of tool rankings: {tool_name, score, expected_reward} sorted desc."""
        # Simple heuristic: give equal scores, can be replaced by model inference
        ranked = []
        n = max(1, len(tools))
        for t in tools:
            ranked.append({"tool_name": getattr(t, 'name', str(t)), "score": 1.0 / n, "expected_reward": 0.5})
        ranked.sort(key=lambda r: r['score'], reverse=True)
        return ranked

    def predict_distribution(self, context: Dict[str, Any], tools: List[Any]) -> Dict[str, float]:
        """Return a mapping tool_name -> probability from model predictions."""
        # If sklearn model loaded, featurize context and predict probs
        if hasattr(self.model, 'predict_proba'):
            # simple featurization: use context_hash if present
            ch = str(context.get('rl_signals', {}).get('composite_reward', '0'))
            feat = [float(ch)] * (self.model.coef_.shape[1] if hasattr(self.model,'coef_') else 1)
            import numpy as np
            probs = self.model.predict_proba(np.array([feat]))[0]
            # Map probs by action_map to tool names
            res = {}
            if self.action_map:
                for aid,tool_name in self.action_map.items():
                    if aid < len(probs):
                        res[tool_name] = float(probs[aid])
            # Normalize to tools list, default small prob
            out = {}
            for t in tools:
                name = getattr(t,'name',str(t))
                out[name] = res.get(name, 1e-6)
            # Renormalize
            s = sum(out.values())
            if s>0:
                for k in out:
                    out[k] = out[k]/s
            return out
        # fallback uniform
        return {getattr(t,'name',str(t)): 1.0/len(tools) for t in tools}


__all__ = ["PolicyRanker"]
