# SPDX-License-Identifier: Apache-2.0
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from zh_engine import translate_js, tokenize  # noqa: E402
from zh_dict import EXACT, TEMPLATE_WORDS  # noqa: E402


def tr(src):
    out, _ = translate_js(src, EXACT, TEMPLATE_WORDS)
    return out


class EngineTest(unittest.TestCase):
    def test_string_literal(self):
        self.assertIn('"设置"', tr('el.child("Settings")'))

    def test_identifier_untouched(self):
        src = "const Settings = 1; Settings.open()"
        self.assertEqual(tr(src), src)

    def test_comment_untouched(self):
        src = '// "Settings"\nconst a = 1'
        self.assertEqual(tr(src), src)

    def test_template_word(self):
        out = tr("`${list.length} agents`")
        self.assertIn("个智能体", out)
        self.assertIn("${list.length}", out)

    def test_nested_template_keeps_backticks(self):
        src = '`Open worktree${r ? ` of ${r.name}` : ""}`'
        out = tr(src)
        self.assertNotIn("\\`", out)
        self.assertIn("`：${r.name}`", out)
        self.assertIn("打开 worktree", out)

    def test_regex_with_quotes(self):
        src = "path.replace(/['\u2018\u2019]/g, '')"
        self.assertEqual(tr(src), src)

    def test_tokenize_roundtrip(self):
        src = (
            'import {View} from "gpui-kit";\n'
            'const re = /[\'"]/g; // comment\n'
            'export default class A extends View {\n'
            '  render() { return div().child(`${n} agents`); }\n'
            '}\n'
        )
        self.assertEqual("".join(t.raw for t in tokenize(src)), src)


if __name__ == "__main__":
    unittest.main()
