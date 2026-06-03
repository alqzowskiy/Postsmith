import os
import sys
import tempfile
import unittest


SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "postsmith", "scripts"
)
sys.path.insert(0, SCRIPTS)

import workspace


class WorkspaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_slugify(self):
        self.assertEqual(workspace.slugify("Launch Carousel!"), "launch-carousel")
        self.assertEqual(workspace.slugify("a  b"), "a-b")
        self.assertEqual(workspace.slugify(""), "job")
        self.assertEqual(workspace.slugify("***"), "job")

    def test_find_workspace_walks_up(self):
        nested = os.path.join(self.root, "a", "b", "c")
        os.makedirs(nested)
        self.assertIsNone(workspace.find_workspace(nested))
        target = os.path.join(self.root, ".postsmith")
        os.makedirs(target)
        found = workspace.find_workspace(nested)
        self.assertEqual(os.path.realpath(found), os.path.realpath(target))

    def test_resolve_creates(self):
        path = workspace.resolve_workspace(create=True, start=self.root)
        self.assertTrue(os.path.isdir(path))
        self.assertEqual(os.path.basename(path), ".postsmith")

    def test_init_scaffolds(self):
        ws = workspace.init_workspace(start=self.root)
        self.assertTrue(os.path.isfile(workspace.config_path(ws)))
        self.assertTrue(os.path.isfile(workspace.registry_path(ws)))
        self.assertTrue(os.path.isfile(workspace.brand_path(ws)))
        self.assertTrue(os.path.isdir(workspace.jobs_dir(ws)))
        self.assertTrue(os.path.isdir(workspace.exports_dir(ws)))
        self.assertTrue(os.path.isdir(workspace.fonts_dir(ws)))

    def test_init_does_not_clobber_brand(self):
        ws = workspace.init_workspace(start=self.root)
        with open(workspace.brand_path(ws), "w", encoding="utf-8") as handle:
            handle.write('{"brand_name": "Mine"}')
        workspace.init_workspace(start=self.root)
        with open(workspace.brand_path(ws), "r", encoding="utf-8") as handle:
            self.assertIn("Mine", handle.read())

    def test_job_id_collision(self):
        ws = workspace.init_workspace(start=self.root)
        first = workspace.make_job_id(ws, "Launch Carousel", "2026-06-02")
        self.assertEqual(first, "2026-06-02-launch-carousel")
        os.makedirs(workspace.job_dir(ws, first))
        second = workspace.make_job_id(ws, "Launch Carousel", "2026-06-02")
        self.assertEqual(second, "2026-06-02-launch-carousel-2")

    def test_config_merges_defaults(self):
        ws = workspace.init_workspace(start=self.root)
        workspace.write_json(workspace.config_path(ws), {"defaults": {"format": "1:1"}})
        config = workspace.load_config(ws)
        self.assertEqual(config["defaults"]["format"], "1:1")
        self.assertEqual(config["defaults"]["port"], 4848)
        self.assertEqual(config["version"], 1)

    def test_upsert_dedups_and_sorts(self):
        ws = workspace.init_workspace(start=self.root)
        workspace.upsert_job(ws, {"id": "a", "created": "2026-06-01T00:00:00Z", "cost": 1})
        workspace.upsert_job(ws, {"id": "b", "created": "2026-06-03T00:00:00Z", "cost": 2})
        workspace.upsert_job(ws, {"id": "a", "created": "2026-06-02T00:00:00Z", "cost": 3})
        jobs = workspace.load_registry(ws)["jobs"]
        self.assertEqual([job["id"] for job in jobs], ["b", "a"])
        self.assertEqual(jobs[1]["cost"], 3)

    def test_resolve_brand_path(self):
        ws = workspace.init_workspace(start=self.root)
        config = workspace.load_config(ws)
        brand = workspace.resolve_brand_path(ws, config)
        self.assertEqual(
            os.path.realpath(brand), os.path.realpath(workspace.brand_path(ws))
        )


if __name__ == "__main__":
    unittest.main()
