import json

import src.ai_providers as ai_providers
from src.ai_providers import set_pre_save, _save_pre_save_payload


# ──────────────────────────────────────────────────────────────
# set_pre_save
# ──────────────────────────────────────────────────────────────
class TestSetPreSave:
    def test_toggle_module_flag(self):
        try:
            set_pre_save(True)
            assert ai_providers.PRE_SAVE_ENABLED is True
        finally:
            set_pre_save(False)
        assert ai_providers.PRE_SAVE_ENABLED is False


# ──────────────────────────────────────────────────────────────
# _save_pre_save_payload
# ──────────────────────────────────────────────────────────────
class TestSavePreSavePayload:
    def test_creates_json_file_for_model_call(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        filename = _save_pre_save_payload(
            action="commit",
            provider="gemini",
            api_model="gemini-2.5-flash",
            system_instruction="You are a Git expert.",
            prompt="Generate a commit message for this diff: áçã",
        )
        assert filename is not None
        assert filename.startswith("_commit-")
        assert filename.endswith(".json")

        data = json.loads((tmp_path / filename).read_text(encoding="utf-8"))
        assert data["action"] == "commit"
        assert data["provider"] == "gemini"
        assert data["model"] == "gemini-2.5-flash"
        assert data["system_instruction"] == "You are a Git expert."
        assert data["prompt"].endswith("áçã")
        assert data["total_chars"] == data["system_instruction_chars"] + data["prompt_chars"]

    def test_creates_json_file_for_chat_call(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        filename = _save_pre_save_payload(
            action="chat",
            provider="deepseek",
            api_model="deepseek-chat",
            system_instruction="You are a pair programmer.",
            chat_history=history,
            new_message="Explain the diff",
        )
        assert filename is not None
        assert filename.startswith("_chat-")

        data = json.loads((tmp_path / filename).read_text(encoding="utf-8"))
        assert data["chat_history"] == history
        assert data["new_message"] == "Explain the diff"
        assert "prompt" not in data
        assert data["total_chars"] > 0
