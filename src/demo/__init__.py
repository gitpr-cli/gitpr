"""Guided tour of GitPR — no API key, no Git repository, no network.

The demo runs the *real* generation pipeline (``core.generate_pr_content``)
with a provider that replays recorded answers, so what the tour shows is what
the tool produces. Everything that would touch the disk or the wire during a
real run is neutralised in ``fake_ai_provider.demo_pipeline``.
"""
