# SPDX-License-Identifier: Apache-2.0
"""Tests for the code-patch layer and the protected-span rule."""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from zh_engine import translate_js, ui_literals  # noqa: E402
from zh_dict import EXACT, TEMPLATE_WORDS  # noqa: E402
from zh_patches import PATCHES, PatchError, patch_source, patches_for  # noqa: E402

HELP = "mods/help/main.js"


def fixture(rel, kind="old", newline="\n"):
    """A stand-in file that contains every anchor for `rel`, in patch order."""
    return newline.join(p[kind].replace("\n", newline) for p in patches_for(rel))


class ProtectedSpanTest(unittest.TestCase):
    def test_block_inside_markers_is_untouched(self):
        src = (
            "/* zh:protect */\n"
            'const GROUPS = { Recent: "recent", Tab: "tab" };\n'
            "/* /zh:protect */\n"
            'el.child("Settings")\n'
        )
        out, n = translate_js(src, EXACT, TEMPLATE_WORDS)
        self.assertIn('Recent: "recent"', out)
        self.assertIn('Tab: "tab"', out)
        self.assertIn('"设置"', out)
        self.assertEqual(n, 1)

    def test_audit_skips_protected(self):
        src = '/* zh:protect */ const M = { Recent: "Recent" }; /* /zh:protect */'
        self.assertEqual(ui_literals(src), [])


class PatchTest(unittest.TestCase):
    def test_every_patch_targets_known_file(self):
        for p in PATCHES:
            self.assertIn("/", p["file"], p["file"])
            self.assertTrue(p["note"])
            self.assertNotEqual(p["old"], p["new"])

    def test_missing_anchor_raises(self):
        with self.assertRaises(PatchError):
            patch_source(HELP, "const nothing = 1;\n")

    def test_applies_all_patches(self):
        out, n = patch_source(HELP, fixture(HELP))
        self.assertEqual(n, len(patches_for(HELP)))
        self.assertIn("zh:protect", out)
        self.assertIn("切换到空间", out)

    def test_idempotent_when_already_applied(self):
        src = fixture(HELP, "new")
        out, n = patch_source(HELP, src)
        self.assertEqual(n, 0)
        self.assertEqual(out, src)

    def test_crlf_preserved(self):
        src = fixture(HELP, "old", "\r\n")
        self.assertNotIn("\n", src.replace("\r\n", ""))
        out, n = patch_source(HELP, src)
        self.assertEqual(n, len(patches_for(HELP)))
        # no bare LF left behind
        self.assertNotIn("\n", out.replace("\r\n", ""))

    def test_backslash_relative_path(self):
        self.assertTrue(patches_for("mods\\help\\main.js"))


if __name__ == "__main__":
    unittest.main()
