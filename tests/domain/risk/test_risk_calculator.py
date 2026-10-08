"""Unit tests for pure risk calculation, clamping, level resolution, and PR aggregation."""

import unittest
from src.domain.risk.risk_calculator import (
    calculate_file_risk,
    calculate_pull_request_risk,
)
from src.domain.risk.risk_rules import RiskConfig
from src.domain.risk.risk_types import (
    FileRisk,
    RiskEvidence,
    RiskLevel,
    RiskSignal,
)


class TestRiskCalculator(unittest.TestCase):

    def test_pure_calculation_is_deterministic(self):
        evidence = [
            RiskEvidence(signal=RiskSignal.CRITICAL_PATH, points=25.0, summary="Auth module"),
            RiskEvidence(signal=RiskSignal.NO_TEST_CHANGE, points=15.0, summary="No tests"),
        ]
        r1 = calculate_file_risk("src/auth.py", 50, 2, evidence)
        r2 = calculate_file_risk("src/auth.py", 50, 2, evidence)

        self.assertEqual(r1.score, 40.0)
        self.assertEqual(r1.level, RiskLevel.MEDIUM)
        self.assertEqual(r1.score, r2.score)
        self.assertEqual(r1.level, r2.level)
        self.assertEqual(len(r1.evidence), len(r2.evidence))

    def test_clamping_saturation_and_floor(self):
        # Upper clamp: points sum > 100
        over_evidence = [
            RiskEvidence(signal=RiskSignal.CRITICAL_PATH, points=50.0, summary="P1"),
            RiskEvidence(signal=RiskSignal.SECURITY_SENSITIVE, points=50.0, summary="P2"),
            RiskEvidence(signal=RiskSignal.DATABASE_MIGRATION, points=30.0, summary="P3"),
        ]
        r_over = calculate_file_risk("src/db.py", 100, 5, over_evidence)
        self.assertEqual(r_over.score, 100.0)
        self.assertEqual(r_over.level, RiskLevel.CRITICAL)

        # Lower clamp: mitigating points sum < 0
        under_evidence = [
            RiskEvidence(signal=RiskSignal.TEST_PRESENT, points=-20.0, summary="Mitigation"),
        ]
        r_under = calculate_file_risk("src/helper.py", 10, 1, under_evidence)
        self.assertEqual(r_under.score, 0.0)
        self.assertEqual(r_under.level, RiskLevel.LOW)

    def test_pr_aggregation_formula_50_30_20(self):
        # File 1: score 60, lines 100
        f1 = FileRisk(
            file_path="src/f1.py",
            score=60.0,
            level=RiskLevel.HIGH,
            changed_lines=100,
            changed_hunks=2,
            evidence=[RiskEvidence(signal=RiskSignal.CRITICAL_PATH, points=25.0, summary="Auth")],
        )
        # File 2: score 20, lines 100
        f2 = FileRisk(
            file_path="src/f2.py",
            score=20.0,
            level=RiskLevel.LOW,
            changed_lines=100,
            changed_hunks=1,
            evidence=[],
        )

        # max_file = 60.0 (50% = 30.0)
        # weighted_avg = (60*100 + 20*100)/200 = 40.0 (30% = 12.0)
        # critical_ev = min(100, 25.0) = 25.0 (20% = 5.0)
        # expected aggregate = 30.0 + 12.0 + 5.0 = 47.0 (MEDIUM)
        pr_risk = calculate_pull_request_risk([f1, f2])
        self.assertEqual(pr_risk.score, 47.0)
        self.assertEqual(pr_risk.level, RiskLevel.MEDIUM)
        self.assertEqual(pr_risk.total_changed_files, 2)
        self.assertEqual(pr_risk.total_changed_lines, 200)

    def test_mandatory_elevation_rules(self):
        # Rule 5: File >= 80 -> PR cannot be below HIGH even if average is low
        f_huge = FileRisk(
            file_path="src/huge.py",
            score=85.0,
            level=RiskLevel.CRITICAL,
            changed_lines=1,
            changed_hunks=1,
        )
        f_small = FileRisk(
            file_path="src/small.py",
            score=5.0,
            level=RiskLevel.LOW,
            changed_lines=1000,
            changed_hunks=1,
        )
        pr_risk_elevated = calculate_pull_request_risk([f_huge, f_small])
        self.assertIn(pr_risk_elevated.level, (RiskLevel.HIGH, RiskLevel.CRITICAL))

        # Rule 6: Blocker finding -> PR is CRITICAL
        f_blocker = FileRisk(
            file_path="src/secret.py",
            score=30.0,
            level=RiskLevel.MEDIUM,
            changed_lines=10,
            changed_hunks=1,
            evidence=[
                RiskEvidence(
                    signal=RiskSignal.FINDING_BLOCKER,
                    points=25.0,
                    summary="Exposed AWS key",
                )
            ],
        )
        pr_blocker = calculate_pull_request_risk([f_blocker])
        self.assertEqual(pr_blocker.level, RiskLevel.CRITICAL)

    def test_empty_files_returns_zero_risk(self):
        pr_risk = calculate_pull_request_risk([])
        self.assertEqual(pr_risk.score, 0.0)
        self.assertEqual(pr_risk.level, RiskLevel.LOW)
        self.assertEqual(pr_risk.total_changed_files, 0)

