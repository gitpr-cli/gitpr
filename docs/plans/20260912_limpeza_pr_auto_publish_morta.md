# Limpeza — `PR_AUTO_PUBLISH` morta + §5 da doc da TUI mentindo

## Context

`PR_AUTO_PUBLISH` apareceu na categoria **Desconhecidas** da tela `gitpr config` e levantou a pergunta legítima: *"ela é responsável por publicar automaticamente um PR, então não deveria estar na seção Pull Request?"*

A investigação provou que **não**. A chave está morta:

- `grep -rni 'auto_publish' src/` → **zero ocorrências**. Não existe em nenhum arquivo do `src/`.
- Ela **não está no `DEFAULT_CONFIG`** — o GitPR atual nem a semeia.
- Está no `~/.gitpr/.env` do usuário (linha 25) porque **uma versão antiga a semeou**. O `setup_environment()` só acrescenta chaves que faltam; nunca remove obsoletas, então a linha é imortal.

A remoção foi **deliberada e planejada**: [docs/plans/20260807_altera_interface_pullrequest_auto_claudecode.md:226](docs/plans/20260807_altera_interface_pullrequest_auto_claudecode.md#L226) §3g diz *"A lógica da env var `PR_AUTO_PUBLISH` deve ser removida já que publicação agora é padrão."* A remoção do código aconteceu. O que sobrou foram **duas mentiras de documentação** e uma linha órfã no `.env`.

**O que substituiu a chave:** a flag `--no-edit` ([src/main.py:1487](src/main.py#L1487) → `_auto_commit_and_publish`, [src/main.py:2219](src/main.py#L2219)). Publicar virou o fluxo padrão; o que se escolhe hoje é *como* — TUI (padrão), `--no-publish` (só o `.md` local) ou `--no-edit` (auto-commit + POST direto). **Nenhuma env var.**

**Resultado pretendido:** a documentação parar de anunciar uma chave que não existe, a §5 da doc da TUI parar de prometer que chaves aparecem fora da tela quando elas aparecem em Desconhecidas, e a linha órfã sair do `.env`.

> **A tela NÃO tem bug.** Desconhecidas é o comportamento projetado — o glossário define que uma chave desconhecida "may belong to a newer GitPR, a plugin, or a shell script of the user's", então a tela a preserva intacta em vez de oferecer remoção. Nada muda em `src/`.

---

## Fatos verificados

| Fato                                       | Como foi verificado                                                                              |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| `PR_AUTO_PUBLISH` não existe em `src/`     | `grep -rni 'auto_publish' src/` → nenhuma ocorrência                                             |
| Não está em `DEFAULT_CONFIG`               | `grep -n 'PR_' src/config.py` — a lista não a inclui                                             |
| Não está no schema                         | `config_schema.py` só tem `PR_DEFAULT_BASE` e `PR_PUBLISH_LOG` como `PR_*`                       |
| Está no `.env` do usuário                  | linha 25: `PR_AUTO_PUBLISH='false'`                                                              |
| `GEMINI.md` **não** a lista                | `grep -c` → 0 ocorrências                                                                        |
| Nenhum `langs/*.json` a menciona           | `grep -rl` → nenhum arquivo                                                                      |
| Nenhum doc de usuário a menciona           | só registros históricos (`claude-code/reports/`, `docs/plans/2026080*`, `docs/survey/`)          |
| Exatamente 3 chaves caem em Desconhecidas  | `GITPR_SCM_TOKEN`, `GITPR_SHOW_LOGS`, `PR_AUTO_PUBLISH` (de 50 no `.env`)                        |
| `remove_config_value()` é a via sancionada | [src/config.py:631](src/config.py#L631), usa `unset_key` (atômico, preserva comentários e ordem) |

---

## Mudanças

### 1. `CLAUDE.md` — linha 294

Remover o token `` `PR_AUTO_PUBLISH`, `` da lista de env vars. É a linha que faz a chave parecer viva — foi ela que sustentou a premissa de que a variável publica PRs. Edição de um token, numa linha.

### 2. `docs/config-tui.md` §5 (linha 129) + as 4 traduções (mesma linha 129)

O título atual promete mais do que entrega. `GITPR_SCM_TOKEN` e `GITPR_SHOW_LOGS` **estão** na tela — read-only, dentro de Desconhecidas. Das três linhas da tabela, só `CI`/`GITHUB_ACTIONS` são de fato invisíveis (não estão no `.env`, então nunca chegam lá).

- **Retítulo** — "Deliberately Not **Editable**" (não "Not in the Screen"):
  | arquivo               | de                                   | para                         |
  | --------------------- | ------------------------------------ | ---------------------------- |
  | `config-tui.md`       | Deliberately Not in the Screen       | Deliberately Not Editable    |
  | `config-tui.pt_br.md` | Deliberadamente Fora da Tela         | Deliberadamente Não Editável |
  | `config-tui.pt_pt.md` | Deliberadamente Fora do Ecrã         | Deliberadamente Não Editável |
  | `config-tui.es_es.md` | Deliberadamente Fuera de la Pantalla | Deliberadamente No Editables |
  | `config-tui.fr_fr.md` | Délibérément Hors de l'Écran         | Délibérément Non Éditables   |

- **Frase de abertura** ligando à §4: a tela nunca esconde uma chave que está no seu arquivo — ela só se recusa a **escrever** numa que não é dela. É por isso que duas das linhas abaixo aparecem em Desconhecidas.
- **Linha nova na tabela**, `PR_AUTO_PUBLISH`: sobra de antes de publicar virar o fluxo padrão. Lida em lugar nenhum — o que a substituiu é a flag `--no-edit`. A linha pode continuar no `.env` de instalações antigas e aparece em Desconhecidas.
- **Ajustar a linha de `CI`/`GITHUB_ACTIONS`**: nunca aparecem porque nunca são escritas neste arquivo (ao contrário das outras duas).

Conteúdo, tabela e numeração das outras seções ficam intactos — a §5 continua com o mesmo papel no documento, só para de mentir.

### 3. `~/.gitpr/.env` — remover a linha órfã

`remove_config_value("PR_AUTO_PUBLISH")` — a função já existente, não um `sed`. Fora do repositório; reversível (basta readicionar a linha).

---

## O que NÃO muda

- **Nenhuma linha de `src/`** — a tela está correta.
- **`DEFAULT_CONFIG`** — a chave já não está lá.
- **Registros históricos** (`docs/claude-code/reports/`, `docs/plans/2026080*`, `docs/survey/20260912_*`) — registram o que era verdade na época; reescrevê-los seria falsificar histórico. O survey de 2026-09-12 já afirma corretamente que a chave não existe em `src/`.
- **`GITPR_SHOW_LOGS`** continua chave morta. Implementar ou remover é uma decisão que não foi tomada — fica fora deste escopo (é dívida registrada).
- **`langs/*.json`** — nenhuma chave de i18n menciona a variável; nada a traduzir.
- **`GEMINI.md`** — verificado, não lista a chave.

---

## Verificação

1. `grep -rn 'PR_AUTO_PUBLISH' CLAUDE.md` → **0** resultado.
2. `grep -n '^## 5\.' docs/config-tui*.md` → as 5 com o título novo, nenhuma ainda dizendo "Fora da Tela"/"Hors de l'Écran".
3. Recálculo de Desconhecidas no `.env` real → sobra `GITPR_SCM_TOKEN` e `GITPR_SHOW_LOGS` (**2**, antes 3):
   ```python
   from src.config_schema import KNOWN_KEYS
   from src.config import read_env_file_values
   print(sorted(k for k in read_env_file_values() if k not in KNOWN_KEYS))
   ```
4. Conferir que os comentários e a ordem do `.env` sobreviveram à remoção (`unset_key` apaga só a linha).
5. Suíte completa: as **6 falhas pré-existentes** continuam iguais, nenhuma nova (é edição de doc, não deve mover nada).
