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
            # prefer using an explicit scaler if present
            try:
                from pathlib import Path
                import joblib
                scaler_path = Path('data/rl/expanded_live/scaler.joblib')
                if scaler_path.exists():
                    scaler = joblib.load(scaler_path)
                else:
                    scaler = None
            except Exception:
                scaler = None

            # featurize using RL signals if present, fall back to context hash
            rl = context.get('rl_signals') or {}
            feat = []
            if rl:
                keys = ['composite_reward','dissonance_reward','surprise_reward','curiosity_reward','information_gain_reward','coherence_reward','exploration_balance']
                for k in keys:
                    feat.append(float(rl.get(k,0.0)))
            else:
                ch = str(context.get('rl_signals', {}).get('composite_reward', '0'))
                feat = [float(ch)] * (self.model.coef_.shape[1] if hasattr(self.model,'coef_') else 1)

            import numpy as np
            x = np.array([feat], dtype=float)
            if scaler is not None:
                # pad or truncate if mismatch
                n_feat_model = self.model.coef_.shape[1] if hasattr(self.model,'coef_') else x.shape[1]
                if x.shape[1] != n_feat_model:
                    # try to adjust by zero-padding or truncating
                    if x.shape[1] < n_feat_model:
                        pad = np.zeros((1, n_feat_model - x.shape[1]))
                        x = np.concatenate([x, pad], axis=1)
                    else:
                        x = x[:, :n_feat_model]
                x = scaler.transform(x)
            probs = self.model.predict_proba(x)[0]
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
