import json
import time
from datetime import datetime
import click
from google import genai
from openai import OpenAI
from pathlib import Path

from src.net import bounded_resolve, bounded_urlopen
from src.spinner import Spinner
from src.i18n import __, CURRENT_LANG


def _make_gemini_client(api_key, timeout_s):
    """Builds a Gemini client with an explicit request timeout.

    google-genai expresses http_options.timeout in MILLISECONDS.
    """
    bounded_resolve("generativelanguage.googleapis.com")
    return genai.Client(
        api_key=api_key, http_options={"timeout": int(timeout_s * 1000)}
    )


def _make_openai_client(api_key, provider, timeout_s):
    """Builds an OpenAI-compatible client (DeepSeek/Ollama) with a timeout in seconds."""
    base_url = (
        "https://api.deepseek.com"
        if provider == "deepseek"
        else "http://localhost:11434/v1"
    )
    if provider == "deepseek":
        bounded_resolve("api.deepseek.com")
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_s)


# Hidden --pre-save debug flag: when enabled, every AI payload is dumped
# to a JSON file in the current directory before being sent to the model.
PRE_SAVE_ENABLED = False


def set_pre_save(enabled):
    """Enable/disable the pre-save payload dump (set once from the CLI)."""
    global PRE_SAVE_ENABLED
    PRE_SAVE_ENABLED = enabled


def _save_pre_save_payload(
    action,
    provider,
    api_model,
    system_instruction,
    prompt=None,
    chat_history=None,
    new_message=None,
):
    """
    Dump the full AI payload to a _{action}-{datetime}.json file in the current directory.
    Returns the filename on success or None on failure (a debug dump must never break the flow).
    """
    filename = f"_{action}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}.json"

    payload = {
        "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "provider": provider,
        "model": api_model,
        "system_instruction": system_instruction,
        "system_instruction_chars": len(system_instruction)
        if system_instruction
        else 0,
    }

    if chat_history is not None:
        payload["chat_history"] = chat_history
        payload["new_message"] = new_message
        payload["chat_history_chars"] = (
            len(json.dumps(chat_history, ensure_ascii=False)) if chat_history else 0
        )
        payload["new_message_chars"] = len(new_message) if new_message else 0
        payload["total_chars"] = (
            payload["system_instruction_chars"]
            + payload["chat_history_chars"]
            + payload["new_message_chars"]
        )
    else:
        payload["prompt"] = prompt
        payload["prompt_chars"] = len(prompt) if prompt else 0
        payload["total_chars"] = (
            payload["system_instruction_chars"] + payload["prompt_chars"]
        )

    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return filename
    except Exception:
        return None


def call_ai_model(
    provider,
    api_key,
    api_model,
    prompt,
    system_instruction,
    quiet=False,
    action="ai_call",
):
    """
    Unified engine for AI calls.
    Supports 'gemini' and 'deepseek'.
    """
    from src.config import get_ai_timeout

    max_retries = 3
    retry_delay = 2
    timeout_s = get_ai_timeout()

    if PRE_SAVE_ENABLED:
        saved_file = _save_pre_save_payload(
            action, provider, api_model, system_instruction, prompt=prompt
        )
        if saved_file and not quiet:
            click.secho(
                __("📝 Pre-save: AI payload saved to {filename}", filename=saved_file),
                fg="yellow",
                dim=True,
            )

    spinner = Spinner(quiet=quiet)
    spinner.start()

    start_time = time.perf_counter()

    try:
        for attempt in range(1, max_retries + 1):
            try:
                meta_raw = {}
                if provider == "gemini":
                    client = _make_gemini_client(api_key, timeout_s)
                    response = client.models.generate_content(
                        model=api_model,
                        contents=prompt,
                        config={
                            "system_instruction": system_instruction,
                            "response_mime_type": "application/json",
                            "temperature": 0.0,
                            "top_p": 0.1,
                            "top_k": 1,
                        },
                    )
                    result_text = response.text

                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        meta_raw = {
                            "prompt_tokens": getattr(
                                response.usage_metadata, "prompt_token_count", 0
                            ),
                            "completion_tokens": getattr(
                                response.usage_metadata, "candidates_token_count", 0
                            ),
                            "total_tokens": getattr(
                                response.usage_metadata, "total_token_count", 0
                            ),
                        }

                elif provider in ["deepseek", "ollama"]:
                    # DeepSeek and Ollama are 100% compatible with the OpenAI library.
                    client = _make_openai_client(api_key, provider, timeout_s)

                    response = client.chat.completions.create(
                        model=api_model,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.0,
                    )
                    result_text = response.choices[0].message.content

                    if hasattr(response, "usage") and response.usage:
                        meta_raw = {
                            "prompt_tokens": getattr(
                                response.usage, "prompt_tokens", 0
                            ),
                            "completion_tokens": getattr(
                                response.usage, "completion_tokens", 0
                            ),
                            "total_tokens": getattr(response.usage, "total_tokens", 0),
                        }

                else:
                    spinner.stop()
                    click.secho(
                        __("❌ Unknown AI provider: {provider}", provider=provider),
                        fg="red",
                    )
                    return None

                # Try to convert the text response into a Python JSON dictionary
                result_json = json.loads(result_text)

                # 🛡️ SHIELD: If the AI returns a list [ { ... } ] by mistake
                if isinstance(result_json, list):
                    result_json = result_json[0] if result_json else {}

                # Inject telemetry metadata silently into the response dictionary
                meta_raw["duration_ms"] = int((time.perf_counter() - start_time) * 1000)
                meta_raw["provider"] = provider
                meta_raw["model"] = api_model
                result_json["_telemetry_meta"] = meta_raw

                spinner.stop()
                return result_json

            except Exception as e:
                if attempt < max_retries:
                    spinner.stop()
                    click.secho(
                        __(
                            "\r⚠️ API instability ({provider}). Retrying ({attempt}/{max_retries})...",
                            provider=provider.capitalize(),
                            attempt=attempt,
                            max_retries=max_retries,
                        ),
                        fg="yellow",
                        dim=True,
                    )
                    time.sleep(retry_delay)
                    spinner = Spinner(quiet=quiet)
                    spinner.start()
                else:
                    spinner.stop()
                    click.secho(
                        __(
                            "\r❌ Critical error contacting {provider} API after {max_retries} attempts: {error}",
                            provider=provider.capitalize(),
                            max_retries=max_retries,
                            error=str(e),
                        ),
                        fg="red",
                        bold=True,
                    )
                    return None
    finally:
        spinner.stop()


def load_chat_commands():
    """Download and cache the translated chat commands."""
    lang_suffix = "" if CURRENT_LANG.startswith("en") else f".{CURRENT_LANG}"
    url = f"https://raw.githubusercontent.com/natanfiuza/gitpr/main/templates/chat_commands{lang_suffix}.json"

    cache_dir = Path.home() / ".gitpr" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"chat_commands{lang_suffix}.json"

    # Try loading from the local cache first to avoid slowing down the terminal
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    # If it is not in the cache, download it from the remote repository.
    # bounded_urlopen also bounds DNS resolution, which urllib's timeout does not.
    try:
        raw = bounded_urlopen(
            url, timeout=5, headers={"User-Agent": "GitPR-Chat"}
        )
        if raw is not None:
            data = json.loads(raw.decode())
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
    except Exception:
        pass  # Fall through to the offline defaults below

    # Safety fallback if the user is offline
    return {
            "/explain": "Explains the diff line by line.",
            "/tests": "Generates unit tests for the changed functions.",
            "/optimize": "Analyzes cyclomatic complexity and performance.",
            "/clear": "Clears conversation and creates a new chat session for the current diff.",
        }


def process_chat_command(message):
    """
    Check whether the message is a command (e.g., /explain).
    Returns a tuple: (is_command, is_clear_command, processed_message)
    """
    msg_trimmed = message.strip().lower()
    if not msg_trimmed.startswith("/"):
        return False, False, message

    commands = load_chat_commands()

    for cmd, prompt in commands.items():
        if msg_trimmed == cmd.lower():
            # Special flag so the UI knows whether to reset the session without calling the AI
            is_clear = cmd.lower() in ["/clear", "/limpar", "/limpiar", "/effacer"]
            return True, is_clear, prompt

    return False, False, message


def call_ai_chat(
    provider,
    api_key,
    api_model,
    system_instruction,
    chat_history,
    new_message,
    quiet=False,
):
    """
    Dedicated engine for the Interactive Chat.
    Keeps the historical context and returns free Markdown (does not force JSON).
    """
    from src.config import get_ai_timeout

    timeout_s = get_ai_timeout()

    if PRE_SAVE_ENABLED:
        saved_file = _save_pre_save_payload(
            "chat",
            provider,
            api_model,
            system_instruction,
            chat_history=chat_history,
            new_message=new_message,
        )
        if saved_file and not quiet:
            click.secho(
                __("📝 Pre-save: AI payload saved to {filename}", filename=saved_file),
                fg="yellow",
                dim=True,
            )

    spinner = Spinner(quiet=quiet)
    spinner.start()

    try:
        if provider == "gemini":
            client = _make_gemini_client(api_key, timeout_s)

            # Format the history into the Gemini SDK format
            formatted_contents = []
            for msg in chat_history:
                role = "model" if msg["role"] == "assistant" else "user"
                formatted_contents.append(
                    {"role": role, "parts": [{"text": msg["content"]}]}
                )

            formatted_contents.append(
                {"role": "user", "parts": [{"text": new_message}]}
            )

            response = client.models.generate_content(
                model=api_model,
                contents=formatted_contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.3,  # Slightly higher so the chat feels more natural
                },
            )
            result_text = response.text

        elif provider in ["deepseek", "ollama"]:
            client = _make_openai_client(api_key, provider, timeout_s)

            messages = [{"role": "system", "content": system_instruction}]
            for msg in chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": new_message})

            response = client.chat.completions.create(
                model=api_model, messages=messages, temperature=0.3
            )
            result_text = response.choices[0].message.content
        else:
            spinner.stop()
            click.secho(
                __("❌ Unknown AI provider: {provider}", provider=provider), fg="red"
            )
            return None

        spinner.stop()
        return result_text

    except Exception as e:
        spinner.stop()
        click.secho(
            __(
                "\r❌ Critical error in Chat API ({provider}): {error}",
                provider=provider.capitalize(),
                error=str(e),
            ),
            fg="red",
            bold=True,
        )
        return None
    finally:
        spinner.stop()
