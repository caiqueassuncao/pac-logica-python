import random
import unittest
from paclogica.logic import signature, formula_str
from paclogica.questions import (RULES, ARGUMENTS, PATTERNS, GENERATORS, TOPIC_NAMES,
                                 make_question, make_value_question)
from paclogica.database import DEFAULT_LEVELS

class QuestionsTest(unittest.TestCase):
    def test_every_topic_generates_valid_questions(self):
        random.seed(1)
        for topic in GENERATORS:
            for _ in range(60):
                q = make_question((topic,))
                self.assertIn(q["answer"], range(len(q["options"])))
                self.assertEqual(len(set(q["options"])), len(q["options"]), q["options"])
                self.assertTrue(q["prompt"] and q["lines"] and q["explanation"])

    def test_rules_have_three_alternatives(self):
        for rule in RULES:
            self.assertEqual(1 + len(rule[3]), 3, rule[1])

    def test_value_question_has_exactly_one_answer(self):
        random.seed(2)
        for _ in range(100):
            q = make_value_question()
            row = q["table"][1][0][2:]
            wanted = "verdadeira" in q["prompt"]
            self.assertEqual(row.count(wanted), 1)
            self.assertEqual(row.index(wanted), q["answer"])

    def test_sentence_distractors_are_not_equivalent(self):
        for template, correct, wrong, _ in PATTERNS:
            sigs = [signature(f, ["p", "q"]) for f in [correct] + wrong]
            for w, sig in zip(wrong, sigs[1:]):
                self.assertNotEqual(sig, sigs[0], f"{template}: {formula_str(w, True)}")

    def test_arguments_have_both_answers(self):
        self.assertTrue(any(a[3] for a in ARGUMENTS))
        self.assertTrue(any(not a[3] for a in ARGUMENTS))

    def test_levels_use_known_topics(self):
        for level in DEFAULT_LEVELS:
            for topic in level[6].split(","):
                self.assertIn(topic, TOPIC_NAMES)

if __name__ == "__main__":
    unittest.main()
