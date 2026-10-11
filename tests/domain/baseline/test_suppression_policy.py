"""Suppressions are decisions, and every one of them has to be auditable.

Three rules make the feature reviewable, and they are what this file pins: no
scope without a reason, no accepted debt without an owner, and the most specific
statement wins over the broader one. The fourth is about provenance — a Policy
Pack's opinion is applied but never written into the repository's own file, so
its reason always arrives tagged with the pack it came from.
"""

import unittest
from datetime import date

from src.domain.baseline import (
    ORIGIN_ENTRY,
    ORIGIN_LOCAL,
    AcceptedDebt,
    BaselineEntry,
    BaselineError,
    BaselineStatus,
    Overrides,
    Suppression,
    SuppressionScope,
    apply_overrides,
    entry_debt,
    entry_suppression,
    match_debt,
    match_suppression,
    overdue_debt,
    overdue_decisions,
    parse_overrides,
    status_of_entry,
    validate_debt,
    validate_suppression,
)

_FINGERPRINT = "sha256:" + "a" * 64
_OTHER_FINGERPRINT = "sha256:" + "b" * 64
_RULE = "sec-aws-key"


def suppression(**fields) -> Suppression:
    return validate_suppression(fields)


def debt(**fields) -> AcceptedDebt:
    return validate_debt(fields)


def matches(item: Suppression, **finding) -> bool:
    fields = dict(
        fingerprint=_FINGERPRINT,
        identity=_RULE,
        file_path="src/keys.py",
        line_start=10,
        line_end=10,
    )
    fields.update(finding)
    return item.matches(**fields)


class TestSuppressionValidation(unittest.TestCase):
    def test_every_scope_needs_a_reason(self):
        samples = {
            SuppressionScope.FINDING: {"fingerprint": _FINGERPRINT},
            SuppressionScope.RULE: {"rule_id": _RULE},
            SuppressionScope.FILE: {"rule_id": _RULE, "file_path": "src/keys.py"},
            SuppressionScope.LINE: {
                "rule_id": _RULE,
                "file_path": "src/keys.py",
                "line_start": 1,
                "line_end": 20,
            },
        }
        for scope, fields in samples.items():
            with self.subTest(scope=scope):
                with self.assertRaises(BaselineError) as caught:
                    validate_suppression(dict(fields, scope=scope.value))
                self.assertIn("reason", str(caught.exception))

                accepted = validate_suppression(
                    dict(fields, scope=scope.value, reason="Synthetic secret in a fixture.")
                )
                self.assertEqual(accepted.scope, scope)
                self.assertEqual(accepted.date, None)

    def test_an_unknown_scope_is_refused(self):
        with self.assertRaises(BaselineError):
            validate_suppression({"scope": "repo", "reason": "Too broad."})

    def test_an_unknown_key_is_refused(self):
        with self.assertRaises(BaselineError) as caught:
            validate_suppression(
                {"scope": "rule", "rule_id": _RULE, "reason": "Noisy.", "expires": "soon"}
            )

        self.assertIn("expires", str(caught.exception))

    def test_a_finding_scope_needs_a_fingerprint(self):
        with self.assertRaises(BaselineError):
            validate_suppression({"scope": "finding", "reason": "Known."})

    def test_a_malformed_fingerprint_is_refused(self):
        with self.assertRaises(BaselineError):
            validate_suppression({"scope": "finding", "fingerprint": "abc", "reason": "Known."})

    def test_a_rule_scope_needs_only_the_rule(self):
        item = suppression(scope="rule", rule_id=_RULE, reason="Noisy rule in legacy code.")

        self.assertEqual(item.file_path, None)
        self.assertEqual(item.line_start, None)

    def test_a_file_scope_needs_a_path(self):
        with self.assertRaises(BaselineError):
            validate_suppression({"scope": "file", "rule_id": _RULE, "reason": "Generated."})

    def test_a_line_scope_needs_a_valid_range(self):
        with self.assertRaises(BaselineError):
            validate_suppression(
                {
                    "scope": "line",
                    "rule_id": _RULE,
                    "file_path": "src/keys.py",
                    "line_start": 20,
                    "reason": "Legacy block.",
                }
            )
        with self.assertRaises(BaselineError):
            validate_suppression(
                {
                    "scope": "line",
                    "rule_id": _RULE,
                    "file_path": "src/keys.py",
                    "line_start": 20,
                    "line_end": 10,
                    "reason": "Legacy block.",
                }
            )

    def test_the_audit_trail_is_optional_but_kept(self):
        item = suppression(
            scope="rule",
            rule_id=_RULE,
            reason="Noisy rule in legacy code.",
            by="alice",
            date="2026-10-10",
        )

        self.assertEqual(item.by, "alice")
        self.assertEqual(item.date, "2026-10-10")


class TestDebtValidation(unittest.TestCase):
    def test_an_owner_is_required(self):
        with self.assertRaises(BaselineError) as caught:
            validate_debt({"fingerprint": _FINGERPRINT, "reason": "Planned migration."})

        self.assertIn("owner", str(caught.exception))

    def test_a_reason_is_required(self):
        with self.assertRaises(BaselineError):
            validate_debt({"fingerprint": _FINGERPRINT, "owner": "time-backend"})

    def test_the_finding_it_covers_is_required(self):
        with self.assertRaises(BaselineError):
            validate_debt({"owner": "time-backend", "reason": "Planned migration."})

    def test_a_deadline_is_optional_but_has_to_be_a_date(self):
        without = debt(
            fingerprint=_FINGERPRINT, owner="time-backend", reason="Planned migration."
        )
        self.assertIsNone(without.due_date)

        with self.assertRaises(BaselineError):
            validate_debt(
                {
                    "fingerprint": _FINGERPRINT,
                    "owner": "time-backend",
                    "reason": "Planned migration.",
                    "due_date": "next sprint",
                }
            )


class TestParseOverrides(unittest.TestCase):
    def test_the_block_may_be_nested_or_at_the_root(self):
        nested = parse_overrides(
            {
                "overrides": {
                    "suppressions": [
                        {"scope": "rule", "rule_id": _RULE, "reason": "Noisy."}
                    ]
                }
            }
        )
        flat = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": _RULE, "reason": "Noisy."}]}
        )

        self.assertEqual(len(nested.suppressions), 1)
        self.assertEqual(nested.suppressions[0].rule_id, flat.suppressions[0].rule_id)

    def test_an_empty_document_is_an_empty_layer(self):
        self.assertTrue(parse_overrides(None).is_empty())
        self.assertTrue(parse_overrides({}).is_empty())

    def test_an_unknown_top_level_key_is_refused(self):
        with self.assertRaises(BaselineError):
            parse_overrides({"suppressions": [], "ignore_rules": []})

    def test_a_suppression_list_that_is_not_a_list_is_refused(self):
        with self.assertRaises(BaselineError):
            parse_overrides({"suppressions": {"scope": "rule"}})

    def test_the_same_finding_cannot_be_suppressed_twice(self):
        with self.assertRaises(BaselineError):
            parse_overrides(
                {
                    "suppressions": [
                        {"scope": "finding", "fingerprint": _FINGERPRINT, "reason": "One."},
                        {"scope": "finding", "fingerprint": _FINGERPRINT, "reason": "Two."},
                    ]
                }
            )

    def test_the_same_finding_cannot_owe_two_debts(self):
        with self.assertRaises(BaselineError):
            parse_overrides(
                {
                    "accepted_debt": [
                        {"fingerprint": _FINGERPRINT, "owner": "a", "reason": "One."},
                        {"fingerprint": _FINGERPRINT, "owner": "b", "reason": "Two."},
                    ]
                }
            )


class TestScopeMatching(unittest.TestCase):
    def test_a_finding_scope_matches_only_that_fingerprint(self):
        item = suppression(scope="finding", fingerprint=_FINGERPRINT, reason="Known.")

        self.assertTrue(matches(item))
        self.assertFalse(matches(item, fingerprint=_OTHER_FINGERPRINT))

    def test_a_rule_scope_matches_anywhere(self):
        item = suppression(scope="rule", rule_id=_RULE, reason="Noisy.")

        self.assertTrue(matches(item, file_path="app/Old.php", line_start=900, line_end=901))
        self.assertFalse(matches(item, identity="category:style"))

    def test_a_file_scope_takes_a_glob(self):
        item = suppression(
            scope="file", rule_id=_RULE, file_path="app/Legacy/*", reason="Generated."
        )

        self.assertTrue(matches(item, file_path="app/Legacy/Thing.php"))
        self.assertFalse(matches(item, file_path="app/Modern/Thing.php"))

    def test_a_file_scope_ignores_the_line(self):
        item = suppression(scope="file", rule_id=_RULE, file_path="src/keys.py", reason="Generated.")

        self.assertTrue(matches(item, line_start=900, line_end=910))

    def test_a_line_scope_covers_what_it_contains(self):
        item = suppression(
            scope="line",
            rule_id=_RULE,
            file_path="src/keys.py",
            line_start=100,
            line_end=120,
            reason="Legacy block in migration.",
        )

        self.assertTrue(matches(item, line_start=105, line_end=105))
        self.assertTrue(matches(item, line_start=100, line_end=120))
        self.assertFalse(matches(item, line_start=99, line_end=105))
        self.assertFalse(matches(item, line_start=118, line_end=130))
        self.assertFalse(matches(item, file_path="src/other.py", line_start=105, line_end=105))

    def test_a_path_is_compared_normalized(self):
        item = suppression(scope="file", rule_id=_RULE, file_path="src/keys.py", reason="Generated.")

        self.assertTrue(matches(item, file_path="src\\Keys.py"))

    def test_matching_uses_the_rule_identity(self):
        """A pack silences AI prose by category, not by a rule that does not exist."""
        item = suppression(scope="rule", rule_id="category:security", reason="Noisy AI prose.")

        self.assertTrue(matches(item, identity="category:security", fingerprint=_OTHER_FINGERPRINT))


class TestPrecedence(unittest.TestCase):
    def test_the_most_specific_scope_wins(self):
        broad = suppression(scope="rule", rule_id=_RULE, reason="Noisy rule.")
        narrow = suppression(
            scope="line",
            rule_id=_RULE,
            file_path="src/keys.py",
            line_start=1,
            line_end=50,
            reason="Legacy block.",
        )

        chosen = match_suppression(
            [broad, narrow],
            fingerprint=_FINGERPRINT,
            identity=_RULE,
            file_path="src/keys.py",
            line_start=10,
            line_end=10,
        )

        self.assertEqual(chosen.reason, "Legacy block.")

    def test_among_equals_the_first_layer_wins(self):
        local = suppression(scope="rule", rule_id=_RULE, reason="Local decision.", by="alice")
        pack = suppression(scope="rule", rule_id=_RULE, reason="Pack decision.")

        chosen = match_suppression(
            [local, pack],
            fingerprint=_FINGERPRINT,
            identity=_RULE,
            file_path="src/keys.py",
            line_start=10,
            line_end=10,
        )

        self.assertEqual(chosen.reason, "Local decision.")

    def test_nothing_matches_when_no_scope_covers_the_finding(self):
        broad = suppression(scope="file", rule_id=_RULE, file_path="app/Old.php", reason="Old.")

        self.assertIsNone(
            match_suppression(
                [broad],
                fingerprint=_FINGERPRINT,
                identity=_RULE,
                file_path="src/keys.py",
                line_start=10,
                line_end=10,
            )
        )


class TestLayers(unittest.TestCase):
    def test_the_layers_are_additive(self):
        local = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "local-rule", "reason": "Local."}]}
        )
        pack = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "pack-rule", "reason": "Pack."}]}
        )

        merged = apply_overrides(local, pack=pack, pack_name="acme/team-policy")

        self.assertEqual([item.rule_id for item in merged.suppressions], ["local-rule", "pack-rule"])

    def test_a_decision_from_a_pack_is_tagged_with_the_pack(self):
        pack = parse_overrides(
            {
                "suppressions": [{"scope": "rule", "rule_id": "pack-rule", "reason": "Pack."}],
                "accepted_debt": [
                    {"fingerprint": _FINGERPRINT, "owner": "platform", "reason": "Owned."}
                ],
            }
        )

        merged = apply_overrides(pack=pack, pack_name="acme/team-policy")

        self.assertEqual(merged.suppressions[0].origin, "policy:acme/team-policy")
        self.assertEqual(merged.accepted_debt[0].origin, "policy:acme/team-policy")

    def test_a_local_decision_keeps_its_own_origin(self):
        local = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "local-rule", "reason": "Local."}]}
        )

        self.assertEqual(apply_overrides(local).suppressions[0].origin, ORIGIN_LOCAL)

    def test_local_overrides_can_be_turned_off(self):
        local = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "local-rule", "reason": "Local."}]}
        )
        pack = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": "pack-rule", "reason": "Pack."}]}
        )

        merged = apply_overrides(local, pack=pack, pack_name="acme/team-policy", allow_local=False)

        self.assertEqual([item.rule_id for item in merged.suppressions], ["pack-rule"])

    def test_debt_is_matched_by_fingerprint(self):
        entries = [
            debt(fingerprint=_FINGERPRINT, owner="time-backend", reason="Planned migration.")
        ]

        self.assertIsNotNone(match_debt(entries, fingerprint=_FINGERPRINT))
        self.assertIsNone(match_debt(entries, fingerprint=_OTHER_FINGERPRINT))


class TestEntryLayers(unittest.TestCase):
    def _entry(self, **overrides) -> BaselineEntry:
        fields = dict(
            fingerprint=_FINGERPRINT,
            rule_id=_RULE,
            category="security",
            file_path="src/keys.py",
            line_start=10,
            line_end=10,
            severity="error",
            source="linter",
            status=BaselineStatus.EXISTING,
        )
        fields.update(overrides)
        return BaselineEntry.from_dict(fields)

    def test_an_entry_that_decided_nothing_yields_no_suppression(self):
        self.assertIsNone(entry_suppression(self._entry()))
        self.assertIsNone(entry_debt(self._entry()))

    def test_an_ignored_entry_carries_its_decision(self):
        recorded = entry_suppression(
            self._entry(
                status=BaselineStatus.IGNORED,
                suppressed=True,
                suppression_reason="Synthetic secret in a fixture.",
                suppression_scope=SuppressionScope.RULE,
                suppressed_by="alice",
                suppressed_at="2026-10-10",
            )
        )

        self.assertEqual(recorded.reason, "Synthetic secret in a fixture.")
        self.assertEqual(recorded.scope, SuppressionScope.RULE)
        self.assertEqual(recorded.origin, ORIGIN_ENTRY)
        self.assertEqual(recorded.by, "alice")

    def test_a_debt_entry_carries_its_owner(self):
        recorded = entry_debt(
            self._entry(
                status=BaselineStatus.ACCEPTED_DEBT,
                accepted_debt_owner="time-backend",
                accepted_debt_reason="Planned migration.",
                accepted_debt_due_date="2026-12-31",
            )
        )

        self.assertEqual(recorded.owner, "time-backend")
        self.assertEqual(recorded.due_date, "2026-12-31")
        self.assertEqual(recorded.origin, ORIGIN_ENTRY)

    def test_status_of_an_entry_with_no_layers_is_undecided(self):
        self.assertIsNone(status_of_entry(self._entry()))

    def test_an_override_reaches_an_entry_that_says_nothing(self):
        overrides = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": _RULE, "reason": "Noisy rule."}]}
        )

        applied = status_of_entry(self._entry(), overrides)

        self.assertEqual(applied.status, BaselineStatus.IGNORED)
        self.assertEqual(applied.origin, ORIGIN_LOCAL)
        self.assertEqual(applied.reason, "Noisy rule.")

    def test_the_entry_outranks_an_override_of_the_same_scope(self):
        """The repository's own record is the narrower statement about itself."""
        overrides = parse_overrides(
            {"suppressions": [{"scope": "rule", "rule_id": _RULE, "reason": "Pack said so."}]}
        )
        entry = self._entry(
            status=BaselineStatus.IGNORED,
            suppressed=True,
            suppression_reason="Reviewed and kept.",
            suppression_scope=SuppressionScope.RULE,
        )

        applied = status_of_entry(entry, overrides)

        self.assertEqual(applied.reason, "Reviewed and kept.")
        self.assertEqual(applied.origin, ORIGIN_ENTRY)

    def test_a_specific_override_outranks_a_broad_entry_decision(self):
        overrides = parse_overrides(
            {
                "suppressions": [
                    {
                        "scope": "finding",
                        "fingerprint": _FINGERPRINT,
                        "reason": "This exact finding is a false positive.",
                    }
                ]
            }
        )
        entry = self._entry(
            status=BaselineStatus.IGNORED,
            suppressed=True,
            suppression_reason="Noisy rule.",
            suppression_scope=SuppressionScope.RULE,
        )

        applied = status_of_entry(entry, overrides)

        self.assertEqual(applied.reason, "This exact finding is a false positive.")
        self.assertEqual(applied.scope, SuppressionScope.FINDING)


class TestOverdueDebt(unittest.TestCase):
    def _debt_entry(self, due_date):
        return BaselineEntry.from_dict(
            {
                "fingerprint": _FINGERPRINT,
                "rule_id": _RULE,
                "category": "security",
                "file_path": "src/keys.py",
                "line_start": 10,
                "line_end": 10,
                "severity": "error",
                "source": "linter",
                "status": BaselineStatus.ACCEPTED_DEBT.value,
                "accepted_debt_owner": "time-backend",
                "accepted_debt_reason": "Planned migration.",
                "accepted_debt_due_date": due_date,
            }
        )

    def test_a_passed_deadline_is_late(self):
        late = overdue_debt([self._debt_entry("2026-10-09")], today=date(2026, 10, 10))

        self.assertEqual(len(late), 1)

    def test_a_deadline_today_is_not_late_yet(self):
        self.assertEqual(
            overdue_debt([self._debt_entry("2026-10-10")], today=date(2026, 10, 10)), []
        )

    def test_a_future_deadline_is_not_late(self):
        self.assertEqual(
            overdue_debt([self._debt_entry("2026-12-31")], today=date(2026, 10, 10)), []
        )

    def test_a_debt_without_a_deadline_never_expires(self):
        self.assertEqual(
            overdue_debt([self._debt_entry(None)], today=date(2026, 10, 10)), []
        )

    def test_an_entry_that_is_not_debt_is_ignored(self):
        entry = BaselineEntry.from_dict(
            {
                "fingerprint": _FINGERPRINT,
                "rule_id": _RULE,
                "category": "security",
                "file_path": "src/keys.py",
                "line_start": 10,
                "line_end": 10,
                "severity": "error",
                "source": "linter",
                "status": BaselineStatus.EXISTING.value,
            }
        )

        self.assertEqual(overdue_debt([entry], today=date(2026, 10, 10)), [])


class TestOverdueDecisions(unittest.TestCase):
    """A deadline can arrive in any layer, so the audit has to read all of them."""

    def _debt_entry(self, due_date):
        return BaselineEntry.from_dict(
            {
                "fingerprint": _FINGERPRINT,
                "rule_id": _RULE,
                "category": "security",
                "file_path": "src/keys.py",
                "line_start": 10,
                "line_end": 10,
                "severity": "error",
                "source": "linter",
                "status": BaselineStatus.ACCEPTED_DEBT.value,
                "accepted_debt_owner": "time-backend",
                "accepted_debt_reason": "Planned migration.",
                "accepted_debt_due_date": due_date,
            }
        )

    def _plain_entry(self, fingerprint=_FINGERPRINT):
        """An entry the file records, with no decision written on it."""
        return BaselineEntry.from_dict(
            {
                "fingerprint": fingerprint,
                "rule_id": _RULE,
                "category": "security",
                "file_path": "src/keys.py",
                "line_start": 10,
                "line_end": 10,
                "severity": "error",
                "source": "linter",
                "status": BaselineStatus.EXISTING.value,
            }
        )

    def _layer(self, **debt_fields):
        fields = {
            "fingerprint": _FINGERPRINT,
            "owner": "platform",
            "reason": "Re-planned by the platform team.",
        }
        fields.update(debt_fields)
        return parse_overrides({"accepted_debt": [fields]})

    def test_a_deadline_declared_only_in_a_layer_is_still_checked(self):
        """A debt the file does not mention is a debt all the same."""
        entry = self._plain_entry()
        overrides = self._layer(due_date="2020-01-31")

        late = overdue_decisions([entry], overrides, today=date(2026, 10, 10))

        self.assertEqual(len(late), 1)
        applied = late[0][1]
        self.assertEqual(applied.due_date, "2020-01-31")
        self.assertEqual(applied.owner, "platform")
        self.assertEqual(applied.origin, ORIGIN_LOCAL)

    def test_the_older_entry_only_reading_still_answers_what_it_did(self):
        """`overdue_debt` is unchanged: it reads the entries, and only them."""
        entry = self._plain_entry()

        self.assertEqual(overdue_debt([entry], today=date(2026, 10, 10)), [])
        self.assertEqual(
            overdue_debt([self._debt_entry("2020-01-31")], today=date(2026, 10, 10)),
            [self._debt_entry("2020-01-31")],
        )

    def test_the_entrys_own_decision_is_the_one_the_audit_reads(self):
        """What the file records beats a layer: a later date there is not a reprieve."""
        entry = self._debt_entry("2020-01-31")

        late = overdue_decisions(
            [entry], self._layer(due_date="2026-12-31"), today=date(2026, 10, 10)
        )

        self.assertEqual(len(late), 1)
        self.assertEqual(late[0][1].due_date, "2020-01-31")
        self.assertEqual(late[0][1].origin, ORIGIN_ENTRY)

    def test_a_deadline_that_will_not_parse_does_not_stop_the_audit(self):
        """A typo in one deadline is not a reason to lose the other late debts."""
        typo = self._debt_entry("not-a-date")
        dated = self._debt_entry("2020-01-31")
        dated.fingerprint = _OTHER_FINGERPRINT

        late = overdue_decisions([typo, dated], None, today=date(2026, 10, 10))

        self.assertEqual([entry.fingerprint for entry, _applied in late], [dated.fingerprint])

    def test_a_resolved_entry_is_never_late(self):
        """Nothing is owed for a finding the diff has already removed."""
        entry = self._debt_entry("2020-01-31")
        entry.status = BaselineStatus.RESOLVED

        self.assertEqual(
            overdue_decisions([entry], None, today=date(2026, 10, 10)), []
        )


class TestEmptyLayers(unittest.TestCase):
    def test_an_empty_overrides_is_reported_as_empty(self):
        self.assertTrue(Overrides().is_empty())
        self.assertFalse(
            Overrides(
                suppressions=[suppression(scope="rule", rule_id=_RULE, reason="Noisy.")]
            ).is_empty()
        )
