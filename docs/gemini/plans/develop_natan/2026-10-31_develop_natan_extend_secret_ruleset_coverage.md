# Implementation Plan — Estender a Cobertura do Ruleset de Segredos

- **Data:** 2026-10-31
- **Branch:** develop_natan
- **Status:** Proposto

## 1. Contexto e Objetivos

O ruleset de secret scanning do GitPR (`src/security_ruleset.py`) foi introduzido no ADR-007 como um conjunto de 7 regras embutidas no pacote (`sec-*`), cobrindo padrões canônicos sob os níveis `error` (bloqueante) e `warning` (informativo).

Três lacunas ficaram abertas para extensão:
1. **Atribuição sem aspas (`API_KEY=abc12345`)**: muito frequente em arquivos `.env`, scripts shell, Dockerfile e properties.
2. **Prefixos de credenciais específicas (`ASIA…`, `github_pat_…`, `xoxc-` e `xoxd-`)**:
   - `ASIA…`: AWS STS Temporary Access Keys (16 caracteres alfanuméricos maiúsculos após o prefixo).
   - `github_pat_…`: GitHub Fine-Grained Personal Access Tokens (82+ caracteres).
   - `xoxc-` e `xoxd-`: Slack client user tokens e cookies/session tokens.
3. **Ausência de fronteira à esquerda no nome da chave**: em `sec-generic-credential-assignment`, a ausência de boundary permitia que palavras terminadas com as chaves (ex.: `bypassword`, `antisensha`) gerassem falsos alertas.

Adicionalmente, conforme a disciplina de Domain Modeling, atualizaremos `CONTEXT.md` com os termos canônicos de segurança e registraremos o **ADR-0008**.

---

## 2. Decisões Arquiteturais

1. **Fronteira à esquerda no nome da chave**:
   Utilizar lookbehind negativo para caracteres alfanuméricos `(?<![a-zA-Z0-9])`. Isso impede correspondências espúrias em palavras contíguas (`bypassword`, `antisenha`), preservando o suporte a prefixos em snake_case ou kebab-case (`db_password`, `user_token`, `APP_SECRET`, `api-key`).

2. **Atribuição sem aspas**:
   Unificar o regex de `sec-generic-credential-assignment` suportando valores com aspas (`['\"]...['\"]`) e valores não cotados (`[^\s'"#;,]{6,}`). No ramo não cotado, aplicamos lookahead negativo para descartar falsos positivos de variáveis e chamadas de runtime (`$VAR`, `${VAR}`, `os.getenv`, `process.env`, `env(`, `null`, `None`, `true`, `false`) além dos placeholders canônicos (`changeme`, `dummy`, `example`, etc.).

3. **Prefixos específicos**:
   Estender as regras canônicas existentes in-place, preservando a namespace e a severidade `error`:
   - `sec-aws-access-key`: `(?<![A-Z0-9])(?:AKIA|ASIA)[0-9A-Z]{16}`
   - `sec-github-token`: `(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{82,})`
   - `sec-slack-token`: `xox[baprscd]-[A-Za-z0-9-]{10,}`

4. **Taxonomia e Localização**:
   - Criar `docs/adr/0008-secret-ruleset-coverage-extension.md` registrando a decisão e suas alternativas.
   - Atualizar `CONTEXT.md` com o vocabulário canônico do ruleset de segurança embutido.

---

## 3. Arquivos Envolvidos

| Arquivo | Mudança | Descrição |
|---|---|---|
| `CONTEXT.md` | MODIFICADO | Adição do termo canônico *Embedded security ruleset* |
| `docs/adr/0008-secret-ruleset-coverage-extension.md` | NOVO | ADR registrando a decisão arquitetural da extensão |
| `src/security_ruleset.py` | MODIFICADO | Atualização dos regexes das 4 regras |
| `tests/test_security_ruleset.py` | MODIFICADO | Casos de teste para novos positivos, quase-acertos e evasão de falsos positivos |

---

## 4. Plano de Verificação

### Testes Automatizados
```bash
python -m pytest tests/test_security_ruleset.py -v
python -m pytest tests/test_linter_metrics.py tests/test_i18n.py -v
```

### Verificação Manual
Testar via engine de linter do GitPR diffs sintéticos com:
- `API_KEY=abc12345` (detectado como warning)
- `db_password = "hunter2xyz"` (detectado como warning)
- `bypassword = "hunter2xyz"` (ignorado)
- `API_KEY = $ENV_VAR` (ignorado)
- `k = ASIAIOSFODNN7EXAMPLE` (detectado como error)
- `k = github_pat_11A...` (detectado como error)
- `k = xoxc-123456789012-abcdefghijklmnop` (detectado como error)
