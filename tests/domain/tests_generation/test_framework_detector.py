import json
import pytest
from pathlib import Path
from src.domain.tests_generation.framework_detector import detect_test_framework
from src.domain.tests_generation.test_content_types import TestFramework


def test_detect_pest_by_file(tmp_path):
    (tmp_path / "pest.php").write_text("<?php", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.PEST
    assert not warnings


def test_detect_phpunit_by_xml(tmp_path):
    (tmp_path / "phpunit.xml").write_text("<phpunit></phpunit>", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.PHPUNIT
    assert not warnings


def test_detect_composer_pest(tmp_path):
    composer = {"require-dev": {"pestphp/pest": "^2.0"}}
    (tmp_path / "composer.json").write_text(json.dumps(composer), encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.PEST


def test_detect_composer_phpunit(tmp_path):
    composer = {"require-dev": {"phpunit/phpunit": "^10.0"}}
    (tmp_path / "composer.json").write_text(json.dumps(composer), encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.PHPUNIT


def test_detect_vitest_config(tmp_path):
    (tmp_path / "vitest.config.ts").write_text("export default {}", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.VITEST


def test_detect_jest_config(tmp_path):
    (tmp_path / "jest.config.js").write_text("module.exports = {}", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.JEST


def test_detect_package_json_vitest(tmp_path):
    pkg = {"devDependencies": {"vitest": "^1.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.VITEST


def test_detect_pytest_ini(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.PYTEST


def test_detect_pyproject_pytest(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\nminversion = '6.0'", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.PYTEST


def test_detect_unknown_fallback(tmp_path):
    fw, warnings = detect_test_framework(str(tmp_path))
    assert fw == TestFramework.UNKNOWN
    assert len(warnings) > 0


def test_override_framework(tmp_path):
    (tmp_path / "pytest.ini").write_text("[pytest]", encoding="utf-8")
    fw, warnings = detect_test_framework(str(tmp_path), framework_override="pest")
    assert fw == TestFramework.PEST

