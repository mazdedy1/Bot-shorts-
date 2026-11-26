import unittest

from editor.timeline import validate_plan

class TimelineValidationTests(unittest.TestCase):
    def make_plan(self, clips):
        return {"narration": "Narasi uji.", "clips": clips}

    def test_flexible_duration_is_not_forced_to_sixty_seconds(self):
        clips = [
            {"start": 0, "end": 20, "caption": "A"},
            {"start": 30, "end": 58, "caption": "B"},
        ]
        validated, narration = validate_plan(self.make_plan(clips), 100)
        self.assertEqual(narration, "Narasi uji.")
        self.assertEqual(sum(c.output_duration for c in validated), 48)

    def test_accepts_timeline_up_to_180_seconds(self):
        clips = [{"start": 0, "end": 180, "caption": "Full"}]
        validated, _ = validate_plan(self.make_plan(clips), 180)
        self.assertEqual(validated[0].output_duration, 180)

    def test_rejects_timeline_over_180_seconds(self):
        clips = [{"start": 0, "end": 170, "effect": "slow"}]
        with self.assertRaises(ValueError):
            validate_plan(self.make_plan(clips), 180)

    def test_rejects_clip_outside_source(self):
        clips = [{"start": 5, "end": 30, "caption": "Invalid"}]
        with self.assertRaises(ValueError):
            validate_plan(self.make_plan(clips), 20)

    def test_rejects_empty_narration(self):
        with self.assertRaises(ValueError):
            validate_plan({"narration": "", "clips": [{"start": 0, "end": 25}]}, 30)

if __name__ == "__main__":
    unittest.main()
