import unittest

from ai.director import _extract_json

class DirectorParserTests(unittest.TestCase):
    def test_parses_plain_json(self):
        self.assertEqual(_extract_json('{"ok": true}'), {"ok": True})

    def test_parses_json_code_fence(self):
        self.assertEqual(_extract_json('```json\n{"ok": true}\n```'), {"ok": True})

if __name__ == "__main__":
    unittest.main()
