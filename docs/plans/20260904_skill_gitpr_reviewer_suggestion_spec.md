# SPEC — GitPR Suggested Reviewers (via blame_engine.py)

> Documento de especificação técnica para implementação via Claude Code skill.
> Escopo: sugerir automaticamente quem deveria revisar um PR, com base em quem mais tocou as linhas alteradas — reaproveitando o motor de blame já existente (`blame_engine.py`, hoje usado para classificação ORIGIN vs REFACTORING na arqueologia de código).

## 0. Contexto obrigatório antes de codificar

Antes de gerar qualquer código, a skill DEVE:

1. Ler `blame_engine.py` na íntegra e extrair: (a) a assinatura exata das funções/classes já existentes, (b) o formato de saída hoje usado para classificar ORIGIN vs REFACTORING, (c) como o motor já invoca `git blame` (via subprocess, via `GitPython`, via `pygit2`, ou outra lib) e se já existe cache/paralelização para arquivos grandes.
2. Verificar se este projeto já implementou a abstração `ScmProvider` (spec anterior "GitPR Multi-Forge"). Se sim, esta feature DEVE consumir reviewers via essa interface. Se a abstração ainda não foi implementada, a skill deve integrar diretamente com `github_api.py` nesta fase, mas isolando a chamada de rede em um único ponto para facilitar migração futura.
3. Confirmar como `core.py` hoje monta o payload de criação de PR (função/método exato, onde estão `title`, `body`, `head`, `base`) para saber onde encaixar a lista de reviewers sugeridos.
4. Verificar se o PR Publisher (TUI Textual) já tem alguma seção de metadados de PR (labels, assignees) onde a lista de reviewers sugeridos poderia ser exibida/editável antes da publicação.
5. Confirmar o formato de `.mailmap` ou normalização de identidade de autor já usado no projeto (se houver), para não duplicar reviewers que são a mesma pessoa com e-mails diferentes.

Não prosseguir com a implementação sem completar os passos 1–3.

## 1. Escopo da feature

- **Objetivo:** ao gerar/publicar um PR, calcular e sugerir 1 a N reviewers com base em quem historicamente mais alterou as linhas presentes no diff do PR.
- **Comando/flag novo:** `gitpr pr --suggest-reviewers` (ou equivalente à convenção de flags já usada no projeto) e integração automática no fluxo padrão de `gitpr pr` como um passo opcional exibido antes da publicação.
- **Fora de escopo nesta fase:** aprendizado de máquina/ranqueamento por "qualidade" de review passado, integração com carga de trabalho atual do reviewer (ex.: quantos PRs ele já tem em aberto), CODEOWNERS parsing (pode ser um follow-up, mas não faz parte desta entrega).
- **Compatibilidade:** a feature deve ser 100% opt-in/não-bloqueante — se o cálculo falhar (repo raso, `shallow clone`, sem histórico suficiente), o fluxo de criação de PR deve continuar normalmente, apenas sem sugestão, com aviso não-fatal.

## 2. Árvore de arquivos a criar/alterar

```
src/domain/review/
├── reviewer_suggestion.py     # NOVO — lógica pura de scoring e ranking

src/infrastructure/git/
└── blame_engine.py            # ALTERAR — expor função reutilizável de blame por hunk/linha

src/application/use_cases/
└── suggest_reviewers.py       # NOVO — orquestra: diff -> blame -> scoring -> normalização de identidade -> resultado

core.py                        # ALTERAR — chamar suggest_reviewers no fluxo de gitpr pr
src/ui/pr_publisher/*          # ALTERAR — exibir reviewers sugeridos na TUI, permitir editar/remover antes de publicar
main.py (ou entrypoint CLI)    # ALTERAR — nova flag --suggest-reviewers / --no-suggest-reviewers

tests/domain/review/
└── test_reviewer_suggestion.py   # NOVO
tests/application/use_cases/
└── test_suggest_reviewers.py     # NOVO
```

## 3. Contrato de dados (obrigatório)

```python
# src/domain/review/reviewer_suggestion.py
from dataclasses import dataclass


@dataclass
class BlameHit:
    """Uma linha do diff atribuída a um autor via git blame."""
    file_path: str
    line_number: int
    author_name: str
    author_email: str
    commit_hash: str
    commit_date: str  # ISO 8601


@dataclass
class ReviewerCandidate:
    author_name: str
    author_email: str
    touched_lines: int          # quantas linhas do diff atual essa pessoa "possui" via blame
    touched_files: int          # em quantos arquivos distintos do diff ela aparece
    last_touch_date: str        # data do toque mais recente entre os hits, ISO 8601
    score: float                # pontuação final normalizada (0.0 a 1.0)


@dataclass
class ReviewerSuggestionResult:
    candidates: list[ReviewerCandidate]   # ordenado por score desc
    excluded_pr_author: bool              # True se o autor do PR foi removido da lista
    warnings: list[str]                   # ex.: "arquivo X sem histórico de blame suficiente"
```

## 4. Algoritmo de scoring

A skill deve implementar o seguinte pipeline, nesta ordem:

1. **Obter o diff do PR/branch** (linhas adicionadas E removidas/contexto modificado), reaproveitando o motor de diff já usado pelo review de IA (map-reduce/smart excludes) — não duplicar lógica de obtenção de diff.
2. **Para cada arquivo alterado**, rodar `git blame` nas linhas que fazem parte do hunk modificado (usar `git blame -L <start>,<end> --line-porcelain <file>` ou equivalente via a lib já usada no projeto), extraindo autor, e-mail, commit e data por linha.
3. **Agregar por autor normalizado.** Normalizar identidade por e-mail (case-insensitive) como chave primária; se o projeto já tiver `.mailmap` ou lógica de unificação de identidade, usá-la aqui em vez de reimplementar.
4. **Calcular score por candidato** combinando três sinais, com pesos configuráveis (default sugerido entre parênteses):
   - `touched_lines` normalizado pelo total de linhas do diff (peso 0.5) — quem tocou mais linhas relevantes tem prioridade.
   - `touched_files` normalizado pelo total de arquivos do diff (peso 0.3) — recompensa quem conhece o PR como um todo, não só um arquivo.
   - Recência do `last_touch_date` (peso 0.2) — decaimento simples (ex.: `1 / (1 + dias_desde_ultimo_toque / 90)`) para priorizar quem tocou o código recentemente sobre quem tocou há anos.
5. **Excluir automaticamente o autor do próprio PR** da lista de candidatos (comparar e-mail normalizado do commit atual/branch com os candidatos).
6. **Excluir bots** conhecidos (heurística: e-mail contendo `noreply`, `bot@`, `[bot]` no nome, ou lista configurável em `.gitpr/config.yml`).
7. **Ordenar por score desc** e truncar para top N (default configurável, sugestão inicial: 3).
8. **Gerar warnings não-fatais** quando: arquivo novo sem histórico de blame, arquivo binário (pular blame), ou repositório com histórico raso (`shallow clone` detectado) — nesses casos, reduzir confiança do resultado mas não falhar o comando.

```python
# src/application/use_cases/suggest_reviewers.py
from src.domain.review.reviewer_suggestion import ReviewerSuggestionResult

DEFAULT_WEIGHTS = {"lines": 0.5, "files": 0.3, "recency": 0.2}
DEFAULT_TOP_N = 3
DEFAULT_RECENCY_HALFLIFE_DAYS = 90

def suggest_reviewers(
    diff_files: list[str],
    diff_hunks: dict[str, list[tuple[int, int]]],  # file -> [(start, end), ...]
    pr_author_email: str,
    repo_path: str,
    top_n: int = DEFAULT_TOP_N,
    weights: dict = None,
    excluded_authors: list[str] = None,
) -> ReviewerSuggestionResult:
    ...
```

## 5. Integração com `blame_engine.py`

Requisito: `blame_engine.py` já existe e resolve blame para a feature de arqueologia (classificação ORIGIN/REFACTORING). Esta spec assume que ele expõe (ou deve ser refatorado para expor) uma função de nível mais baixo e reutilizável, do tipo:

```python
# blame_engine.py — função a expor/confirmar existência
def get_blame_for_range(file_path: str, line_start: int, line_end: int, repo_path: str) -> list[BlameHit]:
    """
    Executa git blame apenas no intervalo de linhas informado.
    Deve retornar lista vazia (não lançar exceção) se o arquivo for novo,
    binário, ou fora do repositório rastreado.
    """
```

Se essa função de granularidade fina (por intervalo de linhas) não existir hoje — por exemplo, se o motor atual só faz blame de arquivo inteiro para a arqueologia — a skill deve adicionar esse método sem quebrar a função existente usada por ORIGIN/REFACTORING. Preferir extração de um método privado comum reutilizado pelas duas funcionalidades, em vez de duplicar a lógica de parsing do `git blame --line-porcelain`.

## 6. Ponto de integração em `core.py` e na TUI

Fluxo alvo:

```python
# core.py, dentro do fluxo de gitpr pr
if config.get("suggest_reviewers", True):
    result = suggest_reviewers(
        diff_files=changed_files,
        diff_hunks=hunks_by_file,
        pr_author_email=current_git_user_email,
        repo_path=repo_root,
        top_n=config.get("reviewer_suggestion_top_n", 3),
    )
    for w in result.warnings:
        log.info(w)  # não-fatal
    pr_draft.suggested_reviewers = [c.author_email for c in result.candidates]
```

Na TUI do PR Publisher: exibir a lista de reviewers sugeridos (nome + score/justificativa curta, ex.: "42% das linhas alteradas, tocou há 5 dias") em uma seção editável — o usuário pode remover, adicionar manualmente, ou aceitar antes de publicar. Ao publicar, se o `ScmProvider`/`github_api.py` suportar `reviewers` no payload de criação de PR (GitHub sim, via campo separado de "request reviewers"; confirmar suporte por provider), enviar a lista escolhida.

## 7. Config

Adicionar ao schema de config existente:

```yaml
review:
  suggest_reviewers: true          # opt-out global
  reviewer_suggestion_top_n: 3
  reviewer_suggestion_weights:
    lines: 0.5
    files: 0.3
    recency: 0.2
  reviewer_suggestion_excluded_authors:
    - "dependabot[bot]"
    - "ci-bot@empresa.com"
```

## 8. Testes obrigatórios (critério de aceite)

1. **Teste unitário de scoring puro** (`test_reviewer_suggestion.py`): dado um conjunto fixo de `BlameHit`, validar que o ranking resultante corresponde ao cálculo manual esperado para pesos default e para pesos customizados.
2. **Teste de exclusão do autor do PR**: candidato com e-mail igual ao `pr_author_email` nunca aparece no resultado, mesmo sendo o maior "owner" das linhas.
3. **Teste de exclusão de bots**: e-mails/nomes na lista de exclusão (default + customizada via config) nunca aparecem no resultado.
4. **Teste de arquivo novo/sem histórico**: `get_blame_for_range` retornando lista vazia para um arquivo não deve derrubar o cálculo geral — apenas gerar warning e seguir com os demais arquivos.
5. **Teste de repositório raso (shallow clone)**: simular blame incompleto e confirmar que o comando não lança exceção, apenas reduz confiança/gera warning.
6. **Teste de integração do use case** (`test_suggest_reviewers.py`) com repositório git real de fixture (criar commits de teste com autores diferentes tocando linhas específicas) — validar ranking de ponta a ponta sem mocks de git.
7. **Teste de não-regressão da arqueologia**: se `blame_engine.py` for alterado para expor a nova função, os testes existentes de classificação ORIGIN/REFACTORING devem continuar passando sem alteração de comportamento.

Critério de "feature completa": todos os testes acima passam, e o fluxo padrão de `gitpr pr` continua funcionando normalmente quando `suggest_reviewers: false` ou quando o cálculo falha silenciosamente (modo degradado).

## 9. Ordem de execução recomendada

1. Inspecionar `blame_engine.py` e confirmar/adicionar `get_blame_for_range` sem alterar comportamento da arqueologia existente. Rodar testes de arqueologia para garantir zero regressão antes de seguir.
2. Implementar `reviewer_suggestion.py` (scoring puro, sem I/O) com testes unitários isolados — esta camada não deve tocar em git nem em rede.
3. Implementar `suggest_reviewers.py` (use case) conectando diff real + blame real, com fixture de repositório git de teste.
4. Integrar em `core.py` no fluxo de `gitpr pr`, atrás de flag opt-out, validando manualmente em um repositório real com histórico de múltiplos autores.
5. Integrar na TUI do PR Publisher (exibição + edição da lista antes de publicar).
6. Conectar ao envio de reviewers na criação do PR via `github_api.py` (ou `ScmProvider`, se já existir), validando que o campo de reviewers da API é de fato populado no PR criado.
7. Atualizar `config.schema.yml` e documentação (README/CLI help) descrevendo a nova flag e os pesos configuráveis.
8. Rodar suite completa de testes do projeto antes de considerar a feature concluída.

Cada etapa acima deve ser um commit/PR isolado e revisável — não implementar scoring, integração de blame, integração em `core.py` e integração de TUI em um único commit grande.

## 10. Encaixe estratégico (contexto de monetização)

Esta é classificada como Tier 1 (alto impacto, baixo esforço) porque reaproveita 100% da infraestrutura de blame já existente para a arqueologia de código — não exige nova infraestrutura de rede, nova dependência, nem backend. Fica no tier **Free/Community** do modelo de monetização já discutido: é um recurso de produtividade individual que aumenta a percepção de valor imediato ("aha moment") e serve como vitrine para o diferencial competitivo do GitPR (uso inteligente do histórico Git local), sem canibalizar o que futuramente será cobrado no tier Team (sugestão de reviewer agregada por organização, dashboards, etc.).
