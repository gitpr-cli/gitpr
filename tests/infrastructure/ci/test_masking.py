"""Tests for sensitive data masking in CI artifacts."""

from src.infrastructure.ci.masking import mask_sensitive_text


def test_mask_aws_access_key():
    raw = "Found AWS access key AKIAIOSFODNN7EXAMPLE in code"
    masked = mask_sensitive_text(raw)
    assert "AKIAIOSFODNN7EXAMPLE" not in masked
    assert "***" in masked


def test_mask_github_pat():
    raw = "Token ghp_123456789012345678901234567890123456 committed"
    masked = mask_sensitive_text(raw)
    assert "ghp_123456789012345678901234567890123456" not in masked
    assert "***" in masked


def test_mask_google_gemini_api_key():
    raw = "AIzaSyD-1234567890abcdefghijklmnopqrstuv"
    masked = mask_sensitive_text(raw)
    assert "AIzaSyD" not in masked
    assert "***" in masked


def test_mask_bearer_token():
    raw = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
    masked = mask_sensitive_text(raw)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in masked
    assert "Bearer ***" in masked


def test_mask_basic_auth_url():
    raw = "Clone URL https://nataniel:supersecretpassword@github.com/repo.git"
    masked = mask_sensitive_text(raw)
    assert "supersecretpassword" not in masked
    assert "https://nataniel:***@github.com/repo.git" in masked


def test_mask_private_key():
    raw = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Yq...\n"
        "-----END RSA PRIVATE KEY-----"
    )
    masked = mask_sensitive_text(raw)
    assert "MIIEowIBAAKCAQEA0Yq..." not in masked
    assert "***" in masked
