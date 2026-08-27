import json
import pytest
from unittest.mock import patch, MagicMock
from src.ai_providers import load_chat_commands, process_chat_command, call_ai_chat
from src.chat_memory import ChatMemoryManager
from src.i18n import __


# ──────────────────────────────────────────────────────────────
# load_chat_commands
# ──────────────────────────────────────────────────────────────
class TestLoadChatCommands:
    def test_cache_hit_avoids_http(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.ai_providers.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.ai_providers.CURRENT_LANG", "en")
        data = {"/explain": "desc"}
        cache = tmp_path / ".gitpr" / "cache" / "chat_commands.json"
        cache.parent.mkdir(parents=True)
        cache.write_text(json.dumps(data))

        # Downloads go through the DNS-bounded helper, not urllib directly.
        with patch("src.ai_providers.bounded_urlopen") as mock_fetch:
            result = load_chat_commands()
            mock_fetch.assert_not_called()
        assert result == data

    def test_download_and_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr("src.ai_providers.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.ai_providers.CURRENT_LANG", "pt_br")
        data = {"/explicar": "desc"}
        with patch(
            "src.ai_providers.bounded_urlopen",
            return_value=json.dumps(data).encode(),
        ):
            result = load_chat_commands()
        cached = json.loads(
            (tmp_path / ".gitpr" / "cache" / "chat_commands.pt_br.json").read_text()
        )
        assert result == data
        assert cached == data

    def test_offline_fallback(self, tmp_path, monkeypatch):
        """bounded_urlopen signals failure (and stalled DNS) by returning None."""
        monkeypatch.setattr("src.ai_providers.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.ai_providers.CURRENT_LANG", "en")
        (tmp_path / ".gitpr" / "cache").mkdir(parents=True)
        with patch("src.ai_providers.bounded_urlopen", return_value=None):
            result = load_chat_commands()
        assert "/explain" in result
        assert "/clear" in result

    def test_stalled_dns_falls_back_without_hanging(self, tmp_path, monkeypatch):
        """A stalled resolver must degrade to the offline defaults, not block."""
        monkeypatch.setattr("src.ai_providers.Path.home", lambda: tmp_path)
        monkeypatch.setattr("src.ai_providers.CURRENT_LANG", "en")
        (tmp_path / ".gitpr" / "cache").mkdir(parents=True)
        with patch("src.ai_providers.bounded_urlopen", return_value=None):
            result = load_chat_commands()
        assert result["/clear"].startswith("Clears")


# ──────────────────────────────────────────────────────────────
# process_chat_command
# ──────────────────────────────────────────────────────────────
class TestProcessChatCommand:
    FAKE_COMMANDS = {
        "/explain": "explain prompt",
        "/clear": "clear prompt",
        "/limpar": "clear ptbr",
    }

    @pytest.fixture(autouse=True)
    def mock_load_commands(self, monkeypatch):
        monkeypatch.setattr(
            "src.ai_providers.load_chat_commands",
            lambda: self.FAKE_COMMANDS,
        )

    def test_normal_command(self):
        is_cmd, is_clear, prompt = process_chat_command("/explain")
        assert is_cmd
        assert not is_clear
        assert prompt == "explain prompt"

    def test_clear_english(self):
        _, is_clear, _ = process_chat_command("/clear")
        assert is_clear

    def test_clear_ptbr(self):
        _, is_clear, _ = process_chat_command("/limpar")
        assert is_clear

    def test_case_insensitive_and_whitespace(self):
        is_cmd, _, prompt = process_chat_command("  /EXPLAIN  ")
        assert is_cmd
        assert prompt == "explain prompt"

    def test_plain_message(self):
        is_cmd, is_clear, msg = process_chat_command("hello")
        assert not is_cmd
        assert msg == "hello"


# ──────────────────────────────────────────────────────────────
# call_ai_chat
# ──────────────────────────────────────────────────────────────
class TestCallAiChat:
    SYSTEM = "You are helpful"

    @patch("src.ai_providers.genai.Client")
    def test_gemini_success(self, mock_client_cls):
        client = MagicMock()
        client.models.generate_content.return_value.text = "reply"
        mock_client_cls.return_value = client

        result = call_ai_chat("gemini", "key", "m", self.SYSTEM,
                              [{"role": "user", "content": "Q"}], "Q2", quiet=True)
        assert result == "reply"
        # verify history formatting: assistant -> model
        call_args = client.models.generate_content.call_args
        contents = call_args[1]["contents"]
        assert contents[0]["role"] == "user"
        assert contents[1]["role"] == "user"

    @patch("src.ai_providers.OpenAI")
    def test_deepseek_success(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="deep reply"))]
        )
        mock_openai_cls.return_value = client
        result = call_ai_chat("deepseek", "key", "m", self.SYSTEM,
                              [], "Hello", quiet=True)
        assert result == "deep reply"
        msgs = client.chat.completions.create.call_args[1]["messages"]
        assert msgs[0]["role"] == "system"
        assert msgs[1]["role"] == "user"

    @patch("src.ai_providers.OpenAI")
    def test_ollama_success(self, mock_openai_cls):
        client = MagicMock()
        client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="local reply"))]
        )
        mock_openai_cls.return_value = client
        result = call_ai_chat("ollama", "key", "m", self.SYSTEM,
                              [], "hi", quiet=True)
        assert result == "local reply"

    def test_unknown_provider(self, capsys):
        result = call_ai_chat("bad", "k", "m", "", [], "", quiet=True)
        assert result is None
        expected = __("❌ Unknown AI provider: {provider}", provider="bad")
        assert expected in capsys.readouterr().out

    @patch("src.ai_providers.genai.Client")
    def test_api_exception(self, mock_client_cls, capsys):
        client = MagicMock()
        client.models.generate_content.side_effect = Exception("boom")
        mock_client_cls.return_value = client
        result = call_ai_chat("gemini", "k", "m", self.SYSTEM,
                              [], "hi", quiet=True)
        assert result is None
        assert "Critical error in Chat API" in capsys.readouterr().out


# ──────────────────────────────────────────────────────────────
# ChatMemoryManager
# ──────────────────────────────────────────────────────────────
class TestChatMemoryManager:
    @pytest.fixture(autouse=True)
    def _patch_home(self, tmp_path, monkeypatch):
        """Redirect Path.home() so cache is created under tmp_path."""
        monkeypatch.setattr("src.chat_memory.Path.home", lambda: tmp_path)
        (tmp_path / ".gitpr" / "cache" / "chat").mkdir(parents=True, exist_ok=True)

    def test_create_new_session(self):
        mgr = ChatMemoryManager("repo", "br", "diff1", "u", "e")
        assert mgr.session_dir.exists()
        assert mgr.config_file.exists()
        assert mgr.conversation_file.exists()
        assert len(mgr.get_history()) == 0

    def test_save_and_get_messages(self):
        mgr = ChatMemoryManager("r", "b", "d", "u", "e")
        mgr.save_message("user", "Hello")
        mgr.save_message("assistant", "Hi")
        hist = mgr.get_history()
        assert len(hist) == 2
        assert hist[0]["role"] == "user"

    def test_reopen_session_reuses_uuid(self):
        mgr1 = ChatMemoryManager("r", "b", "d1", "u", "e")
        uid = mgr1.session_uuid
        mgr1.save_message("user", "old")
        # reopen with new diff
        mgr2 = ChatMemoryManager("r", "b", "d2", "u", "e")
        assert mgr2.session_uuid == uid
        assert len(mgr2.get_history()) == 1

    def test_update_diff_if_changed(self):
        mgr = ChatMemoryManager("r", "b", "v1", "u", "e")
        assert mgr.update_diff_if_changed("v2")  # True -> changed
        assert mgr.get_latest_diff() == "v2"
        assert not mgr.update_diff_if_changed("v2")  # False -> same

    def test_get_latest_diff(self):
        mgr = ChatMemoryManager("r", "b", "initial", "u", "e")
        assert mgr.get_latest_diff() == "initial"
