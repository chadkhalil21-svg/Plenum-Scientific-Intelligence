"""Deterministic small-scale science exam evaluation tests (offline)."""
import unittest
from plenum_ai.science_eval import normalize, choose_rows, format_prompt, evaluate_cases

def case(i, answer="B"):
    return {
        "id": "ARC-fixture-" + str(i),
        "question": f"Which mechanism best explains sample {i}?",
        "choices": {"label": ["A", "B", "C", "D"],
                    "text": ["conduction", "gravity", "refraction", "diffusion"]},
        "answerKey": answer,
    }


class ScienceEvaluationTests(unittest.TestCase):
    def test_answers_not_leaked_to_prompt(self):
        item = normalize(case(1))
        prompt = format_prompt(item)
        self.assertIn("A.", prompt)
        self.assertIn("D.", prompt)
        self.assertNotIn("answerKey", prompt)
        self.assertNotIn("correct_answer", prompt)
        self.assertEqual(item["options"][item["answer_index"]], "gravity")

    def test_stable_random_choice_order_and_selection(self):
        rows = [case(i) for i in range(40)]
        a = choose_rows(rows, 12)
        b = choose_rows(list(reversed(rows)), 12)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 12)
        self.assertEqual(len({x["id"] for x in a}), 12)
        self.assertNotEqual(a[0]["id"], "ARC-fixture-0")

    def test_scoring_with_known_fixture_answers(self):
        rows = choose_rows([case(i) for i in range(16)], 8)
        good = evaluate_cases(rows, lambda x: x["answer_index"])
        self.assertEqual(good["accuracy"], 1.0)
        self.assertEqual(len(good["per_question_results"]), 8)
        self.assertEqual(good["chance_accuracy"], 0.25)
        wrong = evaluate_cases(rows, lambda x: (x["answer_index"]+1) % 4)
        self.assertEqual(wrong["accuracy"], 0.0)

    def test_invalid_input_rejected(self):
        with self.assertRaises(ValueError):
            choose_rows([case(0)], 12)
        with self.assertRaises(ValueError):
            choose_rows([case(i) for i in range(4)], 2)
        with self.assertRaises(ValueError):
            evaluate_cases([normalize(case(1))], lambda _: -1)
        self.assertIsNone(normalize({**case(2), "answerKey": "E"}))

if __name__ == "__main__":
    unittest.main()
