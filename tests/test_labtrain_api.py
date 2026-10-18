import time
import unittest

from logic_arena.lab import handle
from logic_arena.labtrain_api import Job


def wait(job, seconds=60):
    end = time.time() + seconds
    while time.time() < end:
        if job.status()["etat"] not in ("preparation", "en cours"):
            return job.status()
        time.sleep(0.1)
    raise AssertionError("l'entraînement ne se termine pas")


class LabTrainApiTests(unittest.TestCase):
    def test_fixed_run_finishes_and_is_summarised(self):
        job = Job()
        job.start("tictactoe", "fixe-4", steps=200, pause_ms=0)
        s = wait(job)
        self.assertEqual(s["etat"], "termine")
        self.assertEqual(s["resume"]["tailles"], [4, 4])
        self.assertEqual([p["step"] for p in s["historique"]], [100, 200])
        self.assertEqual(set(s["activations"]), {"encodeur", "coeur"})
        self.assertEqual(len(s["activations"]["encodeur"]), 4)
        self.assertEqual(len(s["comparaison"]), 1)
        self.assertTrue(0 <= s["resume"]["test_accord"] <= 1)

    def test_graine_reports_events_and_changes_size(self):
        job = Job()
        job.start("nim", "graine-C", steps=600, pause_ms=0)
        s = wait(job)
        self.assertEqual(s["etat"], "termine")
        self.assertTrue(any(e["type"] == "croissance" for e in s["evenements"]))
        self.assertGreater(s["resume"]["tailles"][0], 2)

    def test_invalid_requests_and_single_job_guard(self):
        job = Job()
        for game, mode, steps in (("go", "fixe-4", 300), ("nim", "magie", 300), ("nim", "fixe-1", 300), ("nim", "graine-Z", 300), ("nim", "fixe-8", 5)):
            with self.assertRaises(ValueError, msg=(game, mode, steps)):
                job.start(game, mode, steps=steps, pause_ms=0)
        job.start("tictactoe", "fixe-8", steps=1000, pause_ms=20)
        with self.assertRaises(ValueError):
            job.start("nim", "fixe-8", steps=300, pause_ms=0)
        job.stop()
        s = wait(job)
        self.assertEqual(s["etat"], "arrete")

    def test_http_layer_refuses_bad_input(self):
        status, payload = handle("POST", "/api/lab/train/start", {}, {"game": "go", "mode": "fixe-4"})
        self.assertEqual(status, 400)
        self.assertFalse(payload["ok"])
        status, payload = handle("GET", "/api/lab/train/status", {}, {})
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
