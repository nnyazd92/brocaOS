Explainability usage guide (quick)

1) Purpose
- Understand which input features most influence the policy's selection of tools.

2) Running basic explanation (linear models)
- Ensure you have a trained sklearn model at models/rl/policy_bc.pkl and the scaler at data/rl/expanded_live/scaler.joblib.
- Create a context with rl_signals (composite_reward, dissonance_reward, surprise_reward, curiosity_reward, information_gain_reward, coherence_reward, exploration_balance).
- Call PolicyRanker.predict_distribution(context, tools) to get probabilities.
- Call broca/rl/explainability.append_explanation(uid, context, feature_names, feature_vector, model) to save a JSONL explanation in data/rl/explanations.jsonl.

3) Interpretation
- For linear models, explanations are per-class lists of top features with signed contributions (feature * coefficient). Positive means pushes model toward that class; negative pushes away.
- For non-linear models, compute permutation importance on a holdout set for robust global importance or use SHAP for local explanations (consider compute cost).

4) Quick CLI example (smoke)
- python3 -c "from broca.rl.policy import PolicyRanker; pr=PolicyRanker(); pr.load_model(None); from broca.tools.registry import ToolRegistry; tools=ToolRegistry().list_tools() or [type('T',(object,),{'name':'terminal'})('terminal')]; ctx={'rl_signals':{...}}; print(pr.predict_distribution(ctx,tools))"

5) Best practices (from web):
- Use permutation importance for model-agnostic, robust feature importance when feasible.
- Use SHAP for detailed local attributions if compute budget allows; otherwise use surrogate linear explanations.
- Normalize/scale features consistently between training and explanation.
- Store explanations with provenance and link to model/dataset memories for audit.

