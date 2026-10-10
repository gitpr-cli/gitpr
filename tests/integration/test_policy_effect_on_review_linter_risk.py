"""A policy pack, end to end, on a real repository.

The unit tests pin what the resolver composes; this file pins what the rest of
GitPR *does* with what it composed. A pack that composes correctly and changes
nothing would pass every test under ``tests/domain/policy`` and be worthless, so
the assertions here are about effects: the review's system instruction carries
the pack's text, the linter obeys the pack's rules and its severity override, the
risk score rises for a path the pack declared critical, and — the one that
matters most — a review cached *before* the pack was activated is not reused
*after* it.

That last one is why the prompt cache is real here rather than stubbed. The
skill context travels in ``instrucao_sistema``, a separate argument the MD5 never
sees, so without the policy in the cache key a run after ``gitpr policy use``
would answer from the previous run's cache while the output claimed the new
policy. Stubbing the cache would hide exactly the bug this file exists to catch.

§12.10 — "no pack, nothing changes" — is the first class here rather than a line
in the middle, because it is the property that lets the feature ship at all.

The repository, the git history and the pack directories are real; only the two
edges that leave the machine (the AI call and the ledger write) are stubbed, and
the two directories the code would write to outside the fixture
(``~/.gitpr/policies`` and the prompt cache) are redirected.
"""

import contextlib
import os
import shutil
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from src.application.use_cases.activate_policy_pack import activate_policy_pack
from src.application.use_cases.calculate_risk import execute_calculate_risk
from src.application.use_cases.resolve_effective_policy import resolve_effective_policy
from src.config import load_linter_rules
from src.core import generate_pr_content, get_skill_context
from src.domain.policy import get_active_policy, set_active_policy
from src.domain.policy.policy_resolver import risk_config_from_policy
from src.domain.risk.risk_rules import RiskSignal, is_test_file, load_risk_config
from src.infrastructure.policy import local_policy_repository
from src.linter_engine import parse_diff_and_lint
from src.review.diff_source import DiffOrigin, DiffSource
from tests.fix.git_fixture import GitRepoTestCase

PACK_NAME = "acme/team-policy"

MANIFEST = """schema_version: 1
name: acme/team-policy
version: 1.0.0
min_gitpr_version: ">=1.3.0"
license: MIT

skills:
  review:
    additional_context: |
      Acme house rule: money is an integer in minor units.

linter:
  rules_file: linter.yml
  severity_overrides:
    - rule_name: acme-no-float-money
      level: warning
      reason: the float check is advisory while the migration is in flight

risk:
  critical_paths:
    - app/Services/**
  test_patterns:
    - spec/**
"""

PACK_RULES = """rules:
  - name: acme-no-float-money
    regex: "float"
    message: "Money is an integer in minor units, not a float."
    extensions: ["*"]
"""

# The repository's own linter file. Deliberately redefines the pack's rule under
# the same name, which is what makes the layering observable.
PROJECT_RULES = """rules:
  - name: acme-no-float-money
    regex: "float"
    message: "PROJECT RULE: money is stored in minor units."
    extensions: ["*"]
"""

FLOAT_LINE = "$price = (float) $request->input('price');"

SERVICE_BEFORE = """<?php

class PricingService
{
    public function total(): int
    {
        return 0;
    }
}
"""

SERVICE_AFTER = """<?php

class PricingService
{
    public function total(): int
    {
        return 100;
    }
}
"""


class PolicyIntegrationTestCase(GitRepoTestCase):
    """A repository, a pack store and a prompt cache, all under ``tempfile``.

    ``setUp`` also moves the process into the repository, because the skill file
    and the project linter file are resolved against the current directory rather
    than against a path argument — and moves it back before the tree is removed,
    since Windows will not delete a directory that is somebody's cwd.
    """

    prefix = "gitpr_policy_integration_"

    def setUp(self):
        super().setUp()
        self._cwd = os.getcwd()
        os.chdir(self.dir)
        self.addCleanup(os.chdir, self._cwd)

        self.root = tempfile.mkdtemp(prefix="gitpr_policy_store_")
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.store = os.path.join(self.root, "policies")
        self.cache_dir = os.path.join(self.root, "cache")

        for attribute, value in (
            ("installed_policies_dir", self.store),
            ("gitpr_home", self.root),
        ):
            patcher = patch.object(
                local_policy_repository, attribute, return_value=value
            )
            patcher.start()
            self.addCleanup(patcher.stop)

        cache_patcher = patch("src.cache.get_cache_base_dir", return_value=Path(self.cache_dir))
        cache_patcher.start()
        self.addCleanup(cache_patcher.stop)

        set_active_policy(None)
        self.addCleanup(set_active_policy, None)

        # Counted on the test case, not inside the stub: the stub is entered and
        # left once per review, and what these tests measure is how many reviews
        # reached the model *across* runs.
        self.ai_calls = 0

    # ── fixtures ─────────────────────────────────────────────────────────
    def write_file(self, name, content):
        self.write(name, content)
        return os.path.join(self.dir, name.replace("/", os.sep))

    def install_pack(self, name=PACK_NAME, manifest=MANIFEST, rules=PACK_RULES):
        """A pack in the redirected store, as ``policy install`` would leave it."""
        directory = os.path.join(self.store, local_policy_repository.install_dir_name(name))
        self.write_file(os.path.join(directory, "policy.yml"), manifest)
        if rules is not None:
            self.write_file(os.path.join(directory, "linter.yml"), rules)
        return directory

    def activate(self, reference=PACK_NAME):
        """Activate and resolve, in the order the CLI does over two runs."""
        activate_policy_pack(reference, self.dir)
        return resolve_effective_policy(self.dir)

    def deactivate(self):
        set_active_policy(None)

    def diff(self, *pathspec):
        """The working tree's diff against HEAD."""
        return self._git("diff", "HEAD", *pathspec).stdout

    @contextlib.contextmanager
    def stubbed_review(self):
        """The AI edges stubbed and the ledger silenced; everything else real.

        ``instrucao_sistema`` is captured because it is where the skill context —
        and therefore the pack — travels. The prompt is captured separately
        because the *cache key* is built from it, so the two answer different
        questions: what the model was told, and what the cache was keyed on.
        """
        sent = {}

        def fake_call(provider, api_key, model, prompt, system_instruction, action=None):
            self.ai_calls += 1
            sent["system_instruction"] = system_instruction
            sent["prompt"] = prompt
            sent["calls"] = self.ai_calls
            return {"review": f"stubbed review #{self.ai_calls}"}

        with contextlib.ExitStack() as stack:
            stack.enter_context(patch("src.core.call_ai_model", side_effect=fake_call))
            stack.enter_context(patch("src.core.get_api_key", return_value="key"))
            stack.enter_context(
                patch("src.core.get_api_model", return_value="stub-model")
            )
            stack.enter_context(patch("src.metrics.log_command_metric"))
            stack.enter_context(patch("src.metrics.log_local_metric"))
            stack.enter_context(patch("src.linter_engine.log_local_metric"))
            yield sent

    def run_review(self, diff):
        """``(result, sent)`` for one review run with the AI stubbed."""
        with self.stubbed_review() as sent:
            result = generate_pr_content("review", "review", diff)
        return result, sent


class TestWithoutAPackNothingChanges(PolicyIntegrationTestCase):
    """§12.10 — the property the whole feature rests on.

    Each of these runs the same code the feature changed and asserts it behaves
    as it did *before* the feature existed. They are the reason a repository that
    never writes a lockfile can upgrade GitPR without reading the release notes.
    """

    def setUp(self):
        super().setUp()
        # The review prompt also carries a risk section by default, which runs
        # real git history analysis. Off here: this class is about what the pack
        # does or does not add, and the risk path has its own tests below.
        env = patch.dict(os.environ, {"GITPR_RISK_INCLUDE_IN_REVIEW": "false"})
        env.start()
        self.addCleanup(env.stop)

    def test_the_policy_is_inactive_and_has_no_cache_scope(self):
        policy = resolve_effective_policy(self.dir)

        self.assertFalse(policy.is_active)
        self.assertEqual(policy.cache_scope(), "")
        self.assertEqual(policy.policy_tag(), "")

    def test_the_skill_context_is_exactly_the_repository_file(self):
        self.write_file(".gitpr/skill/.gitpr.review.md", "REPOSITORY REVIEW RULES\n")

        context = get_skill_context("review", quiet=True)

        self.assertEqual(context, "REPOSITORY REVIEW RULES\n")

    def test_a_repository_with_no_skill_file_and_no_pack_has_no_context(self):
        self.assertFalse(get_skill_context("review", quiet=True))

    def test_the_linter_catalogue_is_identical_with_and_without_a_policy(self):
        self.write_file(".gitpr/skill/.gitpr.linter.yml", PROJECT_RULES)
        resolve_effective_policy(self.dir)

        without = load_linter_rules()
        with_empty_policy = load_linter_rules(get_active_policy())

        self.assertEqual([rule["name"] for rule in with_empty_policy],
                         [rule["name"] for rule in without])
        self.assertEqual(with_empty_policy, without)

    def test_the_risk_config_is_the_very_object_the_project_configured(self):
        resolve_effective_policy(self.dir)
        base = load_risk_config()

        self.assertIs(risk_config_from_policy(get_active_policy(), base), base)

    def test_the_risk_score_is_unchanged(self):
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()
        source = DiffSource(origin=DiffOrigin.LOCAL, content=diff, identifier="head")
        resolve_effective_policy(self.dir)

        computed = execute_calculate_risk(source, repo_path=self.dir)
        explicit = execute_calculate_risk(
            source, repo_path=self.dir, config=load_risk_config()
        )

        self.assertEqual(computed.score, explicit.score)
        self.assertEqual(computed.level, explicit.level)

    def test_an_unchanged_review_is_served_from_the_cache(self):
        """The cache key is the prompt alone — no policy suffix was added."""
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()

        self.run_review(diff)
        self.assertEqual(self.ai_calls, 1)

        _, sent_second = self.run_review(diff)

        self.assertEqual(self.ai_calls, 1, "the second run must not re-ask")
        self.assertNotIn("calls", sent_second, "the cache answered, so the model was not asked")


class TestThePackChangesTheRun(PolicyIntegrationTestCase):
    """§12.11 — the same runs, with a pack active, and only where it declared."""

    def setUp(self):
        super().setUp()
        env = patch.dict(os.environ, {"GITPR_RISK_INCLUDE_IN_REVIEW": "false"})
        env.start()
        self.addCleanup(env.stop)
        self.install_pack()

    # ── skills ───────────────────────────────────────────────────────────
    def test_the_review_system_instruction_carries_the_pack(self):
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()
        self.activate()

        _, sent = self.run_review(diff)

        self.assertIn("Acme house rule", sent["system_instruction"])
        # The origin travels with the text, so a prompt carrying three packs'
        # worth of rules can still be attributed.
        self.assertIn(f"[policy: {PACK_NAME}@1.0.0]", sent["system_instruction"])
        self.assertIn(f"[/policy: {PACK_NAME}@1.0.0]", sent["system_instruction"])

    def test_the_pack_context_is_appended_after_the_repository_skill(self):
        self.write_file(".gitpr/skill/.gitpr.review.md", "REPOSITORY REVIEW RULES\n")
        self.activate()

        context = get_skill_context("review", quiet=True)

        self.assertTrue(context.startswith("REPOSITORY REVIEW RULES"))
        self.assertIn("Acme house rule", context)

    def test_the_pack_context_reaches_the_prompt_with_no_skill_file(self):
        self.activate()

        self.assertIn("Acme house rule", get_skill_context("review", quiet=True))

    # ── the cache ────────────────────────────────────────────────────────
    def test_a_review_cached_before_activation_is_not_reused_after_it(self):
        """The proof the feature is not merely decorative.

        Same diff, same process, same prompt — the only thing that changed is
        that a pack became active. Without the policy in the cache key this
        returns the first answer verbatim and the review reads as if the pack
        had never been activated.
        """
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()

        _, before = self.run_review(diff)
        self.assertEqual(self.ai_calls, 1)
        self.assertNotIn("Acme house rule", before["system_instruction"])

        self.activate()
        result, after = self.run_review(diff)

        self.assertEqual(self.ai_calls, 2, "the pack must invalidate the cache")
        self.assertEqual(result["review"], "stubbed review #2")
        self.assertIn("Acme house rule", after["system_instruction"])

    def test_two_runs_under_the_same_pack_share_one_cache_entry(self):
        """The invalidation is a change of key, not of policy on every run."""
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()
        self.activate()

        self.run_review(diff)
        self.run_review(diff)

        self.assertEqual(self.ai_calls, 1)

    def test_reactivating_the_same_pack_keeps_the_cache_valid(self):
        """The scope is the checksum, not a timestamp: nothing changed, nothing moves."""
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()
        self.activate()
        self.run_review(diff)

        self.activate()
        self.run_review(diff)

        self.assertEqual(self.ai_calls, 1)

    # ── linter ───────────────────────────────────────────────────────────
    def test_the_linter_applies_the_pack_rules(self):
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file(
            "app/Services/Pricing.php", SERVICE_AFTER + f"\n{FLOAT_LINE}\n"
        )
        diff = self.diff()
        self.activate()

        alerts = parse_diff_and_lint(diff, skip_external=True)

        self.assertTrue(
            any("minor units" in message for message in alerts["warnings"]),
            alerts,
        )

    def test_the_pack_severity_override_decides_which_list_the_alert_lands_in(self):
        """The pack ships the rule as a *downgrade*, with its reason attached."""
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file(
            "app/Services/Pricing.php", SERVICE_AFTER + f"\n{FLOAT_LINE}\n"
        )
        diff = self.diff()

        without = parse_diff_and_lint(diff, skip_external=True)
        self.activate()
        with_pack = parse_diff_and_lint(diff, skip_external=True)

        self.assertEqual(without["warnings"], [])
        self.assertEqual(with_pack["errors"], [])
        self.assertEqual(len(with_pack["warnings"]), 1)

    def test_a_project_rule_redefines_the_pack_rule_of_the_same_name(self):
        """Layering: the repository speaks about itself, last.

        The rule *body* comes from the project. The *severity* still comes from
        the pack, and deliberately so — the overrides are applied to the final
        catalogue, because an override that could be silently redefined away by
        the repository it was meant to govern would not be a policy.
        """
        self.write_file(".gitpr/skill/.gitpr.linter.yml", PROJECT_RULES)
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file(
            "app/Services/Pricing.php", SERVICE_AFTER + f"\n{FLOAT_LINE}\n"
        )
        diff = self.diff()
        self.activate()

        alerts = parse_diff_and_lint(diff, skip_external=True)

        self.assertEqual(alerts["errors"], [])
        self.assertTrue(any("PROJECT RULE" in m for m in alerts["warnings"]), alerts)
        self.assertFalse(any("minor units, not a float" in m for m in alerts["warnings"]))

    def test_a_linter_with_no_pack_sees_none_of_the_pack_rules(self):
        """The other half of the layering claim, on the same diff."""
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file(
            "app/Services/Pricing.php", SERVICE_AFTER + f"\n{FLOAT_LINE}\n"
        )
        diff = self.diff()
        resolve_effective_policy(self.dir)

        alerts = parse_diff_and_lint(diff, skip_external=True)

        self.assertEqual(alerts, {"errors": [], "warnings": []})

    # ── risk ─────────────────────────────────────────────────────────────
    def test_a_pack_critical_path_raises_the_score(self):
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        diff = self.diff()
        source = DiffSource(origin=DiffOrigin.LOCAL, content=diff, identifier="head")

        before = execute_calculate_risk(source, repo_path=self.dir)
        self.activate()
        after = execute_calculate_risk(source, repo_path=self.dir)

        signals = [
            evidence.signal
            for file_risk in after.files
            for evidence in file_risk.evidence
        ]
        self.assertNotIn(RiskSignal.CRITICAL_PATH, [e.signal for f in before.files for e in f.evidence])
        self.assertIn(RiskSignal.CRITICAL_PATH, signals)
        self.assertGreater(after.score, before.score)

    def test_the_pack_test_patterns_teach_the_matcher_a_layout_it_did_not_know(self):
        """``spec/`` mirrors ``app/`` — a layout no naming convention can guess."""
        self.activate()
        config = risk_config_from_policy(get_active_policy(), load_risk_config())

        self.assertFalse(is_test_file("spec/Pricing.php"))
        self.assertTrue(is_test_file("spec/Pricing.php", config.test_patterns))

    def test_a_change_under_the_pack_test_patterns_counts_as_the_test_change(self):
        """The pattern is not decoration: it moves the score the way a test does.

        Two things have to line up, and the pack supplies both halves: the file
        under ``spec/`` has to *be* a test file (the pack's ``test_patterns``),
        and it has to correspond to the production file that changed (the name,
        which mirrors ``app/Services/Pricing.php``).
        """
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)
        self.write_file("spec/Pricing.php", "<?php\n// spec\n")
        # A file git does not know about is invisible to ``git diff HEAD``.
        self._git("add", "-N", "--", "spec/Pricing.php")
        diff = self.diff()
        source = DiffSource(origin=DiffOrigin.LOCAL, content=diff, identifier="head")

        before = execute_calculate_risk(source, repo_path=self.dir)
        self.activate()
        after = execute_calculate_risk(source, repo_path=self.dir)

        def signals(risk):
            return [
                evidence.signal for file_risk in risk.files for evidence in file_risk.evidence
            ]

        self.assertNotIn(RiskSignal.TEST_PRESENT, signals(before))
        self.assertIn(RiskSignal.TEST_PRESENT, signals(after))

    def test_the_built_in_risk_protection_survives_the_pack(self):
        """A pack adds somewhere to be careful; it never removes a built-in."""
        self.activate()

        config = risk_config_from_policy(get_active_policy(), load_risk_config())
        patterns = config.critical_patterns[RiskSignal.CRITICAL_PATH]

        self.assertIn("app/Services/**", patterns)
        self.assertIn("**/payment/**", patterns)
        self.assertIn("**/middleware/**", patterns)

    def test_the_project_risk_file_still_wins_where_it_speaks(self):
        self.write_file(
            ".gitpr/skill/gitpr.risk.yml",
            "risk:\n  weights:\n    critical_path: 60\n",
        )
        self.activate()

        config = risk_config_from_policy(get_active_policy(), load_risk_config())

        self.assertEqual(config.weights[RiskSignal.CRITICAL_PATH], 60.0)


class TestTheBundledLaravelPack(PolicyIntegrationTestCase):
    """§12.11 and the feature's own definition of done, on the shipped pack.

    The synthetic pack above isolates one behaviour at a time; this one is the
    real artefact a team would activate, complete with a dependency, so it also
    answers "can this be reproduced on another machine from versioned files" —
    which is what the lockfile is for.
    """

    def setUp(self):
        super().setUp()
        self.commit("app/Http/Controllers/PricingController.php", SERVICE_BEFORE,
                    message="chore: seed")

    def activate_laravel(self):
        activate_policy_pack("gitpr/laravel-quality", self.dir)
        return resolve_effective_policy(self.dir)

    def test_the_lockfile_is_reproducible_elsewhere(self):
        self.activate_laravel()

        with open(
            os.path.join(self.dir, ".gitpr", "policy.lock.yml"),
            "r",
            encoding="utf-8",
            errors="replace",
        ) as handle:
            data = yaml.safe_load(handle)

        self.assertEqual(data["root"]["name"], "gitpr/laravel-quality")
        self.assertEqual(data["root"]["version"], "1.0.0")
        # Nothing machine-specific: a bundled pack is addressed by name, so the
        # teammate who clones the repository resolves it from their own wheel.
        self.assertNotIn("path", data["root"])
        self.assertNotIn(self.dir, str(data))
        self.assertEqual(
            [p["name"] for p in data["packs"]],
            ["gitpr/php-security", "gitpr/laravel-quality"],
        )

    def test_the_dependency_contributes_to_the_review_context(self):
        policy = self.activate_laravel()
        context = policy.skill_context_for("review")

        self.assertIn("This is a Laravel application", context)
        self.assertIn("Judge every change against these", context)
        self.assertIn("[policy: gitpr/php-security@1.0.0]", context)

    def test_activating_the_pack_changes_only_what_it_declares(self):
        """Everything the pack declares arrives; everything else stays put."""
        self.write_file(".gitpr/skill/.gitpr.linter.yml", PROJECT_RULES)
        before_rules = load_linter_rules()
        before_risk = load_risk_config()

        self.activate_laravel()

        after_rules = load_linter_rules(get_active_policy())
        after_risk = risk_config_from_policy(get_active_policy(), load_risk_config())

        # Declared: the packs' rules, on top of the repository's own.
        names = [rule["name"] for rule in after_rules]
        self.assertIn("acme-no-float-money", names)
        for rule in before_rules:
            self.assertIn(rule["name"], names)

        # Declared: critical paths, test patterns and weights.
        critical = after_risk.critical_patterns[RiskSignal.CRITICAL_PATH]
        self.assertIn("app/Http/Controllers/**", critical)
        self.assertIn("**/payment/**", critical)

        # Undeclared: thresholds are the pack's business only when it says so.
        self.assertEqual(after_risk.thresholds, before_risk.thresholds)

    def test_only_the_paths_the_pack_names_become_critical(self):
        self.activate_laravel()

        self.assertIn(RiskSignal.CRITICAL_PATH, self._signals("app/Http/Controllers/PricingController.php"))
        # A path the pack does not name, that no built-in pattern covers either:
        # activating a pack may not turn the whole repository into a critical path.
        self.assertNotIn(RiskSignal.CRITICAL_PATH, self._signals("app/Support/Helper.php"))

    def _signals(self, name):
        """Every risk signal the diff's change to *name* raises, with the pack on.

        ``git add -N`` so a path that is new to the repository shows up in
        ``git diff HEAD`` at all — an untracked file is invisible to a diff, and
        the test would then be scoring the previous call's file. The path is
        passed as a pathspec so the two calls in one test cannot see each other's
        change.
        """
        self.write_file(name, SERVICE_AFTER)
        self._git("add", "-N", "--", name)
        risk = execute_calculate_risk(
            DiffSource(
                origin=DiffOrigin.LOCAL,
                content=self.diff("--", name),
                identifier="head",
            ),
            repo_path=self.dir,
        )
        return [
            evidence.signal for file_risk in risk.files for evidence in file_risk.evidence
        ]

    def test_the_pack_is_refused_when_it_is_not_on_disk(self):
        """The lockfile is a promise; a missing pack has to break it loudly."""
        from src.domain.policy import PolicyError

        with self.assertRaises(PolicyError):
            activate_policy_pack("gitpr/does-not-exist", self.dir)


class TestSanityOfTheFixtureItself(PolicyIntegrationTestCase):
    """The fixture's own claims, so a failure above can be read correctly.

    If the harness quietly stopped stubbing, every assertion in this file would
    still pass — against the developer's real API key. These three check the
    harness instead of the feature.
    """

    def test_the_network_guard_is_installed(self):
        with self.assertRaises(AssertionError):
            socket.create_connection(("example.com", 80))

    def test_a_non_loopback_socket_is_refused(self):
        with self.assertRaises(AssertionError):
            socket.socket().connect(("93.184.216.34", 80))

    def test_the_review_stub_is_what_answers(self):
        self.commit("app/Services/Pricing.php", SERVICE_BEFORE, message="chore: seed")
        self.write_file("app/Services/Pricing.php", SERVICE_AFTER)

        result, _ = self.run_review(self.diff())

        self.assertEqual(self.ai_calls, 1)
        self.assertEqual(result["review"], "stubbed review #1")

    def test_the_prompt_cache_is_redirected_out_of_the_home_directory(self):
        from src.cache import get_cache_base_dir

        self.assertEqual(get_cache_base_dir(), Path(self.cache_dir))
        self.assertNotEqual(
            get_cache_base_dir(), Path.home() / ".gitpr" / "cache" / "prompts"
        )


if __name__ == "__main__":
    unittest.main()
