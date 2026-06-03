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
        slides = [
            {"id": "01", "prompt": "x"},
            {"id": "02", "prompt": "   "},
            {"id": "03"},
        ]
        self.assertEqual(generate.find_empty_slides(slides), ["02", "03"])

    def test_compose_with_style(self):
        job = {"mode": "branded", "style": "anime", "master": "LOOK"}
        slide = {"prompt": "subject"}
        out = generate.compose_prompt(job, slide)
        self.assertTrue(out.startswith("Overall visual style: anime."))
        self.assertIn("LOOK", out)
        self.assertIn("subject", out)

    def test_compose_overlay_clears_space(self):
        job = {"mode": "branded", "master": "LOOK", "text_mode": "overlay"}
        slide = {"prompt": "scene", "caption": {"position": "bottom-left"}}
        out = generate.compose_prompt(job, slide)
        self.assertIn("Leave the bottom-left area", out)

    def test_compose_raw_ignores_style_and_overlay(self):
        job = {"mode": "raw", "style": "anime", "text_mode": "overlay"}
        slide = {"prompt": "subject", "caption": {"position": "top-left"}}
        self.assertEqual(generate.compose_prompt(job, slide), "subject")

    def test_select_slides(self):
        job = {"slides": [{"id": "01"}, {"id": "02"}, {"id": "03"}]}
        self.assertEqual(len(generate.select_slides(job, None)), 3)
        chosen = generate.select_slides(job, "03,01")
        self.assertEqual([slide["id"] for slide in chosen], ["03", "01"])

    def test_select_slides_unknown_id_exits(self):
        job = {"slides": [{"id": "01"}]}
        with self.assertRaises(SystemExit):
            generate.select_slides(job, "09")

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
