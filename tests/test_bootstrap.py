"""Bootstrap integrity checks; these do not exercise an application."""

import json
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]


class BootstrapIntegrityTests(unittest.TestCase):
    def test_local_markdown_links_resolve_inside_repository(self):
        documents = [ROOT / "README.md", ROOT / "AGENTS.md"]
        documents.extend((ROOT / "docs").rglob("*.md"))
        for document in documents:
            # shortcut: inline links only, adopt a Markdown parser if richer syntax is introduced.
            for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", document.read_text()):
                url = urlsplit(target)
                if url.scheme or url.netloc or not url.path:
                    continue
                with self.subTest(document=str(document.relative_to(ROOT)), target=target):
                    path = (document.parent / unquote(url.path)).resolve()
                    self.assertTrue(path.is_relative_to(ROOT), "link escapes repository")
                    self.assertTrue(path.exists(), "missing local link target")

    def test_source_inventory_is_pinned_and_unambiguous(self):
        inventory = json.loads((ROOT / "docs/engineering/sources.json").read_text())
        self.assertEqual(inventory["reviewed_on"], "2026-10-15")
        sources = inventory["sources"]
        expected = {
            "obra/superpowers", "deanpeters/Product-Manager-Skills",
            "julianoczkowski/product-manager", "RamyaLakshmiKS/agentic_software_team",
            "addyosmani/adk-product-engineers",
            "khileshwarpriya-design/AI-Product-Manager-Assistant",
            "vercel-labs/agent-skills", "anthropics/skills",
        }
        names = [source["repository"] for source in sources]
        self.assertEqual(len(names), len(set(names)), "duplicate source record")
        self.assertEqual(set(names), expected)
        for source in sources:
            with self.subTest(repository=source["repository"]):
                self.assertRegex(source["revision"], r"^[0-9a-f]{40}$")
                self.assertEqual(source["url"], "https://github.com/" + source["repository"])
                self.assertTrue(source["inspected_paths"])
                self.assertTrue(source["license_observation"])
                self.assertIn(source["decision"], {"reuse-installed", "defer", "reference-only"})
                self.assertFalse(source["executed"])
                self.assertFalse(source["vendored"])


if __name__ == "__main__":
    unittest.main()
