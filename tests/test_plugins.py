"""Tests for the Plugin System (linter + prompt plugins)."""

import unittest
import os
import tempfile
import yaml
from unittest.mock import patch, MagicMock


class TestPluginDiscovery(unittest.TestCase):
    """Tests for get_plugin_dir, get_linter_plugins, and get_prompt_plugins."""

    def setUp(self):
        """Create a temporary directory structure mimicking ~/.gitpr/."""
        self.tmp = tempfile.TemporaryDirectory()
        self.plugin_base = os.path.join(self.tmp.name, "plugins")
        self.linter_dir = os.path.join(self.plugin_base, "linter")
        self.prompt_dir = os.path.join(self.plugin_base, "prompts")
        os.makedirs(self.linter_dir, exist_ok=True)
        os.makedirs(self.prompt_dir, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    @patch('src.config.ENV_FILE')
    def test_get_plugin_dir_linter(self, mock_env_file):
        """get_plugin_dir('linter') returns the correct path."""
        mock_env_file.__fspath__ = lambda: os.path.join(self.tmp.name, ".env")
        # Patch os.path.dirname to return our tmp dir
        with patch('src.config.os.path.dirname', return_value=self.tmp.name):
            from src.config import get_plugin_dir
            result = get_plugin_dir("linter")
            self.assertTrue(result.endswith(os.path.join("plugins", "linter")))

    @patch('src.config.ENV_FILE')
    def test_get_plugin_dir_prompts(self, mock_env_file):
        """get_plugin_dir('prompts') returns the correct path."""
        mock_env_file.__fspath__ = lambda: os.path.join(self.tmp.name, ".env")
        with patch('src.config.os.path.dirname', return_value=self.tmp.name):
            from src.config import get_plugin_dir
            result = get_plugin_dir("prompts")
            self.assertTrue(result.endswith(os.path.join("plugins", "prompts")))

    @patch('src.config.get_plugin_dir')
    def test_get_linter_plugins_empty(self, mock_get_dir):
        """get_linter_plugins returns [] when directory is empty."""
        mock_get_dir.return_value = self.linter_dir
        from src.config import get_linter_plugins
        result = get_linter_plugins()
        self.assertEqual(result, [])

    @patch('src.config.get_plugin_dir')
    def test_get_linter_plugins_finds_yaml_files(self, mock_get_dir):
        """get_linter_plugins discovers .yml and .yaml files."""
        # Create some plugin files
        open(os.path.join(self.linter_dir, "security.yml"), "w").close()
        open(os.path.join(self.linter_dir, "no-debug.yaml"), "w").close()
        open(os.path.join(self.linter_dir, "README.md"), "w").close()  # should be ignored

        mock_get_dir.return_value = self.linter_dir
        from src.config import get_linter_plugins
        result = get_linter_plugins()
        self.assertEqual(len(result), 2)
        self.assertTrue(any("security.yml" in f for f in result))
        self.assertTrue(any("no-debug.yaml" in f for f in result))

    @patch('src.config.get_plugin_dir')
    def test_get_linter_plugins_nonexistent_dir(self, mock_get_dir):
        """get_linter_plugins returns [] when directory doesn't exist."""
        mock_get_dir.return_value = "/nonexistent/path"
        from src.config import get_linter_plugins
        result = get_linter_plugins()
        self.assertEqual(result, [])

    @patch('src.config.get_plugin_dir')
    def test_get_prompt_plugins_empty(self, mock_get_dir):
        """get_prompt_plugins returns [] when directory is empty."""
        mock_get_dir.return_value = self.prompt_dir
        from src.config import get_prompt_plugins
        result = get_prompt_plugins()
        self.assertEqual(result, [])

    @patch('src.config.get_plugin_dir')
    def test_get_prompt_plugins_finds_md_files(self, mock_get_dir):
        """get_prompt_plugins discovers .md files."""
        open(os.path.join(self.prompt_dir, "audit_security.md"), "w").close()
        open(os.path.join(self.prompt_dir, "generate_tests.md"), "w").close()
        open(os.path.join(self.prompt_dir, "notes.txt"), "w").close()  # should be ignored

        mock_get_dir.return_value = self.prompt_dir
        from src.config import get_prompt_plugins
        result = get_prompt_plugins()
        self.assertEqual(len(result), 2)
        self.assertTrue(any("audit_security.md" in f for f in result))
        self.assertTrue(any("generate_tests.md" in f for f in result))

    @patch('src.config.get_plugin_dir')
    def test_get_prompt_plugins_nonexistent_dir(self, mock_get_dir):
        """get_prompt_plugins returns [] when directory doesn't exist."""
        mock_get_dir.return_value = "/nonexistent/path"
        from src.config import get_prompt_plugins
        result = get_prompt_plugins()
        self.assertEqual(result, [])


class TestLoadLinterRulesWithPlugins(unittest.TestCase):
    """Tests for load_linter_rules() merging local + global rules."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.plugin_linter_dir = os.path.join(self.tmp.name, "plugins", "linter")
        os.makedirs(self.plugin_linter_dir, exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _create_yaml_file(self, path, rules):
        """Helper: write a YAML file with linter rules."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump({"rules": rules}, f)

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_load_local_only(self, mock_get_plugins, mock_resolve):
        """load_linter_rules loads local rules when no plugins exist."""
        local_path = os.path.join(self.tmp.name, "local_linter.yml")
        self._create_yaml_file(local_path, [
            {"name": "local-rule", "regex": "console\\.log", "severity": "error"}
        ])

        mock_resolve.return_value = local_path
        mock_get_plugins.return_value = []

        from src.config import load_linter_rules
        rules = load_linter_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "local-rule")

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_load_global_only(self, mock_get_plugins, mock_resolve):
        """load_linter_rules loads global rules when no local file exists."""
        # Local file doesn't exist
        mock_resolve.return_value = os.path.join(self.tmp.name, "nonexistent.yml")

        global_path = os.path.join(self.plugin_linter_dir, "security.yml")
        self._create_yaml_file(global_path, [
            {"name": "aws-key", "regex": "AKIA[0-9A-Z]{16}", "severity": "error"}
        ])
        mock_get_plugins.return_value = [global_path]

        from src.config import load_linter_rules
        rules = load_linter_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "aws-key")

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_merge_local_and_global(self, mock_get_plugins, mock_resolve):
        """load_linter_rules merges local + global rules into a single list."""
        local_path = os.path.join(self.tmp.name, "local_linter.yml")
        self._create_yaml_file(local_path, [
            {"name": "local-rule", "regex": "FIXME", "severity": "warning"}
        ])

        global_path = os.path.join(self.plugin_linter_dir, "security.yml")
        self._create_yaml_file(global_path, [
            {"name": "aws-key", "regex": "AKIA[0-9A-Z]{16}", "severity": "error"},
            {"name": "jwt-leak", "regex": "eyJ[A-Za-z0-9-_]+\\.[A-Za-z0-9-_]+\\.[A-Za-z0-9-_.+/=]+", "severity": "error"}
        ])

        mock_resolve.return_value = local_path
        mock_get_plugins.return_value = [global_path]

        from src.config import load_linter_rules
        rules = load_linter_rules()
        self.assertEqual(len(rules), 3)
        rule_names = [r["name"] for r in rules]
        self.assertIn("local-rule", rule_names)
        self.assertIn("aws-key", rule_names)
        self.assertIn("jwt-leak", rule_names)

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_no_rules_at_all(self, mock_get_plugins, mock_resolve):
        """load_linter_rules returns [] when neither local nor global rules exist."""
        mock_resolve.return_value = os.path.join(self.tmp.name, "nonexistent.yml")
        mock_get_plugins.return_value = []

        from src.config import load_linter_rules
        rules = load_linter_rules()
        self.assertEqual(rules, [])

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_malformed_global_plugin_is_skipped(self, mock_get_plugins, mock_resolve):
        """Malformed YAML in a global plugin is silently skipped (with warning)."""
        mock_resolve.return_value = os.path.join(self.tmp.name, "nonexistent.yml")

        bad_path = os.path.join(self.plugin_linter_dir, "broken.yml")
        with open(bad_path, "w", encoding="utf-8") as f:
            f.write("invalid: [yaml: broken: syntax\n")

        good_path = os.path.join(self.plugin_linter_dir, "ok.yml")
        self._create_yaml_file(good_path, [
            {"name": "good-rule", "regex": "test", "severity": "info"}
        ])

        mock_get_plugins.return_value = [bad_path, good_path]

        from src.config import load_linter_rules
        rules = load_linter_rules()
        # Should have only the good rule; broken plugin is skipped
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "good-rule")

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_multiple_global_plugins(self, mock_get_plugins, mock_resolve):
        """Multiple global plugins are all loaded."""
        mock_resolve.return_value = os.path.join(self.tmp.name, "nonexistent.yml")

        paths = []
        for i, name in enumerate(["security", "no-debug", "php-psr"]):
            p = os.path.join(self.plugin_linter_dir, f"{name}.yml")
            self._create_yaml_file(p, [{"name": f"rule-{i}", "regex": f"pattern{i}", "severity": "error"}])
            paths.append(p)

        mock_get_plugins.return_value = paths

        from src.config import load_linter_rules
        rules = load_linter_rules()
        self.assertEqual(len(rules), 3)

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_local_yaml_error_returns_empty(self, mock_get_plugins, mock_resolve):
        """Syntax error in local YAML returns [] without crashing."""
        local_path = os.path.join(self.tmp.name, "local_linter.yml")
        with open(local_path, "w", encoding="utf-8") as f:
            f.write("invalid: [yaml: broken\n")

        mock_resolve.return_value = local_path
        mock_get_plugins.return_value = []

        from src.config import load_linter_rules
        rules = load_linter_rules()
        self.assertEqual(rules, [])

    @patch('src.config.resolve_skill_path')
    @patch('src.config.get_linter_plugins')
    def test_local_file_exists_but_no_rules_key(self, mock_get_plugins, mock_resolve):
        """Local YAML without 'rules' key returns [] for local, but global still loads."""
        local_path = os.path.join(self.tmp.name, "local_linter.yml")
        with open(local_path, "w", encoding="utf-8") as f:
            yaml.dump({"title": "no rules here"}, f)

        global_path = os.path.join(self.plugin_linter_dir, "security.yml")
        self._create_yaml_file(global_path, [
            {"name": "global-rule", "regex": "test", "severity": "warning"}
        ])

        mock_resolve.return_value = local_path
        mock_get_plugins.return_value = [global_path]

        from src.config import load_linter_rules
        rules = load_linter_rules()
        # Only the global rule should be loaded
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["name"], "global-rule")


class TestPluginSystemIntegration(unittest.TestCase):
    """Integration-style tests for the plugin infrastructure."""

    @patch('src.config.os.path.dirname')
    def test_setup_environment_creates_plugin_dirs(self, mock_dirname):
        """setup_environment ensures plugin directories exist."""
        import tempfile
        tmp = tempfile.TemporaryDirectory()
        mock_dirname.return_value = tmp.name

        from src.config import setup_environment
        try:
            setup_environment()
        except Exception:
            pass  # setup_environment does other things that may need mocking

        linter_dir = os.path.join(tmp.name, "plugins", "linter")
        prompt_dir = os.path.join(tmp.name, "plugins", "prompts")
        self.assertTrue(os.path.exists(linter_dir), f"Expected {linter_dir} to exist")
        self.assertTrue(os.path.exists(prompt_dir), f"Expected {prompt_dir} to exist")
        tmp.cleanup()


if __name__ == '__main__':
    unittest.main()
