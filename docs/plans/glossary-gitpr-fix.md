# Glossário — `gitpr fix`

> Vocabulário canônico da feature `gitpr fix` (transformar apontamentos de review em patches revisáveis).
> Mantido junto da [spec](20260913_skill_gitpr_fix_command_spec.md) e do [plano](20260913_skill_gitpr_fix_command_plan.md); a lista de desvios aprovados vive no [ADR-004](ADR-004-fix-subcommand-package.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **review** | A saída de `gitpr -r` (`review`) ou `gitpr -f` (`fullreview`), guardada como registro de cache em `~/.gitpr/cache/prompts/review/`. É a **fonte do texto**, nunca do diff: o diff é re-derivado na hora (ver *reviewed diff*). |
| **finding (apontamento)** | Um problema que o review levantou, normalizado pela chamada de IA do `fix` no formato `FindingRef` (`id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`). O `id` (`FIX-001`, `FIX-002`, …) é atribuído **pelo gitpr**, na ordem em que os findings voltaram — nunca pelo modelo. |
| **candidate (candidato)** | `PatchCandidate` = um finding + o patch que o corrige + a classificação + a proveniência. É a unidade que a listagem mostra, o dry run imprime e o `--apply` escreve. Um finding sem patch utilizável **também** vira candidato, com `diff` vazio e classe `experimental`. |
| **patch** | O diff unificado mínimo que corrige um finding. É a **fonte de verdade sobre onde aplica**: o `file_path` do finding só é usado como fallback quando não há patch. |
| **patch_id** | `FIX-001-1a2b3c4d` — o `finding_id` mais os 8 primeiros dígitos hex do MD5 do diff. Derivado, nunca armazenado como fonte: é o endereço que o `--rollback` aceita. |
| **safety class** | Selo de confiança do patch: `safe` (um arquivo, um hunk, poucas linhas, fora dos caminhos sensíveis, não remove chamada), `review_required` (aplica, mas falhou algum critério de `safe`) e `experimental` (não aplica nesta árvore, mexe em mais de um arquivo, ou a IA declarou baixa confiança). |
| **reason code** | O motivo da classificação, como string estável (`apply_check_failed`, `multi_file`, `low_confidence`, `excluded_path`, `multiple_hunks`, `too_many_lines`, `removes_call`, `safe`). O classificador devolve **código, nunca frase**; a frase traduzida é da camada de exibição, e o MCP reporta o código porque quem o consome compara strings. |
| **reviewed diff** | O diff atual re-derivado com a **mesma função que produziu o review** (`get_git_diff()` para `review`, `get_git_full_diff()` para `fullreview`), escolhida pelo `action_type` do registro. É o que ancora o patch à árvore de agora, e não à do dia em que o review rodou. |
| **dry run** | O padrão do comando: imprime o diff e a classificação e **não escreve nada** — nem branch, nem histórico. Escrever exige `--apply`. |
| **apply** | Escrever o patch na árvore de trabalho (`git apply`), precedido de `git apply --check`. Um patch não-`safe` nunca é escrito por um `--apply` comum: a única porta é `--force`, que abre com frase digitada (`apply FIX-001`), não com `y/n`. |
| **batch / `--all-safe`** | O conjunto dos candidatos `safe`, selecionado por `select_safe()` — **definição única**, lida tanto pelo subcomando quanto pela tool MCP. Um lote cria branch por padrão (`GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE`); o original fica intacto. |
| **rollback** | Desfazer um patch aplicado com `git apply --reverse` sobre o diff guardado. Não depende de commit, stash nem reset: o patch do `fix` fica **não commitado** de propósito (o humano revisa antes). Recusa em três casos com motivos distintos: nunca aplicado aqui, já revertido, aplicado em outra branch. |
| **fix history** | `.gitpr/fix_history.json`, **rastreado no git**, com uma entrada por patch aplicado (diff completo + proveniência + `rolled_back_at`). Escrito atomicamente (`.tmp` + `os.replace`). Consequência assumida: aplicar um patch suja um arquivo rastreado, então ele aparece em `gitpr -c` e nas descrições de PR — por isso o arquivo está no `smart-excludes`. |
| **provenance** | `PatchProvenance`: provider, modelo, `prompt_version`, `gitpr_version` e `generated_at` da chamada que gerou o patch. Gravada no histórico junto do diff. |
| **sensitive paths** | `GITPR_FIX_SAFE_EXCLUDED_PATHS` — caminhos de **risco** (migrations, workflows, docker, terraform). Um patch que os toca ainda aplica, mas nunca é `safe`. **Não se confunde com smart-excludes**, que é sobre ruído de diff (lockfiles, minificados): conceito diferente, lista diferente, sem reuso. |
| **skill `.gitpr.fix.md`** | Instrução de sistema da chamada de IA que normaliza o review em patches (persona: Senior Software Engineer). Baixada por `gitpr --skill`, ciente do idioma e sem sobrescrever. |

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Significado |
|---|---|
| `GITPR_FIX_SAFE_MAX_LINES_CHANGED` | Teto de linhas (adicionadas + removidas) para um patch ainda ser `safe` (default `5`). |
| `GITPR_FIX_SAFE_EXCLUDED_PATHS` | Caminhos sensíveis separados por `;` (padrões fnmatch). |
| `GITPR_FIX_REQUIRE_CONFIRMATION` | Pede confirmação antes de escrever um patch `safe` (default `true`); `--yes` equivale para uma execução. |
| `GITPR_FIX_CREATE_BRANCH_ON_ALL_SAFE` | `--all-safe --apply` cria branch antes de escrever (default `true`); `--no-branch` desliga numa execução. |
| `GITPR_FIX_BRANCH_NAME_TEMPLATE` | Nome dessa branch (default `fix/gitpr-{datetime}`); placeholders `{branch}` e `{datetime}`. |

## Notas de fidelidade

- **O chat nunca aplicou patch.** A premissa da spec §8 ("gap de segurança: o F5 aplica patches sem revisão") não existe no código: F5 e `ctrl+s` gravam um `.txt` no CWD com blocos cercados, sem `subprocess` e sem diff válido. Por isso `gitpr fix` é **capacidade nova**, e o único reuso real do chat é o extrator de blocos cercados — que agora é compartilhado (`src/fix/patch_extractor.py`), sem mudança de comportamento visível.
- **Os ids são determinísticos pelo cache.** Mesmo review + mesmo diff = mesmo prompt = mesma resposta do cache MD5, então `FIX-001` significa a mesma coisa entre execuções. Rodar `gitpr -r` de novo gera outro review, logo outros findings e outros ids.
- **A classificação é determinística e sem IA**: mesma summary + mesmas configurações = mesmo veredito, então um patch `safe` no dry run continua `safe` no `--apply`.
- **`filereview` fica de fora.** Os três modos de review caem na mesma pasta de cache; `action_type` é o que os separa, e a auditoria de arquivo único (`-i`) não tem diff de branch para corrigir.
- **`--force` tem outro sentido no `release`** ("regerar seção existente"). Namespaces de subcomando não colidem: nenhum flag do `fix` muda o sentido de um flag existente.
- **O literal i18n corrompido `"Ctrlhift+S"`** (`src/ui/chat_app.py`) é bug pré-existente e ficou como estava — fora do escopo desta entrega.
