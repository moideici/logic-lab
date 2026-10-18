import os
import unittest
from unittest import mock

from logic_arena import external


class ExternalEnvironmentTests(unittest.TestCase):
    def test_playwright_browser_path_defaults_to_the_project_browsers(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
            env = external.browser_environment()
        expected = external.ROOT.parents[1] / "work" / "browsers"
        if expected.is_dir():
            self.assertEqual(env["PLAYWRIGHT_BROWSERS_PATH"], str(expected))
        else:
            self.assertNotIn("PLAYWRIGHT_BROWSERS_PATH", env)

    def test_an_explicit_setting_is_respected(self):
        with mock.patch.dict(os.environ, {"PLAYWRIGHT_BROWSERS_PATH": "D:/autre"}):
            self.assertEqual(external.browser_environment()["PLAYWRIGHT_BROWSERS_PATH"], "D:/autre")

    def test_project_browser_folder_holds_the_chromium_revision_playwright_expects(self):
        browsers = external.ROOT.parents[1] / "work" / "browsers"
        if not browsers.is_dir():
            self.skipTest("navigateurs du projet absents")
        self.assertTrue(any(p.name.startswith("chromium_headless_shell-") for p in browsers.iterdir()))


if __name__ == "__main__":
    unittest.main()
