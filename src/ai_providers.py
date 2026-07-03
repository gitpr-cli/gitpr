import json
import time
import click
from google import genai
from openai import OpenAI

def call_ai_model(provider, api_key, api_model, prompt, system_instruction):
    """
    Motor unificado para chamadas de IA.
    Suporta 'gemini' e 'deepseek'.
    """
    max_retries = 3
    retry_delay = 2

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

            elif provider == "deepseek":
                # O DeepSeek é 100% compatível com a biblioteca da OpenAI
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model=api_model, # Ex: "deepseek-chat"
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0
                )
                result_text = response.choices[0].message.content
            
            else:
                click.secho(f"❌ Provedor de IA desconhecido: {provider}", fg="red")
                return None

            # Tenta converter a resposta de texto para um dicionário JSON do Python
            result_json = json.loads(result_text)

            # 🛡️ ESCUDO: Se a IA retornar uma lista [ { ... } ] por engano
            if isinstance(result_json, list):
                result_json = result_json[0] if result_json else {}

            return result_json

        except Exception as e:
            if attempt < max_retries:
                click.secho(f"⚠️ Instabilidade na API ({provider.capitalize()}). A tentar novamente ({attempt}/{max_retries})...", fg="yellow", dim=True)
                time.sleep(retry_delay)
            else:
                click.secho(f"❌ Erro crítico ao contactar a API do {provider.capitalize()} após {max_retries} tentativas: {str(e)}", fg="red", bold=True)
                return None