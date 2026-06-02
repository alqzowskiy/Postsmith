import os
import sys
import tempfile
import unittest
import zipfile


SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "postsmith", "scripts"
)
sys.path.insert(0, SCRIPTS)

import export


class ExportTest(unittest.TestCase):
    def test_zip_tree_arcnames(self):
        with tempfile.TemporaryDirectory() as root:
            job = os.path.join(root, "jobs", "2026-06-02-x")
            os.makedirs(job)
            with open(os.path.join(job, "01.png"), "wb") as handle:
                handle.write(b"png-bytes")
            with open(os.path.join(job, "job.json"), "w", encoding="utf-8") as handle:
                handle.write("{}")
            zip_path = os.path.join(root, "exports", "x.zip")
            export.zip_tree(job, zip_path, os.path.join(root, "jobs"))
            self.assertTrue(os.path.isfile(zip_path))
            with zipfile.ZipFile(zip_path) as archive:
                names = set(archive.namelist())
            self.assertIn(os.path.join("2026-06-02-x", "01.png"), names)
            self.assertIn(os.path.join("2026-06-02-x", "job.json"), names)


if __name__ == "__main__":
    unittest.main()
