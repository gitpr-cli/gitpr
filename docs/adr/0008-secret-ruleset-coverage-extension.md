# 0008 — Extensão de Cobertura do Embedded Security Ruleset

- **Status:** Aceito
- **Data:** 2026-10-31
- **Decisores:** Natan Fiuza, Antigravity
- **Contexto:** ADR-007, Grill 2026-10-31, Plano `2026-10-31_develop_natan_extend_secret_ruleset_coverage.md`

## Contexto e Decisão

O ruleset de segurança embutido (`src/security_ruleset.py`) introduzido pelo ADR-007 cobria credenciais com aspas e tokens essenciais, mas apresentava três lacunas práticas: atribuições sem aspas em arquivos `.env`/shell (`API_KEY=abc12345`), ausência de tokens temporários da AWS (`ASIA…`), tokens fine-grained do GitHub (`github_pat_…`), tokens de cliente/sessão do Slack (`xoxc-`/`xoxd-`), e falsos positivos causados pela ausência de fronteira à esquerda no nome da chave de atribuição genérica.

Decidimos estender as 7 regras canônicas in-place:
1. Em `sec-generic-credential-assignment`, adicionar lookbehind negativo `(?<![a-zA-Z0-9])` antes dos nomes de chave, garantindo que palavras contíguas (`bypassword`) sejam ignoradas enquanto identificadores em snake_case ou kebab-case (`db_password`, `user_token`, `api-key`) continuem sendo inspecionados.
2. Suportar atribuições sem aspas (`[^\s'"#;,]{6,}`) aplicando filtros negativos contra variáveis e expressões de runtime (`$VAR`, `${VAR}`, `os.getenv`, `process.env`, `env(`, `null`, `None`, `true`, `false`) e placeholders comuns.
3. Incorporar `ASIA` em `sec-aws-access-key` com fronteira alfanumérica à esquerda `(?<![A-Z0-9])`, `github_pat_` em `sec-github-token`, e `xoxc-`/`xoxd-` em `sec-slack-token`, preservando o nível bloqueante `error`.

## Opções Consideradas

- **Criar novas regras separadas (`sec-aws-temporary-key`, etc.):** Rejeitado porque fragmenta o catálogo e inflaciona chaves de i18n sem benefício comportamental — um token vazado do mesmo provedor exige a mesma resposta operacional do desenvolvedor.
- **Usar fronteira `\b` estrita em chaves genéricas:** Rejeitado porque `\b` em Python regex não dispara após `_`, o que desabilitaria a checagem em `db_password`, `api_key` e `auth_token`.
- **Inspeção desregulada de valores sem aspas:** Rejeitado porque atribuir variáveis (`KEY = os.getenv(...)`) ou booleans (`password = false`) geraria falso-positivo imediato no dia a dia.

## Consequências

- Commits com tokens temporários da AWS (`ASIA`), PATs do GitHub (`github_pat_`) e sessões do Slack (`xoxc`/`xoxd`) passam a ser bloqueados no `pre-commit` e `gitpr -l`.
- Arquivos `.env` e scripts shell sem aspas em chaves de API passam a emitir warning informativo, sem falso positivo em declarações dinâmicas de código.
