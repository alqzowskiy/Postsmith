import os
import sys
import unittest


SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "postsmith", "scripts"
)
sys.path.insert(0, SCRIPTS)

import textlayer


class TextLayerTest(unittest.TestCase):
    def test_available_returns_bool(self):
        self.assertIn(textlayer.available(), (True, False))

    def test_hex_to_rgb(self):
        self.assertEqual(textlayer.hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(textlayer.hex_to_rgb("000000"), (0, 0, 0))
        self.assertEqual(textlayer.hex_to_rgb("#E8743B"), (232, 116, 59))

    def test_resolve_color_palette_key(self):
        brand = {"palette": {"accent": "#E8743B", "surface": "#F4EFE6"}}
        self.assertEqual(textlayer.resolve_color("accent", brand, "white"), (232, 116, 59))

    def test_resolve_color_named_and_hex(self):
        self.assertEqual(textlayer.resolve_color("white", {}, "white"), (255, 255, 255))
        self.assertEqual(textlayer.resolve_color("#101010", {}, "white"), (16, 16, 16))

    def test_resolve_color_default(self):
        self.assertEqual(textlayer.resolve_color(None, {}, "white"), (255, 255, 255))

    def test_find_font_returns_path_or_none(self):
        result = textlayer.find_font(None, "Fraunces")
        self.assertTrue(result is None or os.path.exists(result))


if __name__ == "__main__":
    unittest.main()
