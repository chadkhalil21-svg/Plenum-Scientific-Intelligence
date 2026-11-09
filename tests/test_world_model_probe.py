"""Reproducible, limited world-model probe. No real-world ability claims."""
import math
import unittest

from plenum_ai.world_model_probe import (
    SCHEMA, experiment, fit_transition, trajectory, rollout_rmse,
    paired_action_interventions, counterfactual_effect_rmse,
)


class ActionConditionedSimulationProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = experiment()

    def test_separate_training_holdout_and_perturbed_physics(self):
        r = self.report
        self.assertEqual(r["schema"], SCHEMA)
        self.assertNotEqual(r["train_seed"], r["holdout_seed"])
        self.assertNotEqual(r["holdout_seed"], r["shifted_physics_seed"])
        self.assertEqual((r["train_transitions"], r["holdout_transitions"],
                          r["shifted_transitions"]), (448, 192, 192))
        self.assertEqual(set(r["heldout_action_sequences"]), {"1", "8", "32"})
        self.assertFalse(r["JEPA_model_trained"])
        self.assertFalse(r["general_intelligence_demonstrated"])
        self.assertFalse(r["real_world_digital_twin_verified"])
        self.assertFalse(r["real_observational_data_used"])

    def test_actions_improve_predictions_on_unseen_synthetic_sequences(self):
        data = self.report["heldout_action_sequences"]
        for horizon in ("1", "8", "32"):
            with self.subTest(horizon=horizon):
                m = data[horizon]
                self.assertGreater(m["action_conditioned_rmse"], 0)
                self.assertLess(m["action_conditioned_rmse"],
                                m["action_blind_rmse"])
                self.assertLess(m["action_conditioned_rmse"],
                                m["persistence_rmse"])
                self.assertTrue(all(math.isfinite(v) for v in m.values()))

    def test_changed_physics_is_detectable_generalization_limit(self):
        nominal = self.report["heldout_action_sequences"]
        changed = self.report["shifted_physics"]
        for horizon in ("1", "8", "32"):
            with self.subTest(horizon=horizon):
                self.assertGreater(
                    changed[horizon]["action_conditioned_rmse"],
                    nominal[horizon]["action_conditioned_rmse"])

    def test_same_initial_state_opposite_actions_counterfactuals(self):
        pairs = paired_action_interventions(409)
        self.assertEqual(len(pairs), 6)
        for (left, left_actions), (right, right_actions) in pairs:
            self.assertTrue((left[0] == right[0]).all())
            self.assertTrue((left_actions == -right_actions).all())
            self.assertFalse((left[-1] == right[-1]).all())

    def test_counterfactual_action_effects_not_just_motion_fit(self):
        # Freeze models trained on entirely separate episodes and compare
        # intervention effects, not merely predicted absolute positions.
        nominal = self.report["counterfactual_action_reversal"]
        shifted = self.report["shifted_counterfactual"]
        for horizon in ("1", "8", "32"):
            with self.subTest(horizon=horizon):
                actual = nominal[horizon]
                self.assertGreater(actual["action_conditioned_effect_rmse"], 0)
                self.assertLess(actual["action_conditioned_effect_rmse"],
                                actual["action_blind_effect_rmse"])
                self.assertGreater(shifted[horizon]["action_conditioned_effect_rmse"],
                                   actual["action_conditioned_effect_rmse"])
        self.assertFalse(self.report["real_observational_data_used"])
        self.assertFalse(self.report["JEPA_model_trained"])

    def test_counterfactual_estimator_rejects_nonmatching_starts(self):
        training = trajectory(141, episodes=2)
        model = fit_transition(training, with_actions=True)
        a = trajectory(409, episodes=1)[0]
        b = trajectory(410, episodes=1)[0]
        with self.assertRaises(ValueError):
            counterfactual_effect_rmse(model, [(a, b)], 1, True)

    def test_invalid_physical_constants_rejected(self):
        for changes in (
            {"mass": 0}, {"mass": -1}, {"stiffness": 0},
            {"damping": -1}, {"cubic": -1}, {"cubic": 12},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                trajectory(22, **changes, episodes=1)

    def test_retrain_not_permitted_on_heldout_episodes(self):
        training = trajectory(141, episodes=2)
        validation = trajectory(207, episodes=2)
        self.assertFalse((training[0][1] == validation[0][1]).all())
        model = fit_transition(training, with_actions=True)
        # Score is computed only, not used for updating fitted weights.
        before = model.coef_.copy()
        score = rollout_rmse(model, validation, 8, True)
        self.assertTrue(math.isfinite(score))
        self.assertTrue((before == model.coef_).all())


if __name__ == "__main__":
    unittest.main()
