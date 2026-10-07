# Glossário — `gitpr mentor` (Junior Mentor Mode)

> Vocabulário canônico da feature `gitpr mentor` (explicações didáticas e pedagógicas para findings de code review).
> Mantido junto da [spec](20260926_skill_gitpr_junior_mentor_spec.md) e do plano de implementação; a decisão arquitetural vive no [ADR-009](ADR-009-mentor-domain-package.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **mentor mode** | Modo pedagógico/didático do GitPR que enriquece cada finding de review com explicações acessíveis, focando no "porquê", em analogias e em conceitos para aprendizado contínuo, voltado a desenvolvedores juniores e aprendizes. |
| **mentor explanation** | Objeto estruturado (`MentorExplanation`) contendo: `finding_id`, `what_is_happening`, `why_it_matters`, `analogy` (opcional), `learn_more_pointer` (conceito sem URL), `has_sufficient_evidence` e `markdown`. |
| **finding** | Reutiliza exatamente a entidade `FindingRef` (`id`, `file_path`, `line_start`, `line_end`, `severity`, `category`, `message`) normalizada por `src/fix/apply_fix.py`. Os IDs (`FIX-001`, `FIX-002`, ...) são atribuídos pelo GitPR e permanecem estáveis via cache MD5. |
| **learn_more_pointer** | Ponteiro textual curto indicando um conceito de engenharia, princípio (SOLID, DRY, etc.) ou padrão arquitetural. **Nunca** deve conter links externos ou URLs completas. |
| **evidence flag** | Indicador booleano (`has_sufficient_evidence`). Quando `False`, indica que o diff não continha evidências suficientes para inferir o porquê com segurança; o texto é preenchido com mensagem padrão de honestidade epistêmica. |
| **mentor run** | Resultado da execução em lote (`MentorRun`), contendo a tupla de explicações geradas, tupla de IDs pulados por estouro de teto (`skipped_ids`) e o Markdown formatado. |
| **cap (teto)** | Limite de segurança de 10 findings explicados por execução em lote (`MAX_FINDINGS_PER_RUN = 10`), priorizados por severidade (`blocker`/`critical`/`high` primeiro). Findings adicionais são listados para consulta individual via `gitpr mentor --finding <id>`. |

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Significado |
|---|---|
| `GITPR_REVIEW_MENTOR_MODE` | Ativa o modo mentor automaticamente em todo review (`-r` e `-f`) (default: `false`). Equivalente à flag `--mentor`. |
| `GITPR_MENTOR_INCLUDE_ANALOGY` | Define se a IA deve tentar incluir analogias didáticas nas explicações (default: `true`). Se `false`, o campo `analogy` será sempre nulo. |

## Notas de fidelidade

- **Review original como prosa:** O review de IA padrão do GitPR produz texto em prosa (`data["review"]`). O mentor aproveita a etapa de normalização de candidatos do `gitpr fix` (`collect_candidates`) para extrair findings estáveis sem inventar um segundo sistema de IDs.
- **Modo puramente aditivo:** O mentor nunca substitui ou omite o texto técnico do review ou a mensagem original do finding; ele apenas anexa a seção `## 🎓 Mentor` ao final do arquivo `.txt` gerado por `-r` e `-f`.
- **Comando avulso sem reprocessar:** `gitpr mentor [--finding <id>]` consome o review persistido mais recente (`resolve_review()`), operando diretamente no terminal sem gerar arquivos no disco.

