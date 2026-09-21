# Glossário — `gitpr split`

> Vocabulário canônico da feature `gitpr split` (transformar uma árvore de trabalho mista em commits atômicos).
> Mantido junto da [spec](20260918_skill_gitpr_split_command_spec.md); os desvios aprovados vivem no [ADR-006](ADR-006-split-apply-safety.md).

## Termos de domínio

| Termo | Definição |
|---|---|
| **hunk** | Um bloco `@@` de um arquivo no diff unificado. É a **unidade de divisão**: o caso que a feature existe para resolver é um único arquivo com dois hunks pertencendo a preocupações diferentes, então dividir por arquivo não bastaria. |
| **unidade (change unit)** | O que um grupo contém. `ChangeUnit = Hunk \| OpaqueSection`, um alias de união PEP 604 — não uma ABC: os dois membros não compartilham comportamento, então herança não diria nada verdadeiro. O despacho é por `isinstance`, e só onde importa. |
| **opaque section** | Uma seção do diff **sem hunks** — binário, renomeação pura, mudança apenas de modo, arquivo vazio, seção ilegível — guardada inteira e literal. Não é divisível, então vira um grupo atômico de uma unidade e **nunca vai à IA**: não há decisão de agrupamento a pedir, e uma unidade que o modelo não consegue expressar é uma unidade para a qual ele inventa um id. |
| **id da unidade** | `0007-1a2b3c4d` — a posição ordinal na travessia mais os 8 primeiros dígitos hex do MD5 de `file_path + hunk_header + content`. As duas metades são necessárias: a posição é determinística (a travessia é fixada pelo texto do diff) e o hash separa dois arquivos alterados de forma idêntica — uma cópia vendorizada e o original têm o mesmo cabeçalho e o mesmo corpo e diferem só no caminho. |
| **ordinal** | A posição da unidade na travessia original, 0-based. Decide a ordem de reemissão: `build_patch` ordena por ele, porque um patch com hunks fora de ordem crescente aplica nos deslocamentos errados. |
| **file header** | O bloco `diff --git` que precede os hunks de um arquivo (linha `index`, linhas de modo, `---`/`+++`). É **guardado, nunca reconstruído**: `new file mode`, `deleted file mode`, `old mode`/`new mode` e a forma citada do git para caminhos com espaços ou bytes não-ASCII são irrecuperáveis a partir de um caminho, e sintetizá-los produz um patch que o git recusa. |
| **fronteira de hunk** | Onde um hunk termina. Decidida por **contagem** — o hunk acaba quando as contagens declaradas no seu cabeçalho se esgotam, nunca no próximo `@@`. Dentro de um hunk, `--- algo` e `+++ algo` na coluna 0 são indistinguíveis de um par de cabeçalhos, enquanto a linha de contexto sempre carrega o espaço inicial; contar é a única regra correta. A contagem também é o validador: uma seção cujas contagens não fecham degrada **inteira** para uma opaque section, nunca para uma lista parcial de hunks. |
| **grupo (`HunkGroup`)** | Um commit atômico proposto: as unidades que ele estagia, o rótulo de intenção e a justificativa. O `group_id` (`G1`, `G2`, …) é atribuído **pelo gitpr**, na ordem em que o modelo devolveu os grupos — nunca pelo modelo. |
| **plano (`SplitPlan`)** | A proposta inteira: os grupos em ordem, a lista explícita do que ficou de fora (`ungrouped_units`) e os avisos. É o entregável do modo padrão. |
| **ungrouped units** | O resto explícito: unidades que o modelo não classificou, unidades cujo grupo teve de ser abandonado, unidades cortadas por orçamento. Nunca são descartadas em silêncio e nunca são commitadas — ao fim de um `--apply` continuam não commitadas na árvore de trabalho. |
| **split diff** | O diff da feature: `git diff --binary -M -U3 HEAD`. **Não** é o `get_git_diff()` dos outros fluxos (ver ADR-006). |
| **capturar primeiro, desestagiar depois** | A ordem fixa do `--apply`. O diff é lido **com** o índice no estado em que estiver, porque um arquivo novo estagiado só aparece em `git diff HEAD` porque o índice o rastreia — desestagiar antes o tornaria não rastreado, fora de escopo, e o tiraria do plano. Tudo é desestagiado imediatamente antes do primeiro `git apply --cached`. É sólido porque todo hunk de um `git diff HEAD` carrega pré-imagem tirada de HEAD, qualquer que seja o estado do índice; depois da desestagiação o índice **é** HEAD. |
| **índice em HEAD** | O índice após `git read-tree HEAD`, usado na pré-validação. A pré-validação roda contra um índice limpo em arquivo temporário (`GIT_INDEX_FILE`), para que construir um plano não toque no índice do usuário — é isso que faz o critério "construir um plano não escreve nada" ser verificável. |
| **staging seletivo** | Escrever no índice menos do que um arquivo: `git apply --cached` de um patch reconstruído. Capacidade **nova** — antes desta feature a única escrita de índice no projeto era `git add` em nível de arquivo. Passa pelo mesmo `patch_applier` do `gitpr fix`, herdando a defesa de CRLF que entrega o patch como **bytes na entrada padrão**. |
| **pré-validação de conflito** | Antes de o plano ser mostrado, cada grupo passa por `git apply --cached --check` contra um índice em HEAD. Um conflito real fora de um diff `-U3` é raro: o git funde alterações a menos de sete linhas de distância, deixando três linhas de contexto intocado entre os hunks emitidos, então qualquer subconjunto aplica limpo. As duas recusas genuínas são incompatibilidade de fim de linha e hunks sobrepostos. |
| **absorção de arquivo inteiro** | A resposta a um grupo recusado: todas as unidades de todos os arquivos que o grupo toca — de todos os grupos e das ungrouped — fundem-se nele, e a mensagem de commit é **regerada** para o patch fundido, porque uma mensagem descrevendo um subgrupo seria mentira sobre o commit que ela rotula. |
| **fallback terminal** | Quando forçar arquivos inteiros ainda falha (arquivo CRLF, unidade binária), as unidades vão para `ungrouped_units` com um aviso. O laço é limitado e sempre termina; nada é descartado e nada é meio-aplicado. |
| **orçamento (budget)** | `GITPR_SPLIT_MAX_HUNKS` — quantas unidades vão à chamada de agrupamento. O excedente vai para as ungrouped com um aviso nomeando os ids. O corte é **maiores primeiro**, não os N primeiros: cortar na ordem dos arquivos deixaria sistematicamente os últimos arquivos do diff sem análise. |
| **chamada de agrupamento** | A única chamada de IA que decide o plano, **sem lotes**. Lotes são a forma óbvia de cobrir um diff grande e são errados aqui: hunks de uma preocupação em lados opostos de uma fronteira de lote nunca se reúnem, porque nenhum lote vê os hunks do outro — e o modelo então responde com confiança sobre a metade que enxerga. |
| **commit atômico** | Um commit que contém toda alteração de que uma preocupação precisa e nenhuma alteração de outra. |
| **garantia byte a byte** | A promessa central do comando: os arquivos em disco ao fim são idênticos aos arquivos em disco no início. O split redistribui o trabalho entre commits; nunca o altera. É essa garantia que proíbe o `-w` (ver ADR-006). |

## Chaves de configuração (dotenv plano, `~/.gitpr/.env`)

| Chave | Significado |
|---|---|
| `GITPR_SPLIT_MAX_GROUPS` | Teto de commits que um plano pode propor (default `5`). Sem ele, um diff com vinte preocupações pequenas volta como vinte commits — uma história pior do que a que o usuário tinha. |
| `GITPR_SPLIT_MAX_HUNKS` | Teto de unidades enviadas à chamada de agrupamento (default `50`). |
| `GITPR_SPLIT_REQUIRE_CONFIRMATION` | Pede confirmação antes do primeiro commit (default `true`). Vale para `--apply`: sem flag alguma a pergunta **é** o comando e é sempre feita. |

Um valor não positivo ou não interpretável volta ao default em vez de ser honrado: um teto de zero transformaria "divida isto" em "não divida nada" em silêncio, em vez de em um erro visível.

## Notas de fidelidade

- **Não existe parser de hunk no projeto.** A spec §0.1 supunha reusar o do motor map-reduce; ele não existe. O map-reduce divide por **arquivo** (`re.split(r"(^diff --git a/)", …)`) e `_HUNK_HEADER_RE` captura só o início/contagem do lado novo e é carga útil de `summarize_patch` — não pode ser alargado. `hunk_parser.py` é código novo.
- **Não existia staging seletivo.** A spec §5 mandava confirmar; confirmado: nenhum `--cached`, `update-index`, `add -p` ou `git reset` em `src/` antes desta feature.
- **O pipeline de mensagem é reusado de verdade.** `generate_pr_content("commit", "commit", patch)` recebe uma string de diff e devolve `{"commit_message": …}`, trazendo skill, cache MD5 e map-reduce. Nota de campo: o **primeiro parâmetro é morto** — é sobrescrito por `action_folder_map.get(action_type, "misc")` — por isso os chamadores passam `("commit", "commit", …)`.
- **Sem skill template.** `get_skill_context()` responde a um tipo não registrado com a skill de *review* (`DEFAULT_SKILL_TYPE = "review"`), então `.gitpr.split.md` entregaria ao prompt de agrupamento uma persona de revisão de código. Registrá-lo de verdade custaria `SKILL_FILES_BY_TYPE`, a lista de rótulos de ordem verificada, um recurso MCP e templates por idioma. A instrução fica embutida em `hunk_grouper.py`.
- **CRLF é recusado alto, não corrompido.** A captura com `text=True` mais o `rstrip("\r")` do `split_patch_sections` tira os CRs, então `--check` recusa esses arquivos. É falha barulhenta e nunca aplicação corrupta; documentado e coberto por teste de regressão.
- **Sem rollback.** Ao contrário do `gitpr fix` — cujo patch não tem commit para resetar, e por isso tem `--rollback` — o resultado do split são commits comuns, e `git reset` é a ferramenta que o usuário já tem. Uma falha no meio da sequência **para**, não desfaz: os commits já criados são reais e permanecem.
