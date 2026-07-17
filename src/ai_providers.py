import json
import time
import click
from google import genai
from openai import OpenAI
import urllib.request
from pathlib import Path

from src.spinner import Spinner
from src.i18n import __,CURRENT_LANG


def call_ai_model(provider, api_key, api_model, prompt, system_instruction, quiet=False):
    """
    Unified engine for AI calls.
    Supports 'gemini' and 'deepseek'.
    """
    max_retries = 3
    retry_delay = 2
    spinner = Spinner(quiet=quiet)
    spinner.start()

    try:
        for attempt in range(1, max_retries + 1):
            try:
                if provider == "gemini":
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model=api_model,
                        contents=prompt,
                        config={
                            "system_instruction": system_instruction,
                            "response_mime_type": "application/json",
                            "temperature": 0.0,
                            "top_p": 0.1,
                            "top_k": 1
                        }
                    )
                    result_text = response.text

                elif provider in ["deepseek", "ollama"]:
                    # DeepSeek and Ollama are 100% compatible with the OpenAI library.
                    base_url = "https://api.deepseek.com" if provider == "deepseek" else "http://localhost:11434/v1"
                    client = OpenAI(api_key=api_key, base_url=base_url)
                    
                    response = client.chat.completions.create(
                        model=api_model, 
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.0
                    )
                    result_text = response.choices[0].message.content

                else:
                    spinner.stop()
                    click.secho(__("❌ Unknown AI provider: {provider}", provider=provider), fg="red")
                    return None

                # Try to convert the text response into a Python JSON dictionary
                result_json = json.loads(result_text)

                # 🛡️ SHIELD: If the AI returns a list [ { ... } ] by mistake
                if isinstance(result_json, list):
                    result_json = result_json[0] if result_json else {}

                spinner.stop()
                return result_json

            except Exception as e:
                if attempt < max_retries:
                    spinner.stop()
                    click.secho(__("\r⚠️ API instability ({provider}). Retrying ({attempt}/{max_retries})...", provider=provider.capitalize(), attempt=attempt, max_retries=max_retries), fg="yellow", dim=True)
                    time.sleep(retry_delay)
                    spinner = Spinner(quiet=quiet)
                    spinner.start()
                else:
                    spinner.stop()
                    click.secho(__("\r❌ Critical error contacting {provider} API after {max_retries} attempts: {error}", provider=provider.capitalize(), max_retries=max_retries, error=str(e)), fg="red", bold=True)
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

    # If it is not in the cache, download it from the remote repository
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'GitPR-Chat'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return data
    except Exception:
        # Safety fallback if the user is offline
        return {
            "/explain": "Explains the diff line by line.",
            "/tests": "Generates unit tests for the changed functions.",
            "/optimize": "Analyzes cyclomatic complexity and performance.",
            "/clear": "Clears conversation and creates a new chat session for the current diff."
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
            is_clear = (cmd.lower() in ["/clear", "/limpar", "/limpiar", "/effacer"])
            return True, is_clear, prompt
            
    return False, False, message

def call_ai_chat(provider, api_key, api_model, system_instruction, chat_history, new_message, quiet=False):
    """
    Dedicated engine for the Interactive Chat.
    Keeps the historical context and returns free Markdown (does not force JSON).
    """
    spinner = Spinner(quiet=quiet)
    spinner.start()

    try:
        if provider == "gemini":
            client = genai.Client(api_key=api_key)
            
            # Format the history into the Gemini SDK format
            formatted_contents = []
            for msg in chat_history:
                role = "model" if msg["role"] == "assistant" else "user"
                formatted_contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            
            formatted_contents.append({"role": "user", "parts": [{"text": new_message}]})

            response = client.models.generate_content(
                model=api_model,
                contents=formatted_contents,
                config={
                    "system_instruction": system_instruction,
                    "temperature": 0.3 # Slightly higher so the chat feels more natural
                }
            )
            result_text = response.text

        elif provider in ["deepseek", "ollama"]:
            base_url = "https://api.deepseek.com" if provider == "deepseek" else "http://localhost:11434/v1"
            client = OpenAI(api_key=api_key, base_url=base_url)
            
            messages = [{"role": "system", "content": system_instruction}]
            for msg in chat_history:
                messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": new_message})
            
            response = client.chat.completions.create(
                model=api_model, 
                messages=messages,
                temperature=0.3
            )
            result_text = response.choices[0].message.content
        else:
            spinner.stop()
            click.secho(__("❌ Unknown AI provider: {provider}", provider=provider), fg="red")
            return None

        spinner.stop()
        return result_text

    except Exception as e:
        spinner.stop()
        click.secho(__("\r❌ Critical error in Chat API ({provider}): {error}", provider=provider.capitalize(), error=str(e)), fg="red", bold=True)
        return None
    finally:
        spinner.stop()        