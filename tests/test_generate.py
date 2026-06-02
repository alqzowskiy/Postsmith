import os
import sys
import tempfile
import unittest


SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "postsmith", "scripts"
)
sys.path.insert(0, SCRIPTS)

import generate


class GenerateTest(unittest.TestCase):
    def test_per_image_cost(self):
        self.assertEqual(generate.per_image_cost("low", "1024x1024"), 0.006)
        self.assertEqual(generate.per_image_cost("low", "1024x1536"), 0.005)
        self.assertEqual(generate.per_image_cost("high", "1536x1024"), 0.165)
        self.assertEqual(generate.per_image_cost("medium", "1024x1024"), 0.053)

    def test_compose_branded(self):
        job = {"mode": "branded", "master": "LOOK"}
        slide = {"prompt": "subject"}
        self.assertEqual(generate.compose_prompt(job, slide), "LOOK\n\nsubject")

    def test_compose_raw_ignores_master(self):
        job = {"mode": "raw", "master": "LOOK"}
        slide = {"prompt": "subject"}
        self.assertEqual(generate.compose_prompt(job, slide), "subject")

    def test_compose_empty_master(self):
        job = {"mode": "branded", "master": "   "}
        slide = {"prompt": "subject"}
        self.assertEqual(generate.compose_prompt(job, slide), "subject")

    def test_find_empty_slides(self):
        job = {
            "slides": [
                {"id": "01", "prompt": "x"},
                {"id": "02", "prompt": "   "},
                {"id": "03"},
            ]
        }
        self.assertEqual(generate.find_empty_slides(job), ["02", "03"])

    def test_parse_env_file(self):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".env", delete=False, encoding="utf-8"
        )
        handle.write('# a comment line\nOPENAI_API_KEY="sk-xyz"\nFOO=bar\n\n')
        handle.close()
        values = generate.parse_env_file(handle.name)
        os.unlink(handle.name)
        self.assertEqual(values["OPENAI_API_KEY"], "sk-xyz")
        self.assertEqual(values["FOO"], "bar")
        self.assertEqual(len(values), 2)


if __name__ == "__main__":
    unittest.main()
