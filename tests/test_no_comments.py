import os
import re
import tokenize
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOUBLE_SLASH = re.compile(r"(?<!:)//")


def python_files():
    bases = [os.path.join(ROOT, "postsmith", "scripts"), os.path.join(ROOT, "tests")]
    for base in bases:
        for name in sorted(os.listdir(base)):
            if name.endswith(".py"):
                yield os.path.join(base, name)


def markup_files():
    return [os.path.join(ROOT, "postsmith", "assets", "gallery.html")]


class NoCommentsTest(unittest.TestCase):
    def test_python_has_no_comments(self):
        for path in python_files():
            with open(path, "rb") as handle:
                for token in tokenize.tokenize(handle.readline):
                    self.assertNotEqual(
                        token.type, tokenize.COMMENT, path + " contains a comment"
                    )

    def test_markup_has_no_comments(self):
        for path in markup_files():
            with open(path, "r", encoding="utf-8") as handle:
                for number, line in enumerate(handle, 1):
                    where = path + " line " + str(number)
                    self.assertNotIn("<!--", line, where)
                    self.assertNotIn("/*", line, where)
                    self.assertIsNone(DOUBLE_SLASH.search(line), where)


if __name__ == "__main__":
    unittest.main()
