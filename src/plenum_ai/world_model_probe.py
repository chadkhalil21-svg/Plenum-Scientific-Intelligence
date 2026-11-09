"""Bounded world-model prediction experiment using existing SciPy and scikit-learn.

This is an ACTION-CONDITIONED SYNTHETIC TRANSITION BASELINE, not JEPA,
a learned video representation, a validated real-world digital twin, or AGI.
No model download, cloud API, hidden weights, credentials or actuation.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from sklearn.linear_model import Ridge

SCHEMA = "plenum-world-model-synthetic-probe-v1"
DT = 0.12
STEPS = 32


def trajectory(seed, mass=1.0, stiffness=2.2, damping=0.18,
               cubic=0.55, episodes=6, action_sign=1.0):
    """Generate controlled observations from a stated nonlinear 1-D ODE."""
    if (not 0 < mass <= 100 or not 0 < stiffness <= 100
            or not 0 <= damping <= 10 or not 0 <= cubic <= 10):
        raise ValueError("Unphysical oscillator coefficients")
    if action_sign not in (-1.0, 1.0):
        raise ValueError("Controlled paired action reversal requires sign +/-1")
    rng = np.random.default_rng(seed)
    result = []
    for _ in range(episodes):
        state = np.array([rng.uniform(-1, 1), rng.uniform(-0.4, 0.4)],
                         dtype=float)
        states = [state.copy()]
        actions = rng.uniform(-2.5, 2.5, size=STEPS)*action_sign
        for action in actions:
            def rhs(t, y):
                return [y[1],
                        (-stiffness*y[0]-cubic*y[0]**3
                         -damping*y[1]*abs(y[1])+float(action))/mass]
            sim = solve_ivp(rhs, (0, DT), state, method="DOP853",
                            rtol=1e-11, atol=1e-12)
            if not sim.success:
                raise RuntimeError("Physics solver failed")
            state = np.asarray(sim.y[:, -1], dtype=float)
            states.append(state.copy())
        result.append((np.asarray(states), actions))
    return result


def fit_transition(episodes, with_actions):
    """Fit the reviewed upstream linear Ridge baseline, no new model engine."""
    features, targets = [], []
    for states, actions in episodes:
        features.append(
            np.column_stack((states[:-1, :], actions)) if with_actions
            else states[:-1, :])
        targets.append(states[1:, :])
    model = Ridge(alpha=1e-7, fit_intercept=False)
    model.fit(np.vstack(features), np.vstack(targets))
    return model


def rollout_rmse(model, episodes, horizon, with_actions):
    errors = []
    for states, actions in episodes:
        for start in range(0, STEPS-horizon+1, horizon):
            estimate = states[start].copy()
            for offset in range(horizon):
                action = float(actions[start+offset])
                features = np.array(
                    [[estimate[0], estimate[1], action]] if with_actions
                    else [[estimate[0], estimate[1]]])
                estimate = model.predict(features)[0]
            errors.extend((estimate-states[start+horizon]).tolist())
    return float(np.sqrt(np.mean(np.square(errors))))


def persistence_rmse(episodes, horizon):
    errors = []
    for states, _ in episodes:
        for start in range(0, STEPS-horizon+1, horizon):
            errors.extend((states[start]-states[start+horizon]).tolist())
    return float(np.sqrt(np.mean(np.square(errors))))


def paired_action_interventions(seed, **physics):
    """Same initial state and underlying RNG draws, opposite applied forces.

    These are simulator interventions, NOT interventions in the real world.
    """
    a = trajectory(seed, action_sign=1.0, **physics)
    b = trajectory(seed, action_sign=-1.0, **physics)
    return list(zip(a, b))


def counterfactual_effect_rmse(model, pairs, horizon, with_actions):
    """Error in predicted difference under do(action) versus do(-action).

    Only compare trajectories from an identical start, never train on pairs.
    """
    errors = []
    for (left_states, left_actions), (right_states, right_actions) in pairs:
        if not np.allclose(left_states[0], right_states[0], rtol=0, atol=1e-12):
            raise ValueError("Counterfactual starts must match exactly")
        predicts = []
        for actions in (left_actions, right_actions):
            estimate = left_states[0].copy()
            for offset in range(horizon):
                row = ([estimate[0], estimate[1], float(actions[offset])]
                       if with_actions else [estimate[0], estimate[1]])
                estimate = model.predict(np.asarray([row], dtype=float))[0]
            predicts.append(estimate)
        observed_effect = left_states[horizon]-right_states[horizon]
        errors.extend((predicts[0]-predicts[1]-observed_effect).tolist())
    return float(np.sqrt(np.mean(np.square(errors))))


def experiment():
    """Hold out different action sequences; separately stress altered physics."""
    train = trajectory(141, episodes=14)
    holdout = trajectory(207, episodes=6)
    shifted = trajectory(308, mass=1.35, stiffness=3.1,
                         damping=0.26, cubic=0.9, episodes=6)
    intervention_pairs = paired_action_interventions(409)
    shifted_interventions = paired_action_interventions(
        510, mass=1.35, stiffness=3.1, damping=0.26, cubic=0.9,
    )
    action_model = fit_transition(train, True)
    ablated = fit_transition(train, False)

    def score(episodes):
        return {
            str(horizon): {
                "action_conditioned_rmse": round(
                    rollout_rmse(action_model, episodes, horizon, True), 7),
                "action_blind_rmse": round(
                    rollout_rmse(ablated, episodes, horizon, False), 7),
                "persistence_rmse": round(
                    persistence_rmse(episodes, horizon), 7),
            } for horizon in (1, 8, 32)
        }

    def intervention_scores(pairs):
        return {
            str(h): {
                "action_conditioned_effect_rmse": round(
                    counterfactual_effect_rmse(action_model, pairs, h, True), 7),
                "action_blind_effect_rmse": round(
                    counterfactual_effect_rmse(ablated, pairs, h, False), 7),
            } for h in (1, 8, 32)
        }

    return {
        "schema": SCHEMA,
        "reused_upstream": ["SciPy solve_ivp / DOP853",
                            "scikit-learn Ridge", "NumPy"],
        "model_kind": "linear action-conditioned estimator tested against nonlinear physical dynamics",
        "training": "synthetic ODE observations only",
        "train_seed": 141,
        "holdout_seed": 207,
        "shifted_physics_seed": 308,
        "train_transitions": len(train)*STEPS,
        "holdout_transitions": len(holdout)*STEPS,
        "shifted_transitions": len(shifted)*STEPS,
        "heldout_action_sequences": score(holdout),
        "shifted_physics": score(shifted),
        "counterfactual_action_reversal": intervention_scores(intervention_pairs),
        "shifted_counterfactual": intervention_scores(shifted_interventions),
        "counterfactual_design": (
            "Same six held-out simulator initial states, identical RNG draws; "
            "opposite force sequences; compare delta outcomes to frozen "
            "predictors with and without actions. No real-world intervention."
        ),
        "JEPA_model_trained": False,
        "real_world_digital_twin_verified": False,
        "real_observational_data_used": False,
        "general_intelligence_demonstrated": False,
        "limitation": (
            "Synthetic observed-state regression against a known nonlinear ODE, "
            "not masked latent JEPA/video learning, external validation, or a "
            "general physics simulator. Results are not independent of the "
            "chosen simulator and do not establish causal understanding."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=Path("reports/world_model_synthetic_probe.json"))
    args = parser.parse_args()
    result = experiment()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n",
                           encoding="utf-8")
    print(json.dumps({
        "schema": result["schema"],
        "heldout_action_sequences": result["heldout_action_sequences"],
        "shifted_physics": result["shifted_physics"],
        "counterfactual_action_reversal": result["counterfactual_action_reversal"],
        "shifted_counterfactual": result["shifted_counterfactual"],
        "JEPA_model_trained": False,
        "general_intelligence_demonstrated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
