# Documentação Técnica: Fornecedores de IA (--provider)

O GitPR é **agnóstico de IA** e suporta atualmente dois fornecedores: **Google Gemini** e **DeepSeek**. Pode alternar entre eles dinamicamente via linha de comandos ou configuração persistente.

---

## 1. Seleção via Linha de Comandos

```bash
gitpr -p gemini         # Força Google Gemini nesta execução
gitpr -p deepseek       # Força DeepSeek nesta execução
gitpr -c -p gemini      # Commit message com Gemini
gitpr -r -p deepseek    # Code review com DeepSeek
```

A flag `--provider` (`-p`) sobrescreve temporariamente o provider predefinido configurado.

---

## 2. Configuração Persistente

Defina o provider predefinido no ficheiro `~/.gitpr/.env`:

```ini
DEFAULT_AI_PROVIDER=gemini
# ou
DEFAULT_AI_PROVIDER=deepseek
```

---

## 3. Modelos Disponíveis

### 3.1 Google Gemini

| Modelo | Utilização | Variável de Ambiente |
| --- | --- | --- |
| `gemini-2.5-flash` | Primário (avançado) — PRs, reviews, issues | `GEMINI_API_MODEL` |
| `gemini-2.5-flash-lite` | Secundário (simples) — classificação no blame | `SECONDARY_GEMINI_API_MODEL` |

### 3.2 DeepSeek

| Modelo | Utilização | Variável de Ambiente |
| --- | --- | --- |
| `deepseek-chat` | Primário e Secundário | `DEEPSEEK_API_MODEL` / `SECONDARY_DEEPSEEK_API_MODEL` |

---

## 4. Configuração de Chaves de API

As chaves são armazenadas de forma **encriptada** (Fernet) no ficheiro `~/.gitpr/.env`:

```ini
GEMINI_API_KEY_ENCRYPTED=<hash_criptografado>
DEEPSEEK_API_KEY_ENCRYPTED=<hash_criptografado>
```

A chave mestra de desencriptação é gerada automaticamente em `~/.gitpr/secret.key`.

---

## 5. Fallback Automático

Se o provider configurado falhar (erro de rede, quota excedida, etc.), o GitPR tenta automaticamente o **outro provider** disponível. Este comportamento garante que o fluxo de trabalho não seja interrompido por indisponibilidade temporária de um serviço.

---

## 6. Parâmetros de Geração

Ambos os fornecedores são configurados para output determinístico:

| Parâmetro | Valor |
| --- | --- |
| **Temperatura** | 0.0 |
| **Top P** | 0.1 |
| **Formato de saída** | JSON estruturado |
| **Retry** | 3 tentativas, intervalo de 2s |
| **Cache** | MD5 (respostas idênticas não consomem quota) |

> **Nota:** Consulte também a [documentação principal (README.md)](../README.md) para instruções de configuração inicial das chaves de API.
